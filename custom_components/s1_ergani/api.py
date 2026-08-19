from __future__ import annotations

import logging

import aiohttp

from homeassistant.util import dt as dt_util

from .const import (
    APP_ID,
    PUBLIC_IP_FALLBACK,
    PUBLIC_IP_URL,
    SOTYPE_CHECK_IN,
    SOTYPE_CHECK_OUT,
)

_LOGGER = logging.getLogger(__name__)


class S1ErganiApiError(Exception):
    """Base exception for S1 Ergani API errors."""


class S1ErganiApi:
    """Client for the S1 Ergani API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        server: str,
        username: str,
        password: str,
        afm: str,
        device_id: str,
    ) -> None:
        self.session = session
        self.server = server
        self.username = username
        self.password = password
        self.afm = afm
        self.device_id = device_id

        self.login_client_id: str | None = None
        self.client_id: str | None = None

    @property
    def base_url(self) -> str:
        """Return the base URL."""
        return f"https://{self.server}.oncloud.gr"

    @property
    def login_url(self) -> str:
        """Return login/authenticate URL."""
        return f"{self.base_url}/s1services"

    @property
    def checkinout_url(self) -> str:
        """Return check-in/out URL."""
        return (
            f"{self.base_url}"
            "/s1services/js/s1erganicheckinout/checkInOut"
        )

    async def _get_public_ip(self) -> str:
        """Get the public IP address used by the Home Assistant host."""

        try:
            timeout = aiohttp.ClientTimeout(total=5)

            async with self.session.get(
                PUBLIC_IP_URL,
                timeout=timeout,
            ) as response:
                response.raise_for_status()
                data = await response.json()

            public_ip = data.get("ip")

            if not public_ip:
                raise ValueError(
                    "ipify response does not contain 'ip'"
                )

            _LOGGER.info(
                "S1 Ergani: detected public IP %s",
                public_ip,
            )

            return str(public_ip)

        except Exception as err:
            _LOGGER.warning(
                "S1 Ergani: unable to determine public IP: %s. "
                "Using fallback IP %s",
                err,
                PUBLIC_IP_FALLBACK,
            )

            return PUBLIC_IP_FALLBACK

    async def login(self) -> dict:
        """Perform login."""

        payload = {
            "service": "login",
            "username": self.username,
            "password": self.password,
            "appId": APP_ID,
        }

        try:
            async with self.session.post(
                self.login_url,
                json=payload,
            ) as response:
                response.raise_for_status()
                data = await response.json()

        except (aiohttp.ClientError, TimeoutError) as err:
            raise S1ErganiApiError(
                f"Login connection failed: {err}"
            ) from err

        if not data.get("success"):
            raise S1ErganiApiError(
                data.get(
                    "error",
                    "Login failed",
                )
            )

        client_id = data.get("clientID")

        if not client_id:
            raise S1ErganiApiError(
                "Login response does not contain clientID"
            )

        self.login_client_id = str(client_id)

        return data

    async def authenticate(
        self,
        login_data: dict,
    ) -> str:
        """Perform authentication using login response."""

        objs = login_data.get("objs")

        if not objs:
            raise S1ErganiApiError(
                "Login response does not contain objs"
            )

        company_data = objs[0]

        required_fields = (
            "COMPANY",
            "BRANCH",
            "MODULE",
            "REFID",
        )

        missing_fields = [
            field
            for field in required_fields
            if field not in company_data
        ]

        if missing_fields:
            raise S1ErganiApiError(
                "Login response is missing: "
                + ", ".join(missing_fields)
            )

        payload = {
            "service": "authenticate",
            "clientID": login_data["clientID"],
            "COMPANY": company_data["COMPANY"],
            "BRANCH": company_data["BRANCH"],
            "MODULE": company_data["MODULE"],
            "REFID": company_data["REFID"],
        }

        try:
            async with self.session.post(
                self.login_url,
                json=payload,
            ) as response:
                response.raise_for_status()
                data = await response.json()

        except (aiohttp.ClientError, TimeoutError) as err:
            raise S1ErganiApiError(
                f"Authentication connection failed: {err}"
            ) from err

        if not data.get("success"):
            raise S1ErganiApiError(
                data.get(
                    "error",
                    "Authentication failed",
                )
            )

        client_id = data.get("clientID")

        if not client_id:
            raise S1ErganiApiError(
                "Authenticate response does not contain clientID"
            )

        self.client_id = str(client_id)

        return self.client_id

    async def _authenticate(self) -> str:
        """Perform login and authentication."""

        login_data = await self.login()

        return await self.authenticate(login_data)

    async def check(
        self,
        sotype: str,
    ) -> dict:
        """Perform check-in or check-out."""

        if sotype not in (
            SOTYPE_CHECK_IN,
            SOTYPE_CHECK_OUT,
        ):
            raise S1ErganiApiError(
                f"Invalid SOTYPE: {sotype}"
            )

        client_id = await self._authenticate()

        current_time = dt_util.now().strftime(
            "%Y-%m-%d %H:%M"
        )

        public_ip = await self._get_public_ip()

        payload = {
            "clientId": client_id,
            "TRNDATE": current_time,
            "AFM": self.afm,
            "SOTYPE": sotype,
            "IPADDRESS": public_ip,
            "DEVICEID": self.device_id,
        }

        action_name = (
            "CHECK-IN"
            if sotype == SOTYPE_CHECK_IN
            else "CHECK-OUT"
        )

        _LOGGER.info(
            "S1 Ergani %s request: IPADDRESS=%s DEVICEID=%s TRNDATE=%s",
            action_name,
            public_ip,
            self.device_id,
            current_time,
        )

        try:
            async with self.session.post(
                self.checkinout_url,
                json=payload,
            ) as response:
                response.raise_for_status()
                data = await response.json()

        except (aiohttp.ClientError, TimeoutError) as err:
            raise S1ErganiApiError(
                f"Check-in/out connection failed: {err}"
            ) from err

        _LOGGER.info(
            "S1 Ergani %s response: %s",
            action_name,
            data,
        )

        if not data.get("success"):
            raise S1ErganiApiError(
                data.get(
                    "error",
                    "Check-in/out failed",
                )
            )

        return data

    async def check_in(self) -> dict:
        """Perform check-in."""
        return await self.check(SOTYPE_CHECK_IN)

    async def check_out(self) -> dict:
        """Perform check-out."""
        return await self.check(SOTYPE_CHECK_OUT)
# S1 Ergani for Home Assistant

A custom Home Assistant integration for **SoftOne S1 Ergani**.

The integration allows Home Assistant to perform employee check-in and check-out through the S1 Ergani API and can be used directly from Home Assistant automations.

## Features

* Login and authentication with S1 Ergani
* Check-in
* Check-out
* Automatic public IP detection
* Automatic fallback public IP
* Unique persistent `DEVICEID` for each Home Assistant installation
* Configuration through the Home Assistant UI
* Reconfiguration through the Home Assistant UI
* Home Assistant Actions support
* Home Assistant automation support
* Integration icon
* Error handling for connection, authentication and S1 API failures

## Requirements

* Home Assistant
* A valid SoftOne S1 Ergani account
* S1 Ergani API access
* Your AFM
* Internet access from the Home Assistant host

## Installation

### HACS

The recommended installation method is HACS.

If S1 Ergani is not yet available in the default HACS repository:

1. Open **HACS** in Home Assistant.
2. Open **Integrations**.
3. Select the **three-dot menu** in the top-right corner.
4. Select **Custom repositories**.
5. Enter the URL of this GitHub repository.
6. Select **Integration** as the repository type.
7. Select **Add**.
8. Find **S1 Ergani** and select **Download**.
9. Restart Home Assistant.

After restarting Home Assistant:

1. Go to **Settings → Devices & services**.
2. Select **Add Integration**.
3. Search for **S1 Ergani**.
4. Enter your S1 Ergani connection details.
5. Complete the setup.

### Manual installation

1. Download the latest release from GitHub.
2. Copy the following folder:

```text
custom_components/s1_ergani
```

to:

```text
/config/custom_components/
```

The final structure should be:

```text
/config/custom_components/s1_ergani/
├── __init__.py
├── api.py
├── config_flow.py
├── const.py
├── icon.png
├── manifest.json
├── services.yaml
├── strings.json
└── translations/
    └── en.json
```

3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add Integration**.
5. Search for **S1 Ergani**.
6. Enter the required connection details.

## Configuration

S1 Ergani is configured through the Home Assistant UI.

The integration provides the following settings:

| Setting       | Description                                            |
| ------------- | ------------------------------------------------------ |
| **Server**    | S1/SoftOne server name, for example `hrmdev`           |
| **Username**  | S1 account username                                    |
| **Password**  | S1 account password                                    |
| **AFM**       | Company's AFM                                          |
| **Device ID** | Unique identifier for this Home Assistant installation |

### Device ID

The `Device ID` is generated automatically as a UUID with the `HA-` prefix.

Example:

```text
HA-7f4c9d5e-2b41-4f7a-9c83-6d21e8a4b512
```

The Device ID is stored in the Home Assistant Config Entry and remains stable for that installation unless it is manually changed.

Each Home Assistant installation gets its own Device ID.

## Reconfiguration

After the integration has been installed, the configuration can be changed from:

**Settings → Devices & services → S1 Ergani → Reconfigure**

The following settings can be updated:

* Server
* Username
* Password
* AFM
* Device ID

The integration validates the new credentials before applying the changes.

## Public IP address

S1 Ergani requires the client's **public IP address** for check-in and check-out requests.

The integration automatically detects the public IP using:

```text
https://api.ipify.org/
```

The public IP is **not requested from the user** and is not displayed as a configuration field.

If the public IP cannot be detected, the integration uses:

```text
192.168.1.1
```

as a fallback value.

The IP address sent to S1 Ergani is the public IP used by the Home Assistant host to access the Internet.

## Home Assistant Actions

The integration provides two Home Assistant Actions.

### Check-in

```yaml
actions:
  - action: s1_ergani.check_in
```

The check-in request uses:

```text
SOTYPE = 0
```

### Check-out

```yaml
actions:
  - action: s1_ergani.check_out
```

The check-out request uses:

```text
SOTYPE = 1
```

## Automation examples

The following examples can be copied directly into Home Assistant.

Replace:

* `person.YOUR_PERSON` with your Home Assistant person entity
* `notify.mobile_app_YOUR_PHONE` with your mobile notification service
* `Work` with the name of your Home Assistant work zone, if different

### Check-in when arriving at work

This example performs a SoftOne S1 Ergani check-in when the person arrives at the `Work` zone.

```yaml
alias: Arrive at Work
description: ""
triggers:
  - trigger: state
    entity_id:
      - person.YOUR_PERSON
    from:
      - not_home
    to:
      - "Work"
conditions: []
actions:
  - action: s1_ergani.check_in
  - action: notify.mobile_app_YOUR_PHONE
    data:
      message: TTS
      data:
        tts_text: "Καλώς ήρθες. Έγινε check-in"
mode: single
```

### Check-out when leaving work

This example performs a SoftOne S1 Ergani check-out when the person leaves the `Work` zone.

```yaml
alias: Leave Work
description: ""
triggers:
  - trigger: state
    entity_id:
      - person.YOUR_PERSON
    from:
      - "Work"
    to:
      - not_home
conditions: []
actions:
  - action: s1_ergani.check_out
  - action: notify.mobile_app_YOUR_PHONE
    data:
      message: TTS
      data:
        tts_text: "Bye bye. Έγινε checkout"
mode: single
```

## API workflow

For every check-in or check-out, the integration performs the following sequence:

```text
Login
  ↓
Authenticate
  ↓
Detect public IP
  ↓
Build check-in/check-out request
  ↓
Send request to S1 Ergani
  ↓
Return S1 Ergani response
```

The `checkInOut` request contains:

```json
{
  "clientId": "...",
  "TRNDATE": "YYYY-MM-DD HH:MM",
  "AFM": "...",
  "SOTYPE": "0",
  "IPADDRESS": "...",
  "DEVICEID": "HA-..."
}
```

For check-out:

```text
SOTYPE = 1
```

## Successful response

A successful request returns information similar to:

```json
{
  "success": true,
  "firstname": "GEORGIOS",
  "lastname": "ATHANASIOU",
  "submittime": "2026-08-19 17:24"
}
```

## Troubleshooting

### S1 Ergani does not appear

Check that the integration exists at:

```text
/config/custom_components/s1_ergani/
```

and that the folder contains at least:

```text
manifest.json
config_flow.py
__init__.py
```

Restart Home Assistant after installing or updating the integration.

### Login or authentication fails

Check:

* Server
* Username
* Password
* AFM
* S1 Ergani account permissions
* Internet connectivity

The integration reports connection and authentication errors in the Home Assistant logs.

### Check-in or check-out fails

Open the Home Assistant logs and search for:

```text
s1_ergani
```

The integration logs the check request and the response returned by S1 Ergani.

### Public IP cannot be detected

The integration attempts to obtain the public IP through `api.ipify.org`.

If the request fails, the configured fallback value is used:

```text
192.168.1.1
```

## Security

Do not publish or commit any real credentials or personal data.

Never include the following in the GitHub repository:

* S1 username
* S1 password
* AFM
* Authentication tokens
* Temporary `clientID` values
* Personal employee information
* Private configuration data

Use placeholders in examples and documentation.

## Disclaimer

This is a third-party custom integration.

It is not affiliated with, endorsed by, or officially supported by EnterSoftOne.

Use it at your own risk and verify that its use is appropriate for your S1 Ergani environment and organizational requirements.

## License

MIT License.

This project is a free hobby project created for personal use and shared with the Home Assistant community.

This project is provided "as is", without warranty of any kind.

This project is not affiliated with or endorsed by EnterSoftOne.

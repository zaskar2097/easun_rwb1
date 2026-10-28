# Changelog

All notable changes to the **EASUN RWB1 Local Bridge** add-on are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/) and the
project uses [semantic versioning](https://semver.org/).

## 0.1.13

- Add a "Restart dongle" button (MQTT discovery) that sends the dongle the
  cloud restart command (dtu_rpc i=2603).

## 0.1.12

- Fix: the active pull (`refresh_interval`) could stall after an add-on restart
  until the dongle spoke, because the DtuID was only learned from incoming MQTT.
  The add-on now also learns the DtuID from the HTTP bootstrap and accepts a
  `dtu_id` option, so the pull starts immediately.

## 0.1.11

- Flat line-art icon and logo drawn after the real RWB1 dongle (EASUN colours):
  status LEDs in a vertical column, Wi-Fi fan, and a vertical "Solar Plug-RWB1"
  wordmark. Vector source included as `icon.svg`.

## 0.1.5

- Add this changelog, shown in the add-on update dialog.

## 0.1.4

- Docs: explain how to obtain the dongle's `DtuID` and `hash` (from the HTTP
  bootstrap Basic-auth header) and clarify that an empty Mosquitto `logins` list
  is **not** anonymous — the dongle must be added explicitly.

## 0.1.3

- Fix the add-on `url` to point at the real repository.

## 0.1.2

- Docs: document the two reading cadences — `refresh_interval` (active *pull*)
  vs `report_period_ms` (dongle *push*).

## 0.1.1

- `dev_sn` is now a user-provided option (empty by default); no serial number is
  shipped in the repository.

## 0.1.0

- Initial release.
- Local DNS server (default port `8553`) that answers the Siseli domains with the
  Pi's IP.
- HTTP bootstrap server (`:80`) serving `/dtu/checkin`, `/dtu/devices/findSingle`
  and `/dtu/servers/mqtt`.
- MQTT bridge to Mosquitto: acks the dongle's messages, decodes the Modbus
  frames and publishes the inverter sensors via MQTT discovery.

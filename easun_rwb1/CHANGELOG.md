# Changelog

All notable changes to the **EASUN RWB1 Local Bridge** add-on are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/) and the
project uses [semantic versioning](https://semver.org/).

## 0.1.11

- Smaller Wi-Fi symbol, clear of the left border.

## 0.1.10

- Even spacing between the Wi-Fi arcs; a bit more margin around the wordmark.

## 0.1.9

- Transparent background; smaller Wi-Fi symbol; vertical wordmark now reads top-to-bottom.

## 0.1.8

- Redraw the icon/logo to match the real RWB1 label: status LEDs in a vertical
  column on the left, Wi-Fi fan below them, and a vertical "Solar Plug-RWB1"
  wordmark on the right.

## 0.1.7

- Redraw the Wi-Fi symbol on the icon/logo as a proper symmetric fan.

## 0.1.6

- New flat line-art icon and logo (a drawing of the RWB1 dongle, in EASUN
  colours). The vector source is included as `icon.svg`.

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

- Add the add-on icon (inverter photo) and logo.
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

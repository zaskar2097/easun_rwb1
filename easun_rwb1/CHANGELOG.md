# Changelog

All notable changes to the **EASUN RWB1 Local Bridge** add-on are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/) and the
project uses [semantic versioning](https://semver.org/).

## 0.2.0

- Decode all four Modbus blocks the dongle reports (`PS4Z`, `hIg6`, `Sgx0`,
  `zsui`), not just the live one, and publish many more entities (34 total).
- New **live reading**: inverter temperature (NTC), from the `Sgx0` block.
- New **read-only settings & specs** (nominal ratings and charge/battery
  setpoints: bulk/float/equalization/cut-off voltages, charge-current limits,
  equalization timings…). These are published with `entity_category: diagnostic`
  so Home Assistant shows them in a separate **Diagnostic** section, clearly
  apart from the live readings. They are plain sensors — nothing on the inverter
  can be changed from Home Assistant.
- Register map confirmed against the Siseli cloud's own decoded output.

## 0.1.14

- Fix the Restart button: the dtu_rpc command field `c` is a command-type code
  (26 for restart), not a random counter, so the dongle now acts on it.

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

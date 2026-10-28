# EASUN RWB1 Local Bridge (Home Assistant local add-on)

Read your EASUN inverter (dongle **RWB1** / **Siseli** cloud) **100 % locally**,
with no cloud and no internet, and publish the data as sensors in Home Assistant.

The add-on replaces the cloud services the dongle depends on at boot:

- **DNS (:8553)** — answers the `*.siseli.com` domains with the Pi's IP
  (high port so it doesn't take `53`; the router rewrites the dongle's `53` to `8553`).
- **HTTP (:80)** — serves the bootstrap (`/dtu/checkin`, `/dtu/devices/findSingle`,
  `/dtu/servers/mqtt`), pointing the broker at the Pi and providing the time.
- **MQTT** — connects to Mosquitto as a client, acks the dongle's messages,
  decodes the **Modbus** frames (little-endian) and creates the sensors via
  **MQTT discovery**.

## Quick install

1. Copy this folder to `/addons/easun_rwb1/` on Home Assistant.
2. Add-on Store → *Check for updates* → install **EASUN RWB1 Local Bridge**.
3. Configure `mqtt_user`/`mqtt_password` (see the rest under **Documentation**).
4. Configure Mosquitto to accept the dongle and the router to redirect the
   dongle's DNS to the Pi (detailed steps in the **Documentation** page / `DOCS.md`).

Full instructions, options and troubleshooting are in **`DOCS.md`**
(the add-on's *Documentation* tab).

## Structure

```
easun_rwb1/
  config.yaml     # add-on manifest (ports, configurable options)
  build.yaml      # base images per architecture
  Dockerfile      # Python 3 + paho-mqtt
  app/service.py  # DNS + HTTP + MQTT client (acks, decoding, discovery)
  DOCS.md         # instructions page
  README.md
```

> Version 0.1.0 — based on capture and validation of the real RWB1 protocol.
> Check the first boot in the add-on Log.

## License

[MIT](LICENSE) © 2026 zaskar2097.

Independent project, not affiliated with EASUN or Siseli in any way. The protocol
was obtained by reverse-engineering the dongle itself for interoperability and
local use. Use at your own risk.

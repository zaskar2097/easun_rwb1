# EASUN RWB1 Local Bridge

Make your EASUN inverter (dongle **RWB1** / **Siseli** cloud) run **100 % locally** in Home Assistant — no cloud, no internet. The add-on emulates the cloud services (DNS + HTTP bootstrap + broker) and publishes the inverter data as sensors.

## How it works

On boot, the dongle needs 3 things from the "cloud": resolve a domain via **DNS**, perform an **HTTP bootstrap** (time + where the broker is) and then connect over **MQTT**. This add-on provides all three, pointing the dongle at your Pi:

```
          ┌─ DNS  :8553 → answers "siseli" with the Pi's IP
dongle ───┤  HTTP :80   → bootstrap (time, serial number, broker = Pi)
          └─ MQTT :1883  → Mosquitto; the add-on acks the messages,
                           decodes the Modbus and creates the sensors in HA
```

The data never leaves your network.

---

## Prerequisites

1. **Mosquitto broker add-on** installed and running.
2. The **dongle and the Pi on the same subnet** (e.g. `192.168.10.x`).
3. A way to **redirect the dongle's DNS to the Pi** on the router (see the "Router" section).

---

## Installation (add-on repository)

1. **Settings → Add-ons → Add-on Store → ⋮ (top right) → Repositories** and add:
   ```
   https://github.com/zaskar2097/easun_rwb1
   ```
2. Close the dialog. The **EASUN RWB1 Local Bridge** add-on now shows in the
   store (if not, ⋮ → *Check for updates*).
3. Open it and click **Install** (the first build takes a few minutes, since it
   is built locally for your architecture).

To update later: push to the repo, then ⋮ → *Check for updates* → **Update**.

---

## Configuration

All options are set in the add-on's **Configuration** tab.

| Option | What it is | Typical value |
|---|---|---|
| `pi_ip` | The Pi's IP on your LAN. Leave **empty** for auto-detection. | `192.168.10.251` |
| `mqtt_host` | Where Mosquitto is. | `127.0.0.1` |
| `mqtt_port` | Mosquitto's port. | `1883` |
| `mqtt_user` | **Username** the add-on uses to connect to Mosquitto. | see below |
| `mqtt_password` | **Password** for that user. | see below |
| `override_substr` | Domains to redirect to the Pi (by substring). | `siseli` |
| `dns_port` | Port the add-on listens on for DNS on the Pi (high port, so it doesn't take `53`). | `8553` |
| `dns_upstream` | DNS to forward all other queries to. | `1.1.1.1` |
| `refresh_interval` | Seconds between read requests to the dongle (0 = disabled). | `20` |
| `report_period_ms` | Autonomous reporting period the add-on tells the dongle to use. | `60000` |
| `dev_sn` | Your inverter's serial number, returned in the bootstrap. Set it to your own value (kept only in the local add-on options). | `<inverter-serial>` |
| `log_level` | Log verbosity (`debug` helps on first boot). | `info` |

### Mosquitto: create the add-on user

In **Settings → People → Users**, create a user (e.g. `rwb1`) and use that
name/password in `mqtt_user` / `mqtt_password`. (HA's Mosquitto accepts Home
Assistant users by default.)

### Mosquitto: accept the **dongle**

The dongle connects to Mosquitto with these (fixed) credentials of its own:

- **username:** your *DtuID* (the number shown in the Siseli app / the dongle's interface)
- **password:** the dongle's *hash*

Add them to Mosquitto. In the **Mosquitto broker → Configuration** add-on:

```yaml
logins:
  - username: "<YOUR_DtuID>"
    password: "<THE_DONGLE_HASH>"
```

> Don't know the hash? With the add-on at `log_level: debug` and the dongle
> trying to connect, Mosquitto logs the login attempt with the username (DtuID).
> As a last resort, temporarily enable `anonymous: true` in Mosquitto just to get started.

---

## Router — redirect the dongle's DNS to the Pi

The dongle uses a **fixed DNS server** (it ignores DHCP), so its DNS has to be
redirected on the router. Since on the stock firmware the rules don't persist,
use your usual mechanism (a script in `/jffs/scripts/` reapplied by the Pi).

The dongle queries DNS on port **53**, but the add-on listens on a **high port
(`8553`)** so it doesn't take `53` on the Pi. That's why the router rule rewrites
the destination to `PI_IP:8553`.

Rules to apply on the router (replace the dongle's and the Pi's IP):

```sh
iptables -t nat -A PREROUTING  -s <DONGLE_IP> -p udp --dport 53 -j DNAT --to-destination <PI_IP>:8553
iptables -t nat -A POSTROUTING -d <PI_IP> -p udp --dport 8553 -j MASQUERADE
```

Example: `<DONGLE_IP>=192.168.10.134`, `<PI_IP>=192.168.10.251`.

> If you change the `dns_port` option in the add-on, use the same value in both rules.

> **Why only DNS?** Once DNS answers "siseli → Pi's IP", the dongle connects to
> the Pi **directly** (same subnet) on ports 80 and 1883, which the Pi already
> serves. No further rules are needed.

---

## Start and verify

1. Start the add-on and open the **Log** tab. You should see `DNS listening :8553`,
   `HTTP listening :80` and `MQTT connected`.
2. **Restart the dongle** (cut its power for ~30 s).
3. In the Log, in this order: `HTTP checkin` → `HTTP findSingle` →
   `HTTP servers/mqtt` → `Sensors published...`.
4. Under **Settings → Devices & Services → MQTT** the **EASUN RWB1** device
   appears with its sensors (battery, PV, output, power, SOC…).

---

## Troubleshooting

- **No `HTTP checkin` in the log:** the dongle's DNS isn't reaching the Pi.
  Check the router rules and that the Pi's DNS port is reachable.
- **HTTP arrives but no data:** the dongle isn't connecting to Mosquitto —
  check the dongle's login in Mosquitto (section above).
- **Sensors with no values / zero:** normal if the inverter has PV/grid
  disconnected; check the battery and the output, which are always present.
- **Port 80 in use:** make sure no other HTTP server is running on the Pi. DNS
  already uses the high port `8553`, so it doesn't clash with a DNS on `53`
  (e.g. AdGuard).
- **`DNS listening` doesn't appear:** `dns_port` may be in use; change it in the
  options and adjust the router rule accordingly.

---

## Reverting to cloud operation

Remove the router rules (`-D` instead of `-A`) and stop the add-on. On restart
the dongle resolves the real domains again and connects to the Siseli cloud.

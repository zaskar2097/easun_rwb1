#!/usr/bin/env python3
"""EASUN RWB1 Local Bridge — Home Assistant add-on.

Makes the RWB1 dongle run 100% locally (no cloud):
  - DNS server (:8553): answers the cloud domains with the Pi's IP.
  - HTTP server (:80): serves the bootstrap (checkin / findSingle / servers/mqtt).
  - MQTT client (Mosquitto): acks the dongle's messages, decodes the Modbus
    frames and publishes the sensors to Home Assistant via MQTT discovery.
"""
import json, os, socket, struct, threading, time, random, string, logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import paho.mqtt.client as mqtt

# ----------------------------------------------------------------------------
# Options (from Home Assistant, in /data/options.json)
# ----------------------------------------------------------------------------
OPT = {}
try:
    with open("/data/options.json") as f:
        OPT = json.load(f)
except Exception:
    pass

def opt(k, d=None):
    v = OPT.get(k, d)
    return d if v in (None, "") else v

logging.basicConfig(level=getattr(logging, str(opt("log_level","info")).upper(), logging.INFO),
                    format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("rwb1")

def detect_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("223.5.5.5", 53)); ip = s.getsockname()[0]; s.close()
        return ip
    except Exception:
        return "127.0.0.1"

PI_IP        = opt("pi_ip") or detect_ip()
MQTT_HOST    = opt("mqtt_host", "127.0.0.1")
MQTT_PORT    = int(opt("mqtt_port", 1883))
MQTT_USER    = opt("mqtt_user", "")
MQTT_PASS    = opt("mqtt_password", "")
OVERRIDE     = str(opt("override_substr", "siseli")).lower()
DNS_PORT     = int(opt("dns_port", 8553))
UPSTREAM     = (opt("dns_upstream", "1.1.1.1"), 53)
REFRESH      = int(opt("refresh_interval", 20))
REPORT_MS    = int(opt("report_period_ms", 60000))
DEV_SN       = opt("dev_sn", "")

log.info("RWB1 bridge: PI_IP=%s MQTT=%s:%s override=*%s* refresh=%ss",
         PI_IP, MQTT_HOST, MQTT_PORT, OVERRIDE, REFRESH)

def rnd(n): return "".join(random.choices(string.ascii_letters+string.digits, k=n))

# ----------------------------------------------------------------------------
# Modbus: validate CRC and decode registers (little-endian)
# ----------------------------------------------------------------------------
def crc_ok(r):
    c = 0xFFFF
    for x in r[:-2]:
        c ^= x
        for _ in range(8):
            c = (c >> 1) ^ 0xA001 if c & 1 else c >> 1
    return (c & 0xFF) == r[-2] and (c >> 8) == r[-1]

def decode_block(b64s):
    import base64
    try:
        r = base64.b64decode(b64s + "=" * (-len(b64s) % 4))
    except Exception:
        return None
    if len(r) < 5 or r[1] not in (3, 4) or r[2] != len(r) - 5 or not crc_ok(r):
        return None
    d = r[3:3 + r[2]]
    return [(d[i+1] << 8) | d[i] for i in range(0, len(d), 2)]

# Dynamic block (PS4Z) map -> HA sensors.  (key, reg, factor, name, unit, device_class)
SENSORS = [
    ("state",                   0, 1,   "State",               None,  None),
    ("pv_voltage",              1, 0.1, "PV Voltage",          "V",   "voltage"),
    ("grid_voltage",            2, 0.1, "Grid Voltage",        "V",   "voltage"),
    ("grid_frequency",          3, 0.1, "Grid Frequency",      "Hz",  "frequency"),
    ("pv_power",                4, 1,   "PV Power",            "W",   "power"),
    ("battery_voltage",         5, 0.1, "Battery Voltage",     "V",   "voltage"),
    ("battery_soc",             6, 1,   "Battery SOC",         "%",   "battery"),
    ("battery_charge_current",  7, 1,   "Battery Charge Current",    "A", "current"),
    ("battery_discharge_current",8,1,   "Battery Discharge Current", "A", "current"),
    ("output_voltage",          9, 0.1, "Output Voltage",      "V",   "voltage"),
    ("output_frequency",        10,0.1, "Output Frequency",    "Hz",  "frequency"),
    ("output_apparent_power",   11,1,   "Output Apparent Power", "VA", "apparent_power"),
    ("output_active_power",     12,1,   "Load Power",          "W",   "power"),
    ("load",                    13,1,   "Load",                "%",   None),
]

# ----------------------------------------------------------------------------
# DNS server (UDP :8553)
# ----------------------------------------------------------------------------
def dns_parse_qname(data, off):
    labels = []
    while True:
        l = data[off]
        if l == 0: off += 1; break
        if l & 0xc0 == 0xc0: off += 2; break
        labels.append(data[off+1:off+1+l].decode("latin-1")); off += 1 + l
    return ".".join(labels), off

def dns_build_A(query, ip):
    tid = query[:2]
    hdr = tid + struct.pack(">HHHHH", 0x8180, 1, 1, 0, 0)
    _, qend = dns_parse_qname(query, 12)
    question = query[12:qend+4]
    ans = b"\xc0\x0c" + struct.pack(">HHI", 1, 1, 60) + struct.pack(">H", 4) + socket.inet_aton(ip)
    return hdr + question + ans

def dns_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", DNS_PORT))
    log.info("DNS listening :%s  (override *%s* -> %s)", DNS_PORT, OVERRIDE, PI_IP)
    while True:
        try:
            data, addr = s.recvfrom(4096)
            qname, off = dns_parse_qname(data, 12)
            qtype = struct.unpack(">H", data[off:off+2])[0]
            if OVERRIDE in qname.lower() and qtype == 1:
                s.sendto(dns_build_A(data, PI_IP), addr)
                log.debug("DNS %s -> %s", qname, PI_IP)
            else:
                up = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); up.settimeout(5)
                up.sendto(data, UPSTREAM); r, _ = up.recvfrom(4096); up.close()
                s.sendto(r, addr)
        except Exception as e:
            log.warning("DNS error: %s", e)

# ----------------------------------------------------------------------------
# HTTP server (TCP :80) — dongle bootstrap
# ----------------------------------------------------------------------------
class Boot(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def _json(self, obj):
        body = json.dumps(obj, separators=(",", ":")).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json;charset=UTF-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def _read_body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if n: self.rfile.read(n)
    def do_POST(self):
        self._read_body()
        if self.path.startswith("/dtu/checkin"):
            log.info("HTTP checkin")
            self._json({"code":0,"msg":"Success","data":{
                "timeInMills": str(int(time.time()*1000)), "utcOffset":"+00:00",
                "outbound":1, "performanceReportPeriod": REPORT_MS, "firmware": None,
                "gatherProtocol":{"autoAdaptive":0,"verCode":14,"verText":"1.0.0",
                                  "verState":10,"protocolNo":"AM7855189","forceUpdate":0}}})
        elif self.path.startswith("/dtu/devices/findSingle"):
            log.info("HTTP findSingle")
            self._json({"code":0,"msg":"Success","data":{"devSN": DEV_SN}})
        else:
            self._json({"code":0,"msg":"Success","data":{}})
    def do_GET(self):
        if self.path.startswith("/dtu/servers/mqtt"):
            log.info("HTTP servers/mqtt -> %s:1883", PI_IP)
            self._json({"code":0,"msg":"Success","data":{
                "main":{"host":PI_IP,"port":1883,"ssl":0,"sslCertificate":None},
                "mains":[{"host":PI_IP,"port":1883,"ssl":0,"sslCertificate":None}]}})
        else:
            self._json({"code":0,"msg":"Success","data":{}})

def http_server():
    log.info("HTTP listening :80")
    ThreadingHTTPServer(("0.0.0.0", 80), Boot).serve_forever()

# ----------------------------------------------------------------------------
# MQTT client — acks + decoding + discovery
# ----------------------------------------------------------------------------
class Bridge:
    def __init__(self):
        self.dtu_id = None
        self.discovery_done = False
        self.cli = mqtt.Client(client_id="rwb1_bridge_" + rnd(4))
        if MQTT_USER:
            self.cli.username_pw_set(MQTT_USER, MQTT_PASS)
        self.cli.on_connect = self.on_connect
        self.cli.on_message = self.on_message

    def start(self):
        while True:
            try:
                self.cli.connect(MQTT_HOST, MQTT_PORT, 60); break
            except Exception as e:
                log.warning("MQTT not connected (%s); retrying in 5s", e); time.sleep(5)
        self.cli.loop_start()
        threading.Thread(target=self.refresher, daemon=True).start()

    def on_connect(self, c, u, f, rc):
        log.info("MQTT connected (rc=%s). Subscribing dtu/+/pub/#", rc)
        c.subscribe("dtu/+/pub/#")

    def pub(self, topic, obj):
        self.cli.publish(topic, b"\x00" + json.dumps(obj, separators=(",", ":")).encode())

    def refresher(self):
        if REFRESH <= 0: return
        while True:
            time.sleep(REFRESH)
            if self.dtu_id:
                self.pub(f"dtu/{self.dtu_id}/sub/service/dev_rpc",
                         {"c":5,"t":rnd(8),"s":rnd(9),"i":501,"b":{}})

    def on_message(self, c, u, msg):
        topic = msg.topic
        parts = topic.split("/")
        if len(parts) > 1 and parts[0] == "dtu":
            self.dtu_id = parts[1]
        payload = msg.payload
        k = payload.find(b"{")
        if k < 0: return
        try:
            j = json.loads(payload[k:].decode(errors="replace"))
        except Exception:
            return
        ci, t, i, b = j.get("c"), j.get("t"), j.get("i"), j.get("b", {})
        # ACK the events
        if "/pub/event/" in topic and not topic.endswith("_reply") and t is not None:
            rtopic = topic.replace("/pub/", "/sub/") + "_reply"
            self.pub(rtopic, {"c":ci, "t":t, "s":rnd(9),
                              "i": (i+1) if isinstance(i, int) else i, "e":0})
        # Decode data (first block = dynamic)
        if isinstance(b, dict) and isinstance(b.get("ct"), list) and b["ct"]:
            regs = decode_block(b["ct"][0].get("co", ""))
            if regs:
                self.publish_values(regs)

    def publish_values(self, regs):
        if not self.discovery_done:
            self.announce()
        state = {}
        for key, idx, factor, *_ in SENSORS:
            if idx < len(regs):
                v = regs[idx] * factor
                state[key] = round(v, 2) if isinstance(factor, float) else v
        self.cli.publish("rwb1/state", json.dumps(state), retain=True)
        log.debug("state: %s", state)

    def announce(self):
        dev = {"identifiers": [f"rwb1_{self.dtu_id or 'dtu'}"], "name": "EASUN RWB1",
               "manufacturer": "EASUN / Siseli", "model": "RWB1"}
        for key, idx, factor, name, unit, dclass in SENSORS:
            cfg = {"name": name, "unique_id": f"rwb1_{key}",
                   "state_topic": "rwb1/state", "value_template": "{{ value_json." + key + " }}",
                   "device": dev}
            if unit: cfg["unit_of_measurement"] = unit
            if dclass: cfg["device_class"] = dclass; cfg["state_class"] = "measurement"
            self.cli.publish(f"homeassistant/sensor/rwb1/{key}/config",
                             json.dumps(cfg), retain=True)
        self.discovery_done = True
        log.info("Sensors published to Home Assistant (MQTT discovery)")

# ----------------------------------------------------------------------------
def main():
    threading.Thread(target=dns_server, daemon=True).start()
    threading.Thread(target=http_server, daemon=True).start()
    Bridge().start()
    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()

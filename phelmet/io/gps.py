from datetime import datetime, timezone


def nmea_coord(value: str, side: str) -> float:
    cut = 2 if side in ("N", "S") else 3
    deg, mins = float(value[:cut]), float(value[cut:])
    out = deg + mins / 60
    return -out if side in ("S", "W") else out


def parse_nmea(line: str) -> dict | None:
    parts = line.strip().split(",")
    kind = parts[0][-3:] if parts else ""
    if kind == "RMC" and len(parts) >= 10 and parts[2] == "A":
        return {"ts": parts[1], "lat": nmea_coord(parts[3], parts[4]), "lon": nmea_coord(parts[5], parts[6]), "speed_kmh": float(parts[7] or 0) * 1.852, "fix_ok": True, "source": "nmea"}
    if kind == "GGA" and len(parts) >= 9:
        return {"hdop": float(parts[8] or 99), "sats": int(parts[7] or 0), "fix_ok": parts[6] != "0", "source": "nmea"}
    return None


class NmeaGps:
    def __init__(self, port: str, baud: int = 9600) -> None:
        try:
            import serial
        except ImportError as e:
            raise RuntimeError("install pyserial for live NMEA GPS") from e
        self.ser = serial.Serial(port, baud, timeout=.15)
        self.last = {"lat": 0.0, "lon": 0.0, "speed_kmh": 0.0, "hdop": 99.0, "sats": 0, "fix_ok": False, "source": "nmea"}

    def read(self) -> dict:
        row = parse_nmea(self.ser.readline().decode(errors="ignore"))
        if row:
            self.last.update(row)
        self.last["ingest_ts"] = datetime.now(timezone.utc).isoformat()
        return self.last.copy()

    def close(self) -> None:
        self.ser.close()

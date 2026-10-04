import time


class UsbCamSource:
    def __init__(self, index: int = 0) -> None:
        import cv2
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            raise RuntimeError("USB camera unavailable")

    def read(self):
        return self.cap.read()

    def close(self) -> None:
        self.cap.release()


class PiCamera2Source:
    def __init__(self, size=(320, 240)) -> None:
        try:
            from picamera2 import Picamera2
        except ImportError as e:
            raise RuntimeError("install picamera2 on Raspberry Pi") from e
        self.cam = Picamera2()
        self.cam.configure(self.cam.create_video_configuration(main={"size": size, "format": "BGR888"}))
        self.cam.start()

    def read(self):
        return True, self.cam.capture_array()

    def close(self) -> None:
        self.cam.stop()


class Mpu6050:
    def __init__(self) -> None:
        try:
            from mpu6050 import mpu6050
        except ImportError as e:
            raise RuntimeError("install mpu6050 and enable I2C") from e
        self.dev = mpu6050(0x68)

    def read(self) -> dict:
        gyro = self.dev.get_gyro_data()
        accel = self.dev.get_accel_data()
        return {"gyro_y": gyro["y"], "pitch": accel["x"], "t": time.monotonic()}


class NmeaGps:
    def __init__(self, port: str = "/dev/serial0") -> None:
        try:
            import serial
        except ImportError as e:
            raise RuntimeError("install pyserial for GPS") from e
        self.ser = serial.Serial(port, 9600, timeout=.2)

    def read(self) -> dict:
        line = self.ser.readline().decode(errors="ignore")
        if "RMC" not in line:
            return {"speed_kmh": 0}
        parts = line.split(",")
        return {"speed_kmh": float(parts[7] or 0) * 1.852}

    def close(self) -> None:
        self.ser.close()


class GpioBuzzer:
    def __init__(self, pin: int = 18) -> None:
        try:
            from gpiozero import Buzzer
        except ImportError as e:
            raise RuntimeError("install gpiozero for buzzer") from e
        self.dev = Buzzer(pin)

    def beep(self, severity: str) -> None:
        self.dev.beep(.1, .1, n=2 if severity == "HIGH" else 1, background=True)

    def close(self) -> None:
        self.dev.off()

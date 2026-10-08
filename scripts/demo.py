import subprocess
import sys


subprocess.run([sys.executable, "-m", "phelmet.app", "--source", "data/sample/demo.mp4", "--mock-imu", "--mock-gps", "--headless", "--save-video", "demo_out.mp4"], check=True)

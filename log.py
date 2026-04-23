import csv
from datetime import datetime

LOG_FILE = "robot_voice_log.csv"

def init_log():
    with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "voice_command", "recognized_text", "robot_action", "latency_ms"])

def log_entry(voice_command, recognized_text, robot_action, latency_ms):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, voice_command, recognized_text, robot_action, latency_ms])
        f.flush()
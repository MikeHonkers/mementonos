from pathlib import Path
import os
from dotenv import load_dotenv
import time

load_dotenv()
TMP_DIR = Path(os.getenv("DATA_DIR")) / 'tmp'
CHECK_INTERVAL = 5

def cleanup_loop():
    while True:
        now = time.time()
        for p in list(TMP_DIR.iterdir()):
            if p.is_file() and p.name.startswith("dec_"):
                if now - p.stat().st_mtime > 5:
                    try:
                        p.unlink()
                        print(f"Удалён: {p}")
                    except Exception as e:
                        print(f"Ошибка удаления {p}: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    cleanup_loop()
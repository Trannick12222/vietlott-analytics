import sys
import os
import time
import socket
import threading
import webbrowser
import logging
from pathlib import Path

# Fix Windows console encoding if available
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Setup logging to file and console
PROJECT_DIR = Path(__file__).resolve().parent
LOG_FILE = PROJECT_DIR / "desktop_app.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8", mode="a"),
        logging.StreamHandler(sys.stdout if sys.stdout else open(os.devnull, "w"))
    ]
)
logger = logging.getLogger("desktop_app")

sys.path.insert(0, str(PROJECT_DIR))

try:
    import uvicorn
    import webview
    import httpx
    from src.app import app
    from src.database.connection import init_db
except Exception as e:
    logger.exception(f"Import error: {e}")
    sys.exit(1)

def find_free_port(default_port=8000) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', default_port))
            return default_port
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def run_server(port: int):
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False
    )
    server = uvicorn.Server(config)
    server.run()

def wait_for_server(url: str, timeout: float = 12.0):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            r = httpx.get(f"{url}/api/health", timeout=1.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False

def main():
    logger.info("Starting Vietlott Analytics Desktop application...")
    try:
        init_db()
    except Exception as e:
        logger.exception(f"DB Init error: {e}")

    port = find_free_port(8000)
    server_url = f"http://127.0.0.1:{port}"
    
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()
    
    if not wait_for_server(server_url):
        logger.error(f"Cannot start backend server at {server_url}")
        sys.exit(1)
        
    logger.info(f"Server ready at {server_url}. Opening GUI window...")
    
    gui_opened = False
    try:
        window = webview.create_window(
            title="Vietlott Analytics & Prediction - Ứng Dụng Phân Tích Xổ Số",
            url=server_url,
            width=1320,
            height=880,
            min_size=(1000, 680),
            text_select=True,
            confirm_close=False
        )
        gui_opened = True
        webview.start()
    except Exception as e:
        logger.exception(f"pywebview GUI error: {e}")
        # Fallback to browser if pywebview window fails
        logger.info(f"Falling back to default browser for {server_url}")
        webbrowser.open(server_url)
        # Keep process alive while user uses browser
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    logger.info("Application closed.")

if __name__ == "__main__":
    main()

import os
import sys
import time
import socket
import subprocess

PORT = 5000
URL = f"http://127.0.0.1:{PORT}"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def is_server_running(host="127.0.0.1", port=PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

def start_server():
    if is_server_running():
        return

    # Start Flask app in background as detached process
    app_script = os.path.join(BASE_DIR, "app.py")
    if sys.platform == "win32":
        # DETACHED_PROCESS = 0x00000008, CREATE_NEW_PROCESS_GROUP = 0x00000200
        subprocess.Popen(
            [sys.executable, app_script],
            cwd=BASE_DIR,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True
        )
    else:
        subprocess.Popen([sys.executable, app_script], cwd=BASE_DIR)

    # Wait for server to respond
    for _ in range(30):
        if is_server_running():
            break
        time.sleep(0.2)

def launch_app_window():
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]

    for p in edge_paths + chrome_paths:
        if os.path.exists(p):
            subprocess.Popen([
                p,
                f"--app={URL}",
                "--window-size=1300,880",
                "--app-id=IntelligentExpenseTracker"
            ])
            return

    # Fallback to default browser
    import webbrowser
    webbrowser.open(URL)

if __name__ == "__main__":
    start_server()
    launch_app_window()

#!/usr/bin/python3
# systemctl start diskui.service - /etc/systemd/system/diskui.service

from flask import Flask, request
import subprocess
import os
import threading
import time
import datetime
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DEVICE = "/dev/sda"                     # Encrypted disk
MAPPER_NAME = "secure_storage"          # Name after luksOpen
MOUNT_POINT = "/mnt/secure"             # Mount point
LOCK_TIMEOUT = 600                      # 10 minutes in seconds
lock_timer = None                       # Timer for automatic lock

def auto_lock():
    global lock_timer
    time.sleep(LOCK_TIMEOUT)
    if is_unlocked():
        try:
            subprocess.run(["systemctl", "stop", "filebrowser"], check=True)
            subprocess.run(["umount", MOUNT_POINT], check=True)
            subprocess.run(["cryptsetup", "luksClose", MAPPER_NAME], check=True)
            logging.info("Disk auto-locked due to inactivity")
        except subprocess.CalledProcessError as e:
            logging.error(f"Auto-lock failed: {e}")
    lock_timer = None

def is_unlocked():
    return os.path.exists(f"/dev/mapper/{MAPPER_NAME}")

@app.route("/", methods=["GET", "POST"])
def home():
    message = ""
    if request.method == "POST":
        action = request.form.get("action")
        password = request.form.get("password", "")

        if action == "unlock":
            try:
                subprocess.run(
                    ["cryptsetup", "luksOpen", DEVICE, MAPPER_NAME],
                    input=password.encode(),
                    check=True
                )
                subprocess.run(["mount", f"/dev/mapper/{MAPPER_NAME}", MOUNT_POINT], check=True)
                subprocess.run(["systemctl", "start", "filebrowser"], check=True)
                
                global lock_timer
                if lock_timer:
                    lock_timer = None
                lock_timer = threading.Thread(target=auto_lock, daemon=True)
                lock_timer.start()


                message = "✅ Disk unlocked and mounted!"
                logging.info("Disk unlocked and mounted successfully via web UI")
            except subprocess.CalledProcessError:
                message = "❌ Failed to unlock. Wrong password?"
                logging.error("Failed to unlock disk via web UI, possibly wrong password")

        elif action == "lock":
            try:
                subprocess.run(["systemctl", "stop", "filebrowser"], check=True)
                subprocess.run(["umount", MOUNT_POINT], check=True)
                subprocess.run(["cryptsetup", "luksClose", MAPPER_NAME], check=True)
                message = "🔒 Disk locked!"
                logging.info("Disk locked successfully via web UI")
            except subprocess.CalledProcessError:
                message = "❌ Failed to lock. Is it already locked?"
                logging.error("Failed to lock disk via web UI, possibly already locked")

    # Determine the status badge
    status = "Unlocked 🔓" if is_unlocked() else "Locked 🔒"

    return f"""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Disk UI</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container py-5">
            <div class="card shadow-lg p-4 rounded-4">
                <h2 class="mb-3 text-center">🔐 Disk Manager</h2>
                <h4 class="text-center mb-4">Status: 
                    <span class="badge { 'bg-success' if is_unlocked() else 'bg-danger' }">
                        {status}
                    </span>
                </h4>
                
                {f'<div class="alert alert-info text-center">{message}</div>' if message else ''}

                <form method="POST" class="text-center">
                    <div class="mb-3">
                        <input type="password" class="form-control form-control-lg" 
                               name="password" placeholder="Enter LUKS password" {'disabled' if is_unlocked() else 'required'} >
                    </div>
                    <div class="d-flex justify-content-center gap-3">
                        <button type="submit" name="action" value="unlock" {'disabled' if is_unlocked() else ''} class="btn btn-success btn-lg px-4">Unlock</button>
                        <button type="submit" name="action" value="lock" {'disabled' if not is_unlocked() else ''} class="btn btn-danger btn-lg px-4">Lock</button>
                        <a href="" target="_blank" class="btn btn-primary btn-lg px-4">Filebrowser</a>
                    </div>
                </form>
            </div>
        </div>
        <script>
            document.getElementsByTagName('a')[0].href = "//"+window.location.hostname+":8080";
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    if is_unlocked():
        logging.info("Disk is already unlocked, starting auto-lock timer")
        lock_timer = threading.Thread(target=auto_lock, daemon=True)
        lock_timer.start()
    else:
        logging.info("Disk is locked, ready to unlock via web UI")
    app.run(host="0.0.0.0", port=8081)
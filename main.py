import hmac
import os
import socket
import subprocess
import threading
import urllib.error
import urllib.request

from dotenv import load_dotenv
from flask import Flask, abort, request

load_dotenv("/etc/school-server.env")

app = Flask(__name__)
AUTH_TOKEN = os.environ.get("SERVER_AUTH_TOKEN")

# Reconnect wifi to next
# def reconnect_wifi():


def execute_reboot():
    try:
        result = subprocess.run(
            ["sudo", "/usr/bin/systemctl", "reboot", "-i"],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"Reboot command executed with result: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"Reboot command failed with exit code {e.returncode}")
        print(f"Error output: {e.stderr.strip()}")


@app.route("/")
def home():
    return "Hello from school server"


@app.route("/reboot", methods=["POST"])
def reboot():
    if not AUTH_TOKEN:
        print("AUTH_TOKEN is not set in environment variables.")
        abort(500, description="Server configuration error: AUTH_TOKEN is not set.")

    auth = request.headers.get("Authorization", "")
    expected_auth = f"Bearer {AUTH_TOKEN}"

    # using constant time comparison to prevent timing attacks
    if not hmac.compare_digest(auth, expected_auth):
        print(f"Unauthorized access attempt with token: {auth}")
        abort(403)

    threading.Timer(2.0, execute_reboot).start()
    return "The system would reboot in 2 seconds.", 200


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


@app.route("/hasInternet", methods=["GET"])
def has_internet_access():
    try:
        urllib.request.urlopen("http://www.google.com", timeout=5)
        return "Internet connection is available.", 200
    except urllib.error.URLError as e:
        if isinstance(e.reason, (socket.timeout, TimeoutError)):
            print("Request timed out while checking internet connection.")
            return "No internet connection. Request timed out.", 503
        print(f"Network error occurred: {e}")

        return f"No internet connection. Error: {e.reason}", 503
    except OSError as e:
        print(f"Unexpected network error: {e}")
        return f"Unexpected network error: {e}", 503


@app.errorhandler(403)
def forbidden(error):
    return "Forbidden: You don't have permission to access this resource.", 403


@app.errorhandler(500)
def internal_server_error(error):
    return f"Internal Server Error: {error.description}", 500


@app.errorhandler(404)
def not_found(error):
    return "Not Found: The requested resource could not be found.", 404


if __name__ == "__main__":
    app.run(debug=True, port=5003, host="0.0.0.0")

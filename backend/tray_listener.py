"""Optional system tray listener for always-on wake word detection.

Run separately from the web app:
    python tray_listener.py

Requires: pip install pystray pillow speechrecognition pyaudio requests
"""

import logging
import threading
import webbrowser
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tray-listener")

API_URL = "http://localhost:8000"
WAKE_WORDS = ["hey mentor", "jarvis"]


def send_to_mentor(message: str) -> str:
    import requests

    try:
        resp = requests.post(
            f"{API_URL}/api/chat",
            json={"message": message, "session_id": "tray", "execute_commands": True},
            timeout=60,
        )
        return resp.json().get("response", "No response")
    except Exception as exc:
        return f"Connection failed: {exc}"


def listen_loop():
    try:
        import speech_recognition as sr
    except ImportError:
        logger.error("Install speechrecognition and pyaudio: pip install speechrecognition pyaudio")
        return

    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    logger.info("Tray listener active. Say 'Hey Mentor' or 'Jarvis'...")

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)

    while True:
        try:
            with mic as source:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            text = recognizer.recognize_google(audio).lower()
            logger.info("Heard: %s", text)

            if any(w in text for w in WAKE_WORDS):
                command = text
                for w in WAKE_WORDS:
                    command = command.replace(w, "").strip()
                if command:
                    response = send_to_mentor(command)
                    logger.info("Mentor: %s", response[:200])
        except Exception:
            pass


def create_tray_icon():
    try:
        from PIL import Image, ImageDraw
        import pystray
    except ImportError:
        logger.error("Install pystray and pillow: pip install pystray pillow")
        return

    def create_image():
        img = Image.new("RGB", (64, 64), color=(10, 14, 23))
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 56, 56], outline=(0, 240, 255), width=2)
        draw.text((22, 22), "M", fill=(0, 240, 255))
        return img

    def on_open(icon, item):
        webbrowser.open("http://localhost:3000")

    def on_quit(icon, item):
        icon.stop()

    icon = pystray.Icon(
        "mentor-ai",
        create_image(),
        "Project Mentor AI",
        menu=pystray.Menu(
            pystray.MenuItem("Open Dashboard", on_open),
            pystray.MenuItem("Quit", on_quit),
        ),
    )

    listener_thread = threading.Thread(target=listen_loop, daemon=True)
    listener_thread.start()
    icon.run()


if __name__ == "__main__":
    create_tray_icon()

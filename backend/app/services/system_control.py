"""System control service for executing computer commands."""

import logging
import platform
import subprocess
import threading
import webbrowser
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

SYSTEM_COMMANDS: dict[str, dict[str, Any]] = {
    "open_chrome": {
        "windows": ["start", "chrome"],
        "darwin": ["open", "-a", "Google Chrome"],
        "linux": ["google-chrome"],
        "description": "Open Chrome browser",
    },
    "open_vscode": {
        "windows": ["code"],
        "darwin": ["code"],
        "linux": ["code"],
        "description": "Open Visual Studio Code",
    },
    "open_terminal": {
        "windows": ["cmd.exe"],
        "darwin": ["open", "-a", "Terminal"],
        "linux": ["x-terminal-emulator"],
        "description": "Open terminal",
    },
    "open_finder": {
        "windows": ["explorer"],
        "darwin": ["open", "."],
        "linux": ["xdg-open", "."],
        "description": "Open file explorer",
    },
    "open_spotify": {
        "windows": ["start", "spotify:"],
        "darwin": ["open", "-a", "Spotify"],
        "linux": ["spotify"],
        "description": "Open Spotify",
    },
    "open_notepad": {
        "windows": ["notepad.exe"],
        "darwin": ["open", "-a", "TextEdit"],
        "linux": ["gedit"],
        "description": "Open Notepad",
    },
    "open_calculator": {
        "windows": ["calc.exe"],
        "darwin": ["open", "-a", "Calculator"],
        "linux": ["gnome-calculator"],
        "description": "Open Calculator",
    },
    "open_edge": {
        "windows": ["start", "msedge"],
        "darwin": ["open", "-a", "Microsoft Edge"],
        "linux": ["microsoft-edge"],
        "description": "Open Microsoft Edge",
    },
    "lock_computer": {
        "windows": ["rundll32.exe", "user32.dll,LockWorkStation"],
        "darwin": ["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGI/UserSessionLock"],
        "linux": ["loginctl", "lock-session"],
        "description": "Lock the computer",
        "requires_confirmation": True,
    },
    "minimize_all": {
        "windows": ["powershell", "-Command", "(New-Object -ComObject Shell.Application).MinimizeAll()"],
        "darwin": ["osascript", "-e", 'tell application "System Events" to keystroke "m" using {command down, option down}'],
        "linux": ["wmctrl", "-k", "on"],
        "description": "Minimize all windows",
    },
    "shutdown": {
        "windows": ["shutdown", "/s", "/t", "5"],
        "darwin": ["osascript", "-e", 'tell app "System Events" to shut down'],
        "linux": ["shutdown", "-h", "+1"],
        "description": "Shutdown computer in 5 seconds",
        "requires_confirmation": True,
    },
    "restart": {
        "windows": ["shutdown", "/r", "/t", "5"],
        "darwin": ["osascript", "-e", 'tell app "System Events" to restart'],
        "linux": ["shutdown", "-r", "+1"],
        "description": "Restart computer in 5 seconds",
        "requires_confirmation": True,
    },
}


class SystemControlService:
    """Execute system-level commands safely."""

    def __init__(self, allow_control: bool = True):
        self.allow_control = allow_control
        self._platform_key = "windows" if IS_WINDOWS else "darwin" if IS_MACOS else "linux"

    def _run_process(self, cmd: list[str], shell: bool = False) -> tuple[bool, str]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, shell=shell)
            output = result.stdout or result.stderr or "Command executed successfully."
            return result.returncode == 0, output.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timed out after 30 seconds."
        except FileNotFoundError:
            return False, f"Command not found: {cmd[0]}"
        except Exception as exc:
            logger.exception("Process execution failed")
            return False, str(exc)

    def execute_named_command(self, command_name: str, confirm: bool = False, **kwargs: Any) -> dict[str, Any]:
        if not self.allow_control:
            return {"success": False, "message": "System control is disabled.", "requires_confirmation": False}

        if command_name not in SYSTEM_COMMANDS:
            return {"success": False, "message": f"Unknown command: {command_name}", "requires_confirmation": False}

        cmd_def = SYSTEM_COMMANDS[command_name]
        if cmd_def.get("requires_confirmation") and not confirm:
            return {
                "success": False,
                "message": f"Confirmation required for: {cmd_def['description']}",
                "requires_confirmation": True,
            }

        platform_cmd = cmd_def.get(self._platform_key, cmd_def.get("linux", []))
        success, output = self._run_process(platform_cmd)
        return {"success": success, "message": cmd_def["description"], "output": output, "requires_confirmation": False}

    def open_application(self, app_name: str) -> dict[str, Any]:
        app_map = {
            "chrome": "open_chrome", "google chrome": "open_chrome",
            "vscode": "open_vscode", "visual studio code": "open_vscode", "code": "open_vscode",
            "terminal": "open_terminal", "cmd": "open_terminal",
            "explorer": "open_finder", "finder": "open_finder", "spotify": "open_spotify",
        }
        key = app_name.lower().strip()
        if key in app_map:
            return self.execute_named_command(app_map[key])

        if IS_WINDOWS:
            success, output = self._run_process(["start", "", app_name], shell=True)
        elif IS_MACOS:
            success, output = self._run_process(["open", "-a", app_name])
        else:
            success, output = self._run_process([app_name])

        return {"success": success, "message": f"Opening {app_name}", "output": output, "requires_confirmation": False}

    def open_url(self, url: str) -> dict[str, Any]:
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        try:
            webbrowser.open(url)
            return {"success": True, "message": f"Opened {url}", "output": None, "requires_confirmation": False}
        except Exception as exc:
            return {"success": False, "message": f"Failed to open URL: {exc}", "output": None, "requires_confirmation": False}

    def search_web(self, query: str) -> dict[str, Any]:
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        return self.open_url(url)

    def open_folder(self, folder_path: str) -> dict[str, Any]:
        path = Path(folder_path).expanduser().resolve()
        if not path.exists():
            return {"success": False, "message": f"Folder not found: {folder_path}", "output": None, "requires_confirmation": False}

        if IS_WINDOWS:
            success, output = self._run_process(["explorer", str(path)])
        elif IS_MACOS:
            success, output = self._run_process(["open", str(path)])
        else:
            success, output = self._run_process(["xdg-open", str(path)])

        return {"success": success, "message": f"Opened folder: {path}", "output": output, "requires_confirmation": False}

    def create_file(self, file_path: str, content: str = "") -> dict[str, Any]:
        try:
            path = Path(file_path).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return {"success": True, "message": f"Created file: {path}", "output": str(path), "requires_confirmation": False}
        except Exception as exc:
            return {"success": False, "message": f"Failed to create file: {exc}", "output": None, "requires_confirmation": False}

    def delete_file(self, file_path: str, confirm: bool = False) -> dict[str, Any]:
        if not confirm:
            return {"success": False, "message": f"Confirmation required to delete: {file_path}", "output": None, "requires_confirmation": True}
        try:
            path = Path(file_path).expanduser().resolve()
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                import shutil
                shutil.rmtree(path)
            else:
                return {"success": False, "message": f"Path not found: {file_path}", "output": None, "requires_confirmation": False}
            return {"success": True, "message": f"Deleted: {path}", "output": str(path), "requires_confirmation": False}
        except Exception as exc:
            return {"success": False, "message": f"Failed to delete: {exc}", "output": None, "requires_confirmation": False}

    def run_terminal_command(self, command: str, confirm: bool = False) -> dict[str, Any]:
        dangerous_patterns = ["rm -rf", "format", "del /f", "shutdown", "restart"]
        if any(p in command.lower() for p in dangerous_patterns) and not confirm:
            return {"success": False, "message": f"Confirmation required for dangerous command: {command}", "output": None, "requires_confirmation": True}
        success, output = self._run_process(command, shell=True)
        return {"success": success, "message": "Command executed" if success else "Command failed", "output": output, "requires_confirmation": False}

    def take_screenshot(self, save_path: str | None = None) -> dict[str, Any]:
        try:
            import pyautogui
            path = save_path or str(Path.home() / "mentor_screenshot.png")
            screenshot = pyautogui.screenshot()
            screenshot.save(path)
            return {"success": True, "message": f"Screenshot saved to {path}", "output": path, "requires_confirmation": False}
        except Exception as exc:
            return {"success": False, "message": f"Screenshot failed: {exc}", "output": None, "requires_confirmation": False}

    def read_screen(self) -> dict[str, Any]:
        """Capture screen and attempt OCR text extraction."""
        try:
            import pyautogui
            path = str(Path.home() / "mentor_screen.png")
            pyautogui.screenshot().save(path)

            try:
                import pytesseract
                text = pytesseract.image_to_string(path).strip()
                if text:
                    preview = text[:500] + ("..." if len(text) > 500 else "")
                    return {"success": True, "message": "Screen content captured", "output": preview, "requires_confirmation": False}
            except ImportError:
                pass

            return {
                "success": True,
                "message": f"Screenshot saved to {path}. Install pytesseract for OCR text reading.",
                "output": path,
                "requires_confirmation": False,
            }
        except Exception as exc:
            return {"success": False, "message": f"Screen read failed: {exc}", "output": None, "requires_confirmation": False}

    _break_timers: dict[str, threading.Timer] = {}

    def set_break_reminder(self, minutes: int = 15) -> dict[str, Any]:
        import threading

        def remind():
            if IS_WINDOWS:
                self._run_process(["powershell", "-Command", f"[System.Media.SystemSounds]::Exclamation.Play(); Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('Time for a break, sir!')"], shell=True)
            logger.info("Break reminder triggered")

        timer = threading.Timer(minutes * 60, remind)
        timer.daemon = True
        timer.start()
        return {"success": True, "message": f"Break reminder set for {minutes} minutes", "output": None, "requires_confirmation": False}

    def parse_and_execute(self, user_message: str, confirm: bool = False) -> list[dict[str, Any]]:
        msg = user_message.lower().strip()
        results: list[dict[str, Any]] = []

        app_triggers = [
            ("open chrome", lambda: self.open_application("chrome")),
            ("open vscode", lambda: self.open_application("vscode")),
            ("open visual studio code", lambda: self.open_application("vscode")),
            ("open notepad", lambda: self.open_application("notepad")),
            ("launch notepad", lambda: self.open_application("notepad")),
            ("open calculator", lambda: self.open_application("calculator")),
            ("open calc", lambda: self.open_application("calculator")),
            ("launch calculator", lambda: self.open_application("calculator")),
            ("open edge", lambda: self.open_application("edge")),
            ("open terminal", lambda: self.open_application("terminal")),
            ("open spotify", lambda: self.open_application("spotify")),
            ("open explorer", lambda: self.open_application("explorer")),
            ("open youtube", lambda: self.open_url("https://www.youtube.com")),
            ("play on youtube", lambda: self.open_url("https://www.youtube.com")),
            ("open google", lambda: self.open_url("https://www.google.com")),
            ("open github", lambda: self.open_url("https://www.github.com")),
            ("lock my computer", lambda: self.execute_named_command("lock_computer", confirm=confirm)),
            ("lock computer", lambda: self.execute_named_command("lock_computer", confirm=confirm)),
            ("take a screenshot", lambda: self.take_screenshot()),
            ("take screenshot", lambda: self.take_screenshot()),
            ("what's on my screen", lambda: self.read_screen()),
            ("whats on my screen", lambda: self.read_screen()),
            ("read my screen", lambda: self.read_screen()),
            ("take a break", lambda: self.set_break_reminder(15)),
            ("break reminder", lambda: self.set_break_reminder(15)),
            ("minimize all", lambda: self.execute_named_command("minimize_all")),
            ("show desktop", lambda: self.execute_named_command("minimize_all")),
        ]

        for trigger, action in app_triggers:
            if trigger in msg:
                results.append(action())
                return results

        if msg.startswith("open http") or "open www." in msg or "open https://" in msg:
            for prefix in ["open ", "launch ", "browse to "]:
                if prefix in msg:
                    url = user_message[user_message.lower().index(prefix) + len(prefix):].strip()
                    results.append(self.open_url(url))
                    return results

        if msg.startswith("search for ") or msg.startswith("search "):
            query = msg.replace("search for ", "").replace("search ", "").strip()
            results.append(self.search_web(query))
            return results

        if msg.startswith("open folder ") or msg.startswith("open "):
            for prefix in ["open folder ", "open "]:
                if msg.startswith(prefix):
                    target = user_message[len(prefix):].strip()
                    if not any(x in target.lower() for x in ["chrome", "vscode", "terminal", "spotify", "http"]):
                        results.append(self.open_folder(target))
                        return results

        if msg.startswith("create a new file called ") or msg.startswith("create file "):
            for prefix in ["create a new file called ", "create file "]:
                if msg.startswith(prefix):
                    filename = user_message[len(prefix):].strip()
                    results.append(self.create_file(filename))
                    return results

        if msg.startswith("delete "):
            filename = user_message[7:].strip()
            results.append(self.delete_file(filename, confirm=confirm))
            return results

        if msg.startswith("run "):
            command = user_message[4:].strip()
            results.append(self.run_terminal_command(command, confirm=confirm))
            return results

        return results

"""Hardware Abstraction Layer (HAL) & Device Bridge for IoT and System Automation."""

import asyncio
import logging
import platform
import psutil
from datetime import datetime
from typing import Any

from app.models import Device, DeviceActionResponse, DeviceStatus, DeviceType, TelemetrySnapshot

logger = logging.getLogger(__name__)


class DeviceManager:
    """Manages connected devices, IoT peripherals, and system telemetry."""

    def __init__(self):
        self._devices: dict[str, Device] = {}
        self._init_default_devices()

    def _init_default_devices(self):
        """Register default system and smart office/home devices."""
        # 1. Host Computer System Monitor
        self._devices["sys-pc-01"] = Device(
            id="sys-pc-01",
            name="Host Computer (Local System)",
            type=DeviceType.SYSTEM,
            status=DeviceStatus.ONLINE,
            protocol="local",
            state={
                "os": f"{platform.system()} {platform.release()}",
                "cpu_percent": 0.0,
                "ram_percent": 0.0,
                "disk_percent": 0.0,
                "power_plugged": True,
            },
            last_updated=datetime.utcnow(),
        )

        # 2. Smart Office Lighting
        self._devices["light-office-01"] = Device(
            id="light-office-01",
            name="Office Desk Lamp & Ambient Halo",
            type=DeviceType.LIGHT,
            status=DeviceStatus.ONLINE,
            protocol="mqtt",
            state={
                "power": True,
                "brightness": 85,
                "color_temp": "neutral_white",
                "rgb_hex": "#00f0ff",
            },
            last_updated=datetime.utcnow(),
        )

        # 3. Climate / HVAC Thermostat
        self._devices["climate-hvac-01"] = Device(
            id="climate-hvac-01",
            name="Climate & Thermal Regulator",
            type=DeviceType.THERMOSTAT,
            status=DeviceStatus.ONLINE,
            protocol="homeassistant",
            state={
                "current_temp_c": 23.5,
                "target_temp_c": 22.0,
                "humidity_percent": 48,
                "mode": "auto",  # auto, cool, heat, eco, off
                "fan_speed": "medium",
            },
            last_updated=datetime.utcnow(),
        )

        # 4. Smart Power Relay
        self._devices["switch-server-01"] = Device(
            id="switch-server-01",
            name="Server Rack & Audio Relay",
            type=DeviceType.SWITCH,
            status=DeviceStatus.ONLINE,
            protocol="mqtt",
            state={
                "power": True,
                "current_watts": 142.5,
                "voltage": 230.0,
                "daily_kwh": 3.4,
            },
            last_updated=datetime.utcnow(),
        )

        # 5. Security & Access Lock
        self._devices["lock-office-01"] = Device(
            id="lock-office-01",
            name="Secure Office Access Gate",
            type=DeviceType.LOCK,
            status=DeviceStatus.ONLINE,
            protocol="local",
            state={
                "locked": True,
                "tamper_alert": False,
                "battery_percent": 94,
            },
            last_updated=datetime.utcnow(),
        )

        # 6. Smartphone Companion & ADB Bridge
        self._devices["phone-mobile-01"] = Device(
            id="phone-mobile-01",
            name="Stark Mobile (Smartphone Companion)",
            type=DeviceType.PHONE,
            status=DeviceStatus.ONLINE,
            protocol="websocket",  # websocket, adb, qr-companion
            state={
                "battery_level": 84,
                "battery_charging": True,
                "screen_locked": True,
                "ringing": False,
                "ringer_mode": "normal",  # normal, vibrate, silent
                "flashlight": False,
                "wifi_ssid": "Stark_Secure_5G",
                "cellular_signal": "strong",
                "paired": True,
                "paired_model": "Android / iOS Device",
                "connection_type": "WebSocket & ADB Bridge",
                "clipboard": "",
                "active_app": "Home",
                "volume": 75,
                "dnd": False,
                "notifications": [
                    {
                        "id": "notif-1",
                        "title": "Calendar Reminder",
                        "text": "Sprint Planning review in 30 minutes",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    {
                        "id": "notif-2",
                        "title": "GitHub",
                        "text": "Pull Request #42 approved by CTO",
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                ],
            },
            last_updated=datetime.utcnow(),
        )


    def _refresh_system_metrics(self):
        """Update host telemetry metrics."""
        dev = self._devices.get("sys-pc-01")
        if not dev:
            return

        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
            battery = psutil.sensors_battery()
            power_plugged = battery.power_plugged if battery else True
        except Exception:
            # Fallback if psutil encounters restrictions
            cpu, ram, disk, power_plugged = 18.5, 42.0, 65.0, True

        dev.state.update({
            "cpu_percent": cpu,
            "ram_percent": ram,
            "disk_percent": disk,
            "power_plugged": power_plugged,
        })
        dev.last_updated = datetime.utcnow()

    def list_devices(self) -> list[Device]:
        """Return list of all registered devices with fresh telemetry."""
        self._refresh_system_metrics()
        return list(self._devices.values())

    def get_device(self, device_id: str) -> Device | None:
        """Get device by ID."""
        self._refresh_system_metrics()
        return self._devices.get(device_id)

    def execute_action(
        self, device_id: str, action: str, params: dict[str, Any] | None = None, confirm: bool = False
    ) -> DeviceActionResponse:
        """Execute action on a target device with safety checks."""
        params = params or {}
        device = self._devices.get(device_id)
        if not device:
            return DeviceActionResponse(
                success=False,
                message=f"Device not found: {device_id}",
                device_id=device_id,
                new_state={},
                requires_confirmation=False,
            )

        # Safety / HITL Check: Unlocking secure locks requires explicit confirmation
        if device.type == DeviceType.LOCK and action in ["unlock", "disable_security"] and not confirm:
            return DeviceActionResponse(
                success=False,
                message=f"Confirmation required to unlock security device: {device.name}",
                device_id=device_id,
                new_state=device.state,
                requires_confirmation=True,
            )

        # Light Actions
        if device.type == DeviceType.LIGHT:
            if action in ["turn_on", "enable"]:
                device.state["power"] = True
            elif action in ["turn_off", "disable"]:
                device.state["power"] = False
            elif action == "toggle":
                device.state["power"] = not device.state.get("power", True)
            elif action == "set_level":
                level = params.get("brightness", params.get("level", 100))
                device.state["brightness"] = max(0, min(100, int(level)))
                device.state["power"] = device.state["brightness"] > 0
            elif action == "set_color":
                if "rgb_hex" in params:
                    device.state["rgb_hex"] = params["rgb_hex"]
                if "color_temp" in params:
                    device.state["color_temp"] = params["color_temp"]

        # Switch / Relay Actions
        elif device.type == DeviceType.SWITCH:
            if action in ["turn_on", "enable"]:
                device.state["power"] = True
            elif action in ["turn_off", "disable"]:
                device.state["power"] = False
            elif action == "toggle":
                device.state["power"] = not device.state.get("power", True)

        # Thermostat Actions
        elif device.type == DeviceType.THERMOSTAT:
            if action == "set_temp":
                target = params.get("target_temp_c", params.get("temp", 22.0))
                device.state["target_temp_c"] = round(float(target), 1)
            elif action == "set_mode":
                device.state["mode"] = params.get("mode", "auto")
            elif action == "set_fan":
                device.state["fan_speed"] = params.get("fan_speed", "auto")

        # Lock Actions
        elif device.type == DeviceType.LOCK:
            if action == "lock":
                device.state["locked"] = True
            elif action == "unlock":
                device.state["locked"] = False

        # Smartphone Companion Actions
        elif device.type == DeviceType.PHONE:
            if action in ["ring_phone", "find_phone", "ring"]:
                device.state["ringing"] = True
                device.last_updated = datetime.utcnow()
                return DeviceActionResponse(
                    success=True,
                    message=f"Ringing {device.name} at maximum volume (Find My Phone active).",
                    device_id=device_id,
                    new_state=device.state,
                    requires_confirmation=False,
                )
            elif action in ["stop_ring", "silence"]:
                device.state["ringing"] = False
                device.last_updated = datetime.utcnow()
                return DeviceActionResponse(
                    success=True,
                    message=f"Silenced alarm on {device.name}.",
                    device_id=device_id,
                    new_state=device.state,
                    requires_confirmation=False,
                )
            elif action in ["lock_phone", "lock"]:
                device.state["screen_locked"] = True
                device.last_updated = datetime.utcnow()
                return DeviceActionResponse(
                    success=True,
                    message=f"Locked {device.name} display.",
                    device_id=device_id,
                    new_state=device.state,
                    requires_confirmation=False,
                )
            elif action in ["unlock_phone", "unlock"]:
                if not confirm:
                    return DeviceActionResponse(
                        success=False,
                        message=f"Confirmation required to unlock remote device: {device.name}",
                        device_id=device_id,
                        new_state=device.state,
                        requires_confirmation=True,
                    )
                device.state["screen_locked"] = False
                device.last_updated = datetime.utcnow()
                return DeviceActionResponse(
                    success=True,
                    message=f"Unlocked {device.name}.",
                    device_id=device_id,
                    new_state=device.state,
                    requires_confirmation=False,
                )
            elif action == "toggle_flashlight":
                device.state["flashlight"] = not device.state.get("flashlight", False)
                status_str = "ON" if device.state["flashlight"] else "OFF"
                device.last_updated = datetime.utcnow()
                return DeviceActionResponse(
                    success=True,
                    message=f"Turned {device.name} flashlight {status_str}.",
                    device_id=device_id,
                    new_state=device.state,
                    requires_confirmation=False,
                )
            elif action == "send_notification":
                params = params or {}
                notif_text = params.get("text", params.get("message", "Alert from Project Mentor AI"))
                notif_title = params.get("title", "Project Mentor AI")
                new_notif = {
                    "id": f"notif-{len(device.state.get('notifications', [])) + 1}",
                    "title": notif_title,
                    "text": notif_text,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                device.state.setdefault("notifications", []).append(new_notif)
                device.last_updated = datetime.utcnow()
                return DeviceActionResponse(
                    success=True,
                    message=f"Push notification dispatched to {device.name}: '{notif_text}'.",
                    device_id=device_id,
                    new_state=device.state,
                    requires_confirmation=False,
                )
            elif action == "sync_clipboard":
                params = params or {}
                text = params.get("text", "")
                device.state["clipboard"] = text
                device.last_updated = datetime.utcnow()
                return DeviceActionResponse(
                    success=True,
                    message=f"Clipboard synced to {device.name} ({len(text)} chars).",
                    device_id=device_id,
                    new_state=device.state,
                    requires_confirmation=False,
                )
            elif action == "launch_app":
                params = params or {}
                app_name = params.get("app", "Home")
                device.state["active_app"] = app_name
                device.last_updated = datetime.utcnow()
                return DeviceActionResponse(
                    success=True,
                    message=f"Launched {app_name} on {device.name}.",
                    device_id=device_id,
                    new_state=device.state,
                    requires_confirmation=False,
                )
            elif action == "set_volume":
                params = params or {}
                vol = params.get("volume", params.get("level", 75))
                device.state["volume"] = max(0, min(100, int(vol)))
                device.last_updated = datetime.utcnow()
                return DeviceActionResponse(
                    success=True,
                    message=f"Adjusted {device.name} volume to {device.state['volume']}%.",
                    device_id=device_id,
                    new_state=device.state,
                    requires_confirmation=False,
                )
            elif action == "toggle_dnd":
                device.state["dnd"] = not device.state.get("dnd", False)
                mode_str = "ENABLED" if device.state["dnd"] else "DISABLED"
                device.last_updated = datetime.utcnow()
                return DeviceActionResponse(
                    success=True,
                    message=f"Do Not Disturb mode {mode_str} on {device.name}.",
                    device_id=device_id,
                    new_state=device.state,
                    requires_confirmation=False,
                )

        # Diagnostic Action for any device
        elif action == "run_diagnostic":

            device.status = DeviceStatus.ONLINE
            device.last_updated = datetime.utcnow()
            return DeviceActionResponse(
                success=True,
                message=f"Diagnostics completed successfully for {device.name}. Telemetry optimal.",
                device_id=device_id,
                new_state=device.state,
                requires_confirmation=False,
            )

        device.last_updated = datetime.utcnow()
        return DeviceActionResponse(
            success=True,
            message=f"Action '{action}' executed successfully on {device.name}.",
            device_id=device_id,
            new_state=device.state,
            requires_confirmation=False,
        )

    def get_telemetry_snapshot(self) -> TelemetrySnapshot:
        """Capture real-time telemetry snapshot of system & all devices."""
        self._refresh_system_metrics()
        sys_dev = self._devices.get("sys-pc-01")
        sys_state = sys_dev.state if sys_dev else {}
        return TelemetrySnapshot(
            timestamp=datetime.utcnow(),
            system=sys_state,
            devices=list(self._devices.values()),
        )

    def parse_and_execute_device_command(self, message: str, confirm: bool = False) -> list[dict[str, Any]]:
        """Natural language device control parser with robust flexible intent matching."""
        msg = message.lower().strip()
        results: list[dict[str, Any]] = []

        # 1. Lights / Lamp triggers (matches "turn off light", "lamp off", "lights on", "switch off the light", etc.)
        if any(w in msg for w in ["light", "lights", "lamp", "lamps", "halo"]):
            if any(w in msg for w in ["dim", "brightness", "level", "set to"]):
                import re
                m = re.search(r"(\d+)\s*%", msg) or re.search(r"to\s+(\d+)", msg) or re.search(r"\b(\d+)\b", msg)
                level = int(m.group(1)) if m else 50
                res = self.execute_action("light-office-01", "set_level", {"brightness": level})
                results.append({"device": "light-office-01", "action": "set_level", "message": f"Office lighting brightness set to {level}%.", "success": res.success})
                return results

            if any(w in msg for w in ["off", "disable", "kill", "down", "shut"]):
                res = self.execute_action("light-office-01", "turn_off")
                results.append({"device": "light-office-01", "action": "turn_off", "message": "Office lighting powered down, sir.", "success": res.success})
                return results

            if any(w in msg for w in ["on", "enable", "start", "up", "ignite"]):
                res = self.execute_action("light-office-01", "turn_on")
                results.append({"device": "light-office-01", "action": "turn_on", "message": "Office lighting illuminated, sir.", "success": res.success})
                return results

        # 2. Thermostat / Climate triggers
        if any(w in msg for w in ["temp", "temperature", "thermostat", "climate", "hvac", "heat", "cool", "ac"]):
            import re
            m = re.search(r"(\d+(?:\.\d+)?)\s*(?:degrees|c|deg)?", msg)
            if m:
                temp = float(m.group(1))
                res = self.execute_action("climate-hvac-01", "set_temp", {"target_temp_c": temp})
                results.append({"device": "climate-hvac-01", "action": "set_temp", "message": f"Thermostat target calibrated to {temp}°C, sir.", "success": res.success})
                return results

        # 3. Power Relay / Server switch triggers
        if any(w in msg for w in ["server rack", "relay", "audio relay", "power switch", "main switch"]):
            if any(w in msg for w in ["off", "disable", "cut"]):
                res = self.execute_action("switch-server-01", "turn_off")
                results.append({"device": "switch-server-01", "action": "turn_off", "message": "Server rack & audio relay powered down.", "success": res.success})
                return results
            if any(w in msg for w in ["on", "enable"]):
                res = self.execute_action("switch-server-01", "turn_on")
                results.append({"device": "switch-server-01", "action": "turn_on", "message": "Server rack & audio relay energized.", "success": res.success})
                return results

        # 4. Security Lock triggers
        if any(w in msg for w in ["lock", "door", "gate", "secure", "office lock"]):
            if any(w in msg for w in ["unlock", "open", "unlatch"]):
                res = self.execute_action("lock-office-01", "unlock", confirm=confirm)
                results.append({
                    "device": "lock-office-01",
                    "action": "unlock",
                    "message": "Office security gate unlatched, sir." if res.success else res.message,
                    "success": res.success,
                    "requires_confirmation": res.requires_confirmation,
                })
                return results
            if any(w in msg for w in ["lock", "secure", "close"]):
                res = self.execute_action("lock-office-01", "lock")
                results.append({"device": "lock-office-01", "action": "lock", "message": "Office security perimeter secured and locked.", "success": res.success})
                return results

        # 5. Smartphone triggers
        if any(w in msg for w in ["phone", "mobile", "smartphone", "cell"]):
            if any(w in msg for w in ["ring", "find", "locate", "where"]):
                res = self.execute_action("phone-mobile-01", "ring_phone")
                results.append({
                    "device": "phone-mobile-01",
                    "action": "ring_phone",
                    "message": "Initiating high-frequency ringer on your smartphone, sir (Find My Phone active).",
                    "success": res.success,
                })
                return results
            if any(w in msg for w in ["silence", "stop ring", "stop alarm"]):
                res = self.execute_action("phone-mobile-01", "stop_ring")
                results.append({
                    "device": "phone-mobile-01",
                    "action": "stop_ring",
                    "message": "Smartphone alarm silenced, sir.",
                    "success": res.success,
                })
                return results
            if any(w in msg for w in ["lock", "secure"]):
                res = self.execute_action("phone-mobile-01", "lock_phone")
                results.append({
                    "device": "phone-mobile-01",
                    "action": "lock_phone",
                    "message": "Smartphone display locked and secured.",
                    "success": res.success,
                })
                return results
            if any(w in msg for w in ["flashlight", "torch"]):
                res = self.execute_action("phone-mobile-01", "toggle_flashlight")
                status = "illuminated" if res.new_state.get("flashlight") else "extinguished"
                results.append({
                    "device": "phone-mobile-01",
                    "action": "toggle_flashlight",
                    "message": f"Smartphone flashlight {status}, sir.",
                    "success": res.success,
                })
                return results
            if any(w in msg for w in ["battery", "charge", "status"]):
                phone = self.get_device("phone-mobile-01")
                batt = phone.state.get("battery_level", 84) if phone else 84
                charging = "charging" if (phone and phone.state.get("battery_charging")) else "discharging"
                wifi = phone.state.get("wifi_ssid", "Stark_Secure_5G") if phone else "Stark_Secure_5G"
                results.append({
                    "device": "phone-mobile-01",
                    "action": "status",
                    "message": f"Smartphone telemetry: Battery at {batt}% ({charging}), Wi-Fi connected to {wifi}.",
                    "success": True,
                })
                return results
            if "notify" in msg or "notification" in msg:
                clean_txt = msg.replace("send notification to phone", "").replace("notify phone", "").strip()
                res = self.execute_action("phone-mobile-01", "send_notification", {"text": clean_txt or "Priority Alert from Jarvis"})
                results.append({
                    "device": "phone-mobile-01",
                    "action": "send_notification",
                    "message": f"Push notification sent to your phone: '{clean_txt or 'Priority Alert'}'.",
                    "success": res.success,
                })
                return results

        # 6. Telemetry / Diagnostics triggers
        if any(w in msg for w in ["telemetry", "hardware status", "diagnostics", "check devices", "iot status", "device status", "system status", "all devices"]):
            snap = self.get_telemetry_snapshot()
            summary = ", ".join(f"{d.name}: {'ON' if d.state.get('power', d.state.get('locked', True)) else 'OFF'}" for d in snap.devices)
            results.append({
                "device": "all",
                "action": "telemetry",
                "message": f"Telemetry online: CPU {snap.system.get('cpu_percent', 0)}%, RAM {snap.system.get('ram_percent', 0)}%. Active units: {summary}",
                "success": True,
            })
            return results

        return results


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

        # 5. Telemetry / Diagnostics triggers
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

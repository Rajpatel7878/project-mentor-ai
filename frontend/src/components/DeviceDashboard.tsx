'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  Cpu,
  HardDrive,
  Lightbulb,
  Lock,
  Power,
  RefreshCw,
  Server,
  ShieldCheck,
  Sliders,
  Thermometer,
  Unlock,
  Zap,
} from 'lucide-react';
import { fetchTelemetry, executeDeviceAction, type Device, type TelemetrySnapshot } from '@/lib/api';
import { HitlConfirmationModal } from './HitlConfirmationModal';

export function DeviceDashboard() {
  const [telemetry, setTelemetry] = useState<TelemetrySnapshot | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  // HITL State
  const [hitlModal, setHitlModal] = useState<{
    isOpen: boolean;
    deviceId: string;
    action: string;
    title: string;
    description: string;
    params?: Record<string, any>;
  }>({
    isOpen: false,
    deviceId: '',
    action: '',
    title: '',
    description: '',
  });

  const loadTelemetry = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await fetchTelemetry();
      setTelemetry(data);
    } catch (err) {
      console.error('Telemetry fetch failed', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTelemetry();
    const interval = setInterval(loadTelemetry, 5000);
    return () => clearInterval(interval);
  }, [loadTelemetry]);

  const handleAction = async (
    deviceId: string,
    action: string,
    params: Record<string, any> = {},
    confirm: boolean = false
  ) => {
    try {
      setActionInProgress(`${deviceId}:${action}`);
      const res = await executeDeviceAction(deviceId, action, params, confirm);

      if (res.requires_confirmation) {
        setHitlModal({
          isOpen: true,
          deviceId,
          action,
          title: `Authorize ${action.toUpperCase()} on ${deviceId}`,
          description: res.message,
          params,
        });
        return;
      }

      setFeedbackMessage(res.message);
      setTimeout(() => setFeedbackMessage(null), 4000);
      await loadTelemetry();
    } catch (err: any) {
      setFeedbackMessage(err.message || 'Action failed');
      setTimeout(() => setFeedbackMessage(null), 4000);
    } finally {
      setActionInProgress(null);
    }
  };

  const confirmHitlAction = async () => {
    const { deviceId, action, params } = hitlModal;
    setHitlModal((prev) => ({ ...prev, isOpen: false }));
    await handleAction(deviceId, action, params, true);
  };

  const hostDevice = telemetry?.devices.find((d) => d.id === 'sys-pc-01');
  const otherDevices = telemetry?.devices.filter((d) => d.id !== 'sys-pc-01') || [];

  return (
    <div className="flex-1 flex flex-col p-6 overflow-y-auto space-y-6">
      {/* Header & Quick Status */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl tracking-wider glow-text">
            HARDWARE & IOT INTEGRATION BRIDGE
          </h2>
          <p className="text-xs text-white/50 tracking-wider">
            BIDIRECTIONAL DEVICE ABSTRACTION LAYER (HAL) • LIVE TELEMETRY
          </p>
        </div>
        <div className="flex items-center gap-3">
          {feedbackMessage && (
            <motion.span
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-xs font-mono text-cyan-glow bg-cyan-950/60 border border-cyan-500/30 px-3 py-1.5 rounded-lg"
            >
              {feedbackMessage}
            </motion.span>
          )}
          <button
            onClick={loadTelemetry}
            disabled={isLoading}
            className="flex items-center gap-2 px-3 py-1.5 glass-panel rounded-lg hover:bg-white/10 text-xs font-display tracking-wider text-cyan-glow transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            SYNC TELEMETRY
          </button>
        </div>
      </div>

      {/* Host System Monitor Card */}
      {hostDevice && (
        <div className="glass-panel rounded-xl p-5 border border-cyan-glow/20 holographic-gradient">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-cyan-500/20 text-cyan-glow">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-display text-sm tracking-wide text-white/90">
                  {hostDevice.name}
                </h3>
                <span className="text-xs text-cyan-glow/60 font-mono">
                  {hostDevice.state.os || 'Windows System'} • Protocol: Local Bus
                </span>
              </div>
            </div>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-green-500/20 text-green-400 border border-green-500/30">
              OPTIMAL
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* CPU */}
            <div className="p-3 rounded-lg bg-black/30 border border-white/5 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-white/60 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-cyan-glow" /> CPU Load
                </span>
                <span className="font-mono text-cyan-glow">
                  {hostDevice.state.cpu_percent?.toFixed(1) || '0.0'}%
                </span>
              </div>
              <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-cyan-500 to-blue-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, hostDevice.state.cpu_percent || 0)}%` }}
                />
              </div>
            </div>

            {/* RAM */}
            <div className="p-3 rounded-lg bg-black/30 border border-white/5 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-white/60 flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-blue-400" /> RAM Allocated
                </span>
                <span className="font-mono text-blue-400">
                  {hostDevice.state.ram_percent?.toFixed(1) || '0.0'}%
                </span>
              </div>
              <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, hostDevice.state.ram_percent || 0)}%` }}
                />
              </div>
            </div>

            {/* Disk */}
            <div className="p-3 rounded-lg bg-black/30 border border-white/5 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-white/60 flex items-center gap-1.5">
                  <HardDrive className="w-3.5 h-3.5 text-emerald-400" /> Disk Volume
                </span>
                <span className="font-mono text-emerald-400">
                  {hostDevice.state.disk_percent?.toFixed(1) || '0.0'}%
                </span>
              </div>
              <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-emerald-500 to-teal-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, hostDevice.state.disk_percent || 0)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Connected IoT Devices Grid */}
      <div>
        <h3 className="font-display text-xs tracking-widest text-cyan-glow/70 uppercase mb-3">
          PERIPHERAL ACTUATORS & PROTOCOL BUS
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {otherDevices.map((dev) => (
            <div
              key={dev.id}
              className="glass-panel rounded-xl p-5 border border-white/10 flex flex-col justify-between space-y-4 hover:border-cyan-glow/30 transition-all"
            >
              {/* Card Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2.5 rounded-xl border ${
                      dev.state.power || dev.state.locked
                        ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-glow'
                        : 'bg-white/5 border-white/10 text-white/40'
                    }`}
                  >
                    {dev.type === 'light' && <Lightbulb className="w-5 h-5" />}
                    {dev.type === 'thermostat' && <Thermometer className="w-5 h-5" />}
                    {dev.type === 'switch' && <Server className="w-5 h-5" />}
                    {dev.type === 'lock' && (dev.state.locked ? <Lock className="w-5 h-5" /> : <Unlock className="w-5 h-5 text-amber-400" />)}
                  </div>
                  <div>
                    <h4 className="font-display text-sm text-white/90">{dev.name}</h4>
                    <span className="text-xs text-white/40 font-mono uppercase">
                      ID: {dev.id} • Protocol: {dev.protocol}
                    </span>
                  </div>
                </div>

                <span
                  className={`text-xs px-2 py-0.5 rounded font-mono ${
                    dev.status === 'online'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-red-500/20 text-red-400 border border-red-500/30'
                  }`}
                >
                  {dev.status.toUpperCase()}
                </span>
              </div>

              {/* Dynamic State Controls */}
              {/* 1. LIGHT CONTROLS */}
              {dev.type === 'light' && (
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-white/60">Illumination Power:</span>
                    <button
                      onClick={() => handleAction(dev.id, 'toggle')}
                      className={`flex items-center gap-1.5 px-3 py-1 rounded-lg font-display text-xs tracking-wider transition-all ${
                        dev.state.power
                          ? 'bg-cyan-500 text-black font-semibold shadow-md shadow-cyan-500/30'
                          : 'bg-white/10 text-white/60 hover:bg-white/20'
                      }`}
                    >
                      <Power className="w-3.5 h-3.5" />
                      {dev.state.power ? 'ACTIVE' : 'STANDBY'}
                    </button>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-white/60">
                      <span>Brightness Level</span>
                      <span className="font-mono text-cyan-glow">{dev.state.brightness}%</span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={dev.state.brightness || 0}
                      onChange={(e) =>
                        handleAction(dev.id, 'set_level', { brightness: parseInt(e.target.value) })
                      }
                      className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                    />
                  </div>
                </div>
              )}

              {/* 2. THERMOSTAT CONTROLS */}
              {dev.type === 'thermostat' && (
                <div className="space-y-3 pt-2">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2 rounded-lg bg-black/30 border border-white/5">
                      <span className="text-white/40 block">Current Temp</span>
                      <span className="font-mono text-base text-white/90">
                        {dev.state.current_temp_c}°C
                      </span>
                    </div>
                    <div className="p-2 rounded-lg bg-black/30 border border-white/5">
                      <span className="text-white/40 block">Relative Humidity</span>
                      <span className="font-mono text-base text-cyan-glow">
                        {dev.state.humidity_percent}%
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <span className="text-white/60">Target Climate (°C):</span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() =>
                          handleAction(dev.id, 'set_temp', {
                            target_temp_c: (dev.state.target_temp_c || 22) - 0.5,
                          })
                        }
                        className="w-7 h-7 rounded bg-white/10 hover:bg-white/20 flex items-center justify-center font-bold"
                      >
                        -
                      </button>
                      <span className="font-mono text-sm font-semibold text-cyan-glow px-2">
                        {dev.state.target_temp_c}°C
                      </span>
                      <button
                        onClick={() =>
                          handleAction(dev.id, 'set_temp', {
                            target_temp_c: (dev.state.target_temp_c || 22) + 0.5,
                          })
                        }
                        className="w-7 h-7 rounded bg-white/10 hover:bg-white/20 flex items-center justify-center font-bold"
                      >
                        +
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* 3. SMART SWITCH CONTROLS */}
              {dev.type === 'switch' && (
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-white/60">Relay Power Switch:</span>
                    <button
                      onClick={() => handleAction(dev.id, 'toggle')}
                      className={`flex items-center gap-1.5 px-3 py-1 rounded-lg font-display text-xs tracking-wider transition-all ${
                        dev.state.power
                          ? 'bg-emerald-500 text-black font-semibold'
                          : 'bg-white/10 text-white/60'
                      }`}
                    >
                      <Zap className="w-3.5 h-3.5" />
                      {dev.state.power ? 'ENERGIZED' : 'OPEN CIRCUIT'}
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    <div className="p-2 rounded bg-black/30 border border-white/5">
                      <span className="text-white/40 block">Power Draw</span>
                      <span className="text-emerald-400">{dev.state.current_watts} W</span>
                    </div>
                    <div className="p-2 rounded bg-black/30 border border-white/5">
                      <span className="text-white/40 block">Line Potential</span>
                      <span className="text-white/90">{dev.state.voltage} V</span>
                    </div>
                  </div>
                </div>
              )}

              {/* 4. SECURITY LOCK CONTROLS (HITL Protected) */}
              {dev.type === 'lock' && (
                <div className="space-y-3 pt-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-white/60">Perimeter Status:</span>
                    <span
                      className={`font-mono font-semibold ${
                        dev.state.locked ? 'text-green-400' : 'text-amber-400'
                      }`}
                    >
                      {dev.state.locked ? 'ENGAGED / LOCKED' : 'UNSECURED / OPEN'}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {dev.state.locked ? (
                      <button
                        onClick={() => handleAction(dev.id, 'unlock')}
                        className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 text-xs font-display tracking-wider transition-all"
                      >
                        <Unlock className="w-4 h-4" />
                        REQUEST UNLOCK (HITL CONFIRMATION)
                      </button>
                    ) : (
                      <button
                        onClick={() => handleAction(dev.id, 'lock')}
                        className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-green-500/20 hover:bg-green-500/30 border border-green-500/40 text-green-300 text-xs font-display tracking-wider transition-all"
                      >
                        <Lock className="w-4 h-4" />
                        ENGAGE SECURITY LOCK
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Card Footer: Diagnostic Trigger */}
              <div className="pt-2 border-t border-white/5 flex justify-end">
                <button
                  onClick={() => handleAction(dev.id, 'run_diagnostic')}
                  disabled={actionInProgress === `${dev.id}:run_diagnostic`}
                  className="text-xs text-white/50 hover:text-cyan-glow flex items-center gap-1 font-mono transition-colors"
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Run Self-Test
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Human-in-the-Loop Modal */}
      <HitlConfirmationModal
        isOpen={hitlModal.isOpen}
        title={hitlModal.title}
        description={hitlModal.description}
        actionPayload={hitlModal.params}
        onConfirm={confirmHitlAction}
        onCancel={() => setHitlModal((prev) => ({ ...prev, isOpen: false }))}
      />
    </div>
  );
}

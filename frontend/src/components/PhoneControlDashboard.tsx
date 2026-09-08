'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Smartphone,
  Battery,
  BatteryCharging,
  Wifi,
  Signal,
  Bell,
  BellOff,
  Flashlight,
  Lock,
  Unlock,
  Volume2,
  VolumeX,
  Share2,
  QrCode,
  Send,
  Radio,
  CheckCircle,
  RefreshCw,
  Copy,
  Check,
} from 'lucide-react';
import {
  fetchPhoneStatus,
  executePhoneAction,
  pairPhone,
  type PhoneStatus,
  type PhoneNotification,
} from '@/lib/api';
import { jarvisAudio } from '@/lib/soundEffects';

const QUICK_APPS = [
  { name: 'WhatsApp', icon: '💬', color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' },
  { name: 'Google Maps', icon: '🗺️', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  { name: 'Camera', icon: '📷', color: 'bg-purple-500/20 text-purple-400 border-purple-500/30' },
  { name: 'Spotify', icon: '🎵', color: 'bg-green-500/20 text-green-400 border-green-500/30' },
  { name: 'Notes', icon: '📝', color: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
];

export function PhoneControlDashboard() {
  const [phone, setPhone] = useState<PhoneStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [clipboardText, setClipboardText] = useState('');
  const [clipboardCopied, setClipboardCopied] = useState(false);
  const [customNotification, setCustomNotification] = useState('');
  const [showQrModal, setShowQrModal] = useState(false);
  const [pairingData, setPairingData] = useState<{
    pairing_token: string;
    qr_data: string;
    companion_url: string;
  } | null>(null);

  const loadStatus = useCallback(async () => {
    try {
      const data = await fetchPhoneStatus();
      setPhone(data);
    } catch (err) {
      console.warn('Could not fetch phone status:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 5000);
    return () => clearInterval(interval);
  }, [loadStatus]);

  const handleAction = async (action: string, params: Record<string, any> = {}, confirm: boolean = false) => {
    setActionLoading(action);
    try {
      if (action === 'ring_phone') {
        jarvisAudio.playPhoneRing();
      } else {
        jarvisAudio.playSuccessChirp();
      }

      await executePhoneAction(action, params, confirm);
      await loadStatus();
    } catch (err) {
      console.error(`Action ${action} failed:`, err);
      jarvisAudio.playAlertSound();
    } finally {
      setActionLoading(null);
    }
  };

  const handleOpenPairing = async () => {
    try {
      jarvisAudio.playBootChime();
      const res = await pairPhone();
      setPairingData(res);
      setShowQrModal(true);
    } catch (err) {
      console.error('Pairing failed:', err);
      jarvisAudio.playAlertSound();
    }
  };

  const handleSyncClipboard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clipboardText.trim()) return;
    await handleAction('sync_clipboard', { text: clipboardText });
    setClipboardCopied(true);
    setTimeout(() => setClipboardCopied(false), 3000);
  };

  const handleSendNotification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customNotification.trim()) return;
    await handleAction('send_notification', { text: customNotification });
    setCustomNotification('');
  };

  const isRinging = phone?.state.ringing;
  const isLocked = phone?.state.screen_locked;
  const flashlightOn = phone?.state.flashlight;
  const batteryLevel = phone?.state.battery_level ?? 84;
  const isCharging = phone?.state.battery_charging ?? true;

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-y-auto space-y-6 pr-2">
      {/* Top Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-white/10 relative overflow-hidden">
        <div className="absolute -top-12 -right-12 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-display font-semibold tracking-wider bg-cyan-500/20 text-cyan-glow border border-cyan-500/30">
                SMARTPHONE BRIDGE & REMOTE
              </span>
              <span className="text-xs text-white/40">Protocol: WebSocket & ADB</span>
            </div>
            <h2 className="font-display text-xl font-bold tracking-wide glow-text text-white">
              Mobile Device Telemetry & Control Suite
            </h2>
            <p className="text-xs text-white/60 mt-1 max-w-2xl leading-relaxed">
              Seamlessly command and inspect your smartphone from JARVIS. Locate your phone with maximum
              alarm volume, sync clipboard text, toggle flashlights, and push notifications to your lock screen.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleOpenPairing}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-cyan-500/20 text-cyan-glow border border-cyan-500/30 hover:bg-cyan-500/30 text-xs font-display font-semibold tracking-wider uppercase transition-all"
            >
              <QrCode className="w-3.5 h-3.5" />
              Pair Phone (QR)
            </button>
            <button
              onClick={loadStatus}
              className="p-2 rounded-xl border border-white/10 text-white/60 hover:text-white hover:bg-white/5 transition-all"
              title="Refresh Telemetry"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid: Device Phone Mockup & Remote Control Deck */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
        {/* Left Column: Visual Smartphone Mockup HUD */}
        <div className="lg:col-span-5 flex flex-col items-center justify-center p-6 glass-panel rounded-2xl border border-white/10 relative overflow-hidden">
          {/* Audio Ringing Wave Pulse Animation */}
          {isRinging && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <span className="w-64 h-64 rounded-full border-2 border-red-500/40 animate-ping" />
              <span className="w-80 h-80 rounded-full border-2 border-cyan-500/30 animate-pulse absolute" />
            </div>
          )}

          {/* Smartphone Frame */}
          <div className="relative w-64 h-[440px] rounded-[36px] bg-black/90 border-4 border-cyan-500/40 shadow-2xl shadow-cyan-500/20 p-3 flex flex-col justify-between overflow-hidden">
            {/* Phone Speaker & Camera Notch */}
            <div className="absolute top-2 inset-x-0 mx-auto w-24 h-4 bg-black rounded-full border border-white/10 flex items-center justify-center gap-2 z-20">
              <div className="w-2.5 h-2.5 rounded-full bg-cyan-900 border border-cyan-400/40" />
              <div className="w-8 h-1 rounded-full bg-white/20" />
            </div>

            {/* Phone Screen Status Bar */}
            <div className="relative z-10 pt-4 flex items-center justify-between px-2 text-[10px] text-white/70 font-mono">
              <span>{new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
              <div className="flex items-center gap-2">
                <Wifi className="w-3 h-3 text-cyan-glow" />
                <Signal className="w-3 h-3 text-cyan-glow" />
                <div className="flex items-center gap-0.5">
                  <span>{batteryLevel}%</span>
                  {isCharging ? (
                    <BatteryCharging className="w-3.5 h-3.5 text-green-400" />
                  ) : (
                    <Battery className="w-3.5 h-3.5 text-cyan-glow" />
                  )}
                </div>
              </div>
            </div>

            {/* Screen Content Body */}
            <div className="relative z-10 flex-1 flex flex-col items-center justify-center text-center p-3 space-y-3">
              {isRinging ? (
                <div className="space-y-2 animate-bounce">
                  <div className="w-14 h-14 rounded-full bg-red-500/20 border border-red-500/60 mx-auto flex items-center justify-center text-red-400 shadow-lg shadow-red-500/30">
                    <Bell className="w-7 h-7 animate-wiggle" />
                  </div>
                  <div>
                    <h4 className="text-xs font-display font-bold text-red-400 uppercase tracking-widest">
                      FIND MY PHONE ACTIVE
                    </h4>
                    <p className="text-[10px] text-white/70">Ringing at 100% volume</p>
                  </div>
                  <button
                    onClick={() => handleAction('stop_ring')}
                    className="px-3 py-1 rounded-lg bg-red-500 text-black font-display font-bold text-[10px] uppercase tracking-wider"
                  >
                    Silence Alarm
                  </button>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="w-12 h-12 rounded-full bg-cyan-500/10 border border-cyan-500/30 mx-auto flex items-center justify-center text-cyan-glow">
                    <Smartphone className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="text-xs font-display font-bold text-white tracking-wide">
                      {phone?.name || 'Stark Mobile'}
                    </h4>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 font-mono">
                      SYNCED
                    </span>
                  </div>
                  <div className="p-2 rounded-xl bg-white/5 border border-white/5 text-[10px] text-left font-mono space-y-1">
                    <div className="text-white/40">Active App: <strong className="text-white">{phone?.state.active_app || 'Home'}</strong></div>
                    <div className="text-white/40">Lock: <strong className="text-white">{isLocked ? 'SECURED' : 'UNLOCKED'}</strong></div>
                    <div className="text-white/40">Flashlight: <strong className="text-cyan-glow">{flashlightOn ? 'ACTIVE' : 'OFF'}</strong></div>
                  </div>
                </div>
              )}
            </div>

            {/* Phone Home Bar */}
            <div className="w-20 h-1 bg-white/30 rounded-full mx-auto mb-1" />
          </div>

          <p className="text-[10px] text-white/40 mt-4 text-center">
            {phone?.state.paired_model || 'Android & iOS Companion Active'} • Wi-Fi: {phone?.state.wifi_ssid || 'Stark_Secure_5G'}
          </p>
        </div>

        {/* Right Column: Remote Control Action Deck */}
        <div className="lg:col-span-7 space-y-4">
          {/* Quick Remote Controls */}
          <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-3">
            <h3 className="text-xs font-display font-bold uppercase tracking-wider text-white flex items-center gap-2">
              <Radio className="w-4 h-4 text-cyan-glow" />
              Instant Remote Triggers
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {/* Find My Phone / Ring */}
              <button
                type="button"
                disabled={actionLoading === 'ring_phone'}
                onClick={() => handleAction(isRinging ? 'stop_ring' : 'ring_phone')}
                className={`p-3 rounded-xl border text-center transition-all ${
                  isRinging
                    ? 'bg-red-500/20 border-red-500 text-red-400 animate-pulse'
                    : 'bg-black/30 border-white/10 hover:border-cyan-500/50 hover:bg-cyan-500/10 text-white'
                }`}
              >
                <Bell className="w-5 h-5 mx-auto mb-1 text-cyan-glow" />
                <span className="text-[11px] font-display font-bold uppercase block">
                  {isRinging ? 'Silence' : 'Find Phone'}
                </span>
                <span className="text-[9px] text-white/40 block">Max Volume Ring</span>
              </button>

              {/* Lock Phone */}
              <button
                type="button"
                disabled={actionLoading === 'lock_phone'}
                onClick={() => handleAction('lock_phone')}
                className="p-3 rounded-xl bg-black/30 border border-white/10 hover:border-cyan-500/50 hover:bg-cyan-500/10 text-white text-center transition-all"
              >
                <Lock className="w-5 h-5 mx-auto mb-1 text-cyan-glow" />
                <span className="text-[11px] font-display font-bold uppercase block">Lock Screen</span>
                <span className="text-[9px] text-white/40 block">Secure Mobile</span>
              </button>

              {/* Flashlight */}
              <button
                type="button"
                disabled={actionLoading === 'toggle_flashlight'}
                onClick={() => handleAction('toggle_flashlight')}
                className={`p-3 rounded-xl border text-center transition-all ${
                  flashlightOn
                    ? 'bg-yellow-500/20 border-yellow-500 text-yellow-300'
                    : 'bg-black/30 border-white/10 hover:border-cyan-500/50 hover:bg-cyan-500/10 text-white'
                }`}
              >
                <Flashlight className="w-5 h-5 mx-auto mb-1 text-cyan-glow" />
                <span className="text-[11px] font-display font-bold uppercase block">Flashlight</span>
                <span className="text-[9px] text-white/40 block">
                  {flashlightOn ? 'Torch ON' : 'Torch OFF'}
                </span>
              </button>

              {/* Do Not Disturb */}
              <button
                type="button"
                disabled={actionLoading === 'toggle_dnd'}
                onClick={() => handleAction('toggle_dnd')}
                className="p-3 rounded-xl bg-black/30 border border-white/10 hover:border-cyan-500/50 hover:bg-cyan-500/10 text-white text-center transition-all"
              >
                {phone?.state.dnd ? (
                  <BellOff className="w-5 h-5 mx-auto mb-1 text-purple-400" />
                ) : (
                  <Volume2 className="w-5 h-5 mx-auto mb-1 text-cyan-glow" />
                )}
                <span className="text-[11px] font-display font-bold uppercase block">Silent / DND</span>
                <span className="text-[9px] text-white/40 block">Toggle Mode</span>
              </button>
            </div>
          </div>

          {/* Quick App Launcher */}
          <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-3">
            <h3 className="text-xs font-display font-bold uppercase tracking-wider text-white">
              Remote App Launcher (ADB / Companion)
            </h3>
            <div className="flex flex-wrap gap-2">
              {QUICK_APPS.map((app) => (
                <button
                  key={app.name}
                  type="button"
                  onClick={() => handleAction('launch_app', { app: app.name })}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-all hover:scale-105 ${app.color}`}
                >
                  <span>{app.icon}</span>
                  <span>{app.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Clipboard & Notification Dispatch */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Clipboard Sync */}
            <form onSubmit={handleSyncClipboard} className="glass-panel p-4 rounded-xl border border-white/10 space-y-2">
              <span className="text-[10px] font-display uppercase tracking-wider text-white/60 block">
                Sync Clipboard to Phone
              </span>
              <div className="flex items-center gap-1.5">
                <input
                  type="text"
                  value={clipboardText}
                  onChange={(e) => setClipboardText(e.target.value)}
                  placeholder="Paste URL, code, or note..."
                  className="flex-1 px-2.5 py-1.5 rounded-lg bg-black/40 border border-white/10 text-xs text-white placeholder-white/30 focus:border-cyan-500/60 focus:outline-none"
                />
                <button
                  type="submit"
                  className="p-2 rounded-lg bg-cyan-500/20 text-cyan-glow hover:bg-cyan-500/30 transition-all"
                  title="Send to Phone Clipboard"
                >
                  {clipboardCopied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </form>

            {/* Push Notification */}
            <form onSubmit={handleSendNotification} className="glass-panel p-4 rounded-xl border border-white/10 space-y-2">
              <span className="text-[10px] font-display uppercase tracking-wider text-white/60 block">
                Push Alert to Phone Lock Screen
              </span>
              <div className="flex items-center gap-1.5">
                <input
                  type="text"
                  value={customNotification}
                  onChange={(e) => setCustomNotification(e.target.value)}
                  placeholder="e.g. Remember to test build..."
                  className="flex-1 px-2.5 py-1.5 rounded-lg bg-black/40 border border-white/10 text-xs text-white placeholder-white/30 focus:border-cyan-500/60 focus:outline-none"
                />
                <button
                  type="submit"
                  className="p-2 rounded-lg bg-cyan-500/20 text-cyan-glow hover:bg-cyan-500/30 transition-all"
                  title="Push Notification"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </form>
          </div>

          {/* Incoming Notifications Stream */}
          <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-2.5">
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <h3 className="text-xs font-display font-bold uppercase tracking-wider text-white flex items-center gap-1.5">
                <Bell className="w-3.5 h-3.5 text-cyan-glow" />
                Phone Notifications Stream
              </h3>
              <span className="text-[10px] text-white/40">
                {phone?.state.notifications?.length ?? 0} active alerts
              </span>
            </div>

            <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
              {phone?.state.notifications && phone.state.notifications.length > 0 ? (
                phone.state.notifications.map((notif: PhoneNotification) => (
                  <div
                    key={notif.id}
                    className="flex items-start justify-between p-2 rounded-xl bg-black/30 border border-white/5 text-xs"
                  >
                    <div>
                      <span className="text-white font-semibold text-[11px] block">
                        {notif.title}
                      </span>
                      <p className="text-[11px] text-white/70">{notif.text}</p>
                    </div>
                    <span className="text-[9px] text-white/40 font-mono">
                      {new Date(notif.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-white/40 text-center py-3">No active notifications.</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* QR Code Phone Pairing Modal */}
      <AnimatePresence>
        {showQrModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-panel p-6 rounded-3xl border border-cyan-500/40 shadow-2xl max-w-sm w-full text-center space-y-4"
            >
              <div className="w-12 h-12 rounded-full bg-cyan-500/20 border border-cyan-500/40 mx-auto flex items-center justify-center text-cyan-glow">
                <QrCode className="w-6 h-6" />
              </div>

              <div>
                <h3 className="text-base font-display font-bold text-white tracking-wide">
                  Pair Smartphone Companion
                </h3>
                <p className="text-xs text-white/60 mt-1">
                  Scan this QR code with your phone camera or visit the companion link to sync real-time phone sensors with JARVIS.
                </p>
              </div>

              {/* Holographic QR Code Box */}
              <div className="p-4 bg-white rounded-2xl mx-auto w-48 h-48 flex flex-col items-center justify-center shadow-lg shadow-cyan-500/20 border-2 border-cyan-400">
                <QrCode className="w-36 h-36 text-black" />
              </div>

              <div className="p-2.5 rounded-xl bg-black/40 border border-white/10 text-xs font-mono text-cyan-glow">
                TOKEN: {pairingData?.pairing_token || 'STARK-PAIR-7878'}
              </div>

              <button
                type="button"
                onClick={() => setShowQrModal(false)}
                className="w-full py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-display font-bold text-xs uppercase tracking-wider transition-all"
              >
                Close Pairing Window
              </button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

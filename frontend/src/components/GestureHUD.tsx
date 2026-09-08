'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Hand,
  Camera,
  CameraOff,
  Maximize2,
  Minimize2,
  X,
  Zap,
  CheckCircle2,
  Info,
} from 'lucide-react';
import { useGestureVision, type GestureEvent } from '@/hooks/useGestureVision';

interface GestureHUDProps {
  enabled: boolean;
  onClose: () => void;
  onGestureTrigger: (event: GestureEvent) => void;
}

const GESTURE_ICONS: Record<string, string> = {
  open_palm: '✋',
  thumbs_up: '👍',
  fist: '✊',
  swipe_left: '👈',
  swipe_right: '👉',
  peace: '✌️',
  none: '🎯',
};

export function GestureHUD({ enabled, onClose, onGestureTrigger }: GestureHUDProps) {
  const [isMinimized, setIsMinimized] = useState(false);
  const [showLegend, setShowLegend] = useState(false);

  const { videoRef, canvasRef, isActive, currentGesture, cameraError } = useGestureVision({
    enabled,
    onGesture: onGestureTrigger,
    cooldownMs: 1200,
  });

  if (!enabled) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 pointer-events-auto">
      {/* Hidden canvas for optical processing */}
      <canvas ref={canvasRef} className="hidden" />

      <AnimatePresence>
        {isMinimized ? (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            className="glass-panel p-2.5 rounded-2xl border border-cyan-500/40 shadow-2xl shadow-cyan-500/20 flex items-center gap-3 cursor-pointer hover:border-cyan-400"
            onClick={() => setIsMinimized(false)}
          >
            <div className="relative flex items-center justify-center w-8 h-8 rounded-full bg-cyan-500/20 text-cyan-glow">
              <Hand className="w-4 h-4 animate-pulse" />
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-green-400 animate-ping" />
            </div>

            <div className="text-left pr-1">
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-display font-bold uppercase tracking-wider text-cyan-300">
                  GESTURE HUD
                </span>
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-green-500/20 text-green-400 font-mono">
                  ACTIVE
                </span>
              </div>
              <p className="text-[10px] text-white/60 font-mono">
                {currentGesture.gesture !== 'none'
                  ? `${GESTURE_ICONS[currentGesture.gesture]} ${currentGesture.label}`
                  : 'Tracking hand...'}
              </p>
            </div>

            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setIsMinimized(false);
              }}
              className="p-1 text-white/50 hover:text-white"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </motion.div>
        ) : (
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            className="w-80 glass-panel rounded-2xl border border-cyan-500/50 shadow-2xl shadow-cyan-500/20 overflow-hidden relative"
          >
            {/* Holographic Top Banner */}
            <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-white/10 bg-cyan-950/40">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                <span className="text-xs font-display font-bold tracking-widest text-cyan-glow uppercase flex items-center gap-1.5">
                  <Hand className="w-3.5 h-3.5" />
                  OPTICAL GESTURE HUD
                </span>
              </div>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => setShowLegend((prev) => !prev)}
                  title="Gesture Command Guide"
                  className={`p-1 rounded-md text-white/60 hover:text-white hover:bg-white/10 ${
                    showLegend ? 'text-cyan-glow bg-cyan-500/20' : ''
                  }`}
                >
                  <Info className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => setIsMinimized(true)}
                  title="Minimize HUD"
                  className="p-1 rounded-md text-white/60 hover:text-white hover:bg-white/10"
                >
                  <Minimize2 className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  title="Close Gesture Vision"
                  className="p-1 rounded-md text-white/60 hover:text-red-400 hover:bg-red-500/10"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Video Viewport & Targeting HUD */}
            <div className="relative aspect-[4/3] bg-black/80 overflow-hidden">
              <video
                ref={videoRef}
                playsInline
                muted
                className="w-full h-full object-cover transform -scale-x-100 opacity-80"
              />

              {/* Holographic Crosshair Overlay */}
              <div className="absolute inset-0 pointer-events-none">
                {/* Corner reticles */}
                <div className="absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2 border-cyan-400" />
                <div className="absolute top-2 right-2 w-4 h-4 border-t-2 border-r-2 border-cyan-400" />
                <div className="absolute bottom-2 left-2 w-4 h-4 border-b-2 border-l-2 border-cyan-400" />
                <div className="absolute bottom-2 right-2 w-4 h-4 border-b-2 border-r-2 border-cyan-400" />

                {/* Center Targeting Box */}
                <div className="absolute inset-x-12 inset-y-8 border border-dashed border-cyan-400/40 rounded-xl flex items-center justify-center">
                  <div className="w-6 h-6 border-t border-b border-cyan-400/60" />
                  <div className="w-6 h-6 border-l border-r border-cyan-400/60 absolute" />
                </div>

                {/* Status Telemetry Ribbon */}
                <div className="absolute top-2.5 left-8 right-8 flex items-center justify-between text-[9px] font-mono text-cyan-300/80">
                  <span>FOV: OPTICAL</span>
                  <span>FPS: 30</span>
                </div>
              </div>

              {/* Camera Permission / Error Warning */}
              {cameraError && (
                <div className="absolute inset-0 bg-black/90 flex flex-col items-center justify-center p-4 text-center">
                  <CameraOff className="w-8 h-8 text-red-400 mb-2" />
                  <p className="text-xs text-red-400 font-semibold mb-1">Webcam Access Blocked</p>
                  <p className="text-[10px] text-white/50">{cameraError}</p>
                </div>
              )}
            </div>

            {/* Active Gesture Detection Status */}
            <div className="p-3 bg-black/40 border-t border-white/10 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">
                    {GESTURE_ICONS[currentGesture.gesture] || '🎯'}
                  </span>
                  <div>
                    <span className="text-xs font-display font-bold uppercase tracking-wider text-white block">
                      {currentGesture.label}
                    </span>
                    <span className="text-[10px] text-cyan-glow/80 font-mono">
                      {currentGesture.confidence > 0
                        ? `CONFIDENCE: ${currentGesture.confidence}%`
                        : 'SHOW HAND TO CAMERA'}
                    </span>
                  </div>
                </div>

                {currentGesture.gesture !== 'none' && (
                  <motion.div
                    initial={{ scale: 0.5 }}
                    animate={{ scale: 1 }}
                    className="p-1 rounded-full bg-cyan-500/20 text-cyan-glow"
                  >
                    <Zap className="w-3.5 h-3.5" />
                  </motion.div>
                )}
              </div>

              {/* Gesture Command Legend (Collapsible) */}
              <AnimatePresence>
                {showLegend && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="pt-2 border-t border-white/5 space-y-1 text-[10px] text-white/70 overflow-hidden"
                  >
                    <div className="flex items-center justify-between py-0.5">
                      <span>✋ <strong>Open Palm</strong></span>
                      <span className="text-cyan-glow">Hold / Pause Speech</span>
                    </div>
                    <div className="flex items-center justify-between py-0.5">
                      <span>👍 <strong>Thumbs Up</strong></span>
                      <span className="text-cyan-glow">Confirm Security / HITL</span>
                    </div>
                    <div className="flex items-center justify-between py-0.5">
                      <span>✊ <strong>Closed Fist</strong></span>
                      <span className="text-cyan-glow">Lock System / Mute</span>
                    </div>
                    <div className="flex items-center justify-between py-0.5">
                      <span>👈 / 👉 <strong>Swipe Hand</strong></span>
                      <span className="text-cyan-glow">Switch Dashboard Tabs</span>
                    </div>
                    <div className="flex items-center justify-between py-0.5">
                      <span>✌️ <strong>Peace / Victory</strong></span>
                      <span className="text-cyan-glow">Telemetry Briefing</span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

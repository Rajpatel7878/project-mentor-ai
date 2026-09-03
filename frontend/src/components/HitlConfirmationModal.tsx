'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, CheckCircle, ShieldAlert, X } from 'lucide-react';

interface HitlConfirmationModalProps {
  isOpen: boolean;
  title: string;
  description: string;
  actionPayload?: Record<string, any>;
  onConfirm: () => void;
  onCancel: () => void;
}

export function HitlConfirmationModal({
  isOpen,
  title,
  description,
  actionPayload,
  onConfirm,
  onCancel,
}: HitlConfirmationModalProps) {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="relative w-full max-w-lg glass-panel rounded-2xl p-6 border border-amber-500/40 shadow-2xl shadow-amber-500/10"
        >
          <button
            onClick={onCancel}
            className="absolute top-4 right-4 text-white/50 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-400">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-display text-lg tracking-wider text-amber-400">
                SECURITY VERIFICATION REQUIRED
              </h3>
              <p className="text-xs text-white/50 uppercase tracking-wider">
                Human-in-the-Loop Protocol
              </p>
            </div>
          </div>

          <div className="space-y-3 mb-6">
            <p className="text-sm font-medium text-white/90">{title}</p>
            <p className="text-xs text-white/60 leading-relaxed">{description}</p>

            {actionPayload && Object.keys(actionPayload).length > 0 && (
              <div className="p-3 rounded-lg bg-black/40 border border-white/10 text-xs font-mono text-cyan-glow/80 overflow-x-auto">
                <pre>{JSON.stringify(actionPayload, null, 2)}</pre>
              </div>
            )}

            <div className="flex items-center gap-2 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300/80 text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>
                This physical or system-level command cannot be automatically reversed.
              </span>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3">
            <button
              onClick={onCancel}
              className="px-4 py-2 rounded-lg border border-white/10 hover:bg-white/5 text-xs font-display tracking-wider text-white/70 transition-colors"
            >
              CANCEL ACTION
            </button>
            <button
              onClick={onConfirm}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-black font-display font-semibold text-xs tracking-wider transition-all shadow-lg shadow-amber-500/20"
            >
              <CheckCircle className="w-4 h-4" />
              AUTHORIZE & EXECUTE
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

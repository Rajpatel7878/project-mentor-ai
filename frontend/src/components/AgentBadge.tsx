'use client';

import { motion } from 'framer-motion';

const AGENT_COLORS: Record<string, string> = {
  mentor: 'from-cyan-500 to-blue-500',
  cto: 'from-blue-500 to-indigo-500',
  pm: 'from-green-500 to-emerald-500',
  marketing: 'from-purple-500 to-pink-500',
  vc: 'from-amber-500 to-orange-500',
};

const AGENT_LABELS: Record<string, string> = {
  mentor: 'MENTOR',
  cto: 'CTO',
  pm: 'PM',
  marketing: 'MKT',
  vc: 'VC',
};

interface AgentBadgeProps {
  agent: string;
}

export function AgentBadge({ agent }: AgentBadgeProps) {
  const color = AGENT_COLORS[agent] || AGENT_COLORS.mentor;
  const label = AGENT_LABELS[agent] || agent.toUpperCase();

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-display bg-gradient-to-r ${color} text-white/90`}>
      {label}
    </span>
  );
}

interface ThinkingIndicatorProps {
  visible: boolean;
}

export function ThinkingIndicator({ visible }: ThinkingIndicatorProps) {
  if (!visible) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="flex items-center gap-3 px-4 py-3 glass-panel rounded-lg"
    >
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-2 h-2 rounded-full bg-cyan-glow"
            animate={{ opacity: [0.3, 1, 0.3], scale: [0.8, 1.2, 0.8] }}
            transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
          />
        ))}
      </div>
      <span className="text-sm text-cyan-glow/70 font-display tracking-wider">PROCESSING...</span>
    </motion.div>
  );
}

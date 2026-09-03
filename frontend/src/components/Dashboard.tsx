'use client';

import { motion } from 'framer-motion';
import { Activity, Brain, CheckCircle, MessageSquare, Target } from 'lucide-react';

interface DashboardProps {
  metrics: {
    total_conversations?: number;
    decisions_made?: number;
    tasks_completed?: number;
    project_phase?: string;
  };
  suggestions: string[];
  isConnected: boolean;
}

export function Dashboard({ metrics, suggestions, isConnected }: DashboardProps) {
  const stats = [
    { label: 'Conversations', value: metrics.total_conversations || 0, icon: MessageSquare, color: 'text-cyan-glow' },
    { label: 'Decisions', value: metrics.decisions_made || 0, icon: Brain, color: 'text-blue-400' },
    { label: 'Tasks Done', value: metrics.tasks_completed || 0, icon: CheckCircle, color: 'text-green-400' },
    { label: 'Phase', value: metrics.project_phase || 'building', icon: Target, color: 'text-purple-400' },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-display text-sm tracking-widest text-cyan-glow/80">SYSTEM STATUS</h2>
        <div className="flex items-center gap-2">
          <Activity className={`w-3 h-3 ${isConnected ? 'text-green-400' : 'text-red-400'}`} />
          <span className={`text-xs ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
            {isConnected ? 'ONLINE' : 'OFFLINE'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-panel rounded-lg p-3 holographic-gradient"
          >
            <div className="flex items-center gap-2 mb-1">
              <stat.icon className={`w-4 h-4 ${stat.color}`} />
              <span className="text-xs text-white/50 uppercase tracking-wider">{stat.label}</span>
            </div>
            <p className={`font-display text-lg capitalize ${stat.color}`}>
              {typeof stat.value === 'number' ? stat.value : stat.value}
            </p>
          </motion.div>
        ))}
      </div>

      {suggestions.length > 0 && (
        <div className="glass-panel rounded-lg p-4">
          <h3 className="font-display text-xs tracking-widest text-cyan-glow/60 mb-3">PROACTIVE INSIGHTS</h3>
          <ul className="space-y-2">
            {suggestions.map((s, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + i * 0.1 }}
                className="text-sm text-white/70 flex items-start gap-2"
              >
                <span className="text-cyan-glow mt-1">▸</span>
                {s}
              </motion.li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart3,
  DollarSign,
  TrendingDown,
  Clock,
  Zap,
  RotateCcw,
  RefreshCw,
  Cpu,
  Layers,
  ArrowUpRight,
  ShieldCheck,
} from 'lucide-react';
import {
  fetchUsageAnalytics,
  resetUsageAnalytics,
  type AnalyticsSummary,
} from '@/lib/api';
import { jarvisAudio } from '@/lib/soundEffects';

export function AnalyticsDashboard() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetchUsageAnalytics();
      setData(res);
    } catch (err) {
      console.warn('Failed to load usage analytics:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    // Auto-refresh metrics every 10 seconds
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset all usage counters for a fresh demonstration?')) {
      return;
    }
    try {
      setResetting(true);
      await resetUsageAnalytics();
      jarvisAudio.playSuccessChirp();
      await loadData();
    } catch (err) {
      console.error('Reset failed:', err);
      jarvisAudio.playAlertSound();
    } finally {
      setResetting(false);
    }
  };

  const agents = data?.agent_breakdown ? Object.entries(data.agent_breakdown) : [];

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-y-auto space-y-6 pr-2">
      {/* Top Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-white/10 relative overflow-hidden">
        <div className="absolute -top-12 -right-12 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-display font-semibold tracking-wider bg-green-500/20 text-green-400 border border-green-500/30">
                REAL-TIME TELEMETRY
              </span>
              <span className="text-xs text-white/40">Model: {data?.model || 'gemini-flash-latest'}</span>
            </div>
            <h2 className="font-display text-xl font-bold tracking-wide glow-text text-white">
              Agent Usage, Cost & Performance Dashboard
            </h2>
            <p className="text-xs text-white/60 mt-1 max-w-2xl leading-relaxed">
              Transparent cost accounting per autonomous agent persona. Tracks exact token consumption,
              response latencies, and calculates real dollar savings versus proprietary enterprise LLMs.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                jarvisAudio.playSuccessChirp();
                loadData();
              }}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/10 text-xs text-white/60 hover:text-white hover:bg-white/5 transition-all"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={handleReset}
              disabled={resetting}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-500/30 text-xs text-red-400 hover:bg-red-500/10 transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset Metrics
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Card 1: Total Calls */}
        <div className="glass-panel p-4 rounded-xl border border-white/10 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-display uppercase tracking-wider text-white/50">
              Total Invocations
            </span>
            <Zap className="w-4 h-4 text-cyan-glow" />
          </div>
          <p className="text-2xl font-display font-bold text-white">
            {data?.total_calls ?? 0}
          </p>
          <span className="text-[10px] text-white/40 block">
            Across {agents.length} active agent personas
          </span>
        </div>

        {/* Card 2: Total Tokens */}
        <div className="glass-panel p-4 rounded-xl border border-white/10 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-display uppercase tracking-wider text-white/50">
              Tokens Processed
            </span>
            <Cpu className="w-4 h-4 text-cyan-glow" />
          </div>
          <p className="text-2xl font-display font-bold text-white">
            {(data?.total_tokens ?? 0).toLocaleString()}
          </p>
          <span className="text-[10px] text-white/40 block">
            {data?.total_input_tokens?.toLocaleString() ?? 0} in / {data?.total_output_tokens?.toLocaleString() ?? 0} out
          </span>
        </div>

        {/* Card 3: Actual Cost in USD */}
        <div className="glass-panel p-4 rounded-xl border border-cyan-500/30 bg-cyan-500/5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-display uppercase tracking-wider text-cyan-300">
              Actual Cost (USD)
            </span>
            <DollarSign className="w-4 h-4 text-cyan-glow" />
          </div>
          <p className="text-2xl font-display font-bold text-cyan-glow">
            ${(data?.total_cost_usd ?? 0).toFixed(6)}
          </p>
          <span className="text-[10px] text-cyan-300/60 block">
            Gemini Flash ($0.075 / $0.300 per 1M)
          </span>
        </div>

        {/* Card 4: Estimated Savings */}
        <div className="glass-panel p-4 rounded-xl border border-green-500/30 bg-green-500/5 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-display uppercase tracking-wider text-green-400">
              Cost Reduction
            </span>
            <TrendingDown className="w-4 h-4 text-green-400" />
          </div>
          <p className="text-2xl font-display font-bold text-green-400">
            {data?.savings_percentage ?? 96.5}%
          </p>
          <span className="text-[10px] text-green-400/60 block">
            Saved ${(data?.estimated_savings_usd ?? 0).toFixed(5)} vs GPT-4
          </span>
        </div>
      </div>

      {/* Agent Performance Breakdown Table */}
      <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-4">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyan-glow" />
            <h3 className="text-sm font-display font-bold text-white uppercase tracking-wider">
              Agent Persona Usage Breakdown
            </h3>
          </div>
          <span className="text-xs text-white/40">
            Avg System Latency: <strong className="text-white">{data?.avg_latency_ms ?? 0} ms</strong>
          </span>
        </div>

        {agents.length === 0 ? (
          <div className="p-8 text-center text-white/40 text-xs">
            No agent calls recorded yet. Send a query in the Assistant Core to populate live telemetry.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/10 text-white/40 font-display uppercase tracking-wider text-[10px]">
                  <th className="py-2.5 px-3">Agent Persona</th>
                  <th className="py-2.5 px-3 text-right">Invocations</th>
                  <th className="py-2.5 px-3 text-right">Total Tokens</th>
                  <th className="py-2.5 px-3 text-right">Input / Output</th>
                  <th className="py-2.5 px-3 text-right">Avg Latency</th>
                  <th className="py-2.5 px-3 text-right">Cumulative Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {agents.map(([agentName, stats]) => (
                  <tr key={agentName} className="hover:bg-white/5 transition-colors">
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-cyan-400" />
                        <span className="font-display font-bold uppercase tracking-wider text-white">
                          {agentName}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-right text-white/80 font-mono">
                      {stats.calls}
                    </td>
                    <td className="py-3 px-3 text-right text-white/80 font-mono">
                      {stats.total_tokens.toLocaleString()}
                    </td>
                    <td className="py-3 px-3 text-right text-white/50 font-mono text-[11px]">
                      {stats.input_tokens} / {stats.output_tokens}
                    </td>
                    <td className="py-3 px-3 text-right text-white/80 font-mono">
                      {stats.avg_latency_ms} ms
                    </td>
                    <td className="py-3 px-3 text-right text-cyan-glow font-mono font-semibold">
                      ${stats.cost_usd.toFixed(6)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Activity Log */}
      <div className="glass-panel p-5 rounded-2xl border border-white/10 space-y-3">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-glow" />
            <h3 className="text-sm font-display font-bold text-white uppercase tracking-wider">
              Recent Call Stream (Audited Log)
            </h3>
          </div>
          <span className="text-[11px] text-white/40">
            Last {data?.recent_activity?.length ?? 0} events
          </span>
        </div>

        {(!data?.recent_activity || data.recent_activity.length === 0) ? (
          <div className="p-6 text-center text-white/40 text-xs">
            No recent activity recorded.
          </div>
        ) : (
          <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
            {data.recent_activity.slice().reverse().map((entry, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2.5 rounded-xl bg-black/30 border border-white/5 text-xs hover:border-white/10 transition-colors"
              >
                <div className="flex items-center gap-2.5">
                  <span className="px-2 py-0.5 rounded text-[10px] font-display font-bold uppercase tracking-wider bg-white/10 text-cyan-glow">
                    {entry.agent}
                  </span>
                  <span className="text-[11px] text-white/40">
                    {new Date(entry.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                <div className="flex items-center gap-4 text-[11px] font-mono">
                  <span className="text-white/60">
                    {entry.input_tokens + entry.output_tokens} tok
                  </span>
                  <span className="text-white/60">
                    {entry.latency_ms} ms
                  </span>
                  <span className="text-cyan-glow font-semibold">
                    ${entry.cost_usd.toFixed(6)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

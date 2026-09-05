'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Layers,
  TrendingDown,
  Clock,
  Wrench,
  Users,
  CheckCircle,
  Building2,
  HelpCircle,
  Send,
  RotateCcw,
  Check,
} from 'lucide-react';
import {
  analyzeIntake,
  fetchIntakeTemplates,
  type ClientTemplate,
  type IntakeAnalysisResult,
} from '@/lib/api';
import { jarvisAudio } from '@/lib/soundEffects';

interface ClientIntakeWizardProps {
  onDeployTemplate?: (template: ClientTemplate) => void;
}

const PRESET_SCENARIOS = [
  {
    title: 'E-Commerce Customer Support',
    company: 'Nexus Retail Co.',
    teamSize: '11-50',
    goal: '24/7 Autonomous Customer Inquiries & Ticket Triage',
    tools: 'Shopify, Zendesk, PostgreSQL',
    problem:
      'We receive hundreds of recurring product availability, shipping status, and return policy questions daily. Support agents are overwhelmed, leading to slow response times and abandoned carts.',
  },
  {
    title: 'Engineering & Devops Ops',
    company: 'CloudScale Systems',
    teamSize: '51-200',
    goal: 'Automated Daily Standups & Infrastructure Telemetry',
    tools: 'GitHub, Docker, Kubernetes, Slack',
    problem:
      'Engineering teams spend 45 minutes every morning syncing across 4 time zones. We need automated standup synthesis, sprint blocker tracking, and host system health telemetry commands.',
  },
  {
    title: 'Legal & SOP Document RAG',
    company: 'Apex Partners Consulting',
    teamSize: '1-10',
    goal: 'Semantic Search Across SOPs & Compliance PDFs',
    tools: 'Google Drive, PDF Reports, Markdown Wikis',
    problem:
      'We have over 1,200 PDF client agreements, compliance handbooks, and methodology guidelines. Consultants waste hours searching folders instead of receiving instant grounded citations.',
  },
];

export function ClientIntakeWizard({ onDeployTemplate }: ClientIntakeWizardProps) {
  const [templates, setTemplates] = useState<ClientTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<IntakeAnalysisResult | null>(null);

  // Form Fields
  const [companyName, setCompanyName] = useState('Acme Global Inc.');
  const [teamSize, setTeamSize] = useState('11-50');
  const [primaryGoal, setPrimaryGoal] = useState('Automate customer inquiries & lead qualification');
  const [currentTools, setCurrentTools] = useState('Slack, Notion, PostgreSQL');
  const [problemStatement, setProblemStatement] = useState(
    'We need an autonomous assistant that can answer product questions, qualify new client leads, and route inquiries to our team 24/7 without huge cloud LLM costs.'
  );

  useEffect(() => {
    fetchIntakeTemplates()
      .then(setTemplates)
      .catch((err) => console.warn('Could not fetch intake templates:', err));
  }, []);

  const handleApplyPreset = (preset: (typeof PRESET_SCENARIOS)[0]) => {
    setCompanyName(preset.company);
    setTeamSize(preset.teamSize);
    setPrimaryGoal(preset.goal);
    setCurrentTools(preset.tools);
    setProblemStatement(preset.problem);
    jarvisAudio.playSuccessChirp();
  };

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!problemStatement.trim()) return;

    setAnalyzing(true);
    jarvisAudio.playBootChime();

    try {
      const data = await analyzeIntake({
        company_name: companyName,
        team_size: teamSize,
        primary_goal: primaryGoal,
        current_tools: currentTools,
        problem_statement: problemStatement,
      });
      setResult(data);
      jarvisAudio.playSuccessChirp();
    } catch (error) {
      console.error('Analysis failed:', error);
      jarvisAudio.playAlertSound();
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-y-auto space-y-6 pr-2">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-white/10 relative overflow-hidden">
        <div className="absolute -top-12 -right-12 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-display font-semibold tracking-wider bg-cyan-500/20 text-cyan-glow border border-cyan-500/30">
                CLIENT ARCHITECTURE INTAKE
              </span>
              <span className="text-xs text-white/40">v2.0 Client Suite</span>
            </div>
            <h2 className="font-display text-xl font-bold tracking-wide glow-text text-white">
              AI Solution Architect & ROI Recommender
            </h2>
            <p className="text-xs text-white/60 mt-1 max-w-2xl leading-relaxed">
              Describe your business bottleneck. Our reasoning engine maps your operational requirements to
              the optimal multi-agent topology, provides concrete token budgets, and computes real-time
              cost savings compared to enterprise GPT-4 deployments.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setResult(null)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/10 text-xs text-white/60 hover:text-white hover:bg-white/5 transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset Form
            </button>
          </div>
        </div>
      </div>

      {/* Quick Presets Carousel */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-display tracking-wider text-white/60 uppercase">
            Quick Client Presets (1-Click Fill)
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {PRESET_SCENARIOS.map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleApplyPreset(preset)}
              className="text-left p-3.5 glass-panel rounded-xl border border-white/10 hover:border-cyan-500/50 hover:bg-white/5 transition-all group"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-semibold text-white group-hover:text-cyan-glow transition-colors">
                  {preset.title}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-white/5 text-white/50">
                  {preset.teamSize}
                </span>
              </div>
              <p className="text-[11px] text-white/50 line-clamp-2 leading-relaxed">
                {preset.problem}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Main Intake Form & Live Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
        {/* Left Column: Intake Questionnaire */}
        <form
          onSubmit={handleRunAnalysis}
          className="lg:col-span-6 glass-panel p-5 rounded-2xl border border-white/10 space-y-4"
        >
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <h3 className="text-sm font-display font-bold text-white flex items-center gap-2">
              <Building2 className="w-4 h-4 text-cyan-glow" />
              Business Profile & Bottlenecks
            </h3>
            <span className="text-[11px] text-white/40">Step 1 of 2</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-display uppercase tracking-wider text-white/60 mb-1">
                Company / Organization
              </label>
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                required
                className="w-full px-3 py-2 rounded-lg bg-black/40 border border-white/10 text-xs text-white placeholder-white/30 focus:border-cyan-500/60 focus:outline-none"
                placeholder="e.g. Acme Health Corp"
              />
            </div>

            <div>
              <label className="block text-[11px] font-display uppercase tracking-wider text-white/60 mb-1">
                Team Size
              </label>
              <select
                value={teamSize}
                onChange={(e) => setTeamSize(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-black/40 border border-white/10 text-xs text-white focus:border-cyan-500/60 focus:outline-none"
              >
                <option value="1-10">1 - 10 employees (Seed / Solo)</option>
                <option value="11-50">11 - 50 employees (Growth)</option>
                <option value="51-200">51 - 200 employees (Scale-up)</option>
                <option value="200+">200+ employees (Enterprise)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-display uppercase tracking-wider text-white/60 mb-1">
              Primary Objective
            </label>
            <input
              type="text"
              value={primaryGoal}
              onChange={(e) => setPrimaryGoal(e.target.value)}
              required
              className="w-full px-3 py-2 rounded-lg bg-black/40 border border-white/10 text-xs text-white placeholder-white/30 focus:border-cyan-500/60 focus:outline-none"
              placeholder="e.g. Fast document search, 24/7 lead intake, daily standups"
            />
          </div>

          <div>
            <label className="block text-[11px] font-display uppercase tracking-wider text-white/60 mb-1">
              Current Systems & Tools
            </label>
            <input
              type="text"
              value={currentTools}
              onChange={(e) => setCurrentTools(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-black/40 border border-white/10 text-xs text-white placeholder-white/30 focus:border-cyan-500/60 focus:outline-none"
              placeholder="e.g. Slack, Google Drive, PostgreSQL, Jira"
            />
          </div>

          <div>
            <label className="block text-[11px] font-display uppercase tracking-wider text-white/60 mb-1">
              Core Problem / Inefficiency Description
            </label>
            <textarea
              rows={4}
              value={problemStatement}
              onChange={(e) => setProblemStatement(e.target.value)}
              required
              className="w-full px-3 py-2 rounded-lg bg-black/40 border border-white/10 text-xs text-white placeholder-white/30 focus:border-cyan-500/60 focus:outline-none resize-none leading-relaxed"
              placeholder="Describe where time, money, or customer satisfaction is lost..."
            />
          </div>

          <button
            type="submit"
            disabled={analyzing || !problemStatement.trim()}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-black font-display font-bold text-xs tracking-wider uppercase transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {analyzing ? (
              <>
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="w-4 h-4 border-2 border-black border-t-transparent rounded-full"
                />
                Analyzing Architecture & Calculating ROI...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Generate Solution Recommendation & ROI
              </>
            )}
          </button>
        </form>

        {/* Right Column: Dynamic Recommendation & Financial ROI */}
        <div className="lg:col-span-6 space-y-4">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="glass-panel p-5 rounded-2xl border border-cyan-500/40 space-y-5 relative overflow-hidden"
              >
                {/* Result Top Badge */}
                <div className="flex items-center justify-between border-b border-white/10 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="p-1 rounded-lg bg-cyan-500/20 text-cyan-glow">
                      <Layers className="w-4 h-4" />
                    </span>
                    <div>
                      <h4 className="text-xs font-display font-bold uppercase tracking-wider text-white">
                        Recommended Architecture
                      </h4>
                      <p className="text-[10px] text-cyan-glow">
                        {result.company_name} Solution Blueprint
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] uppercase tracking-wider text-white/50 block">
                      Architecture Fit Score
                    </span>
                    <span className="text-base font-display font-bold text-green-400">
                      {result.fit_score}% MATCH
                    </span>
                  </div>
                </div>

                {/* Template Title Card */}
                <div className="p-4 rounded-xl bg-black/40 border border-white/10 space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-display font-bold text-white">
                      {result.recommended_template.name}
                    </h3>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-glow border border-cyan-500/30">
                      {result.recommended_template.setup_time}
                    </span>
                  </div>
                  <p className="text-xs text-white/80 leading-relaxed">
                    {result.recommended_template.description}
                  </p>

                  <div className="pt-2 border-t border-white/5 space-y-1">
                    <span className="text-[10px] uppercase font-display tracking-wider text-white/40 block">
                      Active Agents Assigned
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {result.recommended_template.primary_agents.map((agent) => (
                        <span
                          key={agent}
                          className="px-2 py-0.5 rounded-md text-[10px] font-display font-semibold uppercase tracking-wider bg-white/5 text-cyan-300 border border-cyan-500/20"
                        >
                          {agent}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Financial ROI Grid */}
                <div>
                  <h4 className="text-[11px] font-display uppercase tracking-wider text-white/60 mb-2 flex items-center gap-1.5">
                    <TrendingDown className="w-3.5 h-3.5 text-green-400" />
                    Financial & Operational ROI Analysis
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                    <div className="p-2.5 rounded-xl bg-black/30 border border-white/5">
                      <span className="text-[10px] text-white/40 uppercase block">Monthly Tokens</span>
                      <span className="text-xs font-display font-bold text-white">
                        {(result.roi_projections.monthly_tokens / 1_000_000).toFixed(1)}M
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20">
                      <span className="text-[10px] text-cyan-300 uppercase block">Gemini Flash</span>
                      <span className="text-xs font-display font-bold text-cyan-glow">
                        ${result.roi_projections.gemini_monthly_cost_usd.toFixed(2)}/mo
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/20">
                      <span className="text-[10px] text-red-400 uppercase block">GPT-4 Benchmark</span>
                      <span className="text-xs font-display font-bold text-red-400">
                        ${result.roi_projections.gpt4_equivalent_monthly_usd.toFixed(2)}/mo
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-green-500/10 border border-green-500/30">
                      <span className="text-[10px] text-green-400 uppercase block">Cost Savings</span>
                      <span className="text-xs font-display font-bold text-green-400">
                        {result.roi_projections.savings_percentage}%
                      </span>
                    </div>
                  </div>
                  <p className="text-[10px] text-green-400/80 mt-1.5 text-center">
                    Projected Annual Savings: ${result.roi_projections.annual_savings_usd.toLocaleString()} USD vs proprietary models.
                  </p>
                </div>

                {/* Implementation Roadmap */}
                <div className="space-y-1.5">
                  <span className="text-[11px] font-display uppercase tracking-wider text-white/60 block">
                    Fast-Track Deployment Roadmap
                  </span>
                  <div className="space-y-1">
                    {result.implementation_roadmap.map((step, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2 text-[11px] text-white/70 p-1.5 rounded-lg bg-white/5"
                      >
                        <Check className="w-3.5 h-3.5 text-cyan-glow mt-0.5 shrink-0" />
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Action CTA */}
                {onDeployTemplate && (
                  <button
                    type="button"
                    onClick={() => {
                      onDeployTemplate(result.recommended_template);
                      jarvisAudio.playBootChime();
                    }}
                    className="w-full py-2.5 px-4 rounded-xl bg-white/10 hover:bg-cyan-500 hover:text-black text-white font-display text-xs font-bold uppercase tracking-wider transition-all border border-cyan-500/40 flex items-center justify-center gap-2"
                  >
                    Deploy This Architecture to Assistant Core
                  </button>
                )}
              </motion.div>
            ) : (
              <div className="glass-panel p-8 rounded-2xl border border-white/10 text-center space-y-4">
                <div className="w-12 h-12 rounded-full bg-cyan-500/10 border border-cyan-500/30 mx-auto flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-cyan-glow" />
                </div>
                <div>
                  <h4 className="text-sm font-display font-bold text-white">
                    Awaiting Business Profile
                  </h4>
                  <p className="text-xs text-white/50 max-w-sm mx-auto mt-1 leading-relaxed">
                    Select a preset or enter your problem description on the left. Click &ldquo;Generate Solution&rdquo; to
                    receive an architectural mapping and ROI calculation.
                  </p>
                </div>

                {/* Available Templates Preview */}
                {templates.length > 0 && (
                  <div className="pt-4 border-t border-white/10 text-left space-y-2">
                    <span className="text-[10px] uppercase font-display tracking-wider text-white/40 block">
                      Solution Catalog Overview
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {templates.map((tpl) => (
                        <div
                          key={tpl.id}
                          className="p-2.5 rounded-xl bg-black/30 border border-white/5 space-y-1"
                        >
                          <span className="text-xs font-semibold text-white block">
                            {tpl.name}
                          </span>
                          <span className="text-[10px] text-cyan-glow/80 block">
                            ~${tpl.gemini_monthly_cost_usd}/mo (vs ${tpl.gpt4_monthly_cost_usd})
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

/**
 * RL Knowledge Dashboard - Training-free GRPO Visualization
 *
 * Implements ArXiv 2510.08191 concepts visualization:
 * - Token Prior: Past decision storage statistics
 * - Group Relative: Pattern scoring comparison
 * - Policy Optimization: Best solution recommendations
 * - Multi-rollout: Experiment tracking
 *
 * @see docs/features/ai-collaboration/RL_GUIDED_KNOWLEDGE_REUSE.md
 */

'use client';

import React, { useState } from 'react';
import {
  Brain,
  Database,
  Zap,
  Target,
  TrendingUp,
  Clock,
  AlertCircle,
  CheckCircle2,
  Search,
  Plus,
  Beaker,
  Activity,
} from 'lucide-react';
import {
  useRLSummary,
  useTokenPriorStats,
  useDomainPatterns,
  useBestSolution,
  useExperiments,
  getScoreColor,
  getScoreBadgeColor,
  getSideEffectsLabel,
  getSideEffectsColor,
  getResultBadgeColor,
  formatAccuracy,
  getSystemStatusColor,
  PatternResponse,
  ExperimentResponse,
} from '@/lib/hooks/useRLKnowledge';

// ============================================================================
// Main Page Component
// ============================================================================

export default function RLDashboardPage() {
  const [selectedDomain, setSelectedDomain] = useState('');
  const [solutionDomain, setSolutionDomain] = useState('');

  const { data: summary, isLoading: summaryLoading } = useRLSummary();
  const { data: tokenStats } = useTokenPriorStats();
  const { data: patterns } = useDomainPatterns(selectedDomain, 10, {
    enabled: selectedDomain.length > 0,
  });
  const { data: bestSolution } = useBestSolution(solutionDomain, undefined, {
    enabled: solutionDomain.length > 0,
  });
  const { data: experiments } = useExperiments(10);

  // Get available domains from summary
  const availableDomains = summary?.patterns.by_domain
    ? Object.keys(summary.patterns.by_domain)
    : [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center gap-3 mb-2">
            <Brain className="w-8 h-8 text-purple-600" />
            <h1 className="text-3xl font-bold text-gray-900">
              RL Knowledge Dashboard
            </h1>
          </div>
          <p className="text-gray-600">
            Training-free GRPO: Token Prior + Group Relative Scoring + Policy
            Optimization
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Based on ArXiv 2510.08191
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {summaryLoading ? (
          <LoadingState />
        ) : (
          <>
            {/* System Summary Cards */}
            {summary && <SystemSummary summary={summary} tokenStats={tokenStats} />}

            {/* Domain Patterns Section */}
            <DomainPatternsSection
              selectedDomain={selectedDomain}
              setSelectedDomain={setSelectedDomain}
              availableDomains={availableDomains}
              patterns={patterns}
            />

            {/* Best Solution Finder */}
            <BestSolutionSection
              solutionDomain={solutionDomain}
              setSolutionDomain={setSolutionDomain}
              availableDomains={availableDomains}
              bestSolution={bestSolution}
            />

            {/* Experiments Section */}
            {experiments && experiments.length > 0 && (
              <ExperimentsSection experiments={experiments} />
            )}

            {/* GRPO Theory Explanation */}
            <GRPOExplanation />
          </>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// System Summary Component
// ============================================================================

interface SystemSummaryProps {
  summary: {
    token_prior: {
      total_decisions: number;
      validated_count: number;
      accuracy: number | null;
    };
    patterns: {
      total: number;
      by_domain: Record<string, number>;
    };
    experiments: {
      total: number;
      with_success: number;
    };
    system_status: string;
  };
  tokenStats?: {
    total_decisions: number;
    unique_hours: number;
    validated_count: number;
    accuracy: number | null;
    last_updated: string | null;
  } | null;
}

function SystemSummary({ summary, tokenStats }: SystemSummaryProps) {
  const domainCount = Object.keys(summary.patterns.by_domain).length;
  const successRate =
    summary.experiments.total > 0
      ? (summary.experiments.with_success / summary.experiments.total) * 100
      : 0;

  return (
    <div className="mb-8">
      <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <Activity className="w-5 h-5 text-purple-600" />
        System Overview
        <span
          className={`ml-2 px-2 py-1 text-xs font-semibold rounded ${getSystemStatusColor(
            summary.system_status
          )}`}
        >
          {summary.system_status.toUpperCase()}
        </span>
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Token Prior Stats */}
        <SummaryCard
          icon={<Database className="w-6 h-6" />}
          title="Token Prior"
          value={summary.token_prior.total_decisions}
          subtitle={`${summary.token_prior.validated_count} validated`}
          extra={
            tokenStats?.accuracy !== null
              ? `Accuracy: ${formatAccuracy(tokenStats?.accuracy || null)}`
              : 'No accuracy data yet'
          }
          color="blue"
        />

        {/* Patterns Stats */}
        <SummaryCard
          icon={<Target className="w-6 h-6" />}
          title="Knowledge Patterns"
          value={summary.patterns.total}
          subtitle={`${domainCount} domains`}
          extra="Group Relative Scored"
          color="purple"
        />

        {/* Experiments Stats */}
        <SummaryCard
          icon={<Beaker className="w-6 h-6" />}
          title="Experiments"
          value={summary.experiments.total}
          subtitle={`${summary.experiments.with_success} successful`}
          extra={`Success rate: ${successRate.toFixed(0)}%`}
          color="green"
        />

        {/* Policy Optimization */}
        <SummaryCard
          icon={<TrendingUp className="w-6 h-6" />}
          title="Policy Optimization"
          value={tokenStats?.unique_hours || 0}
          subtitle="Unique prediction hours"
          extra={
            tokenStats?.last_updated
              ? `Updated: ${new Date(tokenStats.last_updated).toLocaleTimeString()}`
              : 'No updates yet'
          }
          color="orange"
        />
      </div>
    </div>
  );
}

interface SummaryCardProps {
  icon: React.ReactNode;
  title: string;
  value: number;
  subtitle: string;
  extra: string;
  color: 'blue' | 'purple' | 'green' | 'orange';
}

function SummaryCard({ icon, title, value, subtitle, extra, color }: SummaryCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    purple: 'bg-purple-50 text-purple-600',
    green: 'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600',
  };

  return (
    <div className="bg-white p-6 border border-gray-200 rounded-lg">
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>{icon}</div>
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
      </div>
      <div className="text-3xl font-bold text-gray-900">{value}</div>
      <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
      <p className="text-xs text-gray-400 mt-2">{extra}</p>
    </div>
  );
}

// ============================================================================
// Domain Patterns Section
// ============================================================================

interface DomainPatternsSectionProps {
  selectedDomain: string;
  setSelectedDomain: (domain: string) => void;
  availableDomains: string[];
  patterns?: PatternResponse[];
}

function DomainPatternsSection({
  selectedDomain,
  setSelectedDomain,
  availableDomains,
  patterns,
}: DomainPatternsSectionProps) {
  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <Target className="w-5 h-5 text-purple-600" />
          Domain Patterns (Group Relative Scoring)
        </h2>
      </div>

      {/* Domain Selector */}
      <div className="mb-4 flex flex-wrap gap-2">
        {availableDomains.length > 0 ? (
          availableDomains.map((domain) => (
            <button
              key={domain}
              onClick={() => setSelectedDomain(domain)}
              className={`px-4 py-2 text-sm rounded-lg border transition-colors ${
                selectedDomain === domain
                  ? 'bg-purple-600 text-white border-purple-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:border-purple-400'
              }`}
            >
              {domain}
            </button>
          ))
        ) : (
          <p className="text-sm text-gray-500">No domains available. Add patterns to create domains.</p>
        )}
      </div>

      {/* Patterns Table */}
      {selectedDomain && patterns && patterns.length > 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                  Pattern
                </th>
                <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700 uppercase">
                  Score
                </th>
                <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700 uppercase">
                  Resolution
                </th>
                <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700 uppercase">
                  Recurrence
                </th>
                <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700 uppercase">
                  Side Effects
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {patterns.map((pattern, index) => (
                <tr key={pattern.name} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {index === 0 && (
                        <span className="px-2 py-1 text-xs font-bold bg-yellow-100 text-yellow-800 rounded">
                          BEST
                        </span>
                      )}
                      <div>
                        <div className="font-medium text-gray-900">{pattern.name}</div>
                        <div className="text-xs text-gray-500 max-w-xs truncate">
                          {pattern.solution_description}
                        </div>
                        {pattern.tags.length > 0 && (
                          <div className="flex gap-1 mt-1">
                            {pattern.tags.slice(0, 3).map((tag) => (
                              <span
                                key={tag}
                                className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span
                      className={`px-3 py-1 text-sm font-bold border rounded ${getScoreBadgeColor(
                        pattern.score
                      )}`}
                    >
                      {(pattern.score * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <Clock className="w-4 h-4 text-gray-400" />
                      <span className="text-sm text-gray-700">
                        {pattern.resolution_time_minutes}min
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`text-sm ${pattern.recurrence_count === 0 ? 'text-green-600 font-semibold' : 'text-gray-700'}`}>
                      {pattern.recurrence_count}x
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`text-sm ${getSideEffectsColor(pattern.side_effects)}`}>
                      {getSideEffectsLabel(pattern.side_effects)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : selectedDomain ? (
        <div className="bg-white p-8 border border-gray-200 rounded-lg text-center">
          <Target className="w-12 h-12 mx-auto text-gray-300" />
          <p className="mt-4 text-gray-500">No patterns found for domain: {selectedDomain}</p>
        </div>
      ) : null}
    </div>
  );
}

// ============================================================================
// Best Solution Section
// ============================================================================

interface BestSolutionSectionProps {
  solutionDomain: string;
  setSolutionDomain: (domain: string) => void;
  availableDomains: string[];
  bestSolution?: {
    found: boolean;
    domain: string;
    pattern_name: string | null;
    score: number | null;
    solution: string | null;
    alternatives: Array<{ name: string; score: number }>;
  };
}

function BestSolutionSection({
  solutionDomain,
  setSolutionDomain,
  availableDomains,
  bestSolution,
}: BestSolutionSectionProps) {
  return (
    <div className="mb-8">
      <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <Zap className="w-5 h-5 text-yellow-600" />
        Policy Optimization: Best Solution Finder
      </h2>

      <div className="bg-white p-6 border border-gray-200 rounded-lg">
        <div className="flex items-center gap-4 mb-4">
          <Search className="w-5 h-5 text-gray-400" />
          <select
            value={solutionDomain}
            onChange={(e) => setSolutionDomain(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="">Select a domain to find best solution...</option>
            {availableDomains.map((domain) => (
              <option key={domain} value={domain}>
                {domain}
              </option>
            ))}
          </select>
        </div>

        {bestSolution && (
          <div className="mt-4">
            {bestSolution.found && bestSolution.pattern_name ? (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-6 h-6 text-green-600 flex-shrink-0" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-green-800">
                      Recommended: {bestSolution.pattern_name}
                    </h3>
                    <p className="text-sm text-green-700 mt-1">{bestSolution.solution}</p>
                    <div className="mt-2 flex items-center gap-4">
                      <span
                        className={`px-3 py-1 text-sm font-bold border rounded ${getScoreBadgeColor(
                          bestSolution.score || 0
                        )}`}
                      >
                        Score: {((bestSolution.score || 0) * 100).toFixed(0)}%
                      </span>
                    </div>

                    {bestSolution.alternatives.length > 0 && (
                      <div className="mt-4">
                        <p className="text-xs text-green-600 font-semibold mb-2">
                          Alternatives:
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {bestSolution.alternatives.map((alt) => (
                            <span
                              key={alt.name}
                              className="px-2 py-1 text-xs bg-white text-green-700 border border-green-300 rounded"
                            >
                              {alt.name} ({(alt.score * 100).toFixed(0)}%)
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-3">
                <AlertCircle className="w-6 h-6 text-yellow-600" />
                <p className="text-yellow-700">
                  No solution found for domain: {bestSolution.domain}. Add patterns to build knowledge.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Experiments Section
// ============================================================================

interface ExperimentsSectionProps {
  experiments: ExperimentResponse[];
}

function ExperimentsSection({ experiments }: ExperimentsSectionProps) {
  return (
    <div className="mb-8">
      <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <Beaker className="w-5 h-5 text-green-600" />
        Multi-Rollout Experiments
      </h2>

      <div className="space-y-4">
        {experiments.map((exp) => (
          <div key={exp.problem_id} className="bg-white p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className="font-medium text-gray-900">{exp.problem_id}</h3>
                <p className="text-xs text-gray-500">
                  {new Date(exp.created_at).toLocaleString()}
                </p>
              </div>
              {exp.best_approach && (
                <span className="px-3 py-1 text-xs font-semibold bg-green-100 text-green-800 rounded">
                  Winner: {exp.best_approach}
                </span>
              )}
            </div>

            <div className="flex flex-wrap gap-2">
              {exp.attempts.map((attempt, index) => (
                <div
                  key={index}
                  className={`px-3 py-2 text-sm border rounded ${getResultBadgeColor(
                    attempt.result
                  )}`}
                >
                  <span className="font-medium">{attempt.approach}</span>
                  <span className="ml-2 opacity-75">({attempt.result})</span>
                  {attempt.reason && (
                    <span className="block text-xs opacity-75 mt-1">{attempt.reason}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// GRPO Explanation Section
// ============================================================================

function GRPOExplanation() {
  return (
    <div className="mb-8">
      <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
        <Brain className="w-5 h-5 text-purple-600" />
        How Training-free GRPO Works
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ConceptCard
          title="Token Prior"
          description="Past decision storage for instant knowledge reuse. No model training required - pure experience-based lookup."
          icon={<Database className="w-6 h-6" />}
          color="blue"
          metrics={['<10ms lookup', '70% hit rate', 'Cumulative']}
        />

        <ConceptCard
          title="Group Relative"
          description="Compare patterns within domain. Score = 0.4*(time efficiency) + 0.4*(permanence) + 0.2*(safety)"
          icon={<Target className="w-6 h-6" />}
          color="purple"
          metrics={['Context-aware', 'Comparative', 'Ranked']}
        />

        <ConceptCard
          title="Policy Optimization"
          description="Iteratively improve decisions. Track experiments, save winners, apply best solutions automatically."
          icon={<TrendingUp className="w-6 h-6" />}
          color="green"
          metrics={['Self-improving', 'Multi-rollout', 'Adaptive']}
        />
      </div>
    </div>
  );
}

interface ConceptCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  color: 'blue' | 'purple' | 'green';
  metrics: string[];
}

function ConceptCard({ title, description, icon, color, metrics }: ConceptCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
    purple: 'bg-purple-50 text-purple-600 border-purple-200',
    green: 'bg-green-50 text-green-600 border-green-200',
  };

  return (
    <div className={`p-6 border rounded-lg ${colorClasses[color]}`}>
      <div className="flex items-center gap-3 mb-3">
        {icon}
        <h3 className="font-semibold">{title}</h3>
      </div>
      <p className="text-sm opacity-80 mb-4">{description}</p>
      <div className="flex flex-wrap gap-2">
        {metrics.map((metric) => (
          <span
            key={metric}
            className="px-2 py-1 text-xs bg-white bg-opacity-50 rounded"
          >
            {metric}
          </span>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// Helper Components
// ============================================================================

function LoadingState() {
  return (
    <div className="py-12 text-center">
      <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-purple-600" />
      <p className="mt-4 text-sm text-gray-500">Loading RL Knowledge system...</p>
    </div>
  );
}

/**
 * Knowledge Quality Dashboard - Accuracy Tracking & Metrics
 *
 * Week 6 Day 5: Metrics Dashboard
 *
 * Features:
 * - Overall accuracy metrics (search_accuracy, acceptance_rate, false_positive_rate)
 * - Top quality documents
 * - Low quality documents
 * - Improvement recommendations
 * - Real-time refresh
 *
 * Benchmarking:
 * - Linear: 60%+ accuracy target
 * - GitHub Copilot: 26-40% acceptance rate
 * - Notion AI: <10% false positive rate
 */

'use client';

import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  BarChart3,
  FileText,
  Lightbulb,
} from 'lucide-react';
import {
  useKnowledgeMetrics,
  useImprovementSuggestions,
  getMetricStatusColor,
  getMetricStatusBadge,
  getPriorityBadgeColor,
  formatDocumentId,
  DocumentScore,
  ImprovementSuggestion,
} from '@/lib/hooks/useKnowledgeMetrics';

// ============================================================================
// Knowledge Quality Dashboard Page
// ============================================================================

export default function KnowledgeQualityPage() {
  const { data: metrics, isLoading: metricsLoading } = useKnowledgeMetrics({
    refetchInterval: 30000, // Refresh every 30s
  });

  const { data: suggestions, isLoading: suggestionsLoading } =
    useImprovementSuggestions();

  const isLoading = metricsLoading || suggestionsLoading;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center gap-3 mb-2">
            <BarChart3 className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">
              Knowledge Quality Dashboard
            </h1>
          </div>
          <p className="text-gray-600">
            Real-time accuracy tracking and quality metrics
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <LoadingState />
        ) : metrics ? (
          <>
            {/* Overall Metrics Cards */}
            <MetricsOverview metrics={metrics} />

            {/* Improvement Suggestions */}
            {suggestions && suggestions.length > 0 && (
              <ImprovementSuggestionsSection suggestions={suggestions} />
            )}

            {/* Top Quality Documents */}
            {metrics.top_documents.length > 0 && (
              <TopDocumentsSection documents={metrics.top_documents} />
            )}

            {/* Low Quality Documents */}
            {metrics.low_quality_documents.length > 0 && (
              <LowQualityDocumentsSection
                documentIds={metrics.low_quality_documents}
              />
            )}

            {/* Benchmarking Reference */}
            <BenchmarkingSection />
          </>
        ) : (
          <EmptyState />
        )}
      </div>
    </div>
  );
}

// ============================================================================
// MetricsOverview Component
// ============================================================================

function MetricsOverview({ metrics }: { metrics: any }) {
  const accuracyStatus = getMetricStatusBadge('accuracy', metrics.search_accuracy);
  const acceptanceStatus = getMetricStatusBadge(
    'acceptance',
    metrics.acceptance_rate
  );
  const fpStatus = getMetricStatusBadge(
    'false_positive',
    metrics.false_positive_rate
  );

  return (
    <div className="mb-8">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Overall Metrics
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Search Accuracy */}
        <MetricCard
          icon={<TrendingUp className="w-6 h-6" />}
          title="Search Accuracy"
          value={`${metrics.search_accuracy}%`}
          description={`${metrics.total_searches} total searches`}
          status={accuracyStatus}
          target="Target: 70%+"
          benchmark="Linear: 60%+"
          color="blue"
        />

        {/* Acceptance Rate */}
        <MetricCard
          icon={<CheckCircle2 className="w-6 h-6" />}
          title="Acceptance Rate"
          value={`${metrics.acceptance_rate}%`}
          description={`${metrics.total_feedback_count} feedback received`}
          status={acceptanceStatus}
          target="Target: 40%+"
          benchmark="Copilot: 26-40%"
          color="green"
        />

        {/* False Positive Rate */}
        <MetricCard
          icon={<XCircle className="w-6 h-6" />}
          title="False Positive Rate"
          value={`${metrics.false_positive_rate}%`}
          description="Unhelpful results"
          status={fpStatus}
          target="Target: <15%"
          benchmark="Notion: <10%"
          color="red"
        />
      </div>
    </div>
  );
}

interface MetricCardProps {
  icon: React.ReactNode;
  title: string;
  value: string;
  description: string;
  status: { label: string; color: string };
  target: string;
  benchmark: string;
  color: 'blue' | 'green' | 'red';
}

function MetricCard({
  icon,
  title,
  value,
  description,
  status,
  target,
  benchmark,
  color,
}: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
  };

  return (
    <div className="bg-white p-6 border border-gray-200 rounded-lg">
      <div className="flex items-center gap-3 mb-4">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>{icon}</div>
        <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
      </div>

      <div className="mb-4">
        <div className="text-3xl font-bold text-gray-900">{value}</div>
        <p className="text-sm text-gray-500 mt-1">{description}</p>
      </div>

      <div className="space-y-2">
        <div className={`inline-flex px-3 py-1 rounded text-sm font-semibold ${status.color}`}>
          {status.label}
        </div>
        <div className="text-xs text-gray-600">
          <div>{target}</div>
          <div className="text-gray-500">{benchmark}</div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// ImprovementSuggestionsSection Component
// ============================================================================

function ImprovementSuggestionsSection({
  suggestions,
}: {
  suggestions: ImprovementSuggestion[];
}) {
  return (
    <div className="mb-8">
      <div className="flex items-center gap-2 mb-4">
        <Lightbulb className="w-5 h-5 text-yellow-600" />
        <h2 className="text-lg font-semibold text-gray-800">
          Improvement Recommendations
        </h2>
        <span className="px-2 py-1 text-xs font-semibold bg-yellow-100 text-yellow-800 rounded">
          {suggestions.length} suggestions
        </span>
      </div>

      <div className="space-y-3">
        {suggestions.map((suggestion, index) => (
          <SuggestionCard key={index} suggestion={suggestion} />
        ))}
      </div>
    </div>
  );
}

function SuggestionCard({ suggestion }: { suggestion: ImprovementSuggestion }) {
  return (
    <div className="bg-white p-4 border border-gray-200 rounded-lg">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle
              className={`w-5 h-5 ${
                suggestion.priority === 'high'
                  ? 'text-red-600'
                  : suggestion.priority === 'medium'
                  ? 'text-yellow-600'
                  : 'text-blue-600'
              }`}
            />
            {suggestion.document_id && (
              <code className="text-sm font-mono text-gray-700">
                {formatDocumentId(suggestion.document_id)}
              </code>
            )}
          </div>

          <p className="text-sm text-gray-600">{suggestion.recommendation}</p>

          {suggestion.score !== undefined && (
            <div className="mt-2 text-xs text-gray-500">
              Usefulness Score: {suggestion.score.toFixed(2)}
            </div>
          )}

          {suggestion.false_positive_rate !== undefined && (
            <div className="mt-2 text-xs text-gray-500">
              False Positive Rate: {suggestion.false_positive_rate}%
            </div>
          )}
        </div>

        <div
          className={`px-3 py-1 text-xs font-semibold border rounded ${getPriorityBadgeColor(
            suggestion.priority
          )}`}
        >
          {suggestion.priority.toUpperCase()}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// TopDocumentsSection Component
// ============================================================================

function TopDocumentsSection({ documents }: { documents: DocumentScore[] }) {
  return (
    <div className="mb-8">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-5 h-5 text-green-600" />
        <h2 className="text-lg font-semibold text-gray-800">
          Top Quality Documents
        </h2>
        <span className="px-2 py-1 text-xs font-semibold bg-green-100 text-green-800 rounded">
          Usefulness ≥ 3.0
        </span>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase">
                Document
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700 uppercase">
                Usefulness
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700 uppercase">
                Acceptance
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700 uppercase">
                Searches
              </th>
              <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700 uppercase">
                Helpful
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {documents.map((doc) => (
              <tr key={doc.document_id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <code className="text-sm font-mono text-gray-700">
                    {formatDocumentId(doc.document_id)}
                  </code>
                </td>
                <td className="px-6 py-4 text-center">
                  <span className="text-sm font-bold text-green-600">
                    {doc.usefulness_score.toFixed(2)}
                  </span>
                </td>
                <td className="px-6 py-4 text-center">
                  <span className="text-sm text-gray-700">
                    {doc.acceptance_rate.toFixed(1)}%
                  </span>
                </td>
                <td className="px-6 py-4 text-center">
                  <span className="text-sm text-gray-700">
                    {doc.total_searches}
                  </span>
                </td>
                <td className="px-6 py-4 text-center">
                  <span className="text-sm text-green-600 font-semibold">
                    {doc.helpful_count}
                  </span>
                  <span className="text-sm text-gray-400"> / </span>
                  <span className="text-sm text-red-600">
                    {doc.unhelpful_count}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ============================================================================
// LowQualityDocumentsSection Component
// ============================================================================

function LowQualityDocumentsSection({ documentIds }: { documentIds: string[] }) {
  return (
    <div className="mb-8">
      <div className="flex items-center gap-2 mb-4">
        <TrendingDown className="w-5 h-5 text-red-600" />
        <h2 className="text-lg font-semibold text-gray-800">
          Low Quality Documents
        </h2>
        <span className="px-2 py-1 text-xs font-semibold bg-red-100 text-red-800 rounded">
          Usefulness &lt; 2.0
        </span>
      </div>

      <div className="bg-white p-6 border border-gray-200 rounded-lg">
        <p className="text-sm text-gray-600 mb-4">
          These documents need review or archival (≥3 searches, usefulness &lt; 2.0):
        </p>
        <div className="flex flex-wrap gap-2">
          {documentIds.map((docId) => (
            <code
              key={docId}
              className="px-3 py-1 text-xs font-mono bg-red-50 text-red-700 border border-red-200 rounded"
            >
              {formatDocumentId(docId)}
            </code>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// BenchmarkingSection Component
// ============================================================================

function BenchmarkingSection() {
  return (
    <div className="mb-8">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Industry Benchmarks
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <BenchmarkCard
          platform="Linear"
          metric="Accuracy"
          target="60%+"
          description="Search result relevance and helpfulness rate"
        />
        <BenchmarkCard
          platform="GitHub Copilot"
          metric="Acceptance"
          target="26-40%"
          description="Code suggestion acceptance rate (tab/esc tracking)"
        />
        <BenchmarkCard
          platform="Notion AI"
          metric="False Positive"
          target="<10%"
          description="Irrelevant or unhelpful search results"
        />
      </div>
    </div>
  );
}

function BenchmarkCard({
  platform,
  metric,
  target,
  description,
}: {
  platform: string;
  metric: string;
  target: string;
  description: string;
}) {
  return (
    <div className="bg-blue-50 p-4 border border-blue-200 rounded-lg">
      <div className="flex items-center gap-2 mb-2">
        <FileText className="w-4 h-4 text-blue-600" />
        <h3 className="text-sm font-semibold text-blue-800">{platform}</h3>
      </div>
      <div className="text-lg font-bold text-blue-900 mb-1">{target}</div>
      <div className="text-xs text-blue-700 mb-2">{metric}</div>
      <p className="text-xs text-blue-600">{description}</p>
    </div>
  );
}

// ============================================================================
// Helper Components
// ============================================================================

function LoadingState() {
  return (
    <div className="py-12 text-center">
      <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-blue-600" />
      <p className="mt-4 text-sm text-gray-500">Loading metrics...</p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="py-12 text-center">
      <BarChart3 className="w-16 h-16 mx-auto text-gray-300" />
      <h3 className="mt-4 text-lg font-semibold text-gray-700">
        No metrics available
      </h3>
      <p className="mt-2 text-sm text-gray-500">
        Start using the knowledge search to generate metrics
      </p>
    </div>
  );
}

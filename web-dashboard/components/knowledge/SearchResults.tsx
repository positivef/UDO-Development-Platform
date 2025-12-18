/**
 * SearchResults - Display knowledge search results with tier breakdown
 *
 * Week 6 Day 4 PM: Frontend Integration
 *
 * Features:
 * - Tier breakdown badges (Tier 1/2/3)
 * - Relevance score display
 * - Document snippets
 * - Feedback integration
 * - Performance metrics
 */

'use client';

import React from 'react';
import { FileText, Clock, TrendingUp } from 'lucide-react';
import {
  SearchResultItem,
  SearchResponse,
  getTierBadgeColor,
  getTierLabel,
  getActiveTiers,
  formatSearchTime,
  getRelevanceScoreColor,
} from '@/lib/hooks/useKnowledgeSearch';
import { FeedbackButtons } from '../FeedbackButtons';

// ============================================================================
// Types
// ============================================================================

export interface SearchResultsProps {
  data: SearchResponse;
  isLoading?: boolean;
  sessionId?: string;
}

// ============================================================================
// SearchResults Component
// ============================================================================

export function SearchResults({
  data,
  isLoading = false,
  sessionId,
}: SearchResultsProps) {
  if (isLoading) {
    return (
      <div className="py-12 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-blue-600" />
        <p className="mt-4 text-sm text-gray-500">Searching knowledge base...</p>
      </div>
    );
  }

  if (!data || data.total_results === 0) {
    return (
      <div className="py-12 text-center">
        <FileText className="w-16 h-16 mx-auto text-gray-300" />
        <h3 className="mt-4 text-lg font-semibold text-gray-700">
          No results found
        </h3>
        <p className="mt-2 text-sm text-gray-500">
          Try different keywords or adjust your filters
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Performance Metrics */}
      <div className="flex items-center justify-between p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-center gap-6">
          {/* Total Results */}
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-semibold text-gray-700">
              {data.total_results} {data.total_results === 1 ? 'result' : 'results'}
            </span>
          </div>

          {/* Search Time */}
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-600" />
            <span className="text-sm text-gray-600">
              {formatSearchTime(data.search_time_ms)}
            </span>
          </div>

          {/* Tier Breakdown */}
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            <div className="flex gap-1">
              {data.tier_breakdown.tier1 > 0 && (
                <span className="px-2 py-1 text-xs font-semibold rounded bg-green-100 text-green-800">
                  T1: {data.tier_breakdown.tier1}
                </span>
              )}
              {data.tier_breakdown.tier2 > 0 && (
                <span className="px-2 py-1 text-xs font-semibold rounded bg-blue-100 text-blue-800">
                  T2: {data.tier_breakdown.tier2}
                </span>
              )}
              {data.tier_breakdown.tier3 > 0 && (
                <span className="px-2 py-1 text-xs font-semibold rounded bg-purple-100 text-purple-800">
                  T3: {data.tier_breakdown.tier3}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Query Display */}
        <div className="text-sm text-gray-600">
          Query: <span className="font-mono font-semibold">{data.query}</span>
        </div>
      </div>

      {/* Results List */}
      <div className="space-y-4">
        {data.results.map((result, index) => (
          <SearchResultCard
            key={result.document_id}
            result={result}
            rank={index + 1}
            query={data.query}
            sessionId={sessionId}
          />
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// SearchResultCard Component
// ============================================================================

interface SearchResultCardProps {
  result: SearchResultItem;
  rank: number;
  query: string;
  sessionId?: string;
}

function SearchResultCard({
  result,
  rank,
  query,
  sessionId,
}: SearchResultCardProps) {
  const activeTiers = getActiveTiers(result);

  return (
    <div className="p-6 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          {/* Rank & Title */}
          <div className="flex items-center gap-3 mb-2">
            <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-blue-100 text-blue-600 font-bold text-sm rounded-full">
              {rank}
            </span>
            <h3 className="text-lg font-semibold text-gray-800 truncate">
              {result.document_path}
            </h3>
          </div>

          {/* Snippet */}
          {result.snippet && (
            <p className="mt-2 text-sm text-gray-600 line-clamp-2">
              {result.snippet}
            </p>
          )}
        </div>

        {/* Relevance Score */}
        <div className="flex-shrink-0 text-right">
          <div className={`text-2xl font-bold ${getRelevanceScoreColor(result.relevance_score)}`}>
            {result.relevance_score.toFixed(1)}
          </div>
          <div className="text-xs text-gray-500">Relevance</div>
        </div>
      </div>

      {/* Scoring Breakdown */}
      <div className="mt-4 flex items-center gap-4 flex-wrap">
        {/* Tier Badges */}
        {activeTiers.map((tier) => (
          <div
            key={tier}
            className={`px-3 py-1 text-xs font-semibold border rounded ${getTierBadgeColor(
              tier
            )}`}
          >
            {getTierLabel(tier)}: {result[`tier${tier}_score` as keyof SearchResultItem]}
          </div>
        ))}

        {/* Freshness Bonus */}
        {result.freshness_bonus > 0 && (
          <div className="px-3 py-1 text-xs font-semibold bg-orange-100 text-orange-800 border border-orange-300 rounded">
            Fresh: +{result.freshness_bonus.toFixed(1)}
          </div>
        )}

        {/* Usefulness Score */}
        {result.usefulness_score !== 0 && (
          <div
            className={`px-3 py-1 text-xs font-semibold border rounded ${
              result.usefulness_score > 0
                ? 'bg-green-100 text-green-800 border-green-300'
                : 'bg-red-100 text-red-800 border-red-300'
            }`}
          >
            Useful: {result.usefulness_score > 0 ? '+' : ''}
            {result.usefulness_score.toFixed(1)}
          </div>
        )}
      </div>

      {/* Feedback Buttons */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <FeedbackButtons
          documentId={result.document_id}
          searchQuery={query}
          sessionId={sessionId}
        />
      </div>
    </div>
  );
}

/**
 * Knowledge Search Page - 3-Tier Search System
 *
 * Week 6 Day 4 PM: Frontend Integration
 *
 * Features:
 * - Real-time search with debouncing
 * - 3-tier search breakdown visualization
 * - Performance metrics display
 * - Feedback collection integration
 * - Search statistics dashboard
 */

'use client';

import React, { useState, useCallback } from 'react';
import { BookOpen, TrendingUp, Zap } from 'lucide-react';
import { SearchBar, SearchFilters } from '@/components/knowledge/SearchBar';
import { SearchResults } from '@/components/knowledge/SearchResults';
import {
  useKnowledgeSearch,
  useSearchStats,
} from '@/lib/hooks/useKnowledgeSearch';

// ============================================================================
// Knowledge Search Page
// ============================================================================

export default function KnowledgeSearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({
    max_results: 10,
    min_score: 5.0,
  });
  const [sessionId] = useState(() => `session-${Date.now()}`);

  // Search query
  const {
    data: searchData,
    isLoading: isSearching,
    error: searchError,
  } = useKnowledgeSearch(
    {
      query: searchQuery,
      ...searchFilters,
    },
    {
      enabled: searchQuery.length >= 3,
    }
  );

  // Search statistics
  const { data: stats } = useSearchStats();

  // Handle search
  const handleSearch = useCallback((query: string, filters?: SearchFilters) => {
    setSearchQuery(query);
    if (filters) {
      setSearchFilters(filters);
    }
  }, []);

  // Note: Feedback is handled internally by FeedbackButtons component

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center gap-3 mb-2">
            <BookOpen className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">
              Knowledge Search
            </h1>
          </div>
          <p className="text-gray-600">
            3-Tier search system: Filename → Frontmatter → Content
          </p>
        </div>
      </div>

      {/* Search Statistics Banner */}
      {stats && stats.total_searches > 0 && (
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-8">
                <div className="flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  <div>
                    <div className="text-sm font-semibold">
                      {stats.avg_search_time_ms.toFixed(0)}ms
                    </div>
                    <div className="text-xs opacity-90">Avg Speed</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  <div>
                    <div className="text-sm font-semibold">
                      {stats.tier1_hit_rate.toFixed(0)}%
                    </div>
                    <div className="text-xs opacity-90">Tier 1 Hit Rate</div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5" />
                  <div>
                    <div className="text-sm font-semibold">
                      {stats.avg_results_per_search.toFixed(1)}
                    </div>
                    <div className="text-xs opacity-90">Avg Results</div>
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="text-sm font-semibold">
                  {stats.total_searches} searches
                </div>
                <div className="text-xs opacity-90">All time</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Bar */}
        <div className="mb-8">
          <SearchBar onSearch={handleSearch} autoFocus />
        </div>

        {/* Search Error */}
        {searchError && (
          <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg">
            <h3 className="text-sm font-semibold text-red-800 mb-1">
              Search Error
            </h3>
            <p className="text-sm text-red-600">{searchError.message}</p>
          </div>
        )}

        {/* Search Results */}
        {searchQuery.length >= 3 && (
          <SearchResults
            data={searchData!}
            isLoading={isSearching}
            sessionId={sessionId}
          />
        )}

        {/* Empty State */}
        {searchQuery.length === 0 && (
          <div className="py-12 text-center">
            <BookOpen className="w-20 h-20 mx-auto text-gray-300" />
            <h3 className="mt-4 text-lg font-semibold text-gray-700">
              Start searching
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              Enter a keyword to search the knowledge base
            </p>

            {/* Example Queries */}
            <div className="mt-8 max-w-2xl mx-auto">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">
                Example Searches:
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <ExampleQuery
                  query="ModuleNotFoundError pandas"
                  onClick={() => handleSearch('ModuleNotFoundError pandas')}
                />
                <ExampleQuery
                  query="authentication 401 error"
                  onClick={() => handleSearch('authentication 401 error')}
                />
                <ExampleQuery
                  query="permission denied chmod"
                  onClick={() => handleSearch('permission denied chmod')}
                />
                <ExampleQuery
                  query="React performance optimization"
                  onClick={() => handleSearch('React performance optimization')}
                />
              </div>
            </div>

            {/* Tier Explanation */}
            <div className="mt-12 max-w-3xl mx-auto">
              <h4 className="text-sm font-semibold text-gray-700 mb-4">
                How 3-Tier Search Works:
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
                <TierCard
                  tier={1}
                  title="Filename Pattern"
                  description="Fast pattern matching against filenames (Debug-{Error}-{Component}.md)"
                  speed="<1ms"
                  accuracy="95%"
                  color="green"
                />
                <TierCard
                  tier={2}
                  title="Frontmatter YAML"
                  description="Metadata-based filtering using YAML frontmatter fields"
                  speed="<50ms"
                  accuracy="80%"
                  color="blue"
                />
                <TierCard
                  tier={3}
                  title="Full-Text Content"
                  description="Deep semantic search through document content"
                  speed="<500ms"
                  accuracy="60%"
                  color="purple"
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Helper Components
// ============================================================================

function ExampleQuery({
  query,
  onClick,
}: {
  query: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="px-4 py-2 text-sm text-left bg-white border border-gray-300 rounded-lg hover:bg-gray-50 hover:border-blue-500 transition-colors"
    >
      <code className="text-blue-600">{query}</code>
    </button>
  );
}

interface TierCardProps {
  tier: 1 | 2 | 3;
  title: string;
  description: string;
  speed: string;
  accuracy: string;
  color: 'green' | 'blue' | 'purple';
}

function TierCard({
  tier,
  title,
  description,
  speed,
  accuracy,
  color,
}: TierCardProps) {
  const colorClasses = {
    green: 'bg-green-100 text-green-800 border-green-300',
    blue: 'bg-blue-100 text-blue-800 border-blue-300',
    purple: 'bg-purple-100 text-purple-800 border-purple-300',
  };

  return (
    <div className="p-4 bg-white border border-gray-200 rounded-lg">
      <div
        className={`inline-flex items-center justify-center w-8 h-8 mb-2 text-sm font-bold border rounded-full ${colorClasses[color]}`}
      >
        {tier}
      </div>
      <h5 className="text-sm font-semibold text-gray-800 mb-1">{title}</h5>
      <p className="text-xs text-gray-600 mb-3">{description}</p>
      <div className="flex gap-4 text-xs">
        <div>
          <span className="text-gray-500">Speed:</span>{' '}
          <span className="font-semibold text-gray-700">{speed}</span>
        </div>
        <div>
          <span className="text-gray-500">Accuracy:</span>{' '}
          <span className="font-semibold text-gray-700">{accuracy}</span>
        </div>
      </div>
    </div>
  );
}

/**
 * SearchBar - Knowledge search input component
 *
 * Week 6 Day 4 PM: Frontend Integration
 *
 * Features:
 * - Real-time search input with debouncing
 * - Advanced filters (error_type, max_results, min_score)
 * - Keyboard shortcuts (Cmd/Ctrl + K to focus)
 * - Search history (optional)
 */

'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Search, X, SlidersHorizontal } from 'lucide-react';

// ============================================================================
// Types
// ============================================================================

export interface SearchBarProps {
  onSearch: (query: string, filters?: SearchFilters) => void;
  placeholder?: string;
  autoFocus?: boolean;
  className?: string;
}

export interface SearchFilters {
  error_type?: string;
  max_results?: number;
  min_score?: number;
}

// ============================================================================
// SearchBar Component
// ============================================================================

export function SearchBar({
  onSearch,
  placeholder = 'Search knowledge base... (e.g., "ModuleNotFoundError pandas")',
  autoFocus = false,
  className = '',
}: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    max_results: 10,
    min_score: 5.0,
  });
  const inputRef = useRef<HTMLInputElement>(null);

  // Keyboard shortcut: Cmd/Ctrl + K to focus search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Debounced search
  useEffect(() => {
    if (query.length < 3) return;

    const timer = setTimeout(() => {
      onSearch(query, filters);
    }, 500); // 500ms debounce

    return () => clearTimeout(timer);
  }, [query, filters, onSearch]);

  const handleClear = () => {
    setQuery('');
    inputRef.current?.focus();
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.length >= 3) {
      onSearch(query, filters);
    }
  };

  return (
    <div className={`w-full ${className}`}>
      {/* Main Search Bar */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center">
          {/* Search Icon */}
          <div className="absolute left-4 text-gray-400">
            <Search className="w-5 h-5" />
          </div>

          {/* Input Field */}
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            autoFocus={autoFocus}
            className="w-full pl-12 pr-24 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />

          {/* Right Side Controls */}
          <div className="absolute right-2 flex items-center gap-2">
            {/* Clear Button */}
            {query && (
              <button
                type="button"
                onClick={handleClear}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                aria-label="Clear search"
              >
                <X className="w-4 h-4" />
              </button>
            )}

            {/* Filters Toggle */}
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className={`p-2 rounded transition-colors ${
                showFilters
                  ? 'bg-blue-100 text-blue-600'
                  : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
              }`}
              aria-label="Toggle filters"
            >
              <SlidersHorizontal className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Keyboard Hint */}
        <div className="absolute right-28 top-1/2 -translate-y-1/2 hidden sm:block">
          <kbd className="px-2 py-1 text-xs font-semibold text-gray-500 bg-gray-100 border border-gray-300 rounded">
            ⌘K
          </kbd>
        </div>
      </form>

      {/* Advanced Filters */}
      {showFilters && (
        <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Advanced Filters
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Error Type Filter */}
            <div>
              <label
                htmlFor="error-type"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Error Type
              </label>
              <input
                id="error-type"
                type="text"
                value={filters.error_type || ''}
                onChange={(e) =>
                  setFilters({ ...filters, error_type: e.target.value || undefined })
                }
                placeholder="e.g., ModuleNotFoundError"
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Max Results Filter */}
            <div>
              <label
                htmlFor="max-results"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Max Results
              </label>
              <input
                id="max-results"
                type="number"
                min="1"
                max="50"
                value={filters.max_results || 10}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    max_results: parseInt(e.target.value) || 10,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Min Score Filter */}
            <div>
              <label
                htmlFor="min-score"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Min Relevance Score
              </label>
              <input
                id="min-score"
                type="number"
                min="0"
                step="0.5"
                value={filters.min_score || 5.0}
                onChange={(e) =>
                  setFilters({
                    ...filters,
                    min_score: parseFloat(e.target.value) || 5.0,
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Filter Actions */}
          <div className="mt-4 flex justify-end gap-2">
            <button
              type="button"
              onClick={() =>
                setFilters({
                  max_results: 10,
                  min_score: 5.0,
                })
              }
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
            >
              Reset Filters
            </button>
            <button
              type="button"
              onClick={() => setShowFilters(false)}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Apply
            </button>
          </div>
        </div>
      )}

      {/* Search Instructions */}
      {query.length > 0 && query.length < 3 && (
        <p className="mt-2 text-sm text-gray-500">
          Enter at least 3 characters to search
        </p>
      )}
    </div>
  );
}

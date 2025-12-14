"use client"

import { motion } from "framer-motion"
import { GitCompare, ArrowRight, Plus, Minus, FileText, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { useState } from "react"

interface VersionComparisonProps {
  fromCommit: string
  toCommit: string
  onClose: () => void
}

interface ComparisonData {
  from_commit: string
  to_commit: string
  files_changed: string[]
  files_added: string[]
  files_deleted: string[]
  total_lines_added: number
  total_lines_deleted: number
  commits_between: Array<{
    short_hash: string
    message: string
    author: string
    date: string
  }>
}

export function VersionComparison({ fromCommit, toCommit, onClose }: VersionComparisonProps) {
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch comparison data
  useState(() => {
    const fetchComparison = async () => {
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const res = await fetch(
          `${API_URL}/api/version-history/compare?from_commit=${fromCommit}&to_commit=${toCommit}`
        )

        if (!res.ok) {
          throw new Error("Failed to fetch comparison")
        }

        const data = await res.json()
        setComparisonData(data)
        setIsLoading(false)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error")
        setIsLoading(false)
      }
    }

    fetchComparison()
  })

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-6"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        className="bg-gray-800 rounded-xl border border-gray-700 max-w-4xl w-full max-h-[80vh] overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <GitCompare className="h-6 w-6 text-blue-400" />
            <h2 className="text-xl font-semibold text-white">Version Comparison</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="h-5 w-5 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full" />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <div className="text-red-400 mb-2">Failed to load comparison</div>
              <div className="text-gray-500 text-sm">{error}</div>
            </div>
          ) : comparisonData ? (
            <div className="space-y-6">
              {/* Commit Range */}
              <div className="flex items-center justify-center gap-4 p-4 bg-gray-700/30 rounded-lg">
                <code className="px-3 py-1 bg-gray-900/50 rounded text-blue-400 font-mono text-sm">
                  {comparisonData.from_commit}
                </code>
                <ArrowRight className="h-5 w-5 text-gray-400" />
                <code className="px-3 py-1 bg-gray-900/50 rounded text-green-400 font-mono text-sm">
                  {comparisonData.to_commit}
                </code>
              </div>

              {/* Summary Statistics */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-700/30 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-green-400">
                    +{comparisonData.total_lines_added}
                  </div>
                  <div className="text-sm text-gray-400 mt-1">Lines Added</div>
                </div>

                <div className="bg-gray-700/30 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-red-400">
                    -{comparisonData.total_lines_deleted}
                  </div>
                  <div className="text-sm text-gray-400 mt-1">Lines Deleted</div>
                </div>

                <div className="bg-gray-700/30 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-blue-400">
                    {comparisonData.files_changed.length + comparisonData.files_added.length + comparisonData.files_deleted.length}
                  </div>
                  <div className="text-sm text-gray-400 mt-1">Files Changed</div>
                </div>
              </div>

              {/* Net Change */}
              <div className="bg-gray-700/30 rounded-lg p-4">
                <div className="text-sm text-gray-400 mb-1">Net Change</div>
                <div className={cn(
                  "text-lg font-medium",
                  comparisonData.total_lines_added - comparisonData.total_lines_deleted > 0
                    ? "text-green-400"
                    : "text-red-400"
                )}>
                  {comparisonData.total_lines_added - comparisonData.total_lines_deleted > 0 ? "+" : ""}
                  {comparisonData.total_lines_added - comparisonData.total_lines_deleted} lines
                </div>
              </div>

              {/* File Changes */}
              {comparisonData.files_changed.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-gray-300 flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    Modified Files ({comparisonData.files_changed.length})
                  </h3>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {comparisonData.files_changed.map((file, i) => (
                      <div
                        key={i}
                        className="text-sm text-gray-300 font-mono px-3 py-2 bg-gray-700/30 rounded"
                      >
                        {file}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Added Files */}
              {comparisonData.files_added.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-green-400 flex items-center gap-2">
                    <Plus className="h-4 w-4" />
                    Added Files ({comparisonData.files_added.length})
                  </h3>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {comparisonData.files_added.map((file, i) => (
                      <div
                        key={i}
                        className="text-sm text-green-300 font-mono px-3 py-2 bg-green-900/10 rounded"
                      >
                        + {file}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Deleted Files */}
              {comparisonData.files_deleted.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-red-400 flex items-center gap-2">
                    <Minus className="h-4 w-4" />
                    Deleted Files ({comparisonData.files_deleted.length})
                  </h3>
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {comparisonData.files_deleted.map((file, i) => (
                      <div
                        key={i}
                        className="text-sm text-red-300 font-mono px-3 py-2 bg-red-900/10 rounded"
                      >
                        - {file}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Commits Between */}
              {comparisonData.commits_between.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-gray-300">
                    Commits Between ({comparisonData.commits_between.length})
                  </h3>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {comparisonData.commits_between.map((commit, i) => (
                      <div
                        key={i}
                        className="bg-gray-700/30 rounded-lg p-3"
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <code className="text-xs text-gray-400 font-mono">
                            {commit.short_hash}
                          </code>
                          <span className="text-sm text-white font-medium flex-1">
                            {commit.message}
                          </span>
                        </div>
                        <div className="text-xs text-gray-400">
                          {commit.author} • {new Date(commit.date).toLocaleDateString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

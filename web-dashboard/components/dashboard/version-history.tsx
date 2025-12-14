"use client"

import { motion } from "framer-motion"
import { GitCommit, GitBranch, User, Calendar, FileText, Plus, Minus, Tag, ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"
import { format } from "date-fns"
import { useState } from "react"

interface VersionCommit {
  commit_hash: string
  short_hash: string
  author: string
  author_email: string
  date: string
  message: string
  files_modified: string[]
  files_added: string[]
  files_deleted: string[]
  lines_added: number
  lines_deleted: number
  tags: string[]
  branches: string[]
}

interface VersionHistoryProps {
  commits: VersionCommit[]
  currentBranch: string
  totalCommits: number
}

export function VersionHistory({ commits = [], currentBranch = "main", totalCommits = 0 }: VersionHistoryProps) {
  const [expandedCommits, setExpandedCommits] = useState<Set<string>>(new Set())

  const toggleCommitExpansion = (hash: string) => {
    const newExpanded = new Set(expandedCommits)
    if (newExpanded.has(hash)) {
      newExpanded.delete(hash)
    } else {
      newExpanded.add(hash)
    }
    setExpandedCommits(newExpanded)
  }

  const getCommitTypeColor = (message: string): string => {
    const lowerMessage = message.toLowerCase()
    if (lowerMessage.startsWith("feat:") || lowerMessage.includes("feature")) {
      return "text-green-400 bg-green-500/10"
    } else if (lowerMessage.startsWith("fix:") || lowerMessage.includes("fix")) {
      return "text-red-400 bg-red-500/10"
    } else if (lowerMessage.startsWith("refactor:") || lowerMessage.includes("refactor")) {
      return "text-blue-400 bg-blue-500/10"
    } else if (lowerMessage.startsWith("docs:") || lowerMessage.includes("docs")) {
      return "text-purple-400 bg-purple-500/10"
    } else if (lowerMessage.startsWith("test:") || lowerMessage.includes("test")) {
      return "text-yellow-400 bg-yellow-500/10"
    }
    return "text-gray-400 bg-gray-500/10"
  }

  const getCommitTypeIcon = (message: string) => {
    const lowerMessage = message.toLowerCase()
    if (lowerMessage.startsWith("feat:") || lowerMessage.includes("feature")) {
      return <Plus className="h-4 w-4" />
    } else if (lowerMessage.startsWith("fix:") || lowerMessage.includes("fix")) {
      return <FileText className="h-4 w-4" />
    }
    return <GitCommit className="h-4 w-4" />
  }

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString)
      return format(date, "MMM dd, yyyy HH:mm")
    } catch {
      return dateString
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <GitCommit className="h-5 w-5 text-gray-400" />
          <h2 className="text-xl font-semibold text-white">Version History</h2>
        </div>
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-blue-500/10 border border-blue-500/20">
            <GitBranch className="h-4 w-4 text-blue-400" />
            <span className="text-blue-400 font-medium">{currentBranch}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-400">Total Commits:</span>
            <span className="font-medium text-white">{totalCommits}</span>
          </div>
        </div>
      </div>

      {/* Commit List */}
      <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
        {commits.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <GitCommit className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p>No commits found in this repository.</p>
          </div>
        ) : (
          commits.map((commit, index) => {
            const isExpanded = expandedCommits.has(commit.commit_hash)
            const totalFiles = commit.files_modified.length + commit.files_added.length + commit.files_deleted.length
            const netLines = commit.lines_added - commit.lines_deleted

            return (
              <motion.div
                key={commit.commit_hash}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.03 }}
                className="bg-gray-700/30 rounded-lg overflow-hidden hover:bg-gray-700/40 transition-all border border-gray-600/30"
              >
                {/* Commit Header */}
                <div
                  className="p-4 cursor-pointer"
                  onClick={() => toggleCommitExpansion(commit.commit_hash)}
                >
                  <div className="flex items-start gap-3">
                    <div className={cn("p-2 rounded-lg", getCommitTypeColor(commit.message))}>
                      {getCommitTypeIcon(commit.message)}
                    </div>

                    <div className="flex-1 min-w-0">
                      {/* Commit Message */}
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <h3 className="text-sm font-medium text-white truncate flex-1">
                          {commit.message}
                        </h3>
                        <button
                          className="text-gray-400 hover:text-white transition-colors p-1"
                          onClick={(e) => {
                            e.stopPropagation()
                            toggleCommitExpansion(commit.commit_hash)
                          }}
                        >
                          {isExpanded ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </button>
                      </div>

                      {/* Commit Metadata */}
                      <div className="flex flex-wrap items-center gap-3 text-xs text-gray-400">
                        <div className="flex items-center gap-1">
                          <User className="h-3 w-3" />
                          <span>{commit.author}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          <span>{formatDate(commit.date)}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <GitCommit className="h-3 w-3" />
                          <span className="font-mono">{commit.short_hash}</span>
                        </div>
                      </div>

                      {/* Tags */}
                      {commit.tags.length > 0 && (
                        <div className="flex items-center gap-2 mt-2">
                          {commit.tags.map((tag) => (
                            <span
                              key={tag}
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-yellow-500/10 text-yellow-400 text-xs border border-yellow-500/20"
                            >
                              <Tag className="h-3 w-3" />
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Quick Stats */}
                      <div className="flex items-center gap-4 mt-2 text-xs">
                        <div className="flex items-center gap-1 text-green-400">
                          <Plus className="h-3 w-3" />
                          <span>{commit.lines_added}</span>
                        </div>
                        <div className="flex items-center gap-1 text-red-400">
                          <Minus className="h-3 w-3" />
                          <span>{commit.lines_deleted}</span>
                        </div>
                        <div className="flex items-center gap-1 text-gray-400">
                          <FileText className="h-3 w-3" />
                          <span>{totalFiles} {totalFiles === 1 ? "file" : "files"}</span>
                        </div>
                        <div className={cn(
                          "flex items-center gap-1 font-medium",
                          netLines > 0 ? "text-green-400" : netLines < 0 ? "text-red-400" : "text-gray-400"
                        )}>
                          <span>{netLines > 0 ? "+" : ""}{netLines} lines</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="border-t border-gray-600/30 bg-gray-800/30"
                  >
                    <div className="p-4 space-y-3">
                      {/* Full Commit Hash */}
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-gray-400">Full Hash:</span>
                        <code className="flex-1 px-2 py-1 bg-gray-900/50 rounded text-gray-300 font-mono">
                          {commit.commit_hash}
                        </code>
                      </div>

                      {/* Author Email */}
                      <div className="flex items-center gap-2 text-xs">
                        <span className="text-gray-400">Email:</span>
                        <span className="text-gray-300">{commit.author_email}</span>
                      </div>

                      {/* Modified Files */}
                      {commit.files_modified.length > 0 && (
                        <div className="space-y-1">
                          <div className="text-xs text-gray-400 font-medium">Modified Files:</div>
                          <div className="space-y-1 max-h-32 overflow-y-auto">
                            {commit.files_modified.map((file, i) => (
                              <div
                                key={i}
                                className="text-xs text-gray-300 font-mono px-2 py-1 bg-gray-900/30 rounded"
                              >
                                {file}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Added Files */}
                      {commit.files_added.length > 0 && (
                        <div className="space-y-1">
                          <div className="text-xs text-green-400 font-medium">Added Files:</div>
                          <div className="space-y-1 max-h-32 overflow-y-auto">
                            {commit.files_added.map((file, i) => (
                              <div
                                key={i}
                                className="text-xs text-green-300 font-mono px-2 py-1 bg-green-900/10 rounded"
                              >
                                + {file}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Deleted Files */}
                      {commit.files_deleted.length > 0 && (
                        <div className="space-y-1">
                          <div className="text-xs text-red-400 font-medium">Deleted Files:</div>
                          <div className="space-y-1 max-h-32 overflow-y-auto">
                            {commit.files_deleted.map((file, i) => (
                              <div
                                key={i}
                                className="text-xs text-red-300 font-mono px-2 py-1 bg-red-900/10 rounded"
                              >
                                - {file}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Branches */}
                      {commit.branches.length > 0 && (
                        <div className="flex items-center gap-2 text-xs flex-wrap">
                          <span className="text-gray-400">Branches:</span>
                          {commit.branches.map((branch) => (
                            <span
                              key={branch}
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20"
                            >
                              <GitBranch className="h-3 w-3" />
                              {branch}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )
          })
        )}
      </div>
    </motion.div>
  )
}

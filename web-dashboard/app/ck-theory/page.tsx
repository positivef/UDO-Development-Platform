"use client"

import { useState } from "react"
import { useMutation, useQuery } from "@tanstack/react-query"
import { motion, AnimatePresence } from "framer-motion"
import {
  Palette,
  Lightbulb,
  TrendingUp,
  Users,
  Zap,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Star,
  ThumbsUp,
  MessageSquare
} from "lucide-react"
import { cn } from "@/lib/utils"
import { toast } from "sonner"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface RICEScore {
  reach: number
  impact: number
  confidence: number
  effort: number
  score: number
}

interface DesignAlternative {
  id: "A" | "B" | "C"
  title: string
  description: string
  pros: string[]
  cons: string[]
  rice: RICEScore
  implementation_complexity: string
  estimated_timeline: string
  required_resources: string[]
  risk_factors: string[]
}

interface TradeoffAnalysis {
  summary: string
  recommended_alternative_id: string
  key_tradeoffs: string[]
  decision_factors: string[]
  recommendation: string
}

interface CKTheoryResult {
  id: string
  challenge: string
  alternatives: DesignAlternative[]
  tradeoff_analysis: TradeoffAnalysis
  total_duration_ms: number
  created_at: string
  obsidian_path?: string
}

interface DesignSummary {
  design_id: string
  challenge: string
  recommended_alternative: string
  avg_rice_score: number
  created_at: string
}

export default function CKTheoryPage() {
  const [challenge, setChallenge] = useState("")
  const [constraints, setConstraints] = useState<Record<string, unknown>>({})
  const [result, setResult] = useState<CKTheoryResult | null>(null)
  const [showFeedbackForm, setShowFeedbackForm] = useState(false)
  const [selectedAlt, setSelectedAlt] = useState<string>("")
  const [rating, setRating] = useState(5)
  const [comments, setComments] = useState("")

  // Fetch recent designs
  const { data: recentDesigns, refetch: refetchDesigns } = useQuery<{
    designs: DesignSummary[]
    total: number
  }>({
    queryKey: ["ck-designs"],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/api/v1/ck-theory?limit=5`)
      if (!response.ok) throw new Error("Failed to fetch designs")
      return response.json()
    },
    refetchOnWindowFocus: false,
  })

  // Generate design mutation
  const generateMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${API_URL}/api/v1/ck-theory`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ challenge, constraints }),
      })
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || "Failed to generate design")
      }
      return response.json()
    },
    onSuccess: (data: CKTheoryResult) => {
      setResult(data)
      toast.success("Design alternatives generated!")
      refetchDesigns()
    },
    onError: (error: Error) => {
      toast.error(`Failed to generate design: ${error.message}`)
    },
  })

  // Submit feedback mutation
  const feedbackMutation = useMutation({
    mutationFn: async () => {
      if (!result) throw new Error("No design result")
      const response = await fetch(`${API_URL}/api/v1/ck-theory/${result.id}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          design_id: result.id,
          alternative_id: selectedAlt,
          rating,
          comments,
          selected_alternative: selectedAlt,
          outcome: "pending"
        }),
      })
      if (!response.ok) throw new Error("Failed to submit feedback")
      return response.json()
    },
    onSuccess: () => {
      toast.success("Feedback submitted successfully!")
      setShowFeedbackForm(false)
      setComments("")
    },
    onError: (error: Error) => {
      toast.error(`Failed to submit feedback: ${error.message}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!challenge.trim()) {
      toast.error("Please enter a design challenge")
      return
    }
    generateMutation.mutate()
  }

  const handleFeedbackSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedAlt) {
      toast.error("Please select an alternative")
      return
    }
    feedbackMutation.mutate()
  }

  const getAlternativeColor = (id: string) => {
    switch (id) {
      case "A": return "from-blue-500/20 to-blue-600/20 border-blue-500/30"
      case "B": return "from-purple-500/20 to-purple-600/20 border-purple-500/30"
      case "C": return "from-green-500/20 to-green-600/20 border-green-500/30"
      default: return "from-gray-500/20 to-gray-600/20 border-gray-500/30"
    }
  }

  const getAlternativeTextColor = (id: string) => {
    switch (id) {
      case "A": return "text-blue-400"
      case "B": return "text-purple-400"
      case "C": return "text-green-400"
      default: return "text-gray-400"
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20">
            <Palette className="h-8 w-8 text-purple-400" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-white">C-K Theory</h1>
            <p className="text-gray-400 mt-1">
              Concept-Knowledge Design Theory (3 Alternatives + RICE Scoring)
            </p>
          </div>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Input Form */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-1"
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="p-6 rounded-xl bg-gray-800/50 border border-gray-700/50">
              <h2 className="text-xl font-semibold text-white mb-4">
                Design Challenge
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">
                    What design challenge do you want to solve?
                  </label>
                  <textarea
                    value={challenge}
                    onChange={(e) => setChallenge(e.target.value)}
                    placeholder="E.g., Design an authentication system that supports multiple providers"
                    className={cn(
                      "w-full px-4 py-3 rounded-lg",
                      "bg-gray-900/50 border border-gray-700",
                      "text-white placeholder-gray-500",
                      "focus:outline-none focus:border-purple-500",
                      "transition-colors resize-none"
                    )}
                    rows={4}
                    disabled={generateMutation.isPending}
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-2">
                    Constraints (Optional)
                  </label>
                  <textarea
                    value={JSON.stringify(constraints, null, 2)}
                    onChange={(e) => {
                      try {
                        setConstraints(JSON.parse(e.target.value))
                      } catch {
                        // Invalid JSON, ignore
                      }
                    }}
                    placeholder='{"budget": "2 weeks", "team_size": 2}'
                    className={cn(
                      "w-full px-4 py-3 rounded-lg",
                      "bg-gray-900/50 border border-gray-700",
                      "text-white placeholder-gray-500",
                      "focus:outline-none focus:border-purple-500",
                      "transition-colors resize-none font-mono text-sm"
                    )}
                    rows={3}
                    disabled={generateMutation.isPending}
                  />
                </div>

                <button
                  type="submit"
                  disabled={generateMutation.isPending || !challenge.trim()}
                  className={cn(
                    "w-full px-6 py-3 rounded-lg font-semibold",
                    "bg-gradient-to-r from-purple-500 to-pink-500",
                    "text-white transition-all",
                    "hover:from-purple-600 hover:to-pink-600",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                    "flex items-center justify-center gap-2"
                  )}
                >
                  {generateMutation.isPending ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Generating Alternatives...
                    </>
                  ) : (
                    <>
                      <Lightbulb className="h-5 w-5" />
                      Generate Alternatives
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Recent Designs */}
            {recentDesigns?.designs && recentDesigns.designs.length > 0 && (
              <div className="p-6 rounded-xl bg-gray-800/50 border border-gray-700/50">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Recent Designs
                </h3>
                <div className="space-y-3">
                  {recentDesigns.designs.map((design) => (
                    <button
                      key={design.design_id}
                      onClick={() => {
                        setChallenge(design.challenge)
                      }}
                      className={cn(
                        "w-full p-3 rounded-lg",
                        "bg-gray-900/50 border border-gray-700",
                        "hover:border-purple-500/50 transition-colors",
                        "text-left"
                      )}
                    >
                      <p className="text-sm text-white line-clamp-2 mb-1">
                        {design.challenge}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <Clock className="h-3 w-3" />
                        {new Date(design.created_at).toLocaleDateString()}
                        <span className="ml-auto text-purple-400">
                          RICE: {design.avg_rice_score.toFixed(1)}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </form>
        </motion.div>

        {/* Right Column - Results */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2"
        >
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="space-y-6"
              >
                {/* Tradeoff Analysis */}
                <div className="p-6 rounded-xl bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20">
                  <div className="flex items-center gap-3 mb-4">
                    <TrendingUp className="h-6 w-6 text-purple-400" />
                    <h2 className="text-2xl font-bold text-white">Trade-off Analysis</h2>
                  </div>
                  <p className="text-lg text-gray-200 leading-relaxed mb-4">
                    {result.tradeoff_analysis.summary}
                  </p>
                  <div className="p-4 rounded-lg bg-purple-500/10 border border-purple-500/20">
                    <p className="text-sm font-semibold text-purple-400 mb-2">
                      Recommendation:
                    </p>
                    <p className="text-white">
                      {result.tradeoff_analysis.recommendation}
                    </p>
                  </div>
                  <div className="flex items-center gap-4 mt-4 text-sm text-gray-400">
                    <div className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {(result.total_duration_ms / 1000).toFixed(2)}s
                    </div>
                    <div className="flex items-center gap-1">
                      <CheckCircle2 className="h-4 w-4 text-green-400" />
                      {result.alternatives.length} alternatives
                    </div>
                  </div>
                </div>

                {/* Alternatives Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {result.alternatives.map((alt, index) => (
                    <motion.div
                      key={alt.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={cn(
                        "p-5 rounded-xl border",
                        "bg-gradient-to-br",
                        getAlternativeColor(alt.id)
                      )}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <span className={cn(
                          "text-2xl font-bold",
                          getAlternativeTextColor(alt.id)
                        )}>
                          Alternative {alt.id}
                        </span>
                        <div className="text-right">
                          <p className="text-xs text-gray-400">RICE Score</p>
                          <p className={cn(
                            "text-2xl font-bold",
                            getAlternativeTextColor(alt.id)
                          )}>
                            {alt.rice.score.toFixed(2)}
                          </p>
                        </div>
                      </div>

                      <h3 className="text-lg font-semibold text-white mb-2">
                        {alt.title}
                      </h3>
                      <p className="text-sm text-gray-300 mb-4">
                        {alt.description}
                      </p>

                      {/* RICE Breakdown */}
                      <div className="grid grid-cols-2 gap-2 mb-4 text-xs">
                        <div className="p-2 rounded bg-gray-900/30">
                          <p className="text-gray-400">Reach</p>
                          <p className="font-bold text-white">{alt.rice.reach}/10</p>
                        </div>
                        <div className="p-2 rounded bg-gray-900/30">
                          <p className="text-gray-400">Impact</p>
                          <p className="font-bold text-white">{alt.rice.impact}/10</p>
                        </div>
                        <div className="p-2 rounded bg-gray-900/30">
                          <p className="text-gray-400">Confidence</p>
                          <p className="font-bold text-white">{alt.rice.confidence}/10</p>
                        </div>
                        <div className="p-2 rounded bg-gray-900/30">
                          <p className="text-gray-400">Effort</p>
                          <p className="font-bold text-white">{alt.rice.effort}/10</p>
                        </div>
                      </div>

                      {/* Pros/Cons */}
                      <div className="space-y-3 text-xs">
                        <div>
                          <p className="font-semibold text-green-400 mb-1">Pros:</p>
                          <ul className="list-disc list-inside space-y-0.5">
                            {alt.pros.map((pro, i) => (
                              <li key={i} className="text-gray-300">{pro}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <p className="font-semibold text-red-400 mb-1">Cons:</p>
                          <ul className="list-disc list-inside space-y-0.5">
                            {alt.cons.map((con, i) => (
                              <li key={i} className="text-gray-300">{con}</li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      <button
                        onClick={() => {
                          setSelectedAlt(alt.id)
                          setShowFeedbackForm(true)
                        }}
                        className={cn(
                          "w-full mt-4 px-4 py-2 rounded-lg",
                          "bg-gray-900/50 hover:bg-gray-900/70",
                          "text-white text-sm font-medium",
                          "transition-colors"
                        )}
                      >
                        Select This Alternative
                      </button>
                    </motion.div>
                  ))}
                </div>

                {/* Feedback Form */}
                <AnimatePresence>
                  {showFeedbackForm && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="p-6 rounded-xl bg-gray-800/50 border border-gray-700/50"
                    >
                      <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                        <MessageSquare className="h-5 w-5" />
                        Provide Feedback
                      </h3>
                      <form onSubmit={handleFeedbackSubmit} className="space-y-4">
                        <div>
                          <label className="block text-sm text-gray-400 mb-2">
                            Selected Alternative: <span className="text-white font-semibold">Alternative {selectedAlt}</span>
                          </label>
                        </div>
                        <div>
                          <label className="block text-sm text-gray-400 mb-2">
                            Rating (1-5)
                          </label>
                          <div className="flex gap-2">
                            {[1, 2, 3, 4, 5].map((val) => (
                              <button
                                key={val}
                                type="button"
                                onClick={() => setRating(val)}
                                className={cn(
                                  "p-2 rounded-lg transition-colors",
                                  rating >= val
                                    ? "bg-yellow-500/20 text-yellow-400"
                                    : "bg-gray-700 text-gray-400"
                                )}
                              >
                                <Star className="h-5 w-5" fill={rating >= val ? "currentColor" : "none"} />
                              </button>
                            ))}
                          </div>
                        </div>
                        <div>
                          <label className="block text-sm text-gray-400 mb-2">
                            Comments
                          </label>
                          <textarea
                            value={comments}
                            onChange={(e) => setComments(e.target.value)}
                            placeholder="Share your thoughts on this alternative..."
                            className={cn(
                              "w-full px-4 py-3 rounded-lg",
                              "bg-gray-900/50 border border-gray-700",
                              "text-white placeholder-gray-500",
                              "focus:outline-none focus:border-purple-500",
                              "transition-colors resize-none"
                            )}
                            rows={3}
                          />
                        </div>
                        <div className="flex gap-3">
                          <button
                            type="submit"
                            disabled={feedbackMutation.isPending}
                            className={cn(
                              "flex-1 px-6 py-3 rounded-lg font-semibold",
                              "bg-gradient-to-r from-purple-500 to-pink-500",
                              "text-white transition-all",
                              "hover:from-purple-600 hover:to-pink-600",
                              "disabled:opacity-50 disabled:cursor-not-allowed",
                              "flex items-center justify-center gap-2"
                            )}
                          >
                            {feedbackMutation.isPending ? (
                              <>
                                <Loader2 className="h-5 w-5 animate-spin" />
                                Submitting...
                              </>
                            ) : (
                              <>
                                <ThumbsUp className="h-5 w-5" />
                                Submit Feedback
                              </>
                            )}
                          </button>
                          <button
                            type="button"
                            onClick={() => setShowFeedbackForm(false)}
                            className={cn(
                              "px-6 py-3 rounded-lg font-semibold",
                              "bg-gray-700 text-white",
                              "hover:bg-gray-600 transition-colors"
                            )}
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ) : (
              <motion.div
                key="placeholder"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex flex-col items-center justify-center h-full min-h-[600px] text-center"
              >
                <div className="p-6 rounded-full bg-gray-800/50 mb-6">
                  <Palette className="h-16 w-16 text-gray-600" />
                </div>
                <h3 className="text-2xl font-semibold text-gray-400 mb-2">
                  No Design Generated Yet
                </h3>
                <p className="text-gray-500 max-w-md">
                  Enter a design challenge and click &ldquo;Generate Alternatives&rdquo; to see 3 design
                  alternatives with RICE scoring and trade-off analysis.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  )
}

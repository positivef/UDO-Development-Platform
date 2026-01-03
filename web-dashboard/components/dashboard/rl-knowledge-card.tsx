"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Brain,
  Database,
  FlaskConical,
  Lightbulb,
  TrendingUp,
  Zap,
} from "lucide-react";
import { getRLSummary, type RLSummary } from "@/lib/api/rl-knowledge";
import { cn } from "@/lib/utils";

/**
 * RL Knowledge Card - Displays Training-free GRPO system status
 *
 * Shows:
 * - Token Prior statistics (decisions stored, validation rate)
 * - Pattern counts by domain
 * - Experiment tracking (success rate)
 * - System health status
 */
export function RLKnowledgeCard() {
  const [summary, setSummary] = useState<RLSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSummary() {
      try {
        const data = await getRLSummary();
        setSummary(data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch RL summary:", err);
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setIsLoading(false);
      }
    }

    fetchSummary();
    // Refresh every 30 seconds
    const interval = setInterval(fetchSummary, 30000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <Card className="border-gray-700 bg-gray-800/50">
        <CardHeader className="pb-2">
          <Skeleton className="h-6 w-40" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (error || !summary) {
    return (
      <Card className="border-red-500/30 bg-red-500/10">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-red-400">
            <Brain className="h-5 w-5" />
            RL Knowledge System
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-400">
            {error || "Unable to load RL Knowledge status"}
          </p>
        </CardContent>
      </Card>
    );
  }

  const { token_prior, patterns, experiments, system_status } = summary;

  // Calculate validation rate
  const validationRate =
    token_prior.total_decisions > 0
      ? (token_prior.validated_count / token_prior.total_decisions) * 100
      : 0;

  // Calculate experiment success rate
  const successRate =
    experiments.total > 0
      ? (experiments.with_success / experiments.total) * 100
      : 0;

  // Get top domains
  const topDomains = Object.entries(patterns.by_domain)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 3);

  return (
    <Card className="border-purple-500/30 bg-gradient-to-br from-purple-900/20 to-gray-800/50">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-purple-400">
            <Brain className="h-5 w-5" />
            RL Knowledge System
          </CardTitle>
          <Badge
            variant="outline"
            className={cn(
              "text-xs",
              system_status === "operational"
                ? "border-green-500 text-green-400"
                : "border-yellow-500 text-yellow-400"
            )}
          >
            <Zap className="mr-1 h-3 w-3" />
            {system_status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Token Prior Section */}
        <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="flex items-center gap-2 text-sm font-medium text-gray-300">
              <Database className="h-4 w-4 text-blue-400" />
              Token Prior
            </span>
            <span className="text-xs text-gray-500">
              {token_prior.total_decisions} decisions
            </span>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-400">Validation Rate</span>
              <span
                className={cn(
                  "font-medium",
                  validationRate > 50
                    ? "text-green-400"
                    : validationRate > 25
                      ? "text-yellow-400"
                      : "text-gray-400"
                )}
              >
                {validationRate.toFixed(1)}%
              </span>
            </div>
            <Progress value={validationRate} className="h-1.5" />
          </div>
          {token_prior.accuracy !== null && (
            <div className="mt-2 flex items-center justify-between text-xs">
              <span className="text-gray-400">Accuracy</span>
              <span
                className={cn(
                  "font-medium",
                  token_prior.accuracy > 0.8
                    ? "text-green-400"
                    : token_prior.accuracy > 0.6
                      ? "text-yellow-400"
                      : "text-red-400"
                )}
              >
                {(token_prior.accuracy * 100).toFixed(1)}%
              </span>
            </div>
          )}
        </div>

        {/* Patterns Section */}
        <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="flex items-center gap-2 text-sm font-medium text-gray-300">
              <Lightbulb className="h-4 w-4 text-yellow-400" />
              Knowledge Patterns
            </span>
            <span className="text-xs text-gray-500">{patterns.total} total</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {topDomains.map(([domain, count]) => (
              <Badge
                key={domain}
                variant="secondary"
                className="bg-gray-700/50 text-xs text-gray-300"
              >
                {domain}: {count}
              </Badge>
            ))}
            {topDomains.length === 0 && (
              <span className="text-xs text-gray-500">No patterns yet</span>
            )}
          </div>
        </div>

        {/* Experiments Section */}
        <div className="rounded-lg border border-gray-700 bg-gray-800/50 p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="flex items-center gap-2 text-sm font-medium text-gray-300">
              <FlaskConical className="h-4 w-4 text-green-400" />
              Experiments
            </span>
            <span className="text-xs text-gray-500">
              {experiments.total} tracked
            </span>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-400">Success Rate</span>
              <span
                className={cn(
                  "font-medium",
                  successRate > 70
                    ? "text-green-400"
                    : successRate > 40
                      ? "text-yellow-400"
                      : "text-red-400"
                )}
              >
                {successRate.toFixed(1)}%
              </span>
            </div>
            <Progress
              value={successRate}
              className="h-1.5"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-gray-700 pt-2 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            Training-free GRPO
          </span>
          <span>ArXiv 2510.08191</span>
        </div>
      </CardContent>
    </Card>
  );
}

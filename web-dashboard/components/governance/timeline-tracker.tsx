"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  CheckCircle2,
  Circle,
  Clock,
  AlertTriangle,
  Calendar,
  Loader2,
} from "lucide-react";

// ============================================
// Types
// ============================================

interface Milestone {
  name: string;
  status: "complete" | "in_progress" | "pending";
  date: string;
}

interface TimelineStatus {
  current_phase: string;
  progress_percent: number;
  days_remaining: number;
  milestones: Milestone[];
  risk_level: "low" | "medium" | "high";
}

// ============================================
// API
// ============================================

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchTimeline(): Promise<TimelineStatus | null> {
  try {
    const res = await fetch(`${API_BASE}/api/governance/timeline`, {
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      return await res.json();
    }
    return null;
  } catch {
    return null;
  }
}

// ============================================
// Components
// ============================================

function MilestoneItem({ milestone, index }: { milestone: Milestone; index: number }) {
  const getIcon = () => {
    switch (milestone.status) {
      case "complete":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "in_progress":
        return <Clock className="h-4 w-4 text-blue-500 animate-pulse" />;
      default:
        return <Circle className="h-4 w-4 text-gray-300" />;
    }
  };

  const getTextClass = () => {
    switch (milestone.status) {
      case "complete":
        return "text-muted-foreground line-through";
      case "in_progress":
        return "text-blue-600 font-medium";
      default:
        return "text-gray-400";
    }
  };

  return (
    <div className="flex items-center gap-3 py-1">
      <div className="flex-shrink-0">
        {getIcon()}
      </div>
      <div className="flex-1 min-w-0">
        <p className={`text-sm truncate ${getTextClass()}`}>
          {milestone.name}
        </p>
      </div>
      {milestone.status === "in_progress" && (
        <Badge variant="outline" className="text-xs bg-blue-50 dark:bg-blue-900/20">
          Now
        </Badge>
      )}
    </div>
  );
}

// ============================================
// Main Component
// ============================================

export default function TimelineTracker() {
  const [timeline, setTimeline] = useState<TimelineStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTimeline();
  }, []);

  async function loadTimeline() {
    setLoading(true);
    const data = await fetchTimeline();
    setTimeline(data);
    setLoading(false);
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  // Fallback data if API not available
  const data = timeline || {
    current_phase: "Phase 5: MVP Enhancement",
    progress_percent: 83.3,
    days_remaining: 7,
    milestones: [
      { name: "Phase 0: Immediate Impact", status: "complete" as const, date: "2025-12-23" },
      { name: "Phase 1: Foundation", status: "complete" as const, date: "2025-12-23" },
      { name: "Phase 2: API Development", status: "complete" as const, date: "2025-12-23" },
      { name: "Phase 3: CLI Development", status: "complete" as const, date: "2025-12-23" },
      { name: "Phase 4: Automation", status: "complete" as const, date: "2025-12-24" },
      { name: "Phase 5: MVP Enhancement", status: "in_progress" as const, date: "2025-12-24" },
    ],
    risk_level: "low" as const,
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case "low": return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "medium": return "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200";
      case "high": return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getRiskIcon = (risk: string) => {
    if (risk === "high") return <AlertTriangle className="h-3 w-3" />;
    return null;
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Timeline
          </CardTitle>
          <Badge className={getRiskColor(data.risk_level)}>
            {getRiskIcon(data.risk_level)}
            <span className="ml-1">{data.risk_level.toUpperCase()}</span>
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Progress */}
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-medium">{data.progress_percent.toFixed(0)}%</span>
          </div>
          <Progress value={data.progress_percent} className="h-2" />
        </div>

        {/* Days remaining */}
        <div className="flex items-center justify-center gap-2 py-2 bg-slate-50 dark:bg-slate-800 rounded-lg">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <span className="text-lg font-bold">{data.days_remaining}</span>
          <span className="text-sm text-muted-foreground">days remaining</span>
        </div>

        {/* Current phase */}
        <div className="text-center py-2">
          <p className="text-xs text-muted-foreground">Current Phase</p>
          <p className="text-sm font-medium text-blue-600 dark:text-blue-400">
            {data.current_phase}
          </p>
        </div>

        {/* Milestones */}
        <div className="space-y-1 max-h-48 overflow-y-auto">
          {data.milestones.map((milestone, i) => (
            <MilestoneItem key={i} milestone={milestone} index={i} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

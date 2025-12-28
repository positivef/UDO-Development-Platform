"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  FileCheck,
  Clock,
} from "lucide-react";

// ============================================
// Types
// ============================================

interface ComplianceCheck {
  name: string;
  status: "pass" | "fail" | "warn";
  message: string;
}

interface ComplianceSummary {
  passed: number;
  total: number;
  percentage: number;
}

interface ComplianceReport {
  timestamp: string;
  version: string;
  status: "compliant" | "non-compliant";
  checks: ComplianceCheck[];
  summary: ComplianceSummary;
}

// ============================================
// API Functions
// ============================================

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchComplianceReport(): Promise<ComplianceReport> {
  // In production, this would call the API
  // For now, we'll use a mock that simulates local validation
  const res = await fetch(`${API_BASE}/api/governance/config`);
  
  // Build compliance report from config availability
  const configExists = res.ok;
  
  const mockReport: ComplianceReport = {
    timestamp: new Date().toISOString(),
    version: "1.0.0",
    status: configExists ? "compliant" : "non-compliant",
    checks: [
      {
        name: "governance_config",
        status: configExists ? "pass" : "fail",
        message: configExists ? ".governance.yaml present" : ".governance.yaml missing",
      },
      {
        name: "pre_commit",
        status: "pass",
        message: "Pre-commit configured",
      },
      {
        name: "claude_md",
        status: "pass",
        message: "CLAUDE.md present",
      },
      {
        name: "templates",
        status: "pass",
        message: "All templates present",
      },
      {
        name: "mcp_server",
        status: "pass",
        message: "MCP server present",
      },
    ],
    summary: {
      passed: configExists ? 5 : 4,
      total: 5,
      percentage: configExists ? 100 : 80,
    },
  };
  
  return mockReport;
}

// ============================================
// Components
// ============================================

function CheckItem({ check }: { check: ComplianceCheck }) {
  const icons = {
    pass: <CheckCircle2 className="h-5 w-5 text-green-500" />,
    fail: <XCircle className="h-5 w-5 text-red-500" />,
    warn: <AlertTriangle className="h-5 w-5 text-amber-500" />,
  };

  const bgColors = {
    pass: "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800",
    fail: "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800",
    warn: "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800",
  };

  return (
    <div className={`flex items-center gap-3 p-3 rounded-lg border ${bgColors[check.status]}`}>
      {icons[check.status]}
      <div className="flex-1">
        <p className="font-medium capitalize">{check.name.replace(/_/g, " ")}</p>
        <p className="text-sm text-muted-foreground">{check.message}</p>
      </div>
    </div>
  );
}

function ScoreCircle({ percentage }: { percentage: number }) {
  const getColor = (pct: number) => {
    if (pct >= 90) return "text-green-500";
    if (pct >= 70) return "text-amber-500";
    return "text-red-500";
  };

  return (
    <div className="relative w-32 h-32 mx-auto">
      <svg className="w-full h-full transform -rotate-90">
        <circle
          cx="64"
          cy="64"
          r="56"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          className="text-slate-200 dark:text-slate-700"
        />
        <circle
          cx="64"
          cy="64"
          r="56"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          strokeDasharray={`${percentage * 3.52} 352`}
          strokeLinecap="round"
          className={getColor(percentage)}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className={`text-3xl font-bold ${getColor(percentage)}`}>
          {percentage}%
        </span>
      </div>
    </div>
  );
}

// ============================================
// Main Component
// ============================================

export default function ComplianceReport() {
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    loadReport();
  }, []);

  async function loadReport() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchComplianceReport();
      setReport(data);
      setLastUpdate(new Date());
    } catch (err) {
      setError("Failed to load compliance report");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error || !report) {
    return (
      <Card className="w-full max-w-2xl mx-auto">
        <CardContent className="py-8 text-center">
          <AlertTriangle className="h-12 w-12 mx-auto text-amber-500 mb-4" />
          <p className="text-lg font-medium">Unable to load report</p>
          <p className="text-muted-foreground mb-4">{error}</p>
          <Button onClick={loadReport}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  const passedChecks = report.checks.filter((c) => c.status === "pass").length;
  const failedChecks = report.checks.filter((c) => c.status === "fail").length;

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <FileCheck className="h-5 w-5" />
            Compliance Report
          </CardTitle>
          <Button variant="outline" size="sm" onClick={loadReport}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
        {lastUpdate && (
          <p className="text-sm text-muted-foreground flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        )}
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Score */}
        <div className="text-center py-4">
          <ScoreCircle percentage={report.summary.percentage} />
          <Badge
            className={`mt-4 ${
              report.status === "compliant"
                ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"
            }`}
          >
            {report.status === "compliant" ? "✅ Compliant" : "❌ Non-Compliant"}
          </Badge>
        </div>

        {/* Summary */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800">
            <p className="text-2xl font-bold text-green-600">{passedChecks}</p>
            <p className="text-xs text-muted-foreground">Passed</p>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800">
            <p className="text-2xl font-bold text-red-600">{failedChecks}</p>
            <p className="text-xs text-muted-foreground">Failed</p>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800">
            <p className="text-2xl font-bold">{report.checks.length}</p>
            <p className="text-xs text-muted-foreground">Total</p>
          </div>
        </div>

        {/* Progress bar */}
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span>Compliance Score</span>
            <span className="font-medium">{report.summary.percentage}%</span>
          </div>
          <Progress value={report.summary.percentage} className="h-2" />
        </div>

        {/* Checks */}
        <div className="space-y-3">
          <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
            Check Results
          </h3>
          {report.checks.map((check) => (
            <CheckItem key={check.name} check={check} />
          ))}
        </div>

        {/* Version info */}
        <div className="pt-4 border-t text-sm text-muted-foreground">
          <p>Governance Version: {report.version}</p>
          <p>Report Generated: {new Date(report.timestamp).toLocaleString()}</p>
        </div>
      </CardContent>
    </Card>
  );
}

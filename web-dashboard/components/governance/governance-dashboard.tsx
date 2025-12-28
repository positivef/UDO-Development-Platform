"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Shield, 
  FileCode, 
  LayoutTemplate,
  RefreshCw
} from "lucide-react";

// ============================================
// Types
// ============================================

interface GovernanceTemplate {
  name: string;
  description: string;
  size: string;
  strict_mode: boolean;
  ci_cd_enabled: boolean;
  features: string[];
  exists: boolean;
}

interface ValidationResult {
  passed: boolean;
  total_rules: number;
  passed_rules: number;
  failed_rules: number;
  critical_failures: number;
  message: string;
  details?: string;
}

interface GovernanceConfig {
  version: string;
  project_name: string;
  project_type: string;
  size: string;
  strict_mode: boolean;
  uncertainty_enabled: boolean;
  ci_cd_enabled: boolean;
}

// ============================================
// API Functions
// ============================================

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchRules(): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/governance/rules`);
  if (!res.ok) throw new Error("Failed to fetch rules");
  return res.json();
}

async function fetchTemplates(): Promise<{ templates: GovernanceTemplate[]; total: number }> {
  const res = await fetch(`${API_BASE}/api/governance/templates`);
  if (!res.ok) throw new Error("Failed to fetch templates");
  return res.json();
}

async function validateRules(): Promise<ValidationResult> {
  const res = await fetch(`${API_BASE}/api/governance/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_path: "." }),
  });
  if (!res.ok) throw new Error("Validation failed");
  return res.json();
}

async function fetchConfig(): Promise<GovernanceConfig> {
  const res = await fetch(`${API_BASE}/api/governance/config`);
  if (!res.ok) throw new Error("Failed to fetch config");
  return res.json();
}

async function applyTemplate(templateName: string): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/api/governance/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      project_path: ".", 
      template_name: templateName,
      overwrite: false 
    }),
  });
  if (!res.ok) throw new Error("Failed to apply template");
  return res.json();
}

async function runAutoFix(fixType: string = "lint"): Promise<{ success: boolean; details: string }> {
  const res = await fetch(`${API_BASE}/api/governance/auto-fix`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fix_type: fixType }),
  });
  if (!res.ok) throw new Error("Auto-fix failed");
  return res.json();
}

// ============================================
// Components
// ============================================

function RuleCard({ rule, index, onClick }: { rule: string; index: number; onClick?: () => void }) {
  const icons: Record<string, React.ReactNode> = {
    obsidian_sync: <FileCode className="h-4 w-4" />,
    git_workflow: <Shield className="h-4 w-4" />,
    documentation: <FileCode className="h-4 w-4" />,
    innovation_safety: <Shield className="h-4 w-4" />,
    error_resolution: <AlertTriangle className="h-4 w-4" />,
    pre_commit: <CheckCircle2 className="h-4 w-4" />,
    ci_cd: <RefreshCw className="h-4 w-4" />,
  };

  return (
    <button
      onClick={onClick}
      className="flex items-center gap-2 p-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors cursor-pointer w-full text-left"
    >
      {icons[rule] || <Shield className="h-4 w-4" />}
      <span className="text-sm font-medium capitalize">{rule.replace(/_/g, " ")}</span>
    </button>
  );
}

function TemplateCard({ template, onApply }: { template: GovernanceTemplate; onApply: (name: string) => void }) {
  const sizeColors: Record<string, string> = {
    minimal: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    standard: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    enterprise: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <CardTitle className="text-lg capitalize">{template.name}</CardTitle>
          <Badge className={sizeColors[template.size] || "bg-gray-100"}>
            {template.size}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-3">{template.description}</p>
        
        <div className="flex gap-2 mb-3">
          {template.strict_mode && (
            <Badge variant="outline" className="text-xs">
              <Shield className="h-3 w-3 mr-1" /> Strict
            </Badge>
          )}
          {template.ci_cd_enabled && (
            <Badge variant="outline" className="text-xs">
              <RefreshCw className="h-3 w-3 mr-1" /> CI/CD
            </Badge>
          )}
        </div>

        <div className="flex flex-wrap gap-1">
          {template.features.slice(0, 3).map((feature, i) => (
            <span key={i} className="text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
              {feature}
            </span>
          ))}
          {template.features.length > 3 && (
            <span className="text-xs text-muted-foreground">
              +{template.features.length - 3} more
            </span>
          )}
        </div>

        <Button 
          className="w-full mt-4" 
          variant={template.exists ? "default" : "outline"}
          disabled={!template.exists}
          onClick={() => onApply(template.name)}
        >
          {template.exists ? "Apply Template" : "Template Missing"}
        </Button>
      </CardContent>
    </Card>
  );
}

function ValidationStatus({ result }: { result: ValidationResult | null; loading: boolean }) {
  if (!result) return null;

  const StatusIcon = result.passed ? CheckCircle2 : XCircle;
  const statusColor = result.passed 
    ? "text-green-600 dark:text-green-400" 
    : "text-red-600 dark:text-red-400";

  return (
    <Card className={result.passed ? "border-green-200 dark:border-green-800" : "border-red-200 dark:border-red-800"}>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <StatusIcon className={`h-5 w-5 ${statusColor}`} />
          <CardTitle className="text-lg">Validation Result</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="text-center p-3 rounded-lg bg-slate-100 dark:bg-slate-800">
            <div className="text-2xl font-bold text-green-600">{result.passed_rules}</div>
            <div className="text-xs text-muted-foreground">Passed</div>
          </div>
          <div className="text-center p-3 rounded-lg bg-slate-100 dark:bg-slate-800">
            <div className="text-2xl font-bold text-red-600">{result.failed_rules}</div>
            <div className="text-xs text-muted-foreground">Failed</div>
          </div>
        </div>

        <div className="text-sm">
          <span className="font-medium">Pass Rate: </span>
          <span className={result.passed ? "text-green-600" : "text-amber-600"}>
            {((result.passed_rules / result.total_rules) * 100).toFixed(1)}%
          </span>
        </div>

        <p className="text-sm text-muted-foreground mt-2">{result.message}</p>
      </CardContent>
    </Card>
  );
}

// ============================================
// Main Component
// ============================================

export default function GovernanceDashboard() {
  const [rules, setRules] = useState<string[]>([]);
  const [templates, setTemplates] = useState<GovernanceTemplate[]>([]);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [config, setConfig] = useState<GovernanceConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedRule, setSelectedRule] = useState<string | null>(null);
  const [applyingTemplate, setApplyingTemplate] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [rulesData, templatesData, configData] = await Promise.all([
        fetchRules().catch(() => []),
        fetchTemplates().catch(() => ({ templates: [], total: 0 })),
        fetchConfig().catch(() => null),
      ]);
      setRules(rulesData);
      setTemplates(templatesData.templates);
      setConfig(configData);
    } catch (err) {
      setError("Failed to load governance data. Make sure the API server is running.");
    } finally {
      setLoading(false);
    }
  }

  async function runValidation() {
    setValidating(true);
    setError(null);
    try {
      const result = await validateRules();
      setValidation(result);
      setSuccessMessage("Validation completed successfully!");
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError("Validation failed. Check if validate_system_rules.py exists.");
    } finally {
      setValidating(false);
    }
  }

  async function handleApplyTemplate(templateName: string) {
    setApplyingTemplate(true);
    setError(null);
    try {
      const result = await applyTemplate(templateName);
      setSuccessMessage(`Template "${templateName}" applied successfully!`);
      setTimeout(() => setSuccessMessage(null), 3000);
      await loadData(); // Reload config
    } catch (err) {
      setError(`Failed to apply template "${templateName}". ${err}`);
    } finally {
      setApplyingTemplate(false);
    }
  }

  async function handleAutoFix() {
    setValidating(true);
    setError(null);
    try {
      const result = await runAutoFix("lint");
      setSuccessMessage(`Auto-fix completed: ${result.details}`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError("Auto-fix failed. Make sure Black and isort are installed.");
    } finally {
      setValidating(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Governance Dashboard</h1>
          <p className="text-muted-foreground">
            Project rules, templates, and compliance status
          </p>
        </div>
        <Button onClick={loadData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200 p-4 rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          {error}
        </div>
      )}

      {successMessage && (
        <div className="bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200 p-4 rounded-lg flex items-center gap-2">
          <CheckCircle2 className="h-5 w-5" />
          {successMessage}
        </div>
      )}

      {/* Project Config */}
      {config && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Project Configuration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">Project</p>
                <p className="font-medium">{config.project_name}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Type</p>
                <p className="font-medium capitalize">{config.project_type}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Size</p>
                <Badge variant="outline">{config.size}</Badge>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Version</p>
                <p className="font-medium">{config.version}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Validation Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5" />
              Rule Validation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Validate project against all governance rules.
            </p>
            <div className="space-y-2">
              <Button 
                onClick={runValidation} 
                disabled={validating}
                className="w-full"
              >
                {validating ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Validating...
                  </>
                ) : (
                  <>
                    <Shield className="h-4 w-4 mr-2" />
                    Run Validation
                  </>
                )}
              </Button>
              <Button 
                onClick={handleAutoFix} 
                disabled={validating}
                variant="outline"
                className="w-full"
              >
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Auto-Fix (Lint)
              </Button>
            </div>
          </CardContent>
        </Card>

        {validation && <ValidationStatus result={validation} loading={validating} />}
      </div>

      {/* Available Rules */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <FileCode className="h-5 w-5" />
            Available Rules ({rules.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {rules.map((rule, i) => (
              <RuleCard 
                key={rule} 
                rule={rule} 
                index={i} 
                onClick={() => setSelectedRule(rule)}
              />
            ))}
          </div>
          
          {selectedRule && (
            <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-medium capitalize">{selectedRule.replace(/_/g, " ")}</h4>
                <Button size="sm" variant="ghost" onClick={() => setSelectedRule(null)}>✕</Button>
              </div>
              <p className="text-sm text-muted-foreground">
                {selectedRule === "obsidian_sync" && "Ensures Obsidian vault synchronization and documentation consistency."}
                {selectedRule === "git_workflow" && "Validates Git commit messages, branch naming, and workflow compliance."}
                {selectedRule === "documentation" && "Checks for required documentation files (README, CLAUDE.md, etc.)."}
                {selectedRule === "innovation_safety" && "Ensures safe experimentation with proper rollback mechanisms."}
                {selectedRule === "error_resolution" && "Validates error handling patterns and logging practices."}
                {selectedRule === "pre_commit" && "Ensures pre-commit hooks are configured and active."}
                {selectedRule === "ci_cd" && "Validates CI/CD pipeline configuration and automation."}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Templates */}
      <div>
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <LayoutTemplate className="h-5 w-5" />
          Governance Templates
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {templates.map((template) => (
            <TemplateCard 
              key={template.name} 
              template={template} 
              onApply={handleApplyTemplate}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

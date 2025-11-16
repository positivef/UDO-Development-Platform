"""
3-AI Collaboration Bridge - Orchestrates Claude, Codex, and Gemini
Based on COMPASS Framework v2.1 and Opus Review Recommendations

Features:
- Context preservation across AI tools
- Specialized role assignment
- Parallel and sequential execution modes
- Automatic verification loops

Author: VibeCoding Team
Date: 2025-11-16
Version: 1.0.0
"""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import tempfile
import yaml


class AIRole(Enum):
    """Specialized roles for each AI"""
    # Claude roles
    CLAUDE_IMPLEMENT = "claude-implement"
    CLAUDE_ARCHITECT = "claude-architect"
    CLAUDE_DOCUMENT = "claude-document"

    # Codex roles
    CODEX_VERIFY = "codex-verify"
    CODEX_REVIEW = "codex-review"
    CODEX_DEBUG = "codex-debug"

    # Gemini roles
    GEMINI_CREATE = "gemini-create"
    GEMINI_EXPLORE = "gemini-explore"
    GEMINI_OPTIMIZE = "gemini-optimize"


class ExecutionMode(Enum):
    """Collaboration execution modes"""
    SEQUENTIAL = "sequential"  # One after another
    PARALLEL = "parallel"      # All at once
    ITERATIVE = "iterative"    # Loop until convergence
    ADAPTIVE = "adaptive"      # Dynamic based on results


@dataclass
class AIContext:
    """Shared context between AI tools"""
    task_id: str
    phase: str
    previous_outputs: Dict[str, Any]
    constraints: List[str]
    success_criteria: List[str]
    metadata: Dict[str, Any]
    timestamp: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_yaml(self) -> str:
        """Convert to YAML for context passing"""
        return yaml.dump(asdict(self), default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'AIContext':
        """Create from YAML string"""
        data = yaml.safe_load(yaml_str)
        return cls(**data)


@dataclass
class AIResponse:
    """Response from an AI tool"""
    ai_name: str
    role: AIRole
    output: str
    confidence: float
    issues_found: List[str]
    suggestions: List[str]
    execution_time: float
    metadata: Dict[str, Any]


class CodexInterface:
    """Interface for Codex (GPT Pro) integration"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if Codex is available"""
        try:
            # Try CLI first
            result = subprocess.run(
                ["codex", "--version"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            # Fall back to API key check
            return bool(self.api_key)

    def execute(self, task: str, role: AIRole, context: AIContext) -> AIResponse:
        """Execute Codex with specific role"""
        if not self.available:
            return AIResponse(
                ai_name="codex",
                role=role,
                output="Codex not available",
                confidence=0.0,
                issues_found=[],
                suggestions=[],
                execution_time=0.0,
                metadata={"error": "Codex not configured"}
            )

        start_time = time.time()

        # Create specialized prompt based on role
        prompt = self._create_role_prompt(task, role, context)

        try:
            # Execute via CLI or API
            if self._has_cli():
                output = self._execute_cli(prompt)
            else:
                output = self._execute_api(prompt)

            # Parse Codex output for issues and suggestions
            issues, suggestions = self._parse_output(output)

            return AIResponse(
                ai_name="codex",
                role=role,
                output=output,
                confidence=0.85,  # Codex typically has high confidence
                issues_found=issues,
                suggestions=suggestions,
                execution_time=time.time() - start_time,
                metadata={"method": "cli" if self._has_cli() else "api"}
            )

        except Exception as e:
            return AIResponse(
                ai_name="codex",
                role=role,
                output=f"Error: {str(e)}",
                confidence=0.0,
                issues_found=[],
                suggestions=[],
                execution_time=time.time() - start_time,
                metadata={"error": str(e)}
            )

    def _has_cli(self) -> bool:
        """Check if Codex CLI is available"""
        try:
            subprocess.run(["codex", "--help"], capture_output=True, timeout=1)
            return True
        except:
            return False

    def _create_role_prompt(self, task: str, role: AIRole, context: AIContext) -> str:
        """Create role-specific prompt for Codex"""
        base_prompt = f"""
Task: {task}
Previous Context: {json.dumps(context.previous_outputs, indent=2)}
Constraints: {', '.join(context.constraints)}
Success Criteria: {', '.join(context.success_criteria)}
"""

        if role == AIRole.CODEX_VERIFY:
            return base_prompt + """
Role: Code Verification Specialist
Focus:
1. Verify correctness of implementation
2. Check for edge cases and error handling
3. Validate against success criteria
4. Identify potential bugs

Output Format:
- Issues Found: [list]
- Test Cases Needed: [list]
- Verification Status: PASS/FAIL/PARTIAL
"""

        elif role == AIRole.CODEX_REVIEW:
            return base_prompt + """
Role: Senior Code Reviewer
Focus:
1. Code quality and best practices
2. Performance optimizations
3. Security vulnerabilities
4. Maintainability concerns

Output Format:
- Critical Issues: [list]
- Suggestions: [list]
- Security Findings: [list]
- Performance Notes: [list]
"""

        elif role == AIRole.CODEX_DEBUG:
            return base_prompt + """
Role: Debugging Expert
Focus:
1. Root cause analysis
2. Stack trace interpretation
3. Memory and performance profiling
4. Fix recommendations

Output Format:
- Root Cause: [description]
- Fix Steps: [numbered list]
- Prevention: [recommendations]
"""

        return base_prompt

    def _execute_cli(self, prompt: str) -> str:
        """Execute via Codex CLI"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            temp_file = f.name

        try:
            result = subprocess.run(
                ["codex", "exec", "--prompt", temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout
        finally:
            os.unlink(temp_file)

    def _execute_api(self, prompt: str) -> str:
        """Execute via OpenAI API"""
        # This would use the OpenAI Python client
        # Simplified for demonstration
        return f"[API Response for: {prompt[:100]}...]"

    def _parse_output(self, output: str) -> Tuple[List[str], List[str]]:
        """Parse Codex output for structured information"""
        issues = []
        suggestions = []

        lines = output.split('\n')
        current_section = None

        for line in lines:
            if 'Issues Found:' in line or 'Critical Issues:' in line:
                current_section = 'issues'
            elif 'Suggestions:' in line:
                current_section = 'suggestions'
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                if current_section == 'issues':
                    issues.append(line.strip()[2:])
                elif current_section == 'suggestions':
                    suggestions.append(line.strip()[2:])

        return issues, suggestions


class GeminiInterface:
    """Interface for Gemini CLI integration"""

    def __init__(self):
        self.available = self._check_availability()
        self.daily_limit = 100  # Free tier limit
        self.usage_count = self._load_usage_count()

    def _check_availability(self) -> bool:
        """Check if Gemini CLI is available"""
        try:
            result = subprocess.run(
                ["gemini", "--version"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False

    def _load_usage_count(self) -> int:
        """Load today's usage count"""
        usage_file = Path.home() / ".gemini_usage.json"
        if usage_file.exists():
            try:
                with open(usage_file, 'r') as f:
                    data = json.load(f)
                    if data['date'] == datetime.now().strftime('%Y-%m-%d'):
                        return data['count']
            except:
                pass
        return 0

    def _save_usage_count(self):
        """Save usage count"""
        usage_file = Path.home() / ".gemini_usage.json"
        with open(usage_file, 'w') as f:
            json.dump({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'count': self.usage_count
            }, f)

    def execute(self, task: str, role: AIRole, context: AIContext) -> AIResponse:
        """Execute Gemini with specific role"""
        if not self.available:
            return AIResponse(
                ai_name="gemini",
                role=role,
                output="Gemini CLI not available",
                confidence=0.0,
                issues_found=[],
                suggestions=[],
                execution_time=0.0,
                metadata={"error": "Gemini not configured"}
            )

        if self.usage_count >= self.daily_limit:
            return AIResponse(
                ai_name="gemini",
                role=role,
                output="Daily limit reached",
                confidence=0.0,
                issues_found=[],
                suggestions=[],
                execution_time=0.0,
                metadata={"error": "Daily limit exceeded"}
            )

        start_time = time.time()
        prompt = self._create_role_prompt(task, role, context)

        try:
            # Execute Gemini CLI
            result = subprocess.run(
                ["gemini", prompt],
                capture_output=True,
                text=True,
                timeout=30
            )

            self.usage_count += 1
            self._save_usage_count()

            output = result.stdout
            creativity_score = self._assess_creativity(output)

            return AIResponse(
                ai_name="gemini",
                role=role,
                output=output,
                confidence=0.75,  # Gemini is good for creativity
                issues_found=[],
                suggestions=self._extract_creative_suggestions(output),
                execution_time=time.time() - start_time,
                metadata={"creativity_score": creativity_score}
            )

        except Exception as e:
            return AIResponse(
                ai_name="gemini",
                role=role,
                output=f"Error: {str(e)}",
                confidence=0.0,
                issues_found=[],
                suggestions=[],
                execution_time=time.time() - start_time,
                metadata={"error": str(e)}
            )

    def _create_role_prompt(self, task: str, role: AIRole, context: AIContext) -> str:
        """Create role-specific prompt for Gemini"""
        base = f"Task: {task}\n"

        if role == AIRole.GEMINI_CREATE:
            return base + """
Generate 5 creative solutions with different approaches.
Think outside conventional patterns.
Consider unusual combinations and novel techniques.
"""

        elif role == AIRole.GEMINI_EXPLORE:
            return base + """
Explore all possible angles and perspectives.
Question assumptions and constraints.
Identify hidden opportunities and risks.
"""

        elif role == AIRole.GEMINI_OPTIMIZE:
            return base + """
Find optimization opportunities:
- Performance improvements
- Resource efficiency
- User experience enhancements
- Cost reductions
"""

        return base

    def _assess_creativity(self, output: str) -> float:
        """Assess creativity level of Gemini's output"""
        creative_indicators = [
            "innovative", "novel", "unique", "creative",
            "unconventional", "breakthrough", "paradigm"
        ]

        score = sum(1 for indicator in creative_indicators
                   if indicator in output.lower())
        return min(score / len(creative_indicators), 1.0)

    def _extract_creative_suggestions(self, output: str) -> List[str]:
        """Extract creative suggestions from Gemini output"""
        suggestions = []
        lines = output.split('\n')

        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in
                   ["could", "consider", "what if", "imagine", "perhaps"]):
                suggestions.append(line.strip())

        return suggestions[:5]  # Top 5 suggestions


class ThreeAICollaborationBridge:
    """Main orchestrator for 3-AI collaboration"""

    def __init__(self):
        self.codex = CodexInterface()
        self.gemini = GeminiInterface()
        self.context_store = Path.home() / ".ai_collaboration_context"
        self.context_store.mkdir(exist_ok=True)

        # Collaboration patterns
        self.patterns = {
            "ideation": {
                "sequence": [
                    (AIRole.GEMINI_EXPLORE, "gemini"),
                    (AIRole.CLAUDE_ARCHITECT, "claude"),
                    (AIRole.CODEX_VERIFY, "codex")
                ],
                "mode": ExecutionMode.SEQUENTIAL
            },
            "implementation": {
                "sequence": [
                    (AIRole.CLAUDE_IMPLEMENT, "claude"),
                    (AIRole.CODEX_REVIEW, "codex"),
                    (AIRole.CLAUDE_IMPLEMENT, "claude")  # Fix issues
                ],
                "mode": ExecutionMode.ITERATIVE
            },
            "optimization": {
                "sequence": [
                    (AIRole.CODEX_REVIEW, "codex"),
                    (AIRole.GEMINI_OPTIMIZE, "gemini"),
                    (AIRole.CLAUDE_IMPLEMENT, "claude")
                ],
                "mode": ExecutionMode.SEQUENTIAL
            },
            "debugging": {
                "sequence": [
                    (AIRole.CODEX_DEBUG, "codex"),
                    (AIRole.CLAUDE_IMPLEMENT, "claude"),
                    (AIRole.CODEX_VERIFY, "codex")
                ],
                "mode": ExecutionMode.ITERATIVE
            }
        }

    def collaborate(self,
                   task: str,
                   pattern: str = "implementation",
                   max_iterations: int = 3) -> Dict[str, Any]:
        """Execute 3-AI collaboration"""

        # Initialize context
        context = AIContext(
            task_id=f"task_{int(time.time())}",
            phase=pattern,
            previous_outputs={},
            constraints=self._extract_constraints(task),
            success_criteria=self._extract_criteria(task),
            metadata={"pattern": pattern, "iterations": 0}
        )

        # Save initial context
        self._save_context(context)

        # Get collaboration pattern
        collab_pattern = self.patterns.get(pattern, self.patterns["implementation"])
        mode = collab_pattern["mode"]
        sequence = collab_pattern["sequence"]

        # Execute based on mode
        if mode == ExecutionMode.SEQUENTIAL:
            return self._execute_sequential(task, sequence, context)
        elif mode == ExecutionMode.ITERATIVE:
            return self._execute_iterative(task, sequence, context, max_iterations)
        elif mode == ExecutionMode.PARALLEL:
            return self._execute_parallel(task, sequence, context)
        else:
            return self._execute_adaptive(task, sequence, context)

    def _execute_sequential(self,
                          task: str,
                          sequence: List[Tuple[AIRole, str]],
                          context: AIContext) -> Dict[str, Any]:
        """Execute AIs in sequence"""
        results = []

        for role, ai_name in sequence:
            print(f"\n🤖 Executing {ai_name} in role: {role.value}")

            if ai_name == "claude":
                # Current context (simulated)
                response = self._execute_claude(task, role, context)
            elif ai_name == "codex":
                response = self.codex.execute(task, role, context)
            elif ai_name == "gemini":
                response = self.gemini.execute(task, role, context)
            else:
                continue

            results.append(response)

            # Update context with output
            context.previous_outputs[ai_name] = {
                "role": role.value,
                "output": response.output,
                "issues": response.issues_found,
                "suggestions": response.suggestions
            }

            # Save updated context
            self._save_context(context)

            # Check for critical issues
            if response.issues_found and "critical" in str(response.issues_found).lower():
                print(f"⚠️ Critical issues found by {ai_name}, stopping sequence")
                break

        return self._compile_results(results, context)

    def _execute_iterative(self,
                         task: str,
                         sequence: List[Tuple[AIRole, str]],
                         context: AIContext,
                         max_iterations: int) -> Dict[str, Any]:
        """Execute AIs iteratively until convergence"""
        results = []
        iteration = 0
        converged = False

        while iteration < max_iterations and not converged:
            iteration += 1
            print(f"\n🔄 Iteration {iteration}/{max_iterations}")

            iteration_results = []
            issues_count = 0

            for role, ai_name in sequence:
                if ai_name == "claude":
                    response = self._execute_claude(task, role, context)
                elif ai_name == "codex":
                    response = self.codex.execute(task, role, context)
                elif ai_name == "gemini":
                    response = self.gemini.execute(task, role, context)
                else:
                    continue

                iteration_results.append(response)
                issues_count += len(response.issues_found)

                # Update context
                context.previous_outputs[f"{ai_name}_iter{iteration}"] = {
                    "output": response.output,
                    "issues": response.issues_found
                }

            results.extend(iteration_results)
            context.metadata["iterations"] = iteration

            # Check convergence (no issues found)
            if issues_count == 0:
                converged = True
                print("✅ Converged - no issues found")

        return self._compile_results(results, context)

    def _execute_parallel(self,
                        task: str,
                        sequence: List[Tuple[AIRole, str]],
                        context: AIContext) -> Dict[str, Any]:
        """Execute AIs in parallel (simulated)"""
        # In production, use threading or async
        print("🚀 Executing AIs in parallel")

        results = []
        for role, ai_name in sequence:
            if ai_name == "claude":
                response = self._execute_claude(task, role, context)
            elif ai_name == "codex":
                response = self.codex.execute(task, role, context)
            elif ai_name == "gemini":
                response = self.gemini.execute(task, role, context)
            else:
                continue

            results.append(response)

        return self._compile_results(results, context)

    def _execute_adaptive(self,
                        task: str,
                        sequence: List[Tuple[AIRole, str]],
                        context: AIContext) -> Dict[str, Any]:
        """Adaptively choose execution based on results"""
        results = []

        # Start with first AI
        first_role, first_ai = sequence[0]

        if first_ai == "claude":
            response = self._execute_claude(task, first_role, context)
        elif first_ai == "codex":
            response = self.codex.execute(task, first_role, context)
        else:
            response = self.gemini.execute(task, first_role, context)

        results.append(response)

        # Adapt based on confidence
        if response.confidence < 0.7:
            print(f"⚠️ Low confidence ({response.confidence:.0%}), engaging additional AI")
            # Engage the most appropriate AI based on issues
            if response.issues_found:
                # Use Codex for debugging
                debug_response = self.codex.execute(task, AIRole.CODEX_DEBUG, context)
                results.append(debug_response)
            else:
                # Use Gemini for creative solutions
                creative_response = self.gemini.execute(task, AIRole.GEMINI_CREATE, context)
                results.append(creative_response)

        return self._compile_results(results, context)

    def _execute_claude(self, task: str, role: AIRole, context: AIContext) -> AIResponse:
        """Execute Claude (current context)"""
        # This is executed in the current Claude context
        # In production, this would interface with Claude API

        output = f"""
[Claude executing in role: {role.value}]
Task: {task}

Based on context analysis:
1. Implementing solution with best practices
2. Following established patterns
3. Ensuring code quality and documentation

Output: [Implementation would go here]
"""

        return AIResponse(
            ai_name="claude",
            role=role,
            output=output,
            confidence=0.9,
            issues_found=[],
            suggestions=["Consider adding error handling", "Add unit tests"],
            execution_time=1.5,
            metadata={"context": "current"}
        )

    def _extract_constraints(self, task: str) -> List[str]:
        """Extract constraints from task description"""
        constraints = []

        # Performance constraints
        if "fast" in task.lower() or "performance" in task.lower():
            constraints.append("High performance required")

        # Security constraints
        if "secure" in task.lower() or "auth" in task.lower():
            constraints.append("Security critical")

        # Quality constraints
        if "production" in task.lower() or "enterprise" in task.lower():
            constraints.append("Production quality required")

        return constraints if constraints else ["Standard quality"]

    def _extract_criteria(self, task: str) -> List[str]:
        """Extract success criteria from task"""
        criteria = []

        # Functionality criteria
        criteria.append("All features implemented")
        criteria.append("No critical bugs")

        # Quality criteria
        if "test" in task.lower():
            criteria.append("Test coverage > 80%")

        if "document" in task.lower():
            criteria.append("Complete documentation")

        return criteria

    def _save_context(self, context: AIContext):
        """Save context to disk for persistence"""
        context_file = self.context_store / f"{context.task_id}.yaml"
        with open(context_file, 'w') as f:
            f.write(context.to_yaml())

    def _compile_results(self, responses: List[AIResponse], context: AIContext) -> Dict[str, Any]:
        """Compile results from all AIs"""

        # Aggregate issues and suggestions
        all_issues = []
        all_suggestions = []

        for response in responses:
            all_issues.extend(response.issues_found)
            all_suggestions.extend(response.suggestions)

        # Calculate overall confidence
        if responses:
            avg_confidence = sum(r.confidence for r in responses) / len(responses)
        else:
            avg_confidence = 0.0

        # Determine final status
        if all_issues:
            status = "needs_revision"
        elif avg_confidence > 0.8:
            status = "success"
        else:
            status = "partial_success"

        return {
            "task_id": context.task_id,
            "status": status,
            "overall_confidence": avg_confidence,
            "total_execution_time": sum(r.execution_time for r in responses),
            "ai_responses": [asdict(r) for r in responses],
            "aggregated_issues": list(set(all_issues)),
            "aggregated_suggestions": list(set(all_suggestions)),
            "context": asdict(context),
            "collaboration_pattern": context.phase,
            "iterations": context.metadata.get("iterations", 1)
        }


def main():
    """Demo of 3-AI Collaboration"""
    print("="*80)
    print("🤝 3-AI Collaboration Bridge Demo")
    print("="*80)

    bridge = ThreeAICollaborationBridge()

    # Check AI availability
    print("\n📊 AI Availability:")
    print(f"  - Claude: ✅ (current context)")
    print(f"  - Codex: {'✅' if bridge.codex.available else '❌'}")
    print(f"  - Gemini: {'✅' if bridge.gemini.available else '❌'}")

    # Test patterns
    test_tasks = [
        ("Create a user authentication system with JWT", "implementation"),
        ("Design a scalable microservices architecture", "ideation"),
        ("Fix performance issues in the payment module", "debugging"),
        ("Optimize database queries for better response time", "optimization")
    ]

    for task, pattern in test_tasks:
        print(f"\n{'='*60}")
        print(f"📝 Task: {task}")
        print(f"🎯 Pattern: {pattern}")
        print(f"{'='*60}")

        # Execute collaboration
        result = bridge.collaborate(task, pattern)

        # Display results
        print(f"\n📊 Results:")
        print(f"  - Status: {result['status']}")
        print(f"  - Confidence: {result['overall_confidence']:.0%}")
        print(f"  - Time: {result['total_execution_time']:.1f}s")
        print(f"  - Issues Found: {len(result['aggregated_issues'])}")
        print(f"  - Suggestions: {len(result['aggregated_suggestions'])}")

        if result['aggregated_issues']:
            print(f"\n⚠️ Issues to Address:")
            for issue in result['aggregated_issues'][:3]:
                print(f"  - {issue}")

        if result['aggregated_suggestions']:
            print(f"\n💡 Suggestions:")
            for suggestion in result['aggregated_suggestions'][:3]:
                print(f"  - {suggestion}")

        print(f"\n✅ Collaboration Complete!")
        time.sleep(1)  # Brief pause between tests


if __name__ == "__main__":
    main()
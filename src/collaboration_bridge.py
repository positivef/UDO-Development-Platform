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
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import yaml
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


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
    PARALLEL = "parallel"  # All at once
    ITERATIVE = "iterative"  # Loop until convergence
    ADAPTIVE = "adaptive"  # Dynamic based on results


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
    def from_yaml(cls, yaml_str: str) -> "AIContext":
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


class CodexMCPConnector:
    """Codex MCP 서버 연결 관리자"""

    def __init__(self):
        self.connected = False
        self.last_response = None

    def ping(self) -> bool:
        """연결 상태 확인"""
        try:
            # MCP를 통한 ping 테스트
            result = self._execute_mcp_command("ping", {"message": "health_check"})
            self.connected = result is not None
            return self.connected
        except Exception as e:
            logger.error(f"Codex ping failed: {e}")
            self.connected = False
            return False

    def execute(self, prompt: str, context: Dict = None) -> Dict:
        """Codex 실행"""
        try:
            if not self.connected and not self.ping():
                raise ConnectionError("Codex MCP not available")

            # MCP를 통한 Codex 실행
            params = {"prompt": prompt, "context": context or {}, "mode": "development"}

            result = self._execute_mcp_command("codex", params)
            return {"success": True, "content": result.get("output", ""), "metadata": result.get("metadata", {})}
        except Exception as e:
            logger.error(f"Codex execution failed: {e}")
            return {"success": False, "content": "", "error": str(e)}

    def _execute_mcp_command(self, command: str, params: Dict) -> Optional[Dict]:
        """MCP 명령 실행 (시뮬레이션)"""
        # 실제 구현시 MCP API 호출
        # 현재는 시뮬레이션
        if command == "ping":
            return {"status": "ok", "timestamp": datetime.now().isoformat()}
        elif command == "codex":
            # Codex 실행 시뮬레이션
            return {
                "output": f"# Codex Analysis\n{params.get('prompt', '')}",
                "metadata": {"service": "codex-mcp", "timestamp": datetime.now().isoformat()},
            }
        return None


class GeminiAPIConnector:
    """Gemini API 연결 관리자"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.connected = False

    def validate_connection(self) -> bool:
        """연결 유효성 검증"""
        if not self.api_key:
            logger.warning("Gemini API key not found")
            return False

        # 실제 구현시 API 연결 테스트
        self.connected = True  # 시뮬레이션
        return self.connected

    def generate(self, prompt: str, context: Dict = None) -> Dict:
        """Gemini 텍스트 생성"""
        try:
            if not self.connected and not self.validate_connection():
                raise ConnectionError("Gemini API not available")

            # 실제 구현시 Gemini API 호출
            # 현재는 시뮬레이션
            return {
                "success": True,
                "content": f"[Gemini Response]\n{prompt[:100]}...",
                "metadata": {"model": "gemini-pro", "timestamp": datetime.now().isoformat()},
            }
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return {"success": False, "content": "", "error": str(e)}


class ThreeAICollaborationBridge:
    """Main orchestrator for 3-AI collaboration"""

    def __init__(self):
        self.codex = CodexMCPConnector()
        self.gemini = GeminiAPIConnector()
        self.context_store = Path.home() / ".ai_collaboration_context"
        self.context_store.mkdir(exist_ok=True)

        # Collaboration patterns
        self.patterns = {
            "ideation": {
                "sequence": [
                    (AIRole.GEMINI_EXPLORE, "gemini"),
                    (AIRole.CLAUDE_ARCHITECT, "claude"),
                    (AIRole.CODEX_VERIFY, "codex"),
                ],
                "mode": ExecutionMode.SEQUENTIAL,
            },
            "implementation": {
                "sequence": [
                    (AIRole.CLAUDE_IMPLEMENT, "claude"),
                    (AIRole.CODEX_REVIEW, "codex"),
                    (AIRole.CLAUDE_IMPLEMENT, "claude"),  # Fix issues
                ],
                "mode": ExecutionMode.ITERATIVE,
            },
            "optimization": {
                "sequence": [
                    (AIRole.CODEX_REVIEW, "codex"),
                    (AIRole.GEMINI_OPTIMIZE, "gemini"),
                    (AIRole.CLAUDE_IMPLEMENT, "claude"),
                ],
                "mode": ExecutionMode.SEQUENTIAL,
            },
            "debugging": {
                "sequence": [
                    (AIRole.CODEX_DEBUG, "codex"),
                    (AIRole.CLAUDE_IMPLEMENT, "claude"),
                    (AIRole.CODEX_VERIFY, "codex"),
                ],
                "mode": ExecutionMode.ITERATIVE,
            },
        }
        self._initialize_services()

    def _initialize_services(self):
        """서비스 초기화 및 상태 확인"""
        logger.info("Initializing AI services...")
        self.codex.ping()
        self.gemini.validate_connection()
        logger.info(f"Codex MCP: {'[OK] Connected' if self.codex.connected else '[FAIL] Not available'}")
        logger.info(f"Gemini API: {'[OK] Connected' if self.gemini.connected else '[FAIL] Not available'}")
        logger.info(f"Claude: [OK] Available (current context)")

    def collaborate(self, task: str, pattern: str = "implementation", max_iterations: int = 3) -> Dict[str, Any]:
        """Execute 3-AI collaboration"""

        # Initialize context
        context = AIContext(
            task_id=f"task_{int(time.time())}",
            phase=pattern,
            previous_outputs={},
            constraints=self._extract_constraints(task),
            success_criteria=self._extract_criteria(task),
            metadata={"pattern": pattern, "iterations": 0},
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

    def _execute_sequential(self, task: str, sequence: List[Tuple[AIRole, str]], context: AIContext) -> Dict[str, Any]:
        """Execute AIs in sequence"""
        results = []

        for role, ai_name in sequence:
            logger.info(f"Executing {ai_name} in role: {role.value}")

            if ai_name == "claude":
                response = self._execute_claude(task, role, context)
            elif ai_name == "codex":
                response = self._execute_codex(task, role, context)
            elif ai_name == "gemini":
                response = self._execute_gemini(task, role, context)
            else:
                continue

            results.append(response)

            # Update context with output
            context.previous_outputs[ai_name] = {
                "role": role.value,
                "output": response.output,
                "issues": response.issues_found,
                "suggestions": response.suggestions,
            }

            # Save updated context
            self._save_context(context)

            # Check for critical issues
            if response.issues_found and "critical" in str(response.issues_found).lower():
                logger.warning(f"Critical issues found by {ai_name}, stopping sequence")
                break

        return self._compile_results(results, context)

    def _execute_iterative(
        self, task: str, sequence: List[Tuple[AIRole, str]], context: AIContext, max_iterations: int
    ) -> Dict[str, Any]:
        """Execute AIs iteratively until convergence"""
        results = []
        iteration = 0
        converged = False

        while iteration < max_iterations and not converged:
            iteration += 1
            logger.info(f"Iteration {iteration}/{max_iterations}")

            iteration_results = []
            issues_count = 0

            for role, ai_name in sequence:
                if ai_name == "claude":
                    response = self._execute_claude(task, role, context)
                elif ai_name == "codex":
                    response = self._execute_codex(task, role, context)
                elif ai_name == "gemini":
                    response = self._execute_gemini(task, role, context)
                else:
                    continue

                iteration_results.append(response)
                issues_count += len(response.issues_found)

                # Update context
                context.previous_outputs[f"{ai_name}_iter{iteration}"] = {
                    "output": response.output,
                    "issues": response.issues_found,
                }

            results.extend(iteration_results)
            context.metadata["iterations"] = iteration

            # Check convergence (no issues found)
            if issues_count == 0:
                converged = True
                logger.info("Converged - no issues found")

        return self._compile_results(results, context)

    def _execute_parallel(self, task: str, sequence: List[Tuple[AIRole, str]], context: AIContext) -> Dict[str, Any]:
        """Execute AIs in parallel (simulated)"""
        # In production, use threading or async
        logger.info("Executing AIs in parallel")

        results = []
        for role, ai_name in sequence:
            if ai_name == "claude":
                response = self._execute_claude(task, role, context)
            elif ai_name == "codex":
                response = self._execute_codex(task, role, context)
            elif ai_name == "gemini":
                response = self._execute_gemini(task, role, context)
            else:
                continue

            results.append(response)

        return self._compile_results(results, context)

    def _execute_adaptive(self, task: str, sequence: List[Tuple[AIRole, str]], context: AIContext) -> Dict[str, Any]:
        """Adaptively choose execution based on results"""
        results = []

        # Start with first AI
        first_role, first_ai = sequence[0]

        if first_ai == "claude":
            response = self._execute_claude(task, first_role, context)
        elif first_ai == "codex":
            response = self._execute_codex(task, first_role, context)
        else:
            response = self._execute_gemini(task, first_role, context)

        results.append(response)

        # Adapt based on confidence
        if response.confidence < 0.7:
            logger.warning(f"Low confidence ({response.confidence:.0%}), engaging additional AI")
            # Engage the most appropriate AI based on issues
            if response.issues_found:
                # Use Codex for debugging
                debug_response = self._execute_codex(task, AIRole.CODEX_DEBUG, context)
                results.append(debug_response)
            else:
                # Use Gemini for creative solutions
                creative_response = self._execute_gemini(task, AIRole.GEMINI_CREATE, context)
                results.append(creative_response)

        return self._compile_results(results, context)

    def _execute_claude(self, task: str, role: AIRole, context: AIContext) -> AIResponse:
        """Execute Claude (current context)"""
        start_time = time.time()
        output = f"[Claude executing in role: {role.value}]\nTask: {task}\n\nBased on context analysis:\n1. Implementing solution with best practices\n2. Following established patterns\n3. Ensuring code quality and documentation\n\nOutput: [Implementation would go here]"
        return AIResponse(
            ai_name="claude",
            role=role,
            output=output,
            confidence=0.9,
            issues_found=[],
            suggestions=["Consider adding error handling", "Add unit tests"],
            execution_time=time.time() - start_time,
            metadata={"context": "current"},
        )

    def _execute_codex(self, task: str, role: AIRole, context: AIContext) -> AIResponse:
        """Execute Codex using the new connector"""
        start_time = time.time()
        if not self.codex.connected:
            return AIResponse(
                "codex", role, "Codex not available", 0.0, [], [], time.time() - start_time, {"error": "Codex not connected"}
            )

        prompt = self._create_role_prompt(task, role, context)
        result = self.codex.execute(prompt, asdict(context))

        issues, suggestions = self._parse_output(result.get("content", ""))

        return AIResponse(
            ai_name="codex",
            role=role,
            output=result.get("content", ""),
            confidence=0.85 if result.get("success") else 0.0,
            issues_found=issues,
            suggestions=suggestions,
            execution_time=time.time() - start_time,
            metadata=result.get("metadata", {}),
        )

    def _execute_gemini(self, task: str, role: AIRole, context: AIContext) -> AIResponse:
        """Execute Gemini using the new connector"""
        start_time = time.time()
        if not self.gemini.connected:
            return AIResponse(
                "gemini",
                role,
                "Gemini not available",
                0.0,
                [],
                [],
                time.time() - start_time,
                {"error": "Gemini not connected"},
            )

        prompt = self._create_role_prompt(task, role, context)
        result = self.gemini.generate(prompt, asdict(context))

        return AIResponse(
            ai_name="gemini",
            role=role,
            output=result.get("content", ""),
            confidence=0.75 if result.get("success") else 0.0,
            issues_found=[],
            suggestions=self._extract_creative_suggestions(result.get("content", "")),
            execution_time=time.time() - start_time,
            metadata=result.get("metadata", {}),
        )

    def _create_role_prompt(self, task: str, role: AIRole, context: AIContext) -> str:
        """Create role-specific prompt for the AI"""
        # This method can be expanded to be more sophisticated
        return f"Task: {task}\nRole: {role.value}\nContext: {json.dumps(asdict(context), indent=2)}"

    def _parse_output(self, output: str) -> Tuple[List[str], List[str]]:
        """Parse AI output for structured information"""
        issues = []
        suggestions = []
        lines = output.split("\n")
        current_section = None
        for line in lines:
            if "Issues Found:" in line or "Critical Issues:" in line:
                current_section = "issues"
            elif "Suggestions:" in line:
                current_section = "suggestions"
            elif line.strip().startswith("- ") or line.strip().startswith("* "):
                if current_section == "issues":
                    issues.append(line.strip()[2:])
                elif current_section == "suggestions":
                    suggestions.append(line.strip()[2:])
        return issues, suggestions

    def _extract_creative_suggestions(self, output: str) -> List[str]:
        """Extract creative suggestions from Gemini output"""
        suggestions = []
        lines = output.split("\n")
        for line in lines:
            if any(keyword in line.lower() for keyword in ["could", "consider", "what if", "imagine", "perhaps"]):
                suggestions.append(line.strip())
        return suggestions[:5]

    def _extract_constraints(self, task: str) -> List[str]:
        """Extract constraints from task description"""
        constraints = []
        if "fast" in task.lower() or "performance" in task.lower():
            constraints.append("High performance required")
        if "secure" in task.lower() or "auth" in task.lower():
            constraints.append("Security critical")
        if "production" in task.lower() or "enterprise" in task.lower():
            constraints.append("Production quality required")
        return constraints if constraints else ["Standard quality"]

    def _extract_criteria(self, task: str) -> List[str]:
        """Extract success criteria from task"""
        criteria = ["All features implemented", "No critical bugs"]
        if "test" in task.lower():
            criteria.append("Test coverage > 80%")
        if "document" in task.lower():
            criteria.append("Complete documentation")
        return criteria

    def _save_context(self, context: AIContext):
        """Save context to disk for persistence"""
        context_file = self.context_store / f"{context.task_id}.yaml"
        with open(context_file, "w") as f:
            f.write(context.to_yaml())

    def _compile_results(self, responses: List[AIResponse], context: AIContext) -> Dict[str, Any]:
        """Compile results from all AIs"""
        all_issues = []
        all_suggestions = []
        for response in responses:
            all_issues.extend(response.issues_found)
            all_suggestions.extend(response.suggestions)

        avg_confidence = sum(r.confidence for r in responses) / len(responses) if responses else 0.0
        status = "needs_revision" if all_issues else "success" if avg_confidence > 0.8 else "partial_success"

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
            "iterations": context.metadata.get("iterations", 1),
        }


def main():
    """Demo of 3-AI Collaboration"""
    print("=" * 80)
    print("[*] 3-AI Collaboration Bridge Demo")
    print("=" * 80)

    bridge = ThreeAICollaborationBridge()

    # Check AI availability
    print("\n[*] AI Availability:")
    print(f"  - Claude: [OK] (current context)")
    print(f"  - Codex: {'[OK]' if bridge.codex.connected else '[FAIL]'}")
    print(f"  - Gemini: {'[OK]' if bridge.gemini.connected else '[FAIL]'}")

    # Test patterns
    test_tasks = [
        ("Create a user authentication system with JWT", "implementation"),
        ("Design a scalable microservices architecture", "ideation"),
        ("Fix performance issues in the payment module", "debugging"),
        ("Optimize database queries for better response time", "optimization"),
    ]

    for task, pattern in test_tasks:
        print(f"\n{'='*60}")
        print(f"[*] Task: {task}")
        print(f"[*] Pattern: {pattern}")
        print(f"{'='*60}")

        # Execute collaboration
        result = bridge.collaborate(task, pattern)

        # Display results
        print(f"\n[*] Results:")
        print(f"  - Status: {result['status']}")
        print(f"  - Confidence: {result['overall_confidence']:.0%}")
        print(f"  - Time: {result['total_execution_time']:.1f}s")
        print(f"  - Issues Found: {len(result['aggregated_issues'])}")
        print(f"  - Suggestions: {len(result['aggregated_suggestions'])}")

        if result["aggregated_issues"]:
            print(f"\n[WARN] Issues to Address:")
            for issue in result["aggregated_issues"][:3]:
                print(f"  - {issue}")

        if result["aggregated_suggestions"]:
            print(f"\n[*] Suggestions:")
            for suggestion in result["aggregated_suggestions"][:3]:
                print(f"  - {suggestion}")

        print(f"\n[OK] Collaboration Complete!")
        time.sleep(1)  # Brief pause between tests


if __name__ == "__main__":
    main()

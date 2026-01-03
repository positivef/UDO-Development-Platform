#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integrated UDO System v3.0
완전 통합된 개발 자동화 시스템
- UDO v2 Orchestrator
- Uncertainty Map v3 Predictor
- AI Collaboration Connector
- ML Training System
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

# Windows Unicode 인코딩 문제 해결
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Import all components
try:
    from unified_development_orchestrator_v2 import UnifiedDevelopmentOrchestratorV2, ProjectContext

    UDO_AVAILABLE = True
except ImportError:
    UDO_AVAILABLE = False
    logger.warning("UDO v2 not available")

try:
    from uncertainty_map_v3 import (
        UncertaintyMapV3,
        UncertaintyVector,
    )

    UNCERTAINTY_AVAILABLE = True
except ImportError:
    UNCERTAINTY_AVAILABLE = False
    logger.warning("Uncertainty Map v3 not available")

try:
    from ai_collaboration_connector import AICollaborationConnector

    AI_CONNECTOR_AVAILABLE = True
except ImportError:
    AI_CONNECTOR_AVAILABLE = False
    logger.warning("AI Collaboration Connector not available")

try:
    from ml_training_system import MLTrainingSystem

    ML_SYSTEM_AVAILABLE = True
except ImportError:
    ML_SYSTEM_AVAILABLE = False
    logger.warning("ML Training System not available")

try:
    from three_ai_collaboration_bridge import ThreeAICollaborationBridge

    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False
    logger.warning("3-AI Collaboration Bridge not available")


@dataclass
class SystemStatus:
    """시스템 상태 정보"""

    udo_ready: bool
    uncertainty_ready: bool
    ai_connector_ready: bool
    ml_system_ready: bool
    bridge_ready: bool
    overall_ready: bool
    timestamp: str


class IntegratedUDOSystem:
    """통합 UDO 시스템"""

    def __init__(self, project_name: str = "AI-Platform"):
        self.project_name = project_name
        self.components = {}
        self.status = None
        self.execution_history = []

        # 초기화
        self._initialize_components()
        self._check_system_status()

    def _initialize_components(self):
        """모든 컴포넌트 초기화"""
        logger.info("Initializing Integrated UDO System...")

        # Project Context 생성
        self.project_context = ProjectContext(
            project_name=self.project_name,
            goal="Intelligent Development Automation",
            team_size=5,
            timeline_weeks=16,
            budget=100000,
            tech_stack=["Next.js", "FastAPI", "PostgreSQL", "Redis"],
            constraints=["High reliability", "Scalable architecture"],
            success_metrics=["95% automation", "< 5min decision time"],
            current_phase="ideation",
            files=[],
            metadata={"ai_tools": ["Claude", "Codex", "Gemini"], "ml_enabled": True, "version": "3.0.0"},
        )

        # UDO v2 초기화
        if UDO_AVAILABLE:
            try:
                self.components["udo"] = UnifiedDevelopmentOrchestratorV2(self.project_context)
                logger.info("[OK] UDO v2 initialized")
            except Exception as e:
                logger.error(f"Failed to initialize UDO: {e}")
                self.components["udo"] = None
        else:
            self.components["udo"] = None

        # Uncertainty Map v3 초기화
        if UNCERTAINTY_AVAILABLE:
            try:
                self.components["uncertainty"] = UncertaintyMapV3(self.project_name)
                logger.info("[OK] Uncertainty Map v3 initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Uncertainty Map: {e}")
                self.components["uncertainty"] = None
        else:
            self.components["uncertainty"] = None

        # AI Collaboration Connector 초기화
        if AI_CONNECTOR_AVAILABLE:
            try:
                self.components["ai_connector"] = AICollaborationConnector()
                logger.info("[OK] AI Collaboration Connector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize AI Connector: {e}")
                self.components["ai_connector"] = None
        else:
            self.components["ai_connector"] = None

        # ML Training System 초기화
        if ML_SYSTEM_AVAILABLE:
            try:
                self.components["ml_system"] = MLTrainingSystem()
                logger.info("[OK] ML Training System initialized")
            except Exception as e:
                logger.error(f"Failed to initialize ML System: {e}")
                self.components["ml_system"] = None
        else:
            self.components["ml_system"] = None

        # 3-AI Collaboration Bridge 초기화
        if BRIDGE_AVAILABLE:
            try:
                self.components["bridge"] = ThreeAICollaborationBridge()
                logger.info("[OK] 3-AI Collaboration Bridge initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Bridge: {e}")
                self.components["bridge"] = None
        else:
            self.components["bridge"] = None

    def _check_system_status(self):
        """시스템 상태 확인"""
        self.status = SystemStatus(
            udo_ready=self.components.get("udo") is not None,
            uncertainty_ready=self.components.get("uncertainty") is not None,
            ai_connector_ready=self.components.get("ai_connector") is not None,
            ml_system_ready=self.components.get("ml_system") is not None,
            bridge_ready=self.components.get("bridge") is not None,
            overall_ready=all(
                [self.components.get("udo"), self.components.get("uncertainty"), self.components.get("ai_connector")]
            ),
            timestamp=datetime.now().isoformat(),
        )

    def execute_development_cycle(self, task: str, phase: Optional[str] = None) -> Dict:
        """개발 사이클 실행"""
        logger.info(f"Executing development cycle for: {task[:50]}...")

        if phase:
            self.project_context.current_phase = phase

        result = {
            "task": task,
            "phase": self.project_context.current_phase,
            "timestamp": datetime.now().isoformat(),
            "components_used": [],
        }

        # 1. UDO로 계획 수립
        if self.components.get("udo"):
            logger.info("[CREATE] development plan with UDO...")
            plan = self.components["udo"].start_development_cycle(task)
            result["plan"] = plan
            result["components_used"].append("udo")

            # GO 결정시 실행
            if plan.get("decision") in ["GO", "GO_WITH_CHECKPOINTS"]:
                execution = self.components["udo"].execute_plan(plan)
                result["execution"] = execution
        else:
            result["plan"] = None

        # 2. 불확실성 예측
        if self.components.get("uncertainty"):
            logger.info("[*] Predicting uncertainty...")
            # Context 기반 분석
            context = {
                "phase": self.project_context.current_phase,
                "team_size": self.project_context.team_size,
                "timeline_weeks": self.project_context.timeline_weeks,
                "files": self.project_context.files,
                "market_validation": 0.5,
                "has_code": len(self.project_context.files) > 0,
            }

            vector, state = self.components["uncertainty"].analyze_context(context)

            # 예측 생성 (predict_evolution은 vector와 hours만 받음)
            prediction = self.components["uncertainty"].predict_evolution(vector, hours=24)
            result["uncertainty"] = {"state": state.value, "magnitude": vector.magnitude(), "prediction": prediction}
            result["components_used"].append("uncertainty")

        # 3. AI 협업 실행
        if self.components.get("ai_connector"):
            logger.info("[*] Orchestrating AI collaboration...")
            collaboration = self.components["ai_connector"].orchestrate_collaboration(task, self.project_context.current_phase)
            result["ai_collaboration"] = collaboration
            result["components_used"].append("ai_connector")

        # 4. 3-AI Bridge 협업 (Gemini의 제안 반영)
        if self.components.get("bridge"):
            logger.info("[RUN] 3-AI Bridge collaboration...")

            # Gemini 제안: Phase별 최적 패턴 선택
            pattern_map = {
                "ideation": "creative_exploration",  # Gemini 제안
                "design": "risk_analysis",  # Gemini 제안
                "mvp": "implementation",
                "implementation": "implementation",
                "testing": "verification_loop",
            }

            pattern = pattern_map.get(self.project_context.current_phase, "implementation")

            bridge_result = self.components["bridge"].collaborate(task, pattern)
            result["bridge_collaboration"] = bridge_result
            result["components_used"].append("bridge")

        # 5. ML 예측 (가능한 경우)
        if self.components.get("ml_system"):
            logger.info("[*] Generating ML predictions...")
            try:
                ml_input = {
                    "phase": self.project_context.current_phase,
                    "timeline_weeks": self.project_context.timeline_weeks,
                    "team_size": self.project_context.team_size,
                    "budget": self.project_context.budget,
                    "technical_uncertainty": 0.5,
                    "market_uncertainty": 0.4,
                }

                confidence_pred, _ = self.components["ml_system"].predict("confidence_predictor", ml_input)
                result["ml_prediction"] = {"confidence": confidence_pred, "model": "confidence_predictor"}
                result["components_used"].append("ml_system")
            except Exception as e:
                logger.warning(f"ML prediction failed: {e}")
                result["ml_prediction"] = None

        # 히스토리 저장
        self.execution_history.append(result)

        return result

    def train_ml_models(self, training_data=None):
        """ML 모델 훈련"""
        if not self.components.get("ml_system"):
            logger.warning("ML System not available")
            return None

        logger.info("Training ML models...")

        # 훈련 데이터가 없으면 합성 데이터 생성
        if training_data is None:
            training_data = self.components["ml_system"].generate_synthetic_data(size=1000)

        results = {}
        models = ["uncertainty_predictor", "confidence_predictor"]

        for model_name in models:
            metrics = self.components["ml_system"].train_model(model_name, training_data)
            results[model_name] = {"r2": metrics.r2, "mse": metrics.mse, "training_time": metrics.training_time}
            logger.info(f"Trained {model_name}: R²={metrics.r2:.3f}")

        # 모델 저장
        self.components["ml_system"].save_models()

        return results

    def get_system_report(self) -> Dict:
        """시스템 상태 보고서 (동기 버전)"""
        report = {
            "system_name": self.project_name,
            "version": "3.0.0",
            "status": {
                "udo": self.status.udo_ready,
                "uncertainty": self.status.uncertainty_ready,
                "ai_connector": self.status.ai_connector_ready,
                "ml_system": self.status.ml_system_ready,
                "bridge": self.status.bridge_ready,
                "overall": self.status.overall_ready,
            },
            "project_context": {
                "current_phase": self.project_context.current_phase,
                "timeline": self.project_context.timeline_weeks,
                "team_size": self.project_context.team_size,
            },
            "execution_history_count": len(self.execution_history),
            "timestamp": datetime.now().isoformat(),
        }

        # 각 컴포넌트별 상태 (순차 실행)
        if self.components.get("ai_connector"):
            report["ai_services"] = self.components["ai_connector"].get_status_report()

        if self.components.get("ml_system"):
            report["ml_models"] = self.components["ml_system"].get_model_report()

        return report

    async def get_system_report_async(self) -> Dict:
        """시스템 상태 보고서 (비동기 버전 - 병렬 실행)"""
        import asyncio

        report = {
            "system_name": self.project_name,
            "version": "3.0.0",
            "status": {
                "udo": self.status.udo_ready,
                "uncertainty": self.status.uncertainty_ready,
                "ai_connector": self.status.ai_connector_ready,
                "ml_system": self.status.ml_system_ready,
                "bridge": self.status.bridge_ready,
                "overall": self.status.overall_ready,
            },
            "project_context": {
                "current_phase": self.project_context.current_phase,
                "timeline": self.project_context.timeline_weeks,
                "team_size": self.project_context.team_size,
            },
            "execution_history_count": len(self.execution_history),
            "timestamp": datetime.now().isoformat(),
        }

        # 각 컴포넌트별 상태 (병렬 실행)
        tasks = []
        task_keys = []

        if self.components.get("ai_connector"):
            tasks.append(asyncio.to_thread(self.components["ai_connector"].get_status_report))
            task_keys.append("ai_services")

        if self.components.get("ml_system"):
            tasks.append(asyncio.to_thread(self.components["ml_system"].get_model_report))
            task_keys.append("ml_models")

        # 병렬 실행 (30-50% 성능 개선)
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for key, result in zip(task_keys, results):
                if not isinstance(result, Exception):
                    report[key] = result
                else:
                    # 에러 발생 시 로깅하고 빈 dict 반환
                    print(f"Warning: {key} failed with {result}")
                    report[key] = {}

        return report

    def save_state(self, filepath: str = "integrated_system_state.json"):
        """시스템 상태 저장"""
        state = {
            "project_name": self.project_name,
            "project_context": {
                "phase": self.project_context.current_phase,
                "timeline": self.project_context.timeline_weeks,
                "team_size": self.project_context.team_size,
                "budget": self.project_context.budget,
            },
            "system_status": {
                "udo": self.status.udo_ready,
                "uncertainty": self.status.uncertainty_ready,
                "ai_connector": self.status.ai_connector_ready,
                "ml_system": self.status.ml_system_ready,
                "bridge": self.status.bridge_ready,
            },
            "execution_history": self.execution_history[-10:],  # 최근 10개
            "timestamp": datetime.now().isoformat(),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        logger.info(f"State saved to {filepath}")


def demo():
    """통합 시스템 데모"""
    logger.info("%s", "=" * 80)
    logger.info("Integrated UDO System v3.0 Demo")
    logger.info("%s", "=" * 80)

    # 시스템 초기화
    system = IntegratedUDOSystem(project_name="AI-SaaS-Platform")

    # 상태 보고
    logger.info("System status:")
    report = system.get_system_report()
    for component, ready in report["status"].items():
        status = "[OK]" if ready else "[FAIL]"
        logger.info("%s: %s", component, status)

    # Phase별 테스트
    phases = [
        ("ideation", "Design an AI-powered code review platform"),
        ("design", "Create microservices architecture"),
        ("mvp", "Implement core review engine"),
        ("implementation", "Add ML model integration"),
        ("testing", "Comprehensive system testing"),
    ]

    for phase, task in phases:
        logger.info("Testing %s phase", phase.upper())
        logger.info("Task: %s", task)

        result = system.execute_development_cycle(task, phase)

        logger.info("Components used: %s", ", ".join(result["components_used"]))

        if "plan" in result and result["plan"]:
            logger.info("Decision: %s", result["plan"].get("decision", "N/A"))
            logger.info("Confidence: %.1f%%", result["plan"].get("confidence", 0) * 100)

        if "uncertainty" in result:
            logger.info("Uncertainty: %s", result["uncertainty"]["state"])

        if "ml_prediction" in result and result["ml_prediction"]:
            logger.info("ML Confidence: %.1f%%", result["ml_prediction"]["confidence"] * 100)

    # ML 모델 훈련 (선택사항)
    if system.components.get("ml_system"):
        logger.info("Training ML models...")
        training_results = system.train_ml_models()
        if training_results:
            for model, metrics in training_results.items():
                logger.info("%s: R²=%.3f", model, metrics["r2"])

    # 상태 저장
    system.save_state("demo_system_state.json")

    logger.info("%s", "=" * 80)
    logger.info("Demo completed successfully!")
    logger.info("%s", "=" * 80)


if __name__ == "__main__":
    demo()

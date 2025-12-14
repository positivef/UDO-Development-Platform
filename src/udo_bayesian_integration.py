"""
UDO v2 + Bayesian Learning 통합 모듈
===================================

UDO v2 Orchestrator에 Adaptive Bayesian Learning을 통합하여
실시간 학습 및 적응형 의사결정을 가능하게 합니다.

핵심 기능:
1. Phase별 Bayesian Confidence 적용
2. 의사결정 Threshold 동적 조정
3. 프로젝트 결과 학습
4. 편향 자동 보정
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from adaptive_bayesian_uncertainty import AdaptiveBayesianUncertainty
from uncertainty_map_v3 import UncertaintyVector

logger = logging.getLogger(__name__)


class UDOBayesianIntegration:
    """
    UDO v2 Orchestrator와 Bayesian Learning System 통합

    이 클래스는 UDO v2의 의사결정 로직에 학습된 Bayesian confidence를
    반영하고, 프로젝트 결과로부터 자동으로 학습합니다.
    """

    def __init__(self, project_name: str, storage_dir: Optional[Path] = None):
        """
        Initialize Bayesian integration

        Args:
            project_name: 프로젝트 이름
            storage_dir: 학습 데이터 저장 디렉토리
        """
        self.project_name = project_name
        self.bayesian = AdaptiveBayesianUncertainty(
            project_name=project_name,
            storage_dir=storage_dir or Path.home() / '.udo' / 'bayesian'
        )

        # Phase별 기본 threshold (UDO v2에서 가져옴)
        self.BASE_THRESHOLDS = {
            "ideation": 0.60,
            "design": 0.65,
            "mvp": 0.65,
            "implementation": 0.70,
            "testing": 0.70
        }

        # 통합 메트릭
        self.integration_metrics = {
            "decisions_influenced": 0,
            "threshold_adjustments": 0,
            "bias_corrections": 0,
            "learning_events": 0
        }

        logger.info(f"🧠 UDO-Bayesian Integration initialized for {project_name}")

    def get_adaptive_threshold(self, phase: str, base_confidence: float) -> Tuple[float, Dict[str, Any]]:
        """
        Phase별 적응형 threshold 계산

        Bayesian 학습 결과를 반영하여 동적으로 threshold를 조정합니다.

        Args:
            phase: 개발 단계 (ideation, design, mvp, implementation, testing)
            base_confidence: UDO v2에서 계산한 기본 confidence

        Returns:
            (adjusted_threshold, metadata) tuple
            - adjusted_threshold: Bayesian 보정이 적용된 threshold
            - metadata: 조정 내역 및 설명
        """
        base_threshold = self.BASE_THRESHOLDS.get(phase, 0.65)

        # Bayesian 시스템에서 Phase별 성과 가져오기
        phase_performance = self.bayesian.get_performance_report()

        # 편향 보정 팩터 계산
        bias_profile = phase_performance.get('bias_profile', {})
        bias_type = bias_profile.get('type', 'unbiased')

        # 편향에 따른 threshold 조정
        bias_adjustment = 0.0
        if bias_type == 'optimistic':
            # 과도하게 낙관적 → threshold 상향
            bias_adjustment = +0.05
        elif bias_type == 'highly_optimistic':
            bias_adjustment = +0.10
        elif bias_type == 'pessimistic':
            # 과도하게 비관적 → threshold 하향
            bias_adjustment = -0.05
        elif bias_type == 'highly_pessimistic':
            bias_adjustment = -0.10

        # 학습된 confidence를 반영
        # base_confidence가 높고 과거 성공률이 높으면 threshold 완화
        confidence_factor = (base_confidence - 0.5) * 0.1  # -0.05 ~ +0.05 범위

        # 최종 조정된 threshold
        adjusted_threshold = base_threshold + bias_adjustment + confidence_factor

        # 안전 범위 내로 제한 (0.4 ~ 0.9)
        adjusted_threshold = max(0.4, min(0.9, adjusted_threshold))

        # 조정이 발생했는지 추적
        if abs(adjusted_threshold - base_threshold) > 0.01:
            self.integration_metrics["threshold_adjustments"] += 1

        if abs(bias_adjustment) > 0.01:
            self.integration_metrics["bias_corrections"] += 1

        metadata = {
            "base_threshold": base_threshold,
            "adjusted_threshold": adjusted_threshold,
            "bias_type": bias_type,
            "bias_adjustment": bias_adjustment,
            "confidence_factor": confidence_factor,
            "reason": self._explain_adjustment(bias_type, bias_adjustment, confidence_factor)
        }

        logger.info(f"📊 Phase '{phase}' threshold: {base_threshold:.2f} → {adjusted_threshold:.2f} "
                   f"(bias: {bias_type}, adj: {bias_adjustment:+.2f})")

        return adjusted_threshold, metadata

    def enhance_go_decision(self,
                           phase: str,
                           base_confidence: float,
                           uncertainties: Dict[str, float]) -> Dict[str, Any]:
        """
        UDO v2의 GO/NO_GO 의사결정을 Bayesian 학습으로 강화

        Args:
            phase: 개발 단계
            base_confidence: UDO v2에서 계산한 기본 confidence
            uncertainties: 불확실성 벡터

        Returns:
            향상된 의사결정 정보
        """
        # 적응형 threshold 계산
        adjusted_threshold, threshold_meta = self.get_adaptive_threshold(phase, base_confidence)

        # UncertaintyVector 생성
        uncertainty_vector = UncertaintyVector(
            technical=uncertainties.get('technical', 0.5),
            market=uncertainties.get('market', 0.5),
            resource=uncertainties.get('resource', 0.5),
            timeline=uncertainties.get('timeline', 0.5),
            quality=uncertainties.get('quality', 0.5)
        )

        # Bayesian 예측 수행
        bayesian_prediction = self.bayesian.predict_uncertainty(
            current_vector=uncertainty_vector,
            phase=phase,
            horizon_hours=168  # 1주일 예측
        )

        # 최종 의사결정 confidence 계산
        # UDO v2 confidence + Bayesian confidence의 가중 평균
        bayesian_confidence = bayesian_prediction.get('confidence', 0.5)

        # 70% UDO, 30% Bayesian
        final_confidence = 0.7 * base_confidence + 0.3 * bayesian_confidence

        # 의사결정
        if final_confidence >= adjusted_threshold:
            decision = "GO"
            confidence_gap = final_confidence - adjusted_threshold
        elif final_confidence >= adjusted_threshold * 0.8:
            decision = "GO_WITH_CHECKPOINTS"
            confidence_gap = final_confidence - (adjusted_threshold * 0.8)
        else:
            decision = "NO_GO"
            confidence_gap = final_confidence - adjusted_threshold

        self.integration_metrics["decisions_influenced"] += 1

        result = {
            "decision": decision,
            "final_confidence": final_confidence,
            "confidence_gap": confidence_gap,
            "components": {
                "udo_confidence": base_confidence,
                "bayesian_confidence": bayesian_confidence,
                "weights": {"udo": 0.7, "bayesian": 0.3}
            },
            "threshold": {
                "original": self.BASE_THRESHOLDS.get(phase, 0.65),
                "adjusted": adjusted_threshold,
                "metadata": threshold_meta
            },
            "bayesian_insights": {
                "predicted_uncertainty": bayesian_prediction.get('predicted_magnitude', 0.5),
                "trend": bayesian_prediction.get('overall_trend', 'stable'),
                "quantum_state": bayesian_prediction.get('predicted_state', 'quantum'),
                "recommendations": bayesian_prediction.get('recommendations', [])[:3]  # Top 3
            },
            "explanation": self._explain_decision(decision, final_confidence, adjusted_threshold, threshold_meta)
        }

        logger.info(f"🎯 Decision for '{phase}': {decision} (confidence: {final_confidence:.2%})")

        return result

    def learn_from_project_outcome(self,
                                   phase: str,
                                   predicted_confidence: float,
                                   predicted_uncertainties: Dict[str, float],
                                   actual_success: bool,
                                   actual_uncertainties: Optional[Dict[str, float]] = None):
        """
        프로젝트 결과로부터 학습

        Args:
            phase: 개발 단계
            predicted_confidence: 예측했던 confidence
            predicted_uncertainties: 예측했던 불확실성
            actual_success: 실제 성공 여부
            actual_uncertainties: 실제 관측된 불확실성 (선택)
        """
        # 실제 결과를 UncertaintyVector로 변환
        if actual_uncertainties:
            actual_vector = UncertaintyVector(
                technical=actual_uncertainties.get('technical', 0.5),
                market=actual_uncertainties.get('market', 0.5),
                resource=actual_uncertainties.get('resource', 0.5),
                timeline=actual_uncertainties.get('timeline', 0.5),
                quality=actual_uncertainties.get('quality', 0.5)
            )
        else:
            # 성공/실패 기반으로 추정
            base_value = 0.3 if actual_success else 0.7
            actual_vector = UncertaintyVector(
                technical=base_value,
                market=base_value,
                resource=base_value,
                timeline=base_value,
                quality=base_value
            )

        # Bayesian 시스템이 예측을 먼저 생성
        predicted_vector = UncertaintyVector(
            technical=predicted_uncertainties.get('technical', 0.5),
            market=predicted_uncertainties.get('market', 0.5),
            resource=predicted_uncertainties.get('resource', 0.5),
            timeline=predicted_uncertainties.get('timeline', 0.5),
            quality=predicted_uncertainties.get('quality', 0.5)
        )

        prediction = self.bayesian.predict_uncertainty(
            current_vector=predicted_vector,
            phase=phase,
            horizon_hours=0
        )

        # Bayesian 시스템 업데이트
        self.bayesian.update_with_observation(
            phase=phase,
            predicted=prediction,
            observed_vector=actual_vector,
            outcome_success=actual_success
        )

        self.integration_metrics["learning_events"] += 1

        # 상태 저장
        self.bayesian.save_state()

        logger.info(f"📈 Learned from {phase} outcome: success={actual_success}, "
                   f"predicted_confidence={predicted_confidence:.2%}")

    def get_integration_report(self) -> Dict[str, Any]:
        """
        통합 성과 리포트 생성

        Returns:
            통합 메트릭 및 Bayesian 성능 리포트
        """
        bayesian_report = self.bayesian.get_performance_report()

        return {
            "integration_metrics": self.integration_metrics,
            "bayesian_performance": bayesian_report,
            "summary": {
                "total_decisions": self.integration_metrics["decisions_influenced"],
                "threshold_adjustments": self.integration_metrics["threshold_adjustments"],
                "bias_corrections": self.integration_metrics["bias_corrections"],
                "learning_events": self.integration_metrics["learning_events"],
                "average_confidence": bayesian_report.get('average_confidence', 0),
                "bias_profile": bayesian_report.get('bias_profile', {})
            }
        }

    def _explain_adjustment(self, bias_type: str, bias_adj: float, conf_factor: float) -> str:
        """Threshold 조정 사유 설명"""
        reasons = []

        if bias_type != 'unbiased':
            if 'optimistic' in bias_type:
                reasons.append(f"과거 과도한 낙관 패턴 감지 → threshold 상향 ({bias_adj:+.2f})")
            else:
                reasons.append(f"과거 과도한 비관 패턴 감지 → threshold 하향 ({bias_adj:+.2f})")

        if abs(conf_factor) > 0.01:
            if conf_factor > 0:
                reasons.append(f"높은 기본 confidence → threshold 완화 ({conf_factor:+.2f})")
            else:
                reasons.append(f"낮은 기본 confidence → threshold 강화 ({conf_factor:+.2f})")

        if not reasons:
            return "조정 없음 (표준 threshold 적용)"

        return " | ".join(reasons)

    def _explain_decision(self, decision: str, confidence: float,
                         threshold: float, threshold_meta: Dict) -> str:
        """의사결정 사유 설명"""
        gap = confidence - threshold

        explanations = {
            "GO": f"✅ GO: Confidence ({confidence:.2%}) > Threshold ({threshold:.2%}), Gap: {gap:+.2%}",
            "GO_WITH_CHECKPOINTS": f"⚠️ GO_WITH_CHECKPOINTS: Confidence ({confidence:.2%}) ≥ 80% Threshold, Gap: {gap:+.2%}",
            "NO_GO": f"❌ NO_GO: Confidence ({confidence:.2%}) < Threshold ({threshold:.2%}), Gap: {gap:-.2%}"
        }

        base_explanation = explanations.get(decision, "Unknown decision")

        # Threshold 조정 사유 추가
        if threshold_meta.get('bias_type') != 'unbiased':
            base_explanation += f" | Bias: {threshold_meta['bias_type']}"

        return base_explanation


def demo_integration():
    """통합 시스템 데모"""
    print("\n" + "=" * 60)
    print("UDO V2 + BAYESIAN LEARNING INTEGRATION DEMO")
    print("=" * 60)

    # 통합 시스템 초기화
    integration = UDOBayesianIntegration(project_name="Demo-Project")

    # 시나리오: Implementation Phase 의사결정
    print("\n📊 Scenario: Implementation Phase Decision")

    # UDO v2에서 계산한 기본 값들
    base_confidence = 0.72
    uncertainties = {
        "technical": 0.4,
        "market": 0.3,
        "resource": 0.5,
        "timeline": 0.6,
        "quality": 0.4
    }

    # 강화된 의사결정
    decision = integration.enhance_go_decision(
        phase="implementation",
        base_confidence=base_confidence,
        uncertainties=uncertainties
    )

    print(f"\n🎯 Decision: {decision['decision']}")
    print(f"   Final Confidence: {decision['final_confidence']:.2%}")
    print(f"   Threshold: {decision['threshold']['adjusted']:.2%}")
    print(f"   Explanation: {decision['explanation']}")

    # Bayesian 인사이트
    insights = decision['bayesian_insights']
    print(f"\n🧠 Bayesian Insights:")
    print(f"   Predicted Uncertainty: {insights['predicted_uncertainty']:.2%}")
    print(f"   Trend: {insights['trend']}")
    print(f"   Quantum State: {insights['quantum_state']}")

    # 프로젝트 결과로부터 학습
    print("\n📈 Learning from Outcome...")
    integration.learn_from_project_outcome(
        phase="implementation",
        predicted_confidence=base_confidence,
        predicted_uncertainties=uncertainties,
        actual_success=True,
        actual_uncertainties={
            "technical": 0.3,
            "market": 0.25,
            "resource": 0.4,
            "timeline": 0.5,
            "quality": 0.35
        }
    )

    # 통합 리포트
    print("\n📊 Integration Report:")
    report = integration.get_integration_report()
    print(f"   Decisions Influenced: {report['summary']['total_decisions']}")
    print(f"   Threshold Adjustments: {report['summary']['threshold_adjustments']}")
    print(f"   Bias Corrections: {report['summary']['bias_corrections']}")
    print(f"   Learning Events: {report['summary']['learning_events']}")

    print("\n" + "=" * 60)
    print("✅ INTEGRATION DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    demo_integration()
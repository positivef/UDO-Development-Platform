#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Development Orchestrator (UDO) - 통합 개발 지휘 시스템

Purpose: 모든 컴포넌트를 하나의 시스템으로 통합
- Adaptive Selector v2
- 3-AI Collaboration Bridge
- Uncertainty Map v2
- COMPASS Framework

Author: VibeCoding Team
Date: 2025-11-16
Version: 1.0.1 (Unicode 인코딩 문제 해결)
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import yaml

# Windows Unicode 인코딩 문제 근본 해결
if sys.platform == 'win32':
    # stdout/stderr를 UTF-8 모드로 재구성 (안전하게)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

# 기존 컴포넌트 임포트 - 경로 추가
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))
# obsidian-vibe-coding-docs 경로도 추가 (adaptive_system_selector_v2 위치)
# skill/vibe-coding-enhanced/scripts -> skill -> GitHub -> obsidian-vibe-coding-docs
github_root = script_dir.parent.parent.parent
obsidian_scripts = github_root / "obsidian-vibe-coding-docs" / "scripts"
if obsidian_scripts.exists():
    sys.path.append(str(obsidian_scripts))

try:
    from adaptive_system_selector_v2 import (
        AdaptiveSystemSelectorV2,
        SystemType,
        DevelopmentStage
    )
    SELECTOR_AVAILABLE = True
except:
    SELECTOR_AVAILABLE = False

try:
    from three_ai_collaboration_bridge import (
        ThreeAICollaborationBridge,
        AIRole,
        ExecutionMode
    )
    AI_BRIDGE_AVAILABLE = True
except:
    AI_BRIDGE_AVAILABLE = False

try:
    from uncertainty_map_generator_v2 import (
        UncertaintyMapGeneratorV2,
        UncertaintyLevel
    )
    UNCERTAINTY_AVAILABLE = True
except:
    UNCERTAINTY_AVAILABLE = False


@dataclass
class ProjectContext:
    """프로젝트 전체 컨텍스트"""
    project_name: str
    goal: str
    team_size: int
    timeline_weeks: int
    budget: float
    tech_stack: List[str]
    constraints: List[str]
    success_metrics: List[str]
    current_phase: str  # ideation, design, mvp, implementation, etc.
    files: List[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class DevelopmentDecision:
    """개발 의사결정 기록"""
    timestamp: datetime
    phase: str
    decision_type: str  # system_selection, ai_collaboration, risk_assessment
    input_context: Dict
    recommendation: Dict
    uncertainty_level: float
    user_override: Optional[str]
    actual_outcome: Optional[Dict]
    lessons_learned: Optional[str]


class UnifiedDevelopmentOrchestrator:
    """
    통합 개발 오케스트레이터 - 모든 시스템의 중앙 제어

    역할:
    1. 프로젝트 전체 생명주기 관리
    2. 컴포넌트 간 조율
    3. 의사결정 자동화 & 추적
    4. 지속적 학습 & 개선
    """

    def __init__(self, project_context: ProjectContext):
        self.context = project_context
        self.decision_history: List[DevelopmentDecision] = []

        # 컴포넌트 초기화
        self.selector = AdaptiveSystemSelectorV2() if SELECTOR_AVAILABLE else None
        self.ai_bridge = ThreeAICollaborationBridge() if AI_BRIDGE_AVAILABLE else None
        self.uncertainty = UncertaintyMapGeneratorV2() if UNCERTAINTY_AVAILABLE else None

        # 상태 관리
        self.current_phase = project_context.current_phase
        self.active_systems = []
        self.accumulated_debt = 0.0
        self.time_spent = 0.0

        # COMPASS 프레임워크 통합
        self.compass_phases = self._init_compass_phases()

        print(f"🚀 UDO 초기화 완료: {project_context.project_name}")
        print(f"   Phase: {self.current_phase}")
        print(f"   Components: Selector={SELECTOR_AVAILABLE}, AI={AI_BRIDGE_AVAILABLE}, Uncertainty={UNCERTAINTY_AVAILABLE}")

    def _init_compass_phases(self) -> Dict:
        """COMPASS 프레임워크 단계별 설정"""
        return {
            "phase1_ideation": {
                "goal": "혁신적 아이디어 발굴",
                "recommended_system": "creative-thinking",
                "ai_pattern": "ideation",  # Gemini → Claude → Codex
                "duration_days": 3,
                "success_criteria": ["3개 이상 검증된 아이디어"]
            },
            "phase2_design": {
                "goal": "최적 설계 도출",
                "recommended_system": "creative-thinking",
                "ai_pattern": "design_validation",
                "duration_days": 7,
                "success_criteria": ["아키텍처 문서", "3가지 설계 대안"]
            },
            "phase3_mvp": {
                "goal": "빠른 MVP 구현",
                "recommended_system": "enhanced",
                "ai_pattern": "implementation",
                "duration_days": 14,
                "success_criteria": ["작동하는 프로토타입", "핵심 기능 구현"]
            },
            "phase4_implementation": {
                "goal": "프로덕션 품질 구현",
                "recommended_system": "fusion",
                "ai_pattern": "full_cycle",
                "duration_days": 21,
                "success_criteria": ["테스트 커버리지 80%", "보안 검증"]
            },
            "phase5_launch": {
                "goal": "안전한 출시",
                "recommended_system": "dev-rules",
                "ai_pattern": "verification",
                "duration_days": 7,
                "success_criteria": ["무중단 배포", "모니터링 설정"]
            }
        }

    def start_development_cycle(self, user_request: str) -> Dict:
        """
        개발 사이클 시작 - 통합 의사결정 프로세스

        Flow:
        1. 요청 분석 (Adaptive Selector)
        2. 불확실성 평가 (Uncertainty Map)
        3. AI 협업 패턴 결정 (3-AI Bridge)
        4. 시스템 선택 & 실행
        5. 결과 추적 & 학습
        """

        print(f"\n{'='*60}")
        print(f"🎯 개발 사이클 시작")
        print(f"{'='*60}")
        print(f"요청: {user_request}")
        print(f"현재 Phase: {self.current_phase}")

        # Step 1: 시스템 선택
        system_recommendation = self._select_optimal_system(user_request)

        # Step 2: 불확실성 평가
        uncertainty_assessment = self._assess_uncertainties(user_request, system_recommendation)

        # Step 3: AI 협업 패턴 결정
        ai_collaboration = self._determine_ai_collaboration(
            user_request,
            system_recommendation,
            uncertainty_assessment
        )

        # Step 4: Go/No-Go 결정
        go_decision = self._make_go_decision(
            system_recommendation,
            uncertainty_assessment,
            ai_collaboration
        )

        # Step 5: 실행 계획
        execution_plan = self._create_execution_plan(
            system_recommendation,
            ai_collaboration,
            go_decision
        )

        # 결정 기록
        decision = DevelopmentDecision(
            timestamp=datetime.now(),
            phase=self.current_phase,
            decision_type="cycle_start",
            input_context={"request": user_request},
            recommendation=execution_plan,
            uncertainty_level=uncertainty_assessment['overall_confidence'],
            user_override=None,
            actual_outcome=None,
            lessons_learned=None
        )
        self.decision_history.append(decision)

        return execution_plan

    def _select_optimal_system(self, request: str) -> Dict:
        """최적 시스템 선택 (Adaptive Selector v2 활용)"""

        if not self.selector:
            # 폴백: 간단한 규칙 기반
            return {
                "system": "enhanced",
                "confidence": 0.5,
                "reason": "Selector 없음 - 기본값"
            }

        # 실제 분석
        context = self.selector.analyze_request(
            request,
            team_size=self.context.team_size,
            files=self.context.files or []
        )

        recommendation = self.selector.recommend_system(context)

        print(f"\n📊 시스템 선택 분석:")
        print(f"   추천: {recommendation.primary.value}")
        print(f"   신뢰도: {recommendation.confidence:.0%}")
        print(f"   복잡도: {context.complexity:.2f}")

        return {
            "system": recommendation.primary.value,
            "secondary": recommendation.secondary.value if recommendation.secondary else None,
            "confidence": recommendation.confidence,
            "complexity": context.complexity,
            "reason": recommendation.reasoning,
            "estimated_time": recommendation.expected_time,
            "estimated_quality": recommendation.expected_quality,
            "context": context
        }

    def _assess_uncertainties(self, request: str, system_rec: Dict) -> Dict:
        """불확실성 평가 (Uncertainty Map v2 활용)"""

        if not self.uncertainty:
            return {
                "overall_confidence": 0.7,
                "uncertainties": [],
                "high_risk_count": 0
            }

        # 코드 메트릭 추출
        code_metrics = system_rec.get('context', {}).code_metrics if hasattr(system_rec.get('context', {}), 'code_metrics') else None

        # 불확실성 분석
        uncertainties, overall_confidence = self.uncertainty.analyze_uncertainty(
            context=f"{self.current_phase}: {request}",
            code_metrics=code_metrics.__dict__ if code_metrics else None,
            user_request=request
        )

        high_risk = [u for u in uncertainties if u.risk.value in ['high', 'critical']]

        print(f"\n🗺️ 불확실성 평가:")
        print(f"   전체 신뢰도: {overall_confidence:.0%}")
        print(f"   불확실성 항목: {len(uncertainties)}개")
        print(f"   고위험: {len(high_risk)}개")

        if high_risk:
            print(f"\n   ⚠️ 고위험 영역:")
            for u in high_risk[:3]:
                print(f"      - {u.description} ({u.confidence:.0%})")

        return {
            "overall_confidence": overall_confidence,
            "uncertainties": uncertainties,
            "high_risk_count": len(high_risk),
            "assessment": "HIGH_RISK" if len(high_risk) > 2 else "MODERATE" if overall_confidence < 0.7 else "LOW_RISK"
        }

    def _determine_ai_collaboration(self, request: str, system_rec: Dict, uncertainty: Dict) -> Dict:
        """AI 협업 패턴 결정 (3-AI Bridge 활용)"""

        if not self.ai_bridge:
            return {
                "pattern": "single_ai",
                "ais": ["claude"],
                "reason": "AI Bridge 없음"
            }

        # COMPASS phase에 따른 기본 패턴
        phase_config = self.compass_phases.get(f"phase{self._get_phase_number()}_{self.current_phase}", {})
        suggested_pattern = phase_config.get("ai_pattern", "implementation")

        # 불확실성에 따른 조정
        if uncertainty['assessment'] == "HIGH_RISK":
            # 고위험 → 3-AI 풀 협업
            pattern = "full_cycle"
            reason = "고위험으로 인한 3-AI 검증 필요"
        elif uncertainty['overall_confidence'] < 0.6:
            # 중위험 → Codex 검증 추가
            pattern = "verification"
            reason = "신뢰도 낮아 Codex 검증 추가"
        else:
            # 저위험 → 제안된 패턴 사용
            pattern = suggested_pattern
            reason = f"Phase {self.current_phase} 기본 패턴"

        # AI 가용성 확인
        available_ais = {
            "claude": True,
            "codex": self.ai_bridge.codex.available,
            "gemini": self.ai_bridge.gemini.available
        }

        print(f"\n🤝 AI 협업 패턴:")
        print(f"   패턴: {pattern}")
        print(f"   이유: {reason}")
        print(f"   가용 AI: {[k for k, v in available_ais.items() if v]}")

        return {
            "pattern": pattern,
            "ais": [k for k, v in available_ais.items() if v],
            "reason": reason,
            "available_ais": available_ais
        }

    def _make_go_decision(self, system_rec: Dict, uncertainty: Dict, ai_collab: Dict) -> Dict:
        """Go/No-Go 의사결정"""

        # 결정 요소
        confidence = system_rec['confidence'] * uncertainty['overall_confidence']
        risk_level = uncertainty['assessment']
        high_risk_count = uncertainty['high_risk_count']

        # 의사결정 로직
        if confidence > 0.7 and risk_level in ["LOW_RISK", "MODERATE"]:
            decision = "GO"
            approach = "DIRECT"
        elif confidence > 0.5 and high_risk_count < 3:
            decision = "GO_WITH_CHECKPOINTS"
            approach = "INCREMENTAL"
        elif confidence > 0.3:
            decision = "PROTOTYPE_FIRST"
            approach = "EXPERIMENTAL"
        else:
            decision = "NO_GO"
            approach = "RESEARCH_MORE"

        print(f"\n🚦 Go/No-Go 결정:")
        print(f"   결정: {decision}")
        print(f"   접근: {approach}")
        print(f"   종합 신뢰도: {confidence:.0%}")

        return {
            "decision": decision,
            "approach": approach,
            "confidence": confidence,
            "risk_level": risk_level,
            "checkpoints": self._define_checkpoints(approach) if approach != "DIRECT" else []
        }

    def _define_checkpoints(self, approach: str) -> List[Dict]:
        """체크포인트 정의"""

        if approach == "INCREMENTAL":
            return [
                {"after": "Day 3", "check": "핵심 기능 작동", "rollback_ready": True},
                {"after": "Day 7", "check": "통합 테스트 통과", "rollback_ready": True},
                {"after": "Day 10", "check": "불확실성 재평가", "rollback_ready": False}
            ]
        elif approach == "EXPERIMENTAL":
            return [
                {"after": "Day 1", "check": "POC 작동", "rollback_ready": True},
                {"after": "Day 3", "check": "실험 결과 분석", "go_nogo": True}
            ]

        return []

    def _create_execution_plan(self, system_rec: Dict, ai_collab: Dict, go_decision: Dict) -> Dict:
        """실행 계획 생성"""

        plan = {
            "decision": go_decision['decision'],
            "timestamp": datetime.now().isoformat(),
            "phase": self.current_phase,

            # 시스템 선택
            "system": {
                "primary": system_rec['system'],
                "secondary": system_rec.get('secondary'),
                "confidence": system_rec['confidence']
            },

            # AI 협업
            "ai_collaboration": {
                "pattern": ai_collab['pattern'],
                "ais": ai_collab['ais']
            },

            # 접근 방식
            "approach": go_decision['approach'],
            "checkpoints": go_decision['checkpoints'],

            # 예상
            "estimates": {
                "time": system_rec.get('estimated_time', 'Unknown'),
                "quality": system_rec.get('estimated_quality', 'Unknown')
            },

            # 다음 단계
            "next_steps": self._generate_next_steps(system_rec, go_decision)
        }

        print(f"\n📋 실행 계획 생성 완료")
        print(f"   시스템: {plan['system']['primary']}")
        print(f"   AI: {' + '.join(plan['ai_collaboration']['ais'])}")
        print(f"   접근: {plan['approach']}")

        return plan

    def _generate_next_steps(self, system_rec: Dict, go_decision: Dict) -> List[str]:
        """다음 단계 생성"""

        steps = []

        if go_decision['decision'] == "GO":
            steps.extend([
                f"1. {system_rec['system']} 시스템으로 개발 시작",
                "2. 첫 체크포인트까지 진행",
                "3. 결과 측정 및 기록"
            ])
        elif go_decision['decision'] == "GO_WITH_CHECKPOINTS":
            steps.extend([
                "1. 최소 기능부터 구현",
                f"2. Day 3: {go_decision['checkpoints'][0]['check']}",
                "3. 체크포인트마다 Go/No-Go 재평가"
            ])
        elif go_decision['decision'] == "PROTOTYPE_FIRST":
            steps.extend([
                "1. POC(Proof of Concept) 구현",
                "2. 실험 결과 분석",
                "3. 결과에 따라 전면 구현 or 피벗"
            ])
        else:  # NO_GO
            steps.extend([
                "1. 더 많은 리서치 필요",
                "2. 불확실성 요소 해결",
                "3. 재평가 후 재시도"
            ])

        return steps

    def _get_phase_number(self) -> int:
        """현재 phase 번호 추출"""
        phase_map = {
            "ideation": 1,
            "design": 2,
            "mvp": 3,
            "implementation": 4,
            "launch": 5
        }
        return phase_map.get(self.current_phase, 3)

    def execute_plan(self, plan: Dict) -> Dict:
        """실행 계획 실행"""

        if plan['decision'] == "NO_GO":
            return {
                "status": "BLOCKED",
                "reason": "Go 결정 실패",
                "recommendation": "불확실성 해결 필요"
            }

        print(f"\n{'='*60}")
        print(f"⚡ 실행 시작")
        print(f"{'='*60}")

        # AI 협업 패턴에 따른 실행
        if self.ai_bridge and len(plan['ai_collaboration']['ais']) > 1:
            print(f"\n🤝 {len(plan['ai_collaboration']['ais'])}-AI 협업 시작...")

            # 실제 AI 협업 실행
            result = self.ai_bridge.collaborate(
                task=f"{self.current_phase} 단계 작업",
                pattern=plan['ai_collaboration']['pattern'],
                max_iterations=3
            )

            return {
                "status": "COMPLETED",
                "ai_result": result,
                "execution_time": result.get('total_execution_time', 0)
            }
        else:
            print(f"\n🤖 Claude 단독 실행...")
            return {
                "status": "COMPLETED",
                "message": f"{plan['system']['primary']} 시스템으로 진행",
                "execution_time": 0
            }

    def record_outcome(self, plan: Dict, execution_result: Dict, user_feedback: Optional[str] = None):
        """결과 기록 및 학습"""

        # 마지막 결정 업데이트
        if self.decision_history:
            last_decision = self.decision_history[-1]
            last_decision.actual_outcome = execution_result
            last_decision.lessons_learned = user_feedback

        # 오버라이드 학습
        if user_feedback and "override" in user_feedback.lower():
            if self.selector:
                # Adaptive Rule Engine에 학습
                print(f"\n📝 사용자 오버라이드 학습 중...")

        print(f"\n✅ 결과 기록 완료")

    def generate_report(self) -> str:
        """전체 개발 과정 리포트"""

        report = f"""
# 🎯 통합 개발 리포트

**프로젝트**: {self.context.project_name}
**목표**: {self.context.goal}
**현재 Phase**: {self.current_phase}

## 📊 의사결정 히스토리

"""

        for i, decision in enumerate(self.decision_history, 1):
            report += f"""
### {i}. {decision.decision_type} ({decision.timestamp.strftime('%Y-%m-%d %H:%M')})
- **Phase**: {decision.phase}
- **신뢰도**: {decision.uncertainty_level:.0%}
- **추천**: {decision.recommendation.get('system', {}).get('primary', 'N/A')}
"""
            if decision.user_override:
                report += f"- **사용자 오버라이드**: {decision.user_override}\n"

        return report

    def save_state(self, path: Optional[Path] = None):
        """상태 저장"""

        if not path:
            path = Path(f"udo_state_{self.context.project_name}.json")

        state = {
            "project_context": asdict(self.context),
            "current_phase": self.current_phase,
            "decision_history": [
                {
                    **asdict(d),
                    "timestamp": d.timestamp.isoformat()
                }
                for d in self.decision_history
            ],
            "accumulated_debt": self.accumulated_debt,
            "time_spent": self.time_spent
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        print(f"\n💾 상태 저장 완료: {path}")


def main():
    """UDO 데모"""

    print("="*80)
    print("🚀 Unified Development Orchestrator (UDO) Demo")
    print("="*80)

    # 프로젝트 컨텍스트 생성
    project = ProjectContext(
        project_name="2025-Revenue-App",
        goal="2025년 수익형 웹/앱 개발",
        team_size=5,
        timeline_weeks=12,
        budget=50000,
        tech_stack=["Next.js", "FastAPI", "PostgreSQL"],
        constraints=["3개월 내 출시", "초기 투자 최소화"],
        success_metrics=["DAU 1000+", "MRR $5000+"],
        current_phase="ideation"
    )

    # UDO 초기화
    udo = UnifiedDevelopmentOrchestrator(project)

    # 개발 사이클 시작
    user_request = "2025년 한국 시장에서 수익 가능한 SaaS 아이디어 발굴"

    plan = udo.start_development_cycle(user_request)

    # 실행
    result = udo.execute_plan(plan)

    # 결과 기록
    udo.record_outcome(plan, result)

    # 리포트 생성
    report = udo.generate_report()
    print(report)

    # 상태 저장
    udo.save_state()


if __name__ == "__main__":
    main()

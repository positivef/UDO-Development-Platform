#!/usr/bin/env python3
"""
Uncertainty Map Generator - 불확실성 지도 자동 생성

매 답변마다 포함해야 하는 불확실성 분석을 구조화된 형태로 생성

Usage:
    from uncertainty_map_generator import UncertaintyMapGenerator

    generator = UncertaintyMapGenerator()
    uncertainty_map = generator.generate(
        context="Phase 2 업그레이드 제안",
        known_knowns=["ROI 계산 완료", "조건 충족 확인"],
        known_unknowns=["실제 사용자 적응 속도", "워크플로우 변화"],
        unknown_unknowns=["예상치 못한 통합 이슈"]
    )
    print(uncertainty_map)
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class UncertaintyItem:
    """불확실성 항목"""
    description: str
    confidence: int  # 0-100
    evidence: Optional[str] = None
    risk_level: str = "medium"  # low, medium, high
    measurement_plan: Optional[str] = None
    mitigation: Optional[str] = None


class UncertaintyMapGenerator:
    """불확실성 지도 자동 생성기"""

    def __init__(self):
        self.confidence_thresholds = {
            "known_knowns": 90,
            "known_unknowns": 60,
            "unknown_unknowns": 30
        }

    def generate(
        self,
        context: str,
        known_knowns: List[Dict[str, str]] = None,
        known_unknowns: List[Dict[str, str]] = None,
        unknown_unknowns: List[Dict[str, str]] = None,
        include_table: bool = True
    ) -> str:
        """
        불확실성 지도 마크다운 생성

        Args:
            context: 분석 대상 (예: "Phase 2 업그레이드 제안")
            known_knowns: 확실한 사실들 [{"item": "...", "evidence": "..."}]
            known_unknowns: 알려진 불확실성 [{"item": "...", "risk": "...", "measurement": "..."}]
            unknown_unknowns: 예상치 못한 변수 [{"factor": "...", "impact": "...", "mitigation": "..."}]
            include_table: 종합 평가 표 포함 여부

        Returns:
            마크다운 형식의 불확실성 지도
        """
        known_knowns = known_knowns or []
        known_unknowns = known_unknowns or []
        unknown_unknowns = unknown_unknowns or []

        map_md = f"""## 🗺️ 불확실성 지도 - {context}

### Known Knowns (90% 확신도)
**확실히 아는 것들:**
"""

        # Known Knowns (90%+)
        if known_knowns:
            for item in known_knowns:
                evidence = item.get("evidence", "")
                evidence_text = f" ({evidence})" if evidence else ""
                map_md += f"- ✅ **{item['item']}**{evidence_text}\n"
        else:
            map_md += "- (분석 중...)\n"

        # Known Unknowns (60%)
        map_md += """
### Known Unknowns (60% 확신도)
**알고 있지만 불확실한 것들:**

"""

        if known_unknowns:
            for i, item in enumerate(known_unknowns, 1):
                map_md += f"""**{i}. {item['item']}**
- ❓ **문제**: {item.get('problem', '불확실성 존재')}
- 📊 **리스크**: {item.get('risk', '측정 필요')}
- 🎯 **측정 필요**: {item.get('measurement', '실사용 데이터 수집')}

"""
        else:
            map_md += "- (분석 중...)\n\n"

        # Unknown Unknowns (30%)
        map_md += """### Unknown Unknowns (30% 확신도)
**예상하지 못한 변수들:**

"""

        if unknown_unknowns:
            for i, item in enumerate(unknown_unknowns, 1):
                map_md += f"""**{i}. {item['factor']}**
- 🌫️ **완전히 모름**: {item.get('description', '예상 불가')}
- 💥 **잠재적 영향**: {item.get('impact', '알 수 없음')}
- ⚠️ **대비책**: {item.get('mitigation', '모니터링 필요')}

"""
        else:
            map_md += "- (분석 중...)\n\n"

        # 종합 평가 표
        if include_table:
            map_md += """---

## 📊 종합 불확실성 평가

| 측면 | 확신도 | 리스크 | 완화 전략 |
|------|--------|--------|----------|
"""
            # Known Knowns 요약
            if known_knowns:
                for item in known_knowns[:3]:  # 최대 3개
                    map_md += f"| **{item['item'][:20]}...** | 95% | Low | {item.get('mitigation', '검증 완료')} |\n"

            # Known Unknowns 요약
            if known_unknowns:
                for item in known_unknowns[:3]:
                    risk_level = item.get('risk_level', 'Medium')
                    map_md += f"| **{item['item'][:20]}...** | 60% | {risk_level} | {item.get('mitigation', '측정 후 조정')} |\n"

            # Unknown Unknowns 요약
            if unknown_unknowns:
                for item in unknown_unknowns[:3]:
                    map_md += f"| **{item['factor'][:20]}...** | 30% | High | {item.get('mitigation', '모니터링')} |\n"

        # 권장 접근법
        map_md += """
---

## 🎯 권장 접근법 (불확실성 고려)

### 즉시 실행 (90% 확신)
```
✅ 확실한 부분 진행
- 검증된 사실 기반 실행
```

### 단기 검증 (60% 확신)
```
📊 1-2주 후 데이터 수집:
- 불확실성 측정
- 가설 검증
```

### 장기 모니터링 (30% 확신)
```
⚠️ 지속적 관찰:
- 예상치 못한 패턴
- 조기 경보 시스템
```

**최종 판단**: 진행하되, **정기적 재평가 필수**
"""

        return map_md

    def generate_quick(self, context: str, confidence: int = 70) -> str:
        """
        빠른 불확실성 지도 생성 (간소화 버전)

        Args:
            context: 분석 대상
            confidence: 전반적 확신도 (0-100)

        Returns:
            간소화된 불확실성 지도
        """
        if confidence >= 90:
            tier = "Known Knowns"
            emoji = "✅"
            action = "즉시 실행 권장"
        elif confidence >= 60:
            tier = "Known Unknowns"
            emoji = "⚠️"
            action = "측정 후 진행"
        else:
            tier = "Unknown Unknowns"
            emoji = "🚨"
            action = "신중한 검증 필요"

        return f"""## 🗺️ 불확실성 ({context})

{emoji} **{tier}** - 확신도: {confidence}%

**권장**: {action}

**재평가**: {'1주일 후' if confidence >= 60 else '즉시 데이터 수집'}
"""

    def assess_uncertainty(
        self,
        has_evidence: bool,
        has_past_data: bool,
        is_tested: bool,
        complexity: str = "medium"  # low, medium, high
    ) -> Dict[str, any]:
        """
        자동 불확실성 평가

        Args:
            has_evidence: 증거 존재 여부
            has_past_data: 과거 데이터 존재 여부
            is_tested: 테스트 완료 여부
            complexity: 복잡도

        Returns:
            평가 결과 딕셔너리
        """
        confidence = 50  # 기본값

        # 증거 기반 신뢰도 계산
        if has_evidence:
            confidence += 20
        if has_past_data:
            confidence += 15
        if is_tested:
            confidence += 15

        # 복잡도 패널티
        complexity_penalty = {
            "low": 0,
            "medium": -5,
            "high": -15
        }
        confidence += complexity_penalty.get(complexity, 0)

        # 범위 제한
        confidence = max(0, min(100, confidence))

        # 티어 결정
        if confidence >= 90:
            tier = "known_knowns"
            recommendation = "즉시 실행"
        elif confidence >= 60:
            tier = "known_unknowns"
            recommendation = "측정 후 진행"
        else:
            tier = "unknown_unknowns"
            recommendation = "신중한 검증 필요"

        return {
            "confidence": confidence,
            "tier": tier,
            "recommendation": recommendation,
            "factors": {
                "has_evidence": has_evidence,
                "has_past_data": has_past_data,
                "is_tested": is_tested,
                "complexity": complexity
            }
        }


# 사용 예제
if __name__ == "__main__":
    generator = UncertaintyMapGenerator()

    # 예제 1: 전체 불확실성 지도
    print("=" * 60)
    print("예제 1: 전체 불확실성 지도")
    print("=" * 60)

    full_map = generator.generate(
        context="Phase 2 자동 업그레이드",
        known_knowns=[
            {"item": "ROI 계산 로직 완료", "evidence": "22/22 테스트 통과"},
            {"item": "조건 검증 정확", "evidence": "시뮬레이션 검증"},
            {"item": "롤백 가능", "evidence": "1분 내 원복"}
        ],
        known_unknowns=[
            {
                "item": "사용자 준비도",
                "problem": "조건 충족했지만 워크플로우 적응 중",
                "risk": "너무 빠른 업그레이드 → 혼란",
                "measurement": "사용자 만족도 설문",
                "risk_level": "Medium",
                "mitigation": "1주일 유예 옵션 제공"
            },
            {
                "item": "ROI 임계값 적절성",
                "problem": "200%가 너무 높거나 낮을 수 있음",
                "risk": "Phase 2 도달 못함 or 너무 빠른 도달",
                "measurement": "실제 Phase 1 ROI 분포",
                "risk_level": "Medium",
                "mitigation": "1개월 후 임계값 조정"
            }
        ],
        unknown_unknowns=[
            {
                "factor": "개인별 학습 속도 차이",
                "description": "어떤 사용자는 1주, 어떤 사용자는 6개월",
                "impact": "획일적 기준 부적합",
                "mitigation": "개인화 로직 장기 개발"
            }
        ]
    )

    print(full_map)

    # 예제 2: 빠른 평가
    print("\n" + "=" * 60)
    print("예제 2: 빠른 불확실성 평가")
    print("=" * 60)

    quick_map = generator.generate_quick("시간 제약 제거", confidence=85)
    print(quick_map)

    # 예제 3: 자동 평가
    print("\n" + "=" * 60)
    print("예제 3: 자동 불확실성 평가")
    print("=" * 60)

    assessment = generator.assess_uncertainty(
        has_evidence=True,
        has_past_data=False,
        is_tested=True,
        complexity="medium"
    )

    print(f"Confidence: {assessment['confidence']}%")
    print(f"Tier: {assessment['tier']}")
    print(f"Recommendation: {assessment['recommendation']}")
    print(f"Factors: {assessment['factors']}")

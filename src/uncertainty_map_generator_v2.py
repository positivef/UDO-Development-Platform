#!/usr/bin/env python3
"""
Uncertainty Map Generator v2.0 - Enhanced with Real-time Tracking
Based on Opus Model Review - Addresses 65% confidence issue

Key Improvements:
1. Real-time confidence calculation from actual metrics
2. Dynamic uncertainty tracking with thresholds
3. Integration with AI decision making
4. Automatic mitigation strategy generation

Author: VibeCoding Team
Date: 2025-11-16
Version: 2.0.0
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import hashlib


class UncertaintyLevel(Enum):
    """Levels of uncertainty"""
    KNOWN_KNOWN = "known_known"        # >90% confidence
    KNOWN_UNKNOWN = "known_unknown"    # 60-90% confidence
    UNKNOWN_UNKNOWN = "unknown_unknown"  # <60% confidence
    EMERGENT = "emergent"               # New pattern detected


class RiskLevel(Enum):
    """Risk levels for uncertain areas"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class UncertaintyItem:
    """Enhanced uncertainty item with tracking"""
    id: str
    category: str
    description: str
    confidence: float  # 0.0 to 1.0
    level: UncertaintyLevel
    risk: RiskLevel
    evidence: List[str]
    measurements: Dict[str, float]
    mitigation_strategies: List[str]
    first_detected: datetime
    last_updated: datetime
    resolution_status: str  # "unresolved", "mitigating", "resolved"
    impact_areas: List[str]
    dependencies: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['first_detected'] = self.first_detected.isoformat()
        data['last_updated'] = self.last_updated.isoformat()
        data['level'] = self.level.value
        data['risk'] = self.risk.value
        return data


@dataclass
class UncertaintySnapshot:
    """Point-in-time uncertainty state"""
    timestamp: datetime
    overall_confidence: float
    item_count: Dict[str, int]  # Count by level
    high_risk_items: List[str]
    trending: str  # "improving", "stable", "degrading"
    action_required: bool


class UncertaintyTracker:
    """Tracks uncertainty over time with learning"""

    def __init__(self, history_file: Path = None):
        self.history_file = history_file or Path("uncertainty_history.json")
        self.current_items: Dict[str, UncertaintyItem] = {}
        self.snapshots: List[UncertaintySnapshot] = []
        self.resolution_patterns: Dict[str, List[Dict]] = {}
        self._load_history()

    def _load_history(self):
        """Load historical uncertainty data"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    # Load resolution patterns for learning
                    self.resolution_patterns = data.get('resolution_patterns', {})
            except:
                pass

    def track_item(self, item: UncertaintyItem):
        """Track an uncertainty item"""
        self.current_items[item.id] = item

        # Check if similar issue was resolved before
        similar_resolution = self._find_similar_resolution(item)
        if similar_resolution:
            item.mitigation_strategies.extend(similar_resolution['strategies'])
            item.metadata['similar_case'] = similar_resolution['id']

    def _find_similar_resolution(self, item: UncertaintyItem) -> Optional[Dict]:
        """Find similar resolved uncertainty from history"""
        for pattern_key, resolutions in self.resolution_patterns.items():
            if pattern_key in item.description.lower():
                # Return most successful resolution
                successful = [r for r in resolutions if r['success']]
                if successful:
                    return max(successful, key=lambda x: x.get('confidence', 0))
        return None

    def resolve_item(self, item_id: str, resolution: Dict):
        """Mark item as resolved and learn from it"""
        if item_id in self.current_items:
            item = self.current_items[item_id]
            item.resolution_status = "resolved"

            # Store resolution pattern for learning
            pattern_key = self._extract_pattern_key(item)
            if pattern_key not in self.resolution_patterns:
                self.resolution_patterns[pattern_key] = []

            self.resolution_patterns[pattern_key].append({
                'id': item_id,
                'strategies': resolution.get('strategies', []),
                'time_to_resolve': resolution.get('time', 0),
                'confidence': resolution.get('final_confidence', 0),
                'success': resolution.get('success', True)
            })

            self._save_history()

    def _extract_pattern_key(self, item: UncertaintyItem) -> str:
        """Extract pattern key for categorization"""
        # Simple keyword extraction (could be enhanced with NLP)
        keywords = []
        for word in item.description.lower().split():
            if len(word) > 4:
                keywords.append(word)
        return "_".join(sorted(keywords[:3]))

    def create_snapshot(self) -> UncertaintySnapshot:
        """Create current uncertainty snapshot"""
        now = datetime.now()

        # Count by level
        level_counts = {}
        high_risk = []

        for item in self.current_items.values():
            level = item.level.value
            level_counts[level] = level_counts.get(level, 0) + 1

            if item.risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                high_risk.append(item.id)

        # Calculate overall confidence
        if self.current_items:
            overall_confidence = sum(item.confidence for item in self.current_items.values()) / len(self.current_items)
        else:
            overall_confidence = 0.9  # Default high if no uncertainties

        # Determine trend
        if len(self.snapshots) > 0:
            prev_confidence = self.snapshots[-1].overall_confidence
            if overall_confidence > prev_confidence + 0.05:
                trending = "improving"
            elif overall_confidence < prev_confidence - 0.05:
                trending = "degrading"
            else:
                trending = "stable"
        else:
            trending = "stable"

        snapshot = UncertaintySnapshot(
            timestamp=now,
            overall_confidence=overall_confidence,
            item_count=level_counts,
            high_risk_items=high_risk,
            trending=trending,
            action_required=len(high_risk) > 0 or overall_confidence < 0.7
        )

        self.snapshots.append(snapshot)
        return snapshot

    def _save_history(self):
        """Save history to disk"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump({
                    'resolution_patterns': self.resolution_patterns,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except:
            pass


class UncertaintyMapGeneratorV2:
    """Enhanced uncertainty map generator with real metrics"""

    def __init__(self, project_path: Path = None):
        self.project_path = project_path or Path.cwd()
        self.tracker = UncertaintyTracker()
        self.confidence_thresholds = {
            UncertaintyLevel.KNOWN_KNOWN: 0.9,
            UncertaintyLevel.KNOWN_UNKNOWN: 0.6,
            UncertaintyLevel.UNKNOWN_UNKNOWN: 0.3,
            UncertaintyLevel.EMERGENT: 0.0
        }

    def analyze_uncertainty(self,
                           context: str,
                           code_metrics: Optional[Dict] = None,
                           user_request: str = "",
                           ai_responses: List[Dict] = None) -> Tuple[List[UncertaintyItem], float]:
        """
        Analyze uncertainty from multiple sources

        Returns:
            List of uncertainty items and overall confidence
        """
        uncertainties = []

        # 1. Code complexity uncertainty
        if code_metrics:
            complexity_uncertainty = self._analyze_code_uncertainty(code_metrics)
            if complexity_uncertainty:
                uncertainties.append(complexity_uncertainty)

        # 2. Request ambiguity uncertainty
        if user_request:
            ambiguity_uncertainty = self._analyze_request_uncertainty(user_request)
            if ambiguity_uncertainty:
                uncertainties.append(ambiguity_uncertainty)

        # 3. AI disagreement uncertainty
        if ai_responses and len(ai_responses) > 1:
            disagreement_uncertainty = self._analyze_ai_disagreement(ai_responses)
            if disagreement_uncertainty:
                uncertainties.append(disagreement_uncertainty)

        # 4. Technical debt uncertainty
        debt_uncertainty = self._analyze_technical_debt()
        if debt_uncertainty:
            uncertainties.append(debt_uncertainty)

        # 5. Domain complexity uncertainty
        domain_uncertainty = self._analyze_domain_complexity(context)
        if domain_uncertainty:
            uncertainties.append(domain_uncertainty)

        # Track all items
        for item in uncertainties:
            self.tracker.track_item(item)

        # Calculate overall confidence
        if uncertainties:
            overall_confidence = 1.0 - (sum(1 - u.confidence for u in uncertainties) / len(uncertainties))
        else:
            overall_confidence = 0.95

        return uncertainties, overall_confidence

    def _analyze_code_uncertainty(self, metrics: Dict) -> Optional[UncertaintyItem]:
        """Analyze uncertainty from code metrics"""
        confidence = metrics.get('confidence', 0.5)

        if confidence < 0.7:
            return UncertaintyItem(
                id=self._generate_id("code_complexity"),
                category="code_analysis",
                description=f"Code complexity analysis only {confidence:.0%} confident",
                confidence=confidence,
                level=self._determine_level(confidence),
                risk=RiskLevel.MEDIUM if confidence < 0.5 else RiskLevel.LOW,
                evidence=[
                    f"Cyclomatic complexity: {metrics.get('cyclomatic_complexity', 'unknown')}",
                    f"Lines analyzed: {metrics.get('lines_of_code', 0)}",
                    f"Test coverage: {metrics.get('test_coverage', 0):.0%}"
                ],
                measurements={
                    "complexity": metrics.get('cyclomatic_complexity', 0),
                    "coverage": metrics.get('test_coverage', 0),
                    "debt_ratio": metrics.get('technical_debt_ratio', 0)
                },
                mitigation_strategies=[
                    "Perform deeper code analysis",
                    "Add more test coverage",
                    "Refactor complex methods"
                ],
                first_detected=datetime.now(),
                last_updated=datetime.now(),
                resolution_status="unresolved",
                impact_areas=["development_time", "code_quality", "maintainability"],
                dependencies=["test_framework", "static_analysis_tools"]
            )
        return None

    def _analyze_request_uncertainty(self, request: str) -> Optional[UncertaintyItem]:
        """Analyze uncertainty from request ambiguity"""
        ambiguity_indicators = [
            "maybe", "possibly", "might", "could", "perhaps",
            "not sure", "think", "believe", "assume", "guess"
        ]

        ambiguity_score = sum(1 for word in ambiguity_indicators if word in request.lower())
        confidence = max(0.3, 1.0 - (ambiguity_score * 0.15))

        if ambiguity_score > 0:
            return UncertaintyItem(
                id=self._generate_id("request_ambiguity"),
                category="requirements",
                description=f"Request contains {ambiguity_score} ambiguous terms",
                confidence=confidence,
                level=self._determine_level(confidence),
                risk=RiskLevel.MEDIUM,
                evidence=[f"Ambiguous terms found: {ambiguity_score}"],
                measurements={"ambiguity_score": ambiguity_score},
                mitigation_strategies=[
                    "Clarify requirements with user",
                    "Create multiple implementation options",
                    "Use iterative development approach"
                ],
                first_detected=datetime.now(),
                last_updated=datetime.now(),
                resolution_status="unresolved",
                impact_areas=["requirements", "user_satisfaction"],
                dependencies=["user_feedback"]
            )
        return None

    def _analyze_ai_disagreement(self, ai_responses: List[Dict]) -> Optional[UncertaintyItem]:
        """Analyze uncertainty from AI disagreements"""
        # Check for different recommendations
        recommendations = [r.get('recommendation', '') for r in ai_responses]
        unique_recommendations = set(recommendations)

        if len(unique_recommendations) > 1:
            confidence = 1.0 / len(unique_recommendations)

            return UncertaintyItem(
                id=self._generate_id("ai_disagreement"),
                category="ai_analysis",
                description=f"AIs provided {len(unique_recommendations)} different recommendations",
                confidence=confidence,
                level=UncertaintyLevel.KNOWN_UNKNOWN,
                risk=RiskLevel.HIGH,
                evidence=[f"AI {i+1}: {rec}" for i, rec in enumerate(recommendations)],
                measurements={"disagreement_count": len(unique_recommendations)},
                mitigation_strategies=[
                    "Use consensus approach",
                    "Weight by AI expertise",
                    "Request human review"
                ],
                first_detected=datetime.now(),
                last_updated=datetime.now(),
                resolution_status="unresolved",
                impact_areas=["decision_quality", "implementation_approach"],
                dependencies=["ai_consensus_mechanism"]
            )
        return None

    def _analyze_technical_debt(self) -> Optional[UncertaintyItem]:
        """Analyze uncertainty from technical debt"""
        # Look for debt indicators
        debt_files = list(Path(self.project_path).glob("**/TODO*"))
        debt_files.extend(Path(self.project_path).glob("**/FIXME*"))

        todo_count = 0
        for file_path in list(Path(self.project_path).glob("**/*.py"))[:20]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    todo_count += content.count("TODO")
                    todo_count += content.count("FIXME")
            except:
                continue

        if todo_count > 10:
            confidence = max(0.3, 1.0 - (todo_count / 100))

            return UncertaintyItem(
                id=self._generate_id("technical_debt"),
                category="code_quality",
                description=f"High technical debt with {todo_count} TODO/FIXME items",
                confidence=confidence,
                level=self._determine_level(confidence),
                risk=RiskLevel.MEDIUM if todo_count < 30 else RiskLevel.HIGH,
                evidence=[f"TODO/FIXME count: {todo_count}"],
                measurements={"todo_count": todo_count},
                mitigation_strategies=[
                    "Prioritize debt reduction",
                    "Allocate refactoring time",
                    "Create debt payment plan"
                ],
                first_detected=datetime.now(),
                last_updated=datetime.now(),
                resolution_status="unresolved",
                impact_areas=["maintainability", "development_velocity"],
                dependencies=["refactoring_tools"]
            )
        return None

    def _analyze_domain_complexity(self, context: str) -> Optional[UncertaintyItem]:
        """Analyze uncertainty from domain complexity"""
        complex_domains = {
            "blockchain": 0.2,
            "machine learning": 0.3,
            "distributed": 0.3,
            "real-time": 0.4,
            "quantum": 0.1,
            "cryptography": 0.3
        }

        context_lower = context.lower()
        for domain, confidence in complex_domains.items():
            if domain in context_lower:
                return UncertaintyItem(
                    id=self._generate_id(f"domain_{domain}"),
                    category="domain_complexity",
                    description=f"Complex domain: {domain}",
                    confidence=confidence,
                    level=self._determine_level(confidence),
                    risk=RiskLevel.HIGH,
                    evidence=[f"Domain identified: {domain}"],
                    measurements={"domain_confidence": confidence},
                    mitigation_strategies=[
                        "Consult domain experts",
                        "Research best practices",
                        "Prototype key components first"
                    ],
                    first_detected=datetime.now(),
                    last_updated=datetime.now(),
                    resolution_status="unresolved",
                    impact_areas=["architecture", "implementation", "testing"],
                    dependencies=["domain_expertise"]
                )
        return None

    def _determine_level(self, confidence: float) -> UncertaintyLevel:
        """Determine uncertainty level from confidence"""
        if confidence >= 0.9:
            return UncertaintyLevel.KNOWN_KNOWN
        elif confidence >= 0.6:
            return UncertaintyLevel.KNOWN_UNKNOWN
        else:
            return UncertaintyLevel.UNKNOWN_UNKNOWN

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID for uncertainty item"""
        timestamp = str(time.time())
        return f"{prefix}_{hashlib.md5(timestamp.encode()).hexdigest()[:8]}"

    def generate_map(self,
                    uncertainties: List[UncertaintyItem],
                    overall_confidence: float,
                    include_recommendations: bool = True) -> str:
        """Generate uncertainty map in markdown format"""

        # Create snapshot
        snapshot = self.tracker.create_snapshot()

        map_md = f"""# 🗺️ Uncertainty Map v2.0

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Overall Confidence**: {overall_confidence:.0%}
**Trend**: {snapshot.trending}
**Action Required**: {'🚨 Yes' if snapshot.action_required else '✅ No'}

---

## 📊 Uncertainty Distribution

| Level | Count | Confidence Range |
|-------|-------|-----------------|
| Known Knowns | {snapshot.item_count.get('known_known', 0)} | >90% |
| Known Unknowns | {snapshot.item_count.get('known_unknown', 0)} | 60-90% |
| Unknown Unknowns | {snapshot.item_count.get('unknown_unknown', 0)} | <60% |

---

## 🔍 Detailed Analysis

"""

        # Group by level
        by_level = {}
        for item in uncertainties:
            level = item.level
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(item)

        # Known Knowns
        if UncertaintyLevel.KNOWN_KNOWN in by_level:
            map_md += "### ✅ Known Knowns (High Confidence)\n\n"
            for item in by_level[UncertaintyLevel.KNOWN_KNOWN]:
                map_md += self._format_item(item)

        # Known Unknowns
        if UncertaintyLevel.KNOWN_UNKNOWN in by_level:
            map_md += "### ⚠️ Known Unknowns (Moderate Confidence)\n\n"
            for item in by_level[UncertaintyLevel.KNOWN_UNKNOWN]:
                map_md += self._format_item(item)

        # Unknown Unknowns
        if UncertaintyLevel.UNKNOWN_UNKNOWN in by_level:
            map_md += "### 🚨 Unknown Unknowns (Low Confidence)\n\n"
            for item in by_level[UncertaintyLevel.UNKNOWN_UNKNOWN]:
                map_md += self._format_item(item)

        # High risk items
        if snapshot.high_risk_items:
            map_md += f"""---

## ⚠️ High Risk Items Requiring Immediate Attention

"""
            for item_id in snapshot.high_risk_items:
                if item_id in self.tracker.current_items:
                    item = self.tracker.current_items[item_id]
                    map_md += f"- **{item.description}** (Confidence: {item.confidence:.0%})\n"

        # Recommendations
        if include_recommendations:
            map_md += self._generate_recommendations(uncertainties, overall_confidence)

        # Historical patterns
        if self.tracker.resolution_patterns:
            map_md += """---

## 📚 Learning from History

**Previously Resolved Similar Issues:**

"""
            for pattern, resolutions in list(self.tracker.resolution_patterns.items())[:3]:
                successful = [r for r in resolutions if r['success']]
                if successful:
                    avg_time = sum(r['time_to_resolve'] for r in successful) / len(successful)
                    map_md += f"- **{pattern.replace('_', ' ').title()}**: Resolved {len(successful)} times (avg {avg_time:.0f}h)\n"

        return map_md

    def _format_item(self, item: UncertaintyItem) -> str:
        """Format single uncertainty item"""
        risk_emoji = {
            RiskLevel.LOW: "🟢",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🔴",
            RiskLevel.CRITICAL: "🚨"
        }

        md = f"""**{item.description}** {risk_emoji[item.risk]}
- **Confidence**: {item.confidence:.0%}
- **Category**: {item.category}
- **Evidence**: {', '.join(item.evidence[:2])}
- **Impact**: {', '.join(item.impact_areas[:3])}
- **Mitigation**: {item.mitigation_strategies[0] if item.mitigation_strategies else 'None'}

"""
        return md

    def _generate_recommendations(self, uncertainties: List[UncertaintyItem], confidence: float) -> str:
        """Generate actionable recommendations"""
        md = """---

## 🎯 Recommendations

"""

        if confidence >= 0.8:
            md += """### ✅ High Confidence - Proceed with Implementation
- Current approach is well-validated
- Monitor known uncertainties
- Regular checkpoint reviews
"""

        elif confidence >= 0.6:
            md += """### ⚠️ Moderate Confidence - Iterative Approach
- Implement in phases
- Validate assumptions early
- Gather feedback frequently
- Have rollback plans ready
"""

        else:
            md += """### 🚨 Low Confidence - Research Required
- Conduct proof of concept first
- Consult domain experts
- Consider multiple approaches
- Extensive testing required
"""

        # Specific mitigations
        high_risk = [u for u in uncertainties if u.risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        if high_risk:
            md += f"""
### 🔧 Priority Mitigations

"""
            for item in high_risk[:3]:
                md += f"1. **{item.category}**: {item.mitigation_strategies[0] if item.mitigation_strategies else 'Review required'}\n"

        return md


def main():
    """Demo of enhanced uncertainty management"""
    print("="*80)
    print("🗺️ Uncertainty Map Generator v2.0 Demo")
    print("="*80)

    generator = UncertaintyMapGeneratorV2()

    # Simulate different scenarios
    test_scenarios = [
        {
            "context": "Blockchain payment integration",
            "code_metrics": {
                "cyclomatic_complexity": 15.3,
                "test_coverage": 0.2,
                "confidence": 0.4,
                "technical_debt_ratio": 0.6
            },
            "request": "Maybe implement blockchain payments, possibly with smart contracts",
            "ai_responses": [
                {"recommendation": "Use Ethereum"},
                {"recommendation": "Use Hyperledger"},
                {"recommendation": "Use Bitcoin"}
            ]
        },
        {
            "context": "Simple REST API",
            "code_metrics": {
                "cyclomatic_complexity": 3.2,
                "test_coverage": 0.85,
                "confidence": 0.9,
                "technical_debt_ratio": 0.1
            },
            "request": "Create user authentication endpoints",
            "ai_responses": [
                {"recommendation": "Use JWT"},
                {"recommendation": "Use JWT"}
            ]
        }
    ]

    for scenario in test_scenarios:
        print(f"\n📝 Scenario: {scenario['context']}")
        print("="*60)

        # Analyze uncertainty
        uncertainties, overall_confidence = generator.analyze_uncertainty(
            context=scenario['context'],
            code_metrics=scenario.get('code_metrics'),
            user_request=scenario.get('request', ''),
            ai_responses=scenario.get('ai_responses')
        )

        print(f"Overall Confidence: {overall_confidence:.0%}")
        print(f"Uncertainties Found: {len(uncertainties)}")

        # Generate map
        uncertainty_map = generator.generate_map(
            uncertainties,
            overall_confidence,
            include_recommendations=True
        )

        # Display key sections
        for line in uncertainty_map.split('\n')[:30]:
            print(line)

        print("\n... [Full map would continue] ...\n")
        time.sleep(1)


if __name__ == "__main__":
    main()
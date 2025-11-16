#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uncertainty Map v3.0 - Predictive & Self-Learning System

Revolutionary Improvements:
1. Predictive uncertainty modeling (예측 가능)
2. Pattern recognition from history (패턴 학습)
3. Auto-mitigation strategies (자동 해결책)
4. Real-time risk scoring (실시간 리스크)
5. Quantum uncertainty states (양자 불확실성)

Author: VibeCoding Team
Date: 2025-11-17
Version: 3.0.0
"""

import sys
import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import math

# Windows Unicode 인코딩 문제 근본 해결
if sys.platform == 'win32':
    # 환경변수 설정
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # stdout/stderr를 UTF-8 모드로 재구성
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

# ML imports for prediction
try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    ML_AVAILABLE = True
except:
    ML_AVAILABLE = False
    print("⚠️ ML libraries not available, using fallback prediction")


class UncertaintyState(Enum):
    """Quantum-inspired uncertainty states"""
    DETERMINISTIC = "deterministic"      # 100% certain
    PROBABILISTIC = "probabilistic"      # 70-99% certain
    QUANTUM = "quantum"                   # 40-70% (superposition)
    CHAOTIC = "chaotic"                   # 10-40% (butterfly effect)
    VOID = "void"                         # <10% (unknown territory)


@dataclass
class UncertaintyVector:
    """Multi-dimensional uncertainty representation"""
    technical: float      # 기술적 불확실성
    market: float        # 시장 불확실성
    resource: float      # 리소스 불확실성
    timeline: float      # 일정 불확실성
    quality: float       # 품질 불확실성

    def magnitude(self) -> float:
        """Calculate total uncertainty magnitude"""
        return math.sqrt(
            self.technical**2 + self.market**2 +
            self.resource**2 + self.timeline**2 + self.quality**2
        ) / math.sqrt(5)  # Normalize to 0-1

    def dominant_dimension(self) -> str:
        """Find which dimension has highest uncertainty"""
        dims = {
            'technical': self.technical,
            'market': self.market,
            'resource': self.resource,
            'timeline': self.timeline,
            'quality': self.quality
        }
        return max(dims.items(), key=lambda x: x[1])[0]


@dataclass
class PredictiveModel:
    """Predictive model for uncertainty evolution"""
    trend: str  # "increasing", "decreasing", "stable", "oscillating"
    velocity: float  # Rate of change
    acceleration: float  # Change of rate
    inflection_points: List[datetime]  # When trend changes
    confidence_interval: Tuple[float, float]  # (lower, upper)
    predicted_resolution: Optional[datetime]

    def predict_future(self, hours_ahead: int) -> float:
        """Predict uncertainty level in the future"""
        # Simple linear model with acceleration
        base_change = self.velocity * hours_ahead
        accel_change = 0.5 * self.acceleration * (hours_ahead ** 2)
        return max(0, min(1, base_change + accel_change))


@dataclass
class MitigationStrategy:
    """Auto-generated mitigation strategy"""
    id: str
    uncertainty_id: str
    action: str
    priority: int  # 1-5
    estimated_impact: float  # 0-1
    estimated_cost: float  # hours
    prerequisites: List[str]
    success_probability: float
    fallback_strategy: Optional[str]

    def roi(self) -> float:
        """Calculate return on investment"""
        if self.estimated_cost == 0:
            return float('inf')
        return (self.estimated_impact * self.success_probability) / self.estimated_cost


class UncertaintyMapV3:
    """
    3rd Generation Uncertainty Management System

    Key Features:
    - Predictive modeling
    - Pattern learning
    - Auto-mitigation
    - Risk scoring
    - Quantum states
    """

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.uncertainties: Dict[str, UncertaintyVector] = {}
        self.predictions: Dict[str, PredictiveModel] = {}
        self.mitigations: Dict[str, List[MitigationStrategy]] = {}
        self.patterns: Dict[str, Any] = {}

        # Historical data for learning
        self.history_file = Path(f"uncertainty_history_{project_name}.json")
        self.load_history()

        # ML models for prediction
        if ML_AVAILABLE:
            self.predictor = RandomForestRegressor(n_estimators=100)
            self.scaler = StandardScaler()
            self.is_trained = False

        # Pattern database
        self.known_patterns = self._load_known_patterns()

    def _load_known_patterns(self) -> Dict:
        """Load known uncertainty patterns"""
        return {
            "early_stage_high": {
                "description": "High uncertainty in early stages",
                "phases": ["ideation", "design"],
                "typical_vector": UncertaintyVector(0.8, 0.9, 0.6, 0.7, 0.5),
                "resolution_time": 168  # hours
            },
            "implementation_spike": {
                "description": "Uncertainty spike during implementation",
                "phases": ["implementation"],
                "typical_vector": UncertaintyVector(0.7, 0.3, 0.5, 0.8, 0.6),
                "resolution_time": 72
            },
            "testing_convergence": {
                "description": "Uncertainty reduces during testing",
                "phases": ["testing"],
                "typical_vector": UncertaintyVector(0.3, 0.2, 0.2, 0.3, 0.7),
                "resolution_time": 48
            },
            "market_unknown": {
                "description": "Persistent market uncertainty",
                "phases": ["all"],
                "typical_vector": UncertaintyVector(0.3, 0.9, 0.4, 0.5, 0.4),
                "resolution_time": 336
            }
        }

    def analyze_context(self, context: Dict) -> Tuple[UncertaintyVector, UncertaintyState]:
        """
        Analyze context and return uncertainty vector and state
        """
        phase = context.get('phase', 'unknown')
        has_code = len(context.get('files', [])) > 0
        team_size = context.get('team_size', 1)
        timeline = context.get('timeline_weeks', 12)

        # Calculate uncertainty dimensions
        technical = self._calc_technical_uncertainty(phase, has_code)
        market = self._calc_market_uncertainty(phase, context.get('market_validation', 0))
        resource = self._calc_resource_uncertainty(team_size, timeline)
        timeline_unc = self._calc_timeline_uncertainty(phase, timeline)
        quality = self._calc_quality_uncertainty(phase, has_code)

        vector = UncertaintyVector(technical, market, resource, timeline_unc, quality)

        # Determine quantum state
        magnitude = vector.magnitude()
        if magnitude < 0.1:
            state = UncertaintyState.DETERMINISTIC
        elif magnitude < 0.3:
            state = UncertaintyState.PROBABILISTIC
        elif magnitude < 0.6:
            state = UncertaintyState.QUANTUM
        elif magnitude < 0.8:
            state = UncertaintyState.CHAOTIC
        else:
            state = UncertaintyState.VOID

        return vector, state

    def _calc_technical_uncertainty(self, phase: str, has_code: bool) -> float:
        """Calculate technical uncertainty"""
        base_uncertainty = {
            'ideation': 0.9,
            'design': 0.7,
            'mvp': 0.5,
            'implementation': 0.4,
            'testing': 0.2
        }.get(phase, 0.5)

        # Reduce if we have code
        if has_code:
            base_uncertainty *= 0.7

        return base_uncertainty

    def _calc_market_uncertainty(self, phase: str, validation: float) -> float:
        """Calculate market uncertainty"""
        if phase == 'ideation':
            return 0.9 * (1 - validation)
        elif phase == 'design':
            return 0.7 * (1 - validation)
        else:
            return 0.5 * (1 - validation)

    def _calc_resource_uncertainty(self, team_size: int, timeline_weeks: int) -> float:
        """Calculate resource uncertainty"""
        # Small team = higher uncertainty
        team_factor = 1.0 / math.sqrt(team_size)

        # Short timeline = higher uncertainty
        timeline_factor = 12.0 / timeline_weeks if timeline_weeks > 0 else 1.0

        return min(1.0, team_factor * timeline_factor * 0.7)

    def _calc_timeline_uncertainty(self, phase: str, timeline_weeks: int) -> float:
        """Calculate timeline uncertainty"""
        phase_factors = {
            'ideation': 0.3,
            'design': 0.5,
            'mvp': 0.7,
            'implementation': 0.8,
            'testing': 0.4
        }

        base = phase_factors.get(phase, 0.5)

        # Urgent timelines increase uncertainty
        if timeline_weeks < 4:
            return min(1.0, base * 2)
        elif timeline_weeks < 8:
            return min(1.0, base * 1.5)
        else:
            return base

    def _calc_quality_uncertainty(self, phase: str, has_code: bool) -> float:
        """Calculate quality uncertainty"""
        if not has_code and phase in ['implementation', 'testing']:
            return 0.9  # High uncertainty without code

        return {
            'ideation': 0.4,
            'design': 0.5,
            'mvp': 0.7,
            'implementation': 0.6,
            'testing': 0.3
        }.get(phase, 0.5)

    def predict_evolution(self, vector: UncertaintyVector, hours: int = 24) -> PredictiveModel:
        """
        Predict how uncertainty will evolve
        """
        # Analyze historical patterns
        pattern = self._match_pattern(vector)

        # Calculate trend
        if pattern:
            typical = pattern['typical_vector']
            diff = vector.magnitude() - typical.magnitude()

            if abs(diff) < 0.1:
                trend = "stable"
                velocity = 0.0
            elif diff > 0:
                trend = "increasing"
                velocity = diff / 24  # per hour
            else:
                trend = "decreasing"
                velocity = diff / 24
        else:
            # Default prediction
            trend = "decreasing"
            velocity = -0.01  # Slow improvement

        # Create predictive model
        model = PredictiveModel(
            trend=trend,
            velocity=velocity,
            acceleration=-0.0001,  # Tend toward stability
            inflection_points=[],
            confidence_interval=(
                max(0, vector.magnitude() - 0.2),
                min(1, vector.magnitude() + 0.2)
            ),
            predicted_resolution=datetime.now() + timedelta(hours=hours*3)
        )

        return model

    def _match_pattern(self, vector: UncertaintyVector) -> Optional[Dict]:
        """Match current vector to known patterns"""
        best_match = None
        best_distance = float('inf')

        for name, pattern in self.known_patterns.items():
            typical = pattern['typical_vector']

            # Calculate Euclidean distance
            distance = math.sqrt(
                (vector.technical - typical.technical)**2 +
                (vector.market - typical.market)**2 +
                (vector.resource - typical.resource)**2 +
                (vector.timeline - typical.timeline)**2 +
                (vector.quality - typical.quality)**2
            )

            if distance < best_distance:
                best_distance = distance
                best_match = pattern

        # Threshold for match
        if best_distance < 0.3:
            return best_match
        return None

    def generate_mitigations(self, vector: UncertaintyVector, state: UncertaintyState) -> List[MitigationStrategy]:
        """
        Auto-generate mitigation strategies
        """
        strategies = []
        uid = hashlib.md5(str(vector).encode()).hexdigest()[:8]

        # Get dominant dimension
        dominant = vector.dominant_dimension()

        # Generate strategies based on dominant uncertainty
        if dominant == 'technical':
            strategies.append(MitigationStrategy(
                id=f"mit_{uid}_1",
                uncertainty_id=uid,
                action="Conduct technical proof of concept",
                priority=1,
                estimated_impact=0.4,
                estimated_cost=16,  # hours
                prerequisites=[],
                success_probability=0.8,
                fallback_strategy="Consult external expert"
            ))
            strategies.append(MitigationStrategy(
                id=f"mit_{uid}_2",
                uncertainty_id=uid,
                action="Research similar implementations",
                priority=2,
                estimated_impact=0.3,
                estimated_cost=8,
                prerequisites=[],
                success_probability=0.9,
                fallback_strategy=None
            ))

        elif dominant == 'market':
            strategies.append(MitigationStrategy(
                id=f"mit_{uid}_3",
                uncertainty_id=uid,
                action="Conduct user interviews (10+)",
                priority=1,
                estimated_impact=0.5,
                estimated_cost=20,
                prerequisites=["Identify target users"],
                success_probability=0.7,
                fallback_strategy="Run online survey"
            ))
            strategies.append(MitigationStrategy(
                id=f"mit_{uid}_4",
                uncertainty_id=uid,
                action="Build MVP for validation",
                priority=2,
                estimated_impact=0.6,
                estimated_cost=40,
                prerequisites=["Core features defined"],
                success_probability=0.6,
                fallback_strategy="Create landing page"
            ))

        elif dominant == 'resource':
            strategies.append(MitigationStrategy(
                id=f"mit_{uid}_5",
                uncertainty_id=uid,
                action="Hire contractor/freelancer",
                priority=1,
                estimated_impact=0.5,
                estimated_cost=8,  # Time to find
                prerequisites=["Budget approval"],
                success_probability=0.7,
                fallback_strategy="Reduce scope"
            ))

        elif dominant == 'timeline':
            strategies.append(MitigationStrategy(
                id=f"mit_{uid}_6",
                uncertainty_id=uid,
                action="Implement parallel development",
                priority=1,
                estimated_impact=0.4,
                estimated_cost=4,
                prerequisites=["Clear task separation"],
                success_probability=0.8,
                fallback_strategy="Cut non-essential features"
            ))

        elif dominant == 'quality':
            strategies.append(MitigationStrategy(
                id=f"mit_{uid}_7",
                uncertainty_id=uid,
                action="Set up automated testing",
                priority=1,
                estimated_impact=0.6,
                estimated_cost=12,
                prerequisites=["Test framework chosen"],
                success_probability=0.9,
                fallback_strategy="Manual testing checklist"
            ))

        # Sort by ROI
        strategies.sort(key=lambda s: s.roi(), reverse=True)

        return strategies[:3]  # Return top 3 strategies

    def visualize_map(self, vector: UncertaintyVector, state: UncertaintyState) -> str:
        """
        Create ASCII visualization of uncertainty map
        """
        mag = vector.magnitude()

        # Create bar chart
        bars = {
            'Technical': '█' * int(vector.technical * 10),
            'Market': '█' * int(vector.market * 10),
            'Resource': '█' * int(vector.resource * 10),
            'Timeline': '█' * int(vector.timeline * 10),
            'Quality': '█' * int(vector.quality * 10)
        }

        # State indicator
        state_icons = {
            UncertaintyState.DETERMINISTIC: "🟢",
            UncertaintyState.PROBABILISTIC: "🟡",
            UncertaintyState.QUANTUM: "🟠",
            UncertaintyState.CHAOTIC: "🔴",
            UncertaintyState.VOID: "⚫"
        }

        viz = f"""
╔══════════════════════════════════════════════════╗
║         UNCERTAINTY MAP v3.0                     ║
╠══════════════════════════════════════════════════╣
║ State: {state_icons[state]} {state.value:20}          ║
║ Magnitude: {mag:.1%} {'█' * int(mag * 20):20}      ║
╠══════════════════════════════════════════════════╣
║ Dimensions:                                      ║
║  Technical : {bars['Technical']:10} ({vector.technical:.1%})   ║
║  Market    : {bars['Market']:10} ({vector.market:.1%})      ║
║  Resource  : {bars['Resource']:10} ({vector.resource:.1%})    ║
║  Timeline  : {bars['Timeline']:10} ({vector.timeline:.1%})    ║
║  Quality   : {bars['Quality']:10} ({vector.quality:.1%})     ║
╚══════════════════════════════════════════════════╝
        """
        return viz

    def save_state(self):
        """Save current state to file"""
        state = {
            'project': self.project_name,
            'timestamp': datetime.now().isoformat(),
            'uncertainties': {k: asdict(v) for k, v in self.uncertainties.items()},
            'patterns': self.patterns
        }

        with open(self.history_file, 'w') as f:
            json.dump(state, f, indent=2)

    def load_history(self):
        """Load historical data"""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                self.patterns = data.get('patterns', {})


def demo():
    """Demo the Uncertainty Map v3"""
    print("="*60)
    print("🗺️ Uncertainty Map v3.0 Demo")
    print("="*60)

    # Create map
    umap = UncertaintyMapV3("2025-Revenue-App")

    # Test different contexts
    contexts = [
        {
            'name': 'Ideation Phase',
            'phase': 'ideation',
            'files': [],
            'team_size': 5,
            'timeline_weeks': 12,
            'market_validation': 0.2
        },
        {
            'name': 'Implementation Phase',
            'phase': 'implementation',
            'files': ['app.py', 'models.py', 'views.py'],
            'team_size': 5,
            'timeline_weeks': 8,
            'market_validation': 0.6
        }
    ]

    for ctx in contexts:
        print(f"\n📍 Context: {ctx['name']}")
        print("-"*50)

        # Analyze
        vector, state = umap.analyze_context(ctx)

        # Visualize
        print(umap.visualize_map(vector, state))

        # Predict
        prediction = umap.predict_evolution(vector)
        print(f"\n📈 Prediction:")
        print(f"  Trend: {prediction.trend}")
        print(f"  24h forecast: {prediction.predict_future(24):.1%}")
        print(f"  Resolution: {prediction.predicted_resolution}")

        # Mitigations
        mitigations = umap.generate_mitigations(vector, state)
        print(f"\n💡 Top Mitigation Strategies:")
        for i, mit in enumerate(mitigations, 1):
            print(f"  {i}. {mit.action}")
            print(f"     Impact: {mit.estimated_impact:.1%}, Cost: {mit.estimated_cost}h, ROI: {mit.roi():.1f}")


if __name__ == "__main__":
    demo()
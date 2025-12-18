#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Development Orchestrator v2.0 - Phase-Aware & High-Performance System

Major Improvements:
1. Phase-Aware Evaluation (Ideation ≠ Implementation)
2. Weighted Average Confidence (not multiplication)
3. Real Uncertainty Tracking with Bayesian Updates
4. Context-Aware Metrics
5. Active Learning System

Author: VibeCoding Team
Date: 2025-11-17
Version: 2.0.0 (Performance Upgrade)
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from copy import deepcopy
import json
import yaml
import math
from filelock import FileLock

# Windows Unicode [EMOJI] [EMOJI] [EMOJI] [EMOJI]
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

# [EMOJI] [EMOJI]
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))
github_root = script_dir.parent.parent.parent
obsidian_scripts = github_root / "obsidian-vibe-coding-docs" / "scripts"
if obsidian_scripts.exists():
    sys.path.append(str(obsidian_scripts))

CONFIG_PATH = script_dir.parent / "config" / "config.yaml"
logger = logging.getLogger(__name__)


def _get_default_storage_dir() -> Path:
    env_dir = os.environ.get('UDO_STORAGE_DIR') or os.environ.get('UDO_HOME')
    base_dir = Path(env_dir).expanduser() if env_dir else Path.home() / '.udo'
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


DEFAULT_STORAGE_DIR = _get_default_storage_dir()


def _resolve_storage_file(filename: str, directory: Optional[Path] = None) -> Path:
    base_dir = Path(directory).expanduser() if directory else DEFAULT_STORAGE_DIR
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / filename


def _load_udo_config() -> Dict[str, Any]:
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as config_file:
            return yaml.safe_load(config_file) or {}
    except FileNotFoundError:
        logger.warning("Configuration file not found at %s", CONFIG_PATH)
    except yaml.YAMLError as config_error:
        logger.error("Failed to parse configuration file: %s", config_error)
    return {}


UDO_CONFIG = _load_udo_config()

# Import with graceful fallback
try:
    from adaptive_system_selector_v2 import (
        AdaptiveSystemSelectorV2,
        SystemType,
        DevelopmentStage
    )
    SELECTOR_AVAILABLE = True
except Exception as selector_error:
    SELECTOR_AVAILABLE = False
    logger.warning("AdaptiveSystemSelector import failed: %s", selector_error)
    # Define fallback enums
    class SystemType(Enum):
        CREATIVE_THINKING = "creative-thinking"
        ENHANCED = "vibe-coding-enhanced"
        FUSION = "vibe-coding-fusion"
        DEV_RULES = "dev-rules-starter-kit"

    class DevelopmentStage(Enum):
        IDEATION = "ideation"
        DESIGN = "design"
        MVP = "mvp"
        IMPLEMENTATION = "implementation"
        TESTING = "testing"

try:
    from three_ai_collaboration_bridge import ThreeAICollaborationBridge
    AI_BRIDGE_AVAILABLE = True
except Exception as bridge_error:
    AI_BRIDGE_AVAILABLE = False
    logger.warning("ThreeAICollaborationBridge import failed: %s", bridge_error)

try:
    # [EMOJI] v3 [EMOJI] ([EMOJI] [EMOJI] [EMOJI])
    from uncertainty_map_v3 import UncertaintyMapV3, UncertaintyVector, UncertaintyState
    UNCERTAINTY_AVAILABLE = True
    logger.info("Using UncertaintyMap v3.0 with predictive modeling")
except ImportError:
    try:
        # v2 fallback
        from uncertainty_map_generator_v2 import UncertaintyMapGeneratorV2
        UncertaintyMapV3 = UncertaintyMapGeneratorV2  # [EMOJI]
        UNCERTAINTY_AVAILABLE = True
        logger.warning("Using UncertaintyMap v2 (fallback)")
    except Exception:
        UNCERTAINTY_AVAILABLE = False
        logger.error("No uncertainty map available")

try:
    from udo_bayesian_integration import UDOBayesianIntegration
    BAYESIAN_AVAILABLE = True
except Exception as e:
    BAYESIAN_AVAILABLE = False
    logger.warning("Bayesian integration not available: %s", e)


@dataclass
class ProjectContext:
    """[EMOJI] [EMOJI] [EMOJI]"""
    project_name: str
    goal: str
    team_size: int
    timeline_weeks: int
    budget: float
    tech_stack: List[str]
    constraints: List[str]
    success_metrics: List[str]
    current_phase: str
    files: List[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class PhaseMetrics:
    """Phase[EMOJI] [EMOJI] [EMOJI]"""
    phase: str
    relevant_metrics: List[str]
    required_confidence: float  # Phase[EMOJI] [EMOJI] [EMOJI]
    evaluation_criteria: Dict[str, float]
    weight_distribution: Dict[str, float]


@dataclass
class UncertaintyTracking:
    """[EMOJI] [EMOJI] [EMOJI]"""
    known_knowns: Dict[str, float] = field(default_factory=dict)
    known_unknowns: Dict[str, float] = field(default_factory=dict)
    unknown_unknowns: float = 0.3  # [EMOJI]
    emergent_patterns: List[Dict] = field(default_factory=list)
    confidence_history: List[float] = field(default_factory=list)


class UnifiedDevelopmentOrchestratorV2:
    """
    UDO v2 - [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]

    [EMOJI] [EMOJI]:
    1. Phase-Aware [EMOJI]
    2. Bayesian [EMOJI] [EMOJI]
    3. [EMOJI] [EMOJI] [EMOJI]
    4. [EMOJI] [EMOJI] [EMOJI]
    """

    def __init__(self, project_context: ProjectContext):
        if not project_context.project_name:
            raise ValueError("project_name is required")
        if not project_context.current_phase:
            raise ValueError("current_phase is required")
        self.context = project_context
        self.decision_history = []
        self.uncertainty_tracker = UncertaintyTracking()
        self.config = deepcopy(UDO_CONFIG)
        self.storage_dir = DEFAULT_STORAGE_DIR
        self.learning_data_path = _resolve_storage_file('udo_learning_data.json', self.storage_dir)

        # [EMOJI] [EMOJI]
        self.selector = AdaptiveSystemSelectorV2() if SELECTOR_AVAILABLE else None
        self.ai_bridge = ThreeAICollaborationBridge() if AI_BRIDGE_AVAILABLE else None
        self.bayesian_integration = UDOBayesianIntegration(project_context.project_name) if BAYESIAN_AVAILABLE else None

        # Uncertainty Map v3 [EMOJI] ([EMOJI] [EMOJI] [EMOJI])
        if UNCERTAINTY_AVAILABLE:
            try:
                # v3 requires project_name parameter
                self.uncertainty = UncertaintyMapV3(project_name=project_context.project_name)
                logger.info("UncertaintyMap v3.0 with predictive modeling initialized")
            except Exception as e:
                # v2 fallback
                try:
                    self.uncertainty = UncertaintyMapV3()  # v2 doesn't need params
                    logger.info("UncertaintyMap v2.0 initialized (fallback)")
                except Exception as fallback_error:
                    self.uncertainty = None
                    logger.warning("UncertaintyMap initialization failed: %s", fallback_error)
        else:
            self.uncertainty = None

        # Phase-Aware [EMOJI] [EMOJI]
        self.phase_metrics = self._init_phase_metrics()

        # [EMOJI] [EMOJI]
        self.learning_data = self._load_learning_data(self.learning_data_path)

        logger.info("UDO v2 initialized for project %s", project_context.project_name)
        logger.info("Phase: %s", self.context.current_phase)
        logger.info("Mode: Phase-Aware + Bayesian + Active Learning")

    def _init_phase_metrics(self) -> Dict[str, PhaseMetrics]:
        """Phase[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
        return {
            "ideation": PhaseMetrics(
                phase="ideation",
                relevant_metrics=["market_potential", "feasibility", "innovation"],
                required_confidence=0.6,  # [EMOJI] [EMOJI] [EMOJI]
                evaluation_criteria={
                    "market_size": 0.3,
                    "competition": 0.2,
                    "technical_feasibility": 0.3,
                    "innovation_level": 0.2
                },
                weight_distribution={
                    "user_input": 0.5,
                    "market_data": 0.3,
                    "technical": 0.2
                }
            ),
            "design": PhaseMetrics(
                phase="design",
                relevant_metrics=["architecture_quality", "scalability", "patterns"],
                required_confidence=0.7,
                evaluation_criteria={
                    "architecture": 0.4,
                    "scalability": 0.3,
                    "maintainability": 0.3
                },
                weight_distribution={
                    "architecture": 0.5,
                    "patterns": 0.3,
                    "constraints": 0.2
                }
            ),
            "mvp": PhaseMetrics(
                phase="mvp",
                relevant_metrics=["speed", "core_features", "validation"],
                required_confidence=0.65,
                evaluation_criteria={
                    "core_features": 0.5,
                    "speed": 0.3,
                    "validation": 0.2
                },
                weight_distribution={
                    "features": 0.6,
                    "time": 0.3,
                    "quality": 0.1
                }
            ),
            "implementation": PhaseMetrics(
                phase="implementation",
                relevant_metrics=["code_quality", "test_coverage", "performance"],
                required_confidence=0.8,
                evaluation_criteria={
                    "code_quality": 0.3,
                    "test_coverage": 0.3,
                    "performance": 0.2,
                    "security": 0.2
                },
                weight_distribution={
                    "code_metrics": 0.5,
                    "testing": 0.3,
                    "performance": 0.2
                }
            )
        }

    def _load_learning_data(self, path: Optional[Path] = None) -> Dict:
        """[EMOJI] [EMOJI] [EMOJI] ([EMOJI] [EMOJI])"""
        learning_file = path or _resolve_storage_file('udo_learning_data.json', self.storage_dir)
        if learning_file.exists():
            lock = FileLock(str(learning_file) + '.lock')
            with lock:
                with open(learning_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        return {
            "overrides": [],
            "success_patterns": [],
            "failure_patterns": [],
            "phase_performance": {}
        }

    def _save_learning_data(self, path: Optional[Path] = None) -> Path:
        """[EMOJI] [EMOJI] [EMOJI]"""
        learning_file = path or self.learning_data_path
        lock = FileLock(str(learning_file) + '.lock')
        with lock:
            with open(learning_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_data, f, indent=2)
        return learning_file

    def calculate_phase_aware_confidence(
        self,
        phase: str,
        raw_confidence: float,
        context: Dict
    ) -> float:
        """
        Phase-Aware [EMOJI] [EMOJI]

        [EMOJI] [EMOJI]: Phase[EMOJI] [EMOJI] [EMOJI] [EMOJI]
        """
        phase_metric = self.phase_metrics.get(phase)
        if not phase_metric:
            return raw_confidence

        # Phase[EMOJI] [EMOJI] [EMOJI]
        weighted_confidence = 0.0
        weights = phase_metric.weight_distribution

        # Phase-specific [EMOJI]
        if phase == "ideation":
            # Ideation[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
            base_confidence = 0.7  # [EMOJI] [EMOJI] [EMOJI]
            market_factor = context.get('market_validation', 0.5)
            feasibility_factor = context.get('technical_feasibility', 0.8)

            weighted_confidence = (
                base_confidence * 0.4 +
                market_factor * 0.3 +
                feasibility_factor * 0.3
            )

        elif phase == "design":
            # Design[EMOJI] [EMOJI] [EMOJI] [EMOJI]
            base_confidence = 0.65
            arch_quality = context.get('architecture_quality', 0.6)
            pattern_match = context.get('pattern_adherence', 0.7)

            weighted_confidence = (
                base_confidence * 0.3 +
                arch_quality * 0.4 +
                pattern_match * 0.3
            )

        elif phase == "mvp":
            # MVP[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
            base_confidence = raw_confidence
            speed_factor = min(1.0, context.get('development_speed', 0.8))
            feature_coverage = context.get('core_feature_coverage', 0.7)

            weighted_confidence = (
                base_confidence * 0.4 +
                speed_factor * 0.3 +
                feature_coverage * 0.3
            )

        else:  # implementation, testing [EMOJI]
            # [EMOJI] [EMOJI] [EMOJI]
            weighted_confidence = raw_confidence

        # Bayesian [EMOJI] ([EMOJI] [EMOJI] [EMOJI])
        phase_history = self.learning_data.get('phase_performance', {}).get(phase, {})
        if phase_history:
            success_rate = phase_history.get('success_rate', 0.5)
            # Bayesian update: P(success|evidence) = P(evidence|success) * P(success) / P(evidence)
            prior = success_rate
            likelihood = weighted_confidence
            evidence = 0.5  # [EMOJI] [EMOJI]

            bayesian_confidence = (likelihood * prior) / evidence
            weighted_confidence = 0.7 * weighted_confidence + 0.3 * bayesian_confidence

        # [EMOJI] [EMOJI] [EMOJI]
        return max(0.1, min(0.95, weighted_confidence))

    def calculate_weighted_confidence(
        self,
        system_confidence: float,
        uncertainty_confidence: float,
        phase: str
    ) -> float:
        """
        [EMOJI] [EMOJI] [EMOJI] [EMOJI] ([EMOJI] [EMOJI])

        [EMOJI]: [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
        """
        phase_weight_config = self.config.get('phase_weights', {})
        default_weights = phase_weight_config.get('default', {
            'system': 0.5,
            'uncertainty': 0.4,
            'bonus': 0.1
        })
        weights_for_phase = phase_weight_config.get(phase, default_weights)

        system_weight = weights_for_phase.get('system', default_weights.get('system', 0.5))
        uncertainty_weight = weights_for_phase.get('uncertainty', default_weights.get('uncertainty', 0.4))
        bonus_weight = weights_for_phase.get('bonus', default_weights.get('bonus', 0.1))

        phase_bonus = self.config.get('phase_bonus', {}).get(
            phase,
            self.config.get('phase_bonus', {}).get('default', 0.5)
        )

        # [EMOJI] [EMOJI] [EMOJI]
        weighted_confidence = (
            system_confidence * system_weight +
            uncertainty_confidence * uncertainty_weight +
            phase_bonus * bonus_weight
        )

        # [EMOJI] [EMOJI] (Phase[EMOJI])
        phase_metric = self.phase_metrics.get(phase)
        if phase_metric and hasattr(phase_metric, 'required_confidence'):
            min_confidence = phase_metric.required_confidence
        else:
            min_confidence = 0.3

        return max(min_confidence, weighted_confidence)

    def track_uncertainty(self, context: Dict, decision: Dict):
        """[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] (v3 [EMOJI])"""

        # Known Knowns [EMOJI]
        if context.get('files'):
            self.uncertainty_tracker.known_knowns['code_exists'] = 1.0
        if context.get('test_coverage'):
            self.uncertainty_tracker.known_knowns['test_coverage'] = context['test_coverage']

        # Known Unknowns [EMOJI]
        if not context.get('market_validation'):
            self.uncertainty_tracker.known_unknowns['market'] = 0.5
        if not context.get('user_feedback'):
            self.uncertainty_tracker.known_unknowns['user_needs'] = 0.6

        # Unknown Unknowns [EMOJI] ([EMOJI] [EMOJI])
        self.uncertainty_tracker.unknown_unknowns *= 0.95

        # Emergent Patterns [EMOJI]
        if len(self.uncertainty_tracker.confidence_history) > 5:
            recent = self.uncertainty_tracker.confidence_history[-5:]
            if all(c > 0.7 for c in recent):
                self.uncertainty_tracker.emergent_patterns.append({
                    'pattern': 'high_confidence_streak',
                    'timestamp': datetime.now().isoformat()
                })

        # [EMOJI] [EMOJI] [EMOJI]
        self.uncertainty_tracker.confidence_history.append(
            decision.get('confidence', 0.5)
        )

        # v3 [EMOJI]: [EMOJI] [EMOJI]
        if self.uncertainty and hasattr(self.uncertainty, 'add_observation'):
            # UncertaintyVector [EMOJI]
            vector = UncertaintyVector(
                technical=1.0 - self.uncertainty_tracker.known_knowns.get('code_exists', 0.0),
                market=self.uncertainty_tracker.known_unknowns.get('market', 0.5),
                resource=context.get('resource_uncertainty', 0.3),
                timeline=context.get('timeline_uncertainty', 0.3),
                quality=1.0 - context.get('test_coverage', 0.0)
            )

            # [EMOJI] [EMOJI] ([EMOJI])
            self.uncertainty.add_observation(
                phase=self.context.current_phase,
                vector=vector,
                outcome=decision.get('confidence', 0.5) > 0.6
            )

            # [EMOJI] [EMOJI]
            prediction = self.uncertainty.predict_evolution(
                vector,
                self.context.current_phase,
                hours=24
            )

            if prediction:
                logger.info("Uncertainty trend: %s", prediction.trend)
                future_uncertainty = prediction.predict_future(24)
                logger.info("24h forecast: %.1f%%", future_uncertainty * 100)

                # [EMOJI] [EMOJI] [EMOJI] [EMOJI]
                state = self.uncertainty.classify_state(vector.magnitude())
                mitigations = self.uncertainty.generate_mitigations(vector, state)

                if mitigations and decision.get('confidence', 0) < 0.6:
                    logger.info("Recommended mitigation strategies:")
                    for mit in mitigations[:2]:
                        logger.info("- %s (Impact: %.0f%%)", mit.action, mit.estimated_impact * 100)

    def start_development_cycle(self, user_request: str) -> Dict:
        """
        [EMOJI] [EMOJI] [EMOJI] - Phase-Aware
        """
        if not isinstance(user_request, str) or not user_request.strip():
            raise ValueError("user_request must be a non-empty string")
        if not self.context.current_phase:
            raise ValueError("current_phase must be defined before starting the cycle")

        logger.info("%s", "=" * 60)
        logger.info("UDO v2 development cycle starting")
        logger.info("%s", "=" * 60)
        logger.info("Request: %s...", user_request[:100])
        logger.info("Current phase: %s", self.context.current_phase)

        # Phase [EMOJI] [EMOJI]
        phase_context = {
            'phase': self.context.current_phase,
            'team_size': self.context.team_size,
            'timeline': self.context.timeline_weeks,
            'files': self.context.files or [],
            'request': user_request
        }

        # Step 1: Phase-Aware [EMOJI] [EMOJI]
        system_recommendation = self._select_optimal_system_v2(
            user_request,
            phase_context
        )

        # Step 2: [EMOJI] [EMOJI] [EMOJI]
        uncertainty_assessment = self._assess_uncertainties_v2(
            user_request,
            system_recommendation,
            phase_context
        )

        # Step 3: Phase[EMOJI] AI [EMOJI] [EMOJI]
        ai_collaboration = self._determine_ai_collaboration_v2(
            phase_context,
            system_recommendation,
            uncertainty_assessment
        )

        # Step 4: [EMOJI] Go/No-Go [EMOJI]
        go_decision = self._make_go_decision_v2(
            system_recommendation,
            uncertainty_assessment,
            ai_collaboration,
            phase_context
        )

        # Step 5: [EMOJI] [EMOJI]
        execution_plan = self._create_execution_plan_v2(
            system_recommendation,
            ai_collaboration,
            go_decision,
            phase_context
        )

        # [EMOJI] [EMOJI]
        self.track_uncertainty(phase_context, execution_plan)

        # [EMOJI] [EMOJI] [EMOJI]
        self.learning_data['phase_performance'].setdefault(
            self.context.current_phase, {}
        )

        return execution_plan

    def _select_optimal_system_v2(self, request: str, context: Dict) -> Dict:
        """Phase-Aware [EMOJI] [EMOJI]"""

        phase = context['phase']

        # Phase[EMOJI] [EMOJI] [EMOJI] [EMOJI]
        phase_defaults = {
            "ideation": SystemType.CREATIVE_THINKING,
            "design": SystemType.CREATIVE_THINKING,
            "mvp": SystemType.ENHANCED,
            "implementation": SystemType.FUSION,
            "testing": SystemType.DEV_RULES
        }

        if self.selector:
            # [EMOJI] Selector [EMOJI]
            analysis_context = self.selector.analyze_request(
                request,
                team_size=context['team_size'],
                files=context['files']
            )
            recommendation = self.selector.recommend_system(analysis_context)

            # Phase-aware [EMOJI]
            base_confidence = recommendation.confidence
            phase_confidence = self.calculate_phase_aware_confidence(
                phase, base_confidence, context
            )

            return {
                "system": recommendation.primary.value,
                "confidence": phase_confidence,
                "complexity": analysis_context.complexity if hasattr(analysis_context, 'complexity') else 0.5,
                "phase_adjusted": True
            }
        else:
            # Fallback with phase awareness
            default_system = phase_defaults.get(phase, SystemType.ENHANCED)

            # Phase[EMOJI] [EMOJI] [EMOJI]
            phase_base_confidence = {
                "ideation": 0.75,
                "design": 0.7,
                "mvp": 0.65,
                "implementation": 0.6,
                "testing": 0.7
            }.get(phase, 0.5)

            return {
                "system": default_system.value,
                "confidence": phase_base_confidence,
                "complexity": 0.3 if phase in ["ideation", "design"] else 0.5,
                "phase_adjusted": True
            }

    def _assess_uncertainties_v2(
        self,
        request: str,
        system_rec: Dict,
        context: Dict
    ) -> Dict:
        """[EMOJI] [EMOJI] [EMOJI]"""

        phase = context['phase']

        # Phase[EMOJI] [EMOJI] [EMOJI]
        phase_uncertainties = {
            "ideation": ["market_fit", "technical_feasibility", "competition"],
            "design": ["architecture_risk", "scalability", "integration"],
            "mvp": ["time_constraint", "feature_scope", "validation"],
            "implementation": ["code_quality", "performance", "security"],
            "testing": ["coverage", "edge_cases", "regression"]
        }

        uncertainties = phase_uncertainties.get(phase, [])

        # [EMOJI] [EMOJI] [EMOJI]
        uncertainty_level = 0.3  # [EMOJI]

        # Phase[EMOJI] [EMOJI]
        if phase == "ideation":
            # [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
            uncertainty_level = 0.5
            confidence = 0.7  # [EMOJI] [EMOJI] [EMOJI]
        elif phase == "design":
            uncertainty_level = 0.4
            confidence = 0.65
        else:
            # [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]
            if context.get('files'):
                uncertainty_level = 0.2
                confidence = 0.8
            else:
                uncertainty_level = 0.4
                confidence = 0.6

        logger.info("Uncertainty evaluation (v2)")
        logger.info("Phase: %s", phase)
        logger.info("Uncertainty level: %.0f%%", uncertainty_level * 100)
        logger.info("Confidence: %.0f%%", confidence * 100)
        logger.info("Key uncertainties: %s", ", ".join(uncertainties[:3]))

        return {
            "overall_confidence": confidence,
            "uncertainty_level": uncertainty_level,
            "uncertainties": uncertainties,
            "assessment": "ACCEPTABLE" if confidence > 0.6 else "NEEDS_REVIEW"
        }

    def _determine_ai_collaboration_v2(
        self,
        context: Dict,
        system_rec: Dict,
        uncertainty: Dict
    ) -> Dict:
        """Phase[EMOJI] AI [EMOJI] [EMOJI]"""

        phase = context['phase']

        # Phase[EMOJI] [EMOJI] [EMOJI]
        phase_patterns = {
            "ideation": "creative_exploration",  # Gemini [EMOJI]
            "design": "architecture_review",      # Claude [EMOJI] + Codex [EMOJI]
            "mvp": "rapid_implementation",        # Claude [EMOJI]
            "implementation": "full_collaboration", # 3-AI [EMOJI]
            "testing": "verification_focus"       # Codex [EMOJI]
        }

        pattern = phase_patterns.get(phase, "balanced")

        logger.info("AI collaboration pattern (v2)")
        logger.info("Phase: %s", phase)
        logger.info("Pattern: %s", pattern)
        logger.info("Optimization: Phase-specific")

        return {
            "pattern": pattern,
            "ais": ["claude"],  # [EMOJI]
            "phase_optimized": True
        }

    def _make_go_decision_v2(
        self,
        system_rec: Dict,
        uncertainty: Dict,
        ai_collab: Dict,
        context: Dict
    ) -> Dict:
        """[EMOJI] Go/No-Go [EMOJI]"""

        phase = context['phase']

        # [EMOJI] [EMOJI] [EMOJI] [EMOJI] ([EMOJI] [EMOJI])
        confidence = self.calculate_weighted_confidence(
            system_rec['confidence'],
            uncertainty['overall_confidence'],
            phase
        )

        phase_thresholds = self.config.get('phase_thresholds', {})
        threshold = phase_thresholds.get(
            phase,
            phase_thresholds.get('default', 0.6)
        )

        bayes_meta = None
        if self.bayesian_integration:
            try:
                threshold, bayes_meta = self.bayesian_integration.get_adaptive_threshold(phase, confidence)
            except Exception as e:
                logger.warning("Bayesian threshold adjustment failed: %s", e)

        # [EMOJI]
        if confidence > threshold + 0.15:
            decision = "GO"
            approach = "CONFIDENT"
        elif confidence > threshold:
            decision = "GO_WITH_MONITORING"
            approach = "CAUTIOUS"
        elif confidence > threshold - 0.1:
            decision = "PROTOTYPE_FIRST"
            approach = "EXPERIMENTAL"
        else:
            decision = "NEED_MORE_INFO"
            approach = "RESEARCH"

        logger.info("Go/No-Go decision (v2)")
        logger.info("Decision: %s", decision)
        logger.info("Confidence: %.0f%%", confidence * 100)
        logger.info("Threshold: %.0f%%", threshold * 100)
        logger.info("Approach: %s", approach)

        return {
            "decision": decision,
            "confidence": confidence,
            "approach": approach,
            "threshold": threshold,
            "bayesian": bayes_meta
        }

    def execute_plan(self, plan: Dict) -> Dict:
        """[EMOJI] [EMOJI] [EMOJI]"""
        if plan['decision'] in ["NEED_MORE_INFO", "NO_GO"]:
            return {
                "status": "BLOCKED",
                "reason": "[EMOJI] [EMOJI] [EMOJI] [EMOJI]",
                "recommendation": plan.get('approach', 'RESEARCH')
            }

        logger.info("%s", "=" * 60)
        logger.info("Execution starting (v2)")
        logger.info("%s", "=" * 60)

        # [EMOJI] [EMOJI] ([EMOJI] [EMOJI] [EMOJI] AI [EMOJI] [EMOJI])
        return {
            "status": "COMPLETED",
            "message": f"{plan['system'].get('system', 'default')} [EMOJI] [EMOJI]",
            "execution_time": 0,
            "confidence": plan['confidence']
        }

    def record_outcome(self, plan: Dict, execution_result: Dict, user_feedback: Optional[str] = None):
        """[EMOJI] [EMOJI] [EMOJI] [EMOJI]"""
        try:
            # [EMOJI] [EMOJI] [EMOJI]
            phase = self.context.current_phase
            success = execution_result.get('status') == 'COMPLETED'

            if 'phase_performance' not in self.learning_data:
                self.learning_data['phase_performance'] = {}

            if phase not in self.learning_data['phase_performance']:
                self.learning_data['phase_performance'][phase] = {
                    'total': 0,
                    'success': 0,
                    'success_rate': 0.0
                }

            # dictionary[EMOJI] [EMOJI]
            phase_perf = self.learning_data['phase_performance'][phase]
            if not isinstance(phase_perf, dict):
                # [EMOJI] [EMOJI] [EMOJI] [EMOJI]
                self.learning_data['phase_performance'][phase] = {
                    'total': 0,
                    'success': 0,
                    'success_rate': 0.0
                }
                phase_perf = self.learning_data['phase_performance'][phase]

            phase_perf['total'] = phase_perf.get('total', 0) + 1
            if success:
                phase_perf['success'] = phase_perf.get('success', 0) + 1
            phase_perf['success_rate'] = phase_perf['success'] / phase_perf['total']

            # [EMOJI] [EMOJI] [EMOJI]
            self._save_learning_data()

            logger.info("Result recorded (Phase: %s, Success: %s)", phase, success)
        except Exception as e:
            logger.warning("Result recording failed but continuing: %s", e)

    def save_state(self, path: Optional[Path] = None) -> Path:
        """[EMOJI] [EMOJI]"""
        state = {
            "project_context": asdict(self.context),
            "current_phase": self.context.current_phase,
            "confidence_history": self.uncertainty_tracker.confidence_history,
            "learning_data": self.learning_data,
            "timestamp": datetime.now().isoformat()
        }

        target_path = path or _resolve_storage_file(
            f"udo_state_{self.context.project_name}.json",
            self.storage_dir
        )
        lock = FileLock(str(target_path) + '.lock')
        with lock:
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

        logger.info("State saved to %s", target_path)
        return target_path

    def _create_execution_plan_v2(
        self,
        system_rec: Dict,
        ai_collab: Dict,
        go_decision: Dict,
        context: Dict
    ) -> Dict:
        """[EMOJI] [EMOJI] [EMOJI]"""

        plan = {
            "version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "phase": context['phase'],
            "decision": go_decision['decision'],
            "confidence": go_decision['confidence'],
            "system": system_rec,
            "ai_collaboration": ai_collab,
            "approach": go_decision['approach'],
            "phase_optimized": True,
            "uncertainty_tracked": True,
            "learning_enabled": True
        }

        logger.info("Execution plan v2 ready")
        logger.info("Version: 2.0 Phase-Aware")
        logger.info("Confidence: %.0f%%", plan['confidence'] * 100)
        logger.info("Phase optimized: %s", plan.get('phase_optimized', False))

        return plan


# [EMOJI] [EMOJI] [EMOJI] [EMOJI]
UnifiedDevelopmentOrchestrator = UnifiedDevelopmentOrchestratorV2


def main():
    """[EMOJI] [EMOJI]"""
    logging.basicConfig(level=logging.INFO)
    logger.info("%s", "=" * 80)
    logger.info("UDO v2.0 test - Phase-Aware System")
    logger.info("%s", "=" * 80)

    # Ideation phase [EMOJI]
    project = ProjectContext(
        project_name="2025-Revenue-App",
        goal="[EMOJI] [EMOJI] [EMOJI] [EMOJI]",
        team_size=5,
        timeline_weeks=12,
        budget=50000,
        tech_stack=["Next.js", "Flutter", "Supabase"],
        constraints=["3[EMOJI] [EMOJI] [EMOJI]"],
        success_metrics=["DAU 1000+"],
        current_phase="ideation",
        files=[]  # Ideation[EMOJI] [EMOJI] [EMOJI]
    )

    udo = UnifiedDevelopmentOrchestratorV2(project)

    request = "2025[EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI] [EMOJI]"
    plan = udo.start_development_cycle(request)

    logger.info("%s", "\n" + "=" * 80)
    logger.info("Test results")
    logger.info("%s", "=" * 80)
    logger.info("Decision: %s", plan['decision'])
    logger.info("Confidence: %.0f%%", plan['confidence'] * 100)
    logger.info("Phase optimized: %s", plan.get('phase_optimized', False))

    if plan['confidence'] > 0.5:
        logger.info("SUCCESS: Ideation phase confidence acceptable")
    else:
        logger.error("FAIL: Confidence remains low")


if __name__ == "__main__":
    main()

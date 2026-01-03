#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML Training System - 기계학습 기반 패턴 인식 및 예측 시스템
RandomForest 기반 불확실성 예측 모델
"""

import sys
import os
import json
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import logging
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, accuracy_score, r2_score
import joblib
from filelock import FileLock

# Windows Unicode 인코딩 문제 해결
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _resolve_model_dir(custom_dir: Optional[Any] = None) -> Path:
    base = custom_dir if custom_dir is not None else os.environ.get("UDO_MODEL_DIR")
    target = Path(base).expanduser() if base is not None else Path.home() / ".udo" / "models"
    target.mkdir(parents=True, exist_ok=True)
    return target


@dataclass
class TrainingData:
    """훈련 데이터 구조"""

    features: np.ndarray
    labels: np.ndarray
    metadata: Dict[str, Any]
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ModelMetrics:
    """모델 성능 메트릭"""

    accuracy: float
    mse: float
    r2: float
    cross_val_scores: List[float]
    feature_importance: Dict[str, float]
    training_time: float


class MLTrainingSystem:
    """ML 훈련 시스템"""

    def __init__(self, model_dir: Optional[Any] = None):
        self.model_dir = _resolve_model_dir(model_dir)

        self.models = {}
        self.scalers = {}
        self.training_history = []
        self.feature_names = []

        # 기본 모델 초기화
        self._initialize_models()

    def _initialize_models(self):
        """기본 모델 초기화"""
        # 불확실성 예측 모델
        self.models["uncertainty_predictor"] = RandomForestRegressor(
            n_estimators=100, max_depth=10, min_samples_split=5, min_samples_leaf=2, random_state=42
        )

        # Phase 분류 모델
        self.models["phase_classifier"] = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)

        # 신뢰도 예측 모델
        self.models["confidence_predictor"] = RandomForestRegressor(
            n_estimators=150, max_depth=15, min_samples_split=3, random_state=42
        )

        # 각 모델용 스케일러
        for model_name in self.models.keys():
            self.scalers[model_name] = StandardScaler()

        logger.info(f"Initialized {len(self.models)} ML models")

    def prepare_features(self, raw_data: Dict) -> np.ndarray:
        """원시 데이터를 특징 벡터로 변환"""
        features = []

        # Phase 인코딩
        phase_mapping = {"ideation": 0, "design": 1, "mvp": 2, "implementation": 3, "testing": 4}
        features.append(phase_mapping.get(raw_data.get("phase", "ideation"), 0))

        # 시간적 특징
        features.append(raw_data.get("timeline_weeks", 12))
        features.append(raw_data.get("team_size", 5))
        features.append(raw_data.get("budget", 50000) / 10000)  # 스케일링

        # 불확실성 차원들
        features.append(raw_data.get("technical_uncertainty", 0.5))
        features.append(raw_data.get("market_uncertainty", 0.5))
        features.append(raw_data.get("resource_uncertainty", 0.3))
        features.append(raw_data.get("timeline_uncertainty", 0.3))
        features.append(raw_data.get("quality_uncertainty", 0.4))

        # 기타 메트릭
        features.append(raw_data.get("code_complexity", 0.5))
        features.append(raw_data.get("test_coverage", 0.0))
        features.append(raw_data.get("architecture_quality", 0.7))
        features.append(len(raw_data.get("files", [])))
        features.append(len(raw_data.get("dependencies", [])))

        # Feature names 저장 (첫 번째 호출시만)
        if not self.feature_names:
            self.feature_names = [
                "phase",
                "timeline_weeks",
                "team_size",
                "budget_scaled",
                "tech_uncertainty",
                "market_uncertainty",
                "resource_uncertainty",
                "timeline_uncertainty",
                "quality_uncertainty",
                "code_complexity",
                "test_coverage",
                "architecture_quality",
                "file_count",
                "dependency_count",
            ]

        return np.array(features).reshape(1, -1)

    def train_model(self, model_name: str, training_data: TrainingData, test_size: float = 0.2) -> ModelMetrics:
        """모델 훈련"""
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")

        logger.info(f"Training {model_name}...")
        start_time = datetime.now()

        # 데이터 분할
        X_train, X_test, y_train, y_test = train_test_split(
            training_data.features, training_data.labels, test_size=test_size, random_state=42
        )

        # 스케일링
        X_train_scaled = self.scalers[model_name].fit_transform(X_train)
        X_test_scaled = self.scalers[model_name].transform(X_test)

        # 모델 훈련
        self.models[model_name].fit(X_train_scaled, y_train)

        # 예측
        y_pred = self.models[model_name].predict(X_test_scaled)

        # 메트릭 계산
        if hasattr(self.models[model_name], "predict_proba"):
            # 분류 모델
            accuracy = accuracy_score(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            r2 = 0.0  # 분류에는 R2 사용 안함
        else:
            # 회귀 모델
            accuracy = 0.0  # 회귀에는 정확도 사용 안함
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

        # 교차 검증
        cv_scores = cross_val_score(self.models[model_name], X_train_scaled, y_train, cv=5)

        # 특징 중요도
        feature_importance = {}
        if hasattr(self.models[model_name], "feature_importances_"):
            importances = self.models[model_name].feature_importances_
            for i, name in enumerate(self.feature_names[: len(importances)]):
                feature_importance[name] = float(importances[i])

        # 훈련 시간
        training_time = (datetime.now() - start_time).total_seconds()

        # 메트릭 생성
        metrics = ModelMetrics(
            accuracy=accuracy,
            mse=mse,
            r2=r2,
            cross_val_scores=cv_scores.tolist(),
            feature_importance=feature_importance,
            training_time=training_time,
        )

        # 히스토리 저장
        self.training_history.append(
            {
                "model": model_name,
                "timestamp": datetime.now().isoformat(),
                "metrics": asdict(metrics),
                "data_size": len(training_data.features),
            }
        )

        logger.info(f"Training completed: R2={r2:.3f}, MSE={mse:.3f}")

        return metrics

    def predict(self, model_name: str, input_data: Dict) -> Tuple[float, Dict]:
        """예측 수행"""
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")

        # 특징 준비
        features = self.prepare_features(input_data)

        # 스케일링
        if model_name in self.scalers:
            try:
                features_scaled = self.scalers[model_name].transform(features)
            except:
                # 스케일러가 아직 fit되지 않은 경우
                features_scaled = features
        else:
            features_scaled = features

        # 예측
        prediction = self.models[model_name].predict(features_scaled)[0]

        # 예측 확률 (분류 모델의 경우)
        probabilities = {}
        if hasattr(self.models[model_name], "predict_proba"):
            proba = self.models[model_name].predict_proba(features_scaled)[0]
            probabilities = {i: float(p) for i, p in enumerate(proba)}

        # 메타데이터
        metadata = {
            "model": model_name,
            "timestamp": datetime.now().isoformat(),
            "features_used": self.feature_names,
            "probabilities": probabilities,
        }

        return float(prediction), metadata

    def generate_synthetic_data(self, size: int = 1000) -> TrainingData:
        """합성 훈련 데이터 생성"""
        np.random.seed(42)

        features = []
        labels = []

        for _ in range(size):
            # 랜덤 Phase
            phase = np.random.randint(0, 5)

            # 랜덤 프로젝트 특징
            timeline = np.random.randint(4, 52)
            team_size = np.random.randint(1, 20)
            budget = np.random.uniform(10000, 500000) / 10000

            # 랜덤 불확실성
            uncertainties = np.random.uniform(0, 1, 5)

            # 기타 메트릭
            complexity = np.random.uniform(0, 1)
            coverage = np.random.uniform(0, 1)
            quality = np.random.uniform(0, 1)
            files = np.random.randint(0, 100)
            deps = np.random.randint(0, 50)

            # 특징 벡터
            feature_vector = np.concatenate(
                [[phase, timeline, team_size, budget], uncertainties, [complexity, coverage, quality, files, deps]]
            )
            features.append(feature_vector)

            # 레이블 (신뢰도 - 간단한 규칙 기반)
            confidence = 0.5
            confidence += (1 - uncertainties.mean()) * 0.3  # 낮은 불확실성
            confidence += coverage * 0.2  # 높은 테스트 커버리지
            confidence += quality * 0.1  # 높은 품질
            confidence = np.clip(confidence, 0, 1)
            labels.append(confidence)

        return TrainingData(features=np.array(features), labels=np.array(labels), metadata={"synthetic": True, "size": size})

    def save_models(self, directory: Optional[Any] = None) -> Dict[str, Path]:
        """모든 모델 저장"""
        target_dir = _resolve_model_dir(directory or self.model_dir)
        saved_paths: Dict[str, Path] = {}
        for model_name, model in self.models.items():
            model_path = target_dir / f"{model_name}.pkl"
            lock = FileLock(str(model_path) + ".lock")
            with lock:
                joblib.dump(model, model_path)
            saved_paths[model_name] = model_path

            if model_name in self.scalers:
                scaler_path = target_dir / f"{model_name}_scaler.pkl"
                scaler_lock = FileLock(str(scaler_path) + ".lock")
                with scaler_lock:
                    joblib.dump(self.scalers[model_name], scaler_path)

        history_path = target_dir / "training_history.json"
        history_lock = FileLock(str(history_path) + ".lock")
        with history_lock:
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(self.training_history, f, indent=2)

        logger.info("Saved %d models to %s", len(self.models), target_dir)
        return saved_paths

    def load_models(self):
        """저장된 모델 로드"""
        loaded = 0
        for model_file in self.model_dir.glob("*.pkl"):
            if "_scaler" not in model_file.stem:
                model_name = model_file.stem
                self.models[model_name] = joblib.load(model_file)

                # 스케일러 로드
                scaler_file = self.model_dir / f"{model_name}_scaler.pkl"
                if scaler_file.exists():
                    self.scalers[model_name] = joblib.load(scaler_file)

                loaded += 1

        # 훈련 히스토리 로드
        history_path = self.model_dir / "training_history.json"
        if history_path.exists():
            with open(history_path, "r") as f:
                self.training_history = json.load(f)

        logger.info(f"Loaded {loaded} models from {self.model_dir}")

    def get_model_report(self) -> Dict:
        """모델 상태 보고서"""
        report = {"models": {}, "training_history": len(self.training_history), "last_training": None}

        for model_name, model in self.models.items():
            report["models"][model_name] = {
                "type": model.__class__.__name__,
                "trained": hasattr(model, "n_features_in_"),
                "features": getattr(model, "n_features_in_", 0),
            }

        if self.training_history:
            report["last_training"] = self.training_history[-1]

        return report


def demo():
    """데모 실행"""
    logger.info("%s", "=" * 60)
    logger.info("ML Training System Demo")
    logger.info("%s", "=" * 60)

    # 시스템 초기화
    ml_system = MLTrainingSystem()

    # 합성 데이터 생성
    logger.info("Generating synthetic training data...")
    training_data = ml_system.generate_synthetic_data(size=500)
    logger.info("Generated %d samples", len(training_data.features))

    # 각 모델 훈련
    models_to_train = ["uncertainty_predictor", "confidence_predictor"]

    for model_name in models_to_train:
        logger.info("Training %s", model_name)
        metrics = ml_system.train_model(model_name, training_data)

        logger.info("R² Score: %.3f", metrics.r2)
        logger.info("MSE: %.3f", metrics.mse)
        logger.info("Training time: %.2fs", metrics.training_time)

        # Top 3 중요 특징
        if metrics.feature_importance:
            sorted_features = sorted(metrics.feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]
            logger.info("Top features:")
            for feat, imp in sorted_features:
                logger.info("%s: %.3f", feat, imp)

    # 예측 테스트
    logger.info("Testing predictions...")
    test_input = {
        "phase": "ideation",
        "timeline_weeks": 12,
        "team_size": 5,
        "budget": 50000,
        "technical_uncertainty": 0.7,
        "market_uncertainty": 0.6,
        "resource_uncertainty": 0.3,
        "timeline_uncertainty": 0.4,
        "quality_uncertainty": 0.5,
    }

    for model_name in models_to_train:
        prediction, metadata = ml_system.predict(model_name, test_input)
        logger.info("%s: %.3f", model_name, prediction)

    # 모델 저장
    logger.info("Saving models...")
    ml_system.save_models()

    # 상태 보고
    logger.info("Model report:")
    report = ml_system.get_model_report()
    for model_name, info in report["models"].items():
        status = "[OK] Trained" if info["trained"] else "[WARN] Not trained"
        logger.info("%s: %s (%s)", model_name, status, info["type"])

    logger.info("%s", "=" * 60)
    logger.info("Demo completed!")


if __name__ == "__main__":
    demo()

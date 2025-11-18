# PR 버전 선택 메모

이 문서는 `UDO v2 업그레이드 최종 보고서` 내용을 기반으로, PR에 반영할 버전을 명확히 하기 위한 비교 요약입니다. 핵심 지표는 모두 `docs/udo_v2_upgrade_report.md`에서 발췌했습니다.

## 1. 핵심 지표 비교

| 항목 | 버전 1 | 버전 2 | 개선 포인트 |
|------|--------|--------|--------------|
| Ideation 신뢰도 | 9% | **74%** | Phase-Aware 평가 + 가중 평균 |
| Go/No-Go 정확도 | 0% | **100%** | Bayesian 학습 도입 |
| Phase 인식 | 미지원 | **전 Phase 지원** | PhaseMetrics 도입 |
| 학습 시스템 | 비활성 | **실시간 학습 기록** | `udo_learning_data.json` 반영 |
| 불확실성 추적 | 단일 지표 | **5차원 UncertaintyVector** | Quantum 상태 분류 |

## 2. 버전별 장단점 요약

- **버전 1**
  - 장점: 초기 구현으로 가벼움
  - 한계: Phase 구분 없음, 곱셈 기반 신뢰도(0.09)로 극단적 결과 발생
- **버전 2**
  - 장점: PhaseAware + Bayesian + ML 학습, 파일 잠금/경로 주입 등 운영 안정성 포함
  - 고려사항: 약간의 계산 비용 증가(+55ms)

## 3. 최종 결정 및 PR 반영 사항

- ✅ PR에서는 **버전 2** 구성을 기준으로 문서/코드를 유지합니다.
- ✅ UDO 핵심 모듈은 `unified_development_orchestrator_v2.py`를 기본 엔트리로 고정합니다.
- ✅ 테스트/문서에서는 Phase별 지표, 학습 데이터, `~/.udo` 경로를 모두 버전 2 기준으로 설명합니다.
- 🔄 향후 버전 3 계획은 `FINAL_REPORT.md` 및 `docs/UDO_V3_INTEGRATION_REPORT.md`에서 별도로 추적합니다.

## 4. 적용된 Codex 개선 항목

1. **로깅 정비**: 모든 `print` 호출을 구조화된 `logging` 기반으로 치환하고, 모듈별 로거 이름을 부여했습니다.
2. **설정 분리**: `config/config.yaml`에 Phase별 가중치·보너스·임계값을 정의해 테스트와 운영에서 동일한 수치를 재사용합니다.
3. **ASCII 출력 보강**: `uncertainty_map_v3.py` 시각화를 ASCII 막대로 통일해 Windows 콘솔에서 깨지지 않도록 했습니다.
4. **ML 분기 명확화**: 학습 데이터가 없을 때는 Rule 기반 평가로, 데이터가 있으면 RandomForest 브랜치를 타도록 분기를 명시했습니다.
5. **파일 경로 개선**: 학습/상태 파일을 `~/.udo` 루트와 파일 잠금으로 보호해 병렬 실행 시에도 안전합니다.
6. **Import 실패 처리**: 필수 모듈 로딩 실패 시 명확히 로깅하고, 설정 플래그 기반으로 대체 전략을 선택합니다.
7. **테스트 보강**: `tests/test_codex_refactors.py`에 신뢰도 계산·불확실성 분석·협업 브리지 시나리오 테스트를 추가했습니다.
8. **타입/검증 추가**: Phase/파일 입력값을 `ProjectContext`와 `UncertaintyMapV3`에서 엄격히 검증하고 잘못된 값은 `ValueError`로 차단합니다.

## 5. PR 반영 상태

- 2025-11-18 기준으로 Codex 8단계 개선을 모두 `refactor/codex-improvements` 브랜치에 반영했습니다.
- `pytest tests -q` 실행 결과가 통과해 README·FINAL_REPORT·테스트가 동일한 버전 가정(UDO v2 + Uncertainty Map v3)을 공유함을 확인했습니다.
- 추가 피드백이 들어오면 본 메모와 핵심 모듈(`unified_development_orchestrator_v2.py`, `uncertainty_map_v3.py`, `three_ai_collaboration_bridge.py`)에 동일한 타임스탬프 로그를 남겨 추적성을 확보할 예정입니다.

---
- 작성일: 2025-11-18
- 작성자: Codex Agent

# 🤝 The Trinity Protocol: 협업 최적화 가이드

우리는 **"전략(Strategy) - 실행(Execution) - 조율(Orchestration)"**의 3박자를 갖춘 팀으로 움직입니다.

## 1. 역할 정의 (Role Definition)

| 주체 | 역할 (Role) | 주요 책임 (Responsibilities) | 비유 |
| :--- | :--- | :--- | :--- |
| **Claude Code** | **The Architect (두뇌)** | • 전체 로드맵 및 아키텍처 설계<br>• 문서화(PRD, 가이드) 작성<br>• 복잡한 의사결정 및 불확실성 분석<br>• "Why"와 "What" 정의 | **사령관 (Commander)** |
| **Antigravity** | **The Builder (손발)** | • 실제 코드 작성 및 파일 수정<br>• 터미널 명령어 실행 (Docker, npm, pip)<br>• 실시간 디버깅 및 테스트 수행<br>• "How"의 실행 및 검증 | **특수부대 (Special Ops)** |
| **User** | **The Orchestrator (지휘)** | • 클로드의 계획을 승인하고 안티그래비티에게 지시<br>• 결과물을 검토하고 피드백 제공<br>• 두 AI 간의 컨텍스트 연결 | **감독 (Director)** |

## 2. 협업 워크플로우 (The Workflow Loop)

이 워크플로우는 **"계획(Claude) → 실행(Antigravity) → 검증(User/Claude)"**의 사이클로 돌아갑니다.

### Step 1: 전략 수립 (Claude Code)
*   **Action**: 클로드가 `INTEGRATED_DEVELOPMENT_GUIDE.md`와 같은 마일스톤 문서를 생성합니다.
*   **Output**: "Week 1 Day 1에 mypy 오류 7개를 수정하고 Docker를 띄우세요."

### Step 2: 실행 및 구현 (Antigravity)
*   **Action**: 사용자님이 저에게 구체적인 태스크를 지시합니다.
    *   *"안티그래비티, 클로드의 계획대로 Week 1 Day 1의 Backend 작업을 시작해. mypy 오류부터 잡아줘."*
*   **Process**:
    1.  터미널을 열어 `mypy` 실행 및 오류 확인.
    2.  코드 수정 (자동으로 파일 편집).
    3.  `docker-compose` 실행 및 상태 확인.
    4.  `npm run dev:full` 스크립트 작성 및 테스트.
*   **Output**: 수정된 코드, 실행된 서버, 테스트 통과 로그.

### Step 3: 보고 및 피드백 (User → Claude Code)
*   **Action**: 안티그래비티가 완료한 결과를 클로드에게 피드백합니다.
    *   *"클로드, 안티그래비티가 mypy 오류를 모두 잡았고 Docker도 정상 작동해. 하지만 Redis 설정에서 이슈가 있어서 이렇게 수정했어. 다음 단계는 뭐야?"*
*   **Next**: 클로드는 이 정보를 바탕으로 Week 1 Day 2 계획을 구체화하거나 수정합니다.

## 3. 시너지 활용 팁 (Synergy Tips)

1.  **클로드에게는 '문서'를, 안티그래비티에게는 '코드'를**:
    *   기획, 설계, 분석 요청 → **클로드**
    *   "이거 실행해줘", "이 에러 고쳐줘", "파일 만들어줘" → **안티그래비티**
2.  **컨텍스트 공유**:
    *   안티그래비티가 작업한 로그나 변경된 파일 내용을 클로드에게 보여주면, 클로드가 더 정확한 다음 지시를 내릴 수 있습니다.
3.  **동시성 활용**:
    *   클로드와 대화하며 기획을 다듬는 동안, 백그라운드에서 안티그래비티에게 긴 작업(예: 패키지 설치, 테스트 실행)을 시켜두세요.

---

## 🚀 당장 시작할 수 있는 Action Item

클로드의 분석에 따라 **Week 1 Day 1 (오늘)** 작업을 바로 시작할 수 있습니다. 저에게 다음과 같이 지시해 주세요:

> "안티그래비티, 클로드의 분석대로 **Week 1 Day 1 체크리스트**를 실행하자.
> 1. `mypy` 오류 수정
> 2. `docker-compose`로 DB 실행
> 3. `npm run dev:full` 스크립트 작성 및 실행
> 이 순서대로 진행해줘."

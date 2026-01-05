# 사용자 테스트 빠른 시작 가이드 🚀

**목표**: 5명의 사용자 테스트 세션 진행 (30-45분/인)
**성공 기준**: ≥4.0/5.0 만족도, 0개 크리티컬 버그

---

## 📋 테스트 준비 (5분)

### 1️⃣ 서버 실행

```bash
# 원클릭 서버 실행
start-testing-servers.bat
```

**자동으로 수행**:
- PostgreSQL 상태 확인 및 시작
- 데이터베이스 샘플 데이터 시드 (15개 태스크)
- 백엔드 서버 시작 (http://localhost:8000)
- 프론트엔드 서버 시작 (http://localhost:3000)

### 2️⃣ 확인사항

| 항목 | URL | 상태 |
|------|-----|------|
| 백엔드 API | http://localhost:8000/docs | ✅ Swagger UI 표시 |
| 프론트엔드 | http://localhost:3000 | ✅ 대시보드 로딩 |
| Kanban 보드 | http://localhost:3000/kanban | ✅ 15개 태스크 표시 |

### 3️⃣ 준비물

- [ ] `test-context.zip` 파일 (프로젝트 루트에 있음)
- [ ] 스크린 레코딩 소프트웨어 (OBS Studio, Zoom 녹화 등)
- [ ] 피드백 템플릿 (`docs/templates/WEEK8_DAY4_FEEDBACK_TEMPLATE.md`)
- [ ] 브라우저 개발자 도구 (F12) - 콘솔 에러 모니터링

---

## 🎯 테스트 시나리오 (5가지)

### Scenario 1: Kanban 기본 기능 (10분)

**목표**: CRUD 작업 검증

```
1. 태스크 생성: "User Testing - Database Migration"
   - Phase: Implementation
   - Priority: High
   - Estimated hours: 8

2. 태스크 수정: 설명에 "with zero downtime" 추가
   - 태그 추가: "database", "migration", "critical"

3. Drag & Drop: "To Do" → "In Progress"
   - 낙관적 업데이트 확인
   - API 동기화 확인

4. 태스크 삭제: 확인 후 삭제
   - 보드에서 제거 확인
   - 새로고침 후 지속성 확인
```

**평가 질문**:
- 태스크 생성이 직관적이었나요? (1-5)
- Drag & Drop이 반응적이었나요? (1-5)
- 혼란스럽거나 예상치 못한 동작이 있었나요?

---

### Scenario 2: 의존성 관리 (8분)

**목표**: Q7 Hard Block 기능 검증

```
1. 부모 태스크 생성: "Design API Schema"
   - Phase: Design
   - Priority: High

2. 자식 태스크 생성: "Implement API Endpoints"
   - Phase: Implementation
   - Dependencies: "Design API Schema" (Hard Block)

3. 차단 동작 테스트:
   - 자식 태스크를 "In Progress"로 이동 시도 → 경고 표시
   - 부모 태스크를 "Done"으로 이동
   - 이제 자식 태스크 이동 가능 확인

4. Emergency Override (선택):
   - Override 버튼 클릭
   - 이유 입력 다이얼로그 확인
```

**평가 질문**:
- 의존성 설정이 명확했나요? (1-5)
- 차단 동작이 이해되었나요? (1-5)
- Override 흐름이 너무 쉬웠나요/어려웠나요? (정성 평가)

---

### Scenario 3: 컨텍스트 업로드 (7분)

**목표**: Q4 ZIP 업로드/다운로드 검증

```
1. 태스크 상세 열기 → "Context" 탭

2. test-context.zip 업로드:
   - Drag & Drop 또는 클릭 업로드
   - 진행 상태 바 확인
   - 파일 개수 검증 (3 files 표시)
   - 크기 검증 (50MB 미만)

3. 컨텍스트 다운로드:
   - "Download ZIP" 클릭
   - 다운로드 시간 측정 (<2초 기대)
   - 다운로드된 ZIP에 3개 파일 확인:
     - api.py
     - schema.sql
     - README.md

4. 더블클릭 자동 로드 (미래 기능):
   - 태스크 카드 더블클릭
   - 컨텍스트 자동 로드 확인
```

**평가 질문**:
- 업로드가 원활했나요? (1-5)
- 진행 상태가 명확했나요? (1-5)
- 개선사항이 있나요?

---

### Scenario 4: AI 제안 (10분)

**목표**: Q2 AI Hybrid 기능 검증

```
1. 태스크 생성: "Refactor authentication module"
   - Phase: Implementation
   - Priority: Low

2. "AI Suggestions" 버튼 클릭
   - Claude Sonnet 4.5 응답 대기 (<3초)
   - 3-5개 서브태스크 제안 확인

3. 제안 검토:
   - 2개 승인 (체크박스 선택)
   - 1개 거부 (체크 해제)
   - 1개 수정 (제목/설명 편집)

4. "Apply Selected" 클릭
   - 서브태스크 생성 확인
   - 부모 태스크와 연결 확인
```

**평가 질문**:
- AI 제안이 관련성 있었나요? (1-5)
- 승인/거부 흐름이 명확했나요? (1-5)
- AI 응답 시간이 적절했나요? (1-5)

---

### Scenario 5: 아카이브 & ROI (5분)

**목표**: Q6 AI 요약 + ROI 대시보드 검증

```
1. 태스크 생성: "Week 1 Sprint Planning"
   - Phase: Ideation
   - Status: Done
   - Estimated: 4h, Actual: 3.5h

2. 아카이브:
   - "Archive" 버튼 클릭
   - 아카이브 노트 추가: "Completed sprint planning"
   - GPT-4o AI 요약 생성 확인

3. 아카이브 탐색:
   - /archive 페이지로 이동
   - 아카이브된 태스크 검색
   - AI 요약 확인

4. ROI 대시보드:
   - /roi-dashboard 이동
   - 차트 렌더링 확인 (Recharts)
   - Efficiency 메트릭 확인 (114% in example)
```

**평가 질문**:
- AI 요약이 유용했나요? (1-5)
- 아카이브 탐색이 쉬웠나요? (1-5)
- ROI 차트가 인사이트를 제공했나요? (1-5)

---

## 📊 데이터 수집

### 테스트 중 기록사항

- [ ] 콘솔 에러 스크린샷 (F12 개발자 도구)
- [ ] 사용자 혼란 포인트 (타임스탬프 포함)
- [ ] 긍정적 피드백 (칭찬한 기능)
- [ ] 개선 제안
- [ ] 버그 발견 (심각도 등급: Critical/High/Medium/Low)

### 테스트 후 설문

피드백 템플릿 작성: `docs/templates/WEEK8_DAY4_FEEDBACK_TEMPLATE.md`

**15개 질문**:
- 10개 Likert scale (1-5)
- 5개 정성 평가 (open-ended)
- 1개 NPS (Net Promoter Score)

---

## 🔄 테스트 완료 후

### 서버 종료

```bash
# 모든 서버 종료
stop-testing-servers.bat
```

### 테스트 데이터 정리 (선택)

```bash
# 샘플 데이터 제거
.venv\Scripts\python.exe scripts\seed_test_data.py --clear
```

---

## 📋 성공 체크리스트

### 테스트 세션 완료 기준

- [ ] 5명의 사용자 테스트 완료
- [ ] 5가지 시나리오 모두 실행
- [ ] 피드백 템플릿 5개 수집
- [ ] 스크린 레코딩 5개 저장
- [ ] 콘솔 에러 로그 수집

### 목표 달성 기준

- [ ] 평균 만족도 ≥4.0/5.0
- [ ] Critical 버그 0개
- [ ] High 버그 ≤2개
- [ ] 모든 시나리오 완료율 ≥80%

---

## 🚨 문제 발생 시

### 백엔드 에러

```bash
# 로그 확인
tail -f backend/logs/app.log

# 재시작
stop-testing-servers.bat
start-testing-servers.bat
```

### 프론트엔드 에러

```bash
cd web-dashboard
npm run build  # 빌드 에러 확인
npm run dev    # 재시작
```

### 데이터베이스 에러

```bash
# PostgreSQL 상태 확인
sc query postgresql-x64-16

# 재시작
net stop postgresql-x64-16
net start postgresql-x64-16
```

---

## 📞 지원

**문제 발생 시 연락**:
- GitHub Issues: https://github.com/positivef/UDO-Development-Platform/issues
- 상세 가이드: `docs/guides/WEEK8_DAY4_USER_TESTING_GUIDE.md`
- 체크리스트: `docs/templates/WEEK8_DAY4_TESTING_CHECKLIST.md`

---

**준비 완료! 사용자 테스트를 시작하세요 🎉**

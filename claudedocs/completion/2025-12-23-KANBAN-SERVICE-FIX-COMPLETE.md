---
title: "Kanban Service Dependency Fix Completion"
created: "2025-12-23"
author: "claude"
status: "stable"
category: "completion"
ai_model: "gemini"
session_id: "e14c04f9-ca3f-4f73-9750-296f99b70172"
confidence: 95
retention_days: null
obsidian_sync: true
obsidian_path: "개발일지/2025-12-23/"
milestone: "Kanban Service Fix"
completion_percentage: 100
---

# Kanban 서비스 의존성 문제 해결 완료

## 문제 요약
`/api/kanban/tasks` 엔드포인트가 실제 PostgreSQL 데이터 대신 Mock 데이터를 반환하던 문제

## 원인
- `get_kanban_service()` 의존성 함수가 `async_db` 싱글톤을 제대로 참조하지 못함
- FastAPI 의존성 캐시가 오래된 인스턴스를 반환

## 수정 사항

### 1. `backend/app/routers/kanban_tasks.py`
- `get_kanban_service()` 에 싱글톤 확인 로그 추가
- `Depends(..., use_cache=False)` 로 캐시 비활성화
- `/debug` 엔드포인트 추가 (서비스 진단용)

```diff
+ import logging, sys
+ logger.debug(f"[IDENTITY] async_database module id: {id(sys.modules.get('backend.async_database'))}")
+ logger.debug(f"[IDENTITY] async_db object id: {id(async_db)}")

- service: KanbanTaskService = Depends(get_kanban_service),
+ service: KanbanTaskService = Depends(get_kanban_service, use_cache=False),
```

## 검증 결과

### Backend API 테스트
```bash
curl.exe -s http://127.0.0.1:8000/api/kanban/tasks/debug
```
```json
{
  "service_type": "KanbanTaskService",
  "is_mock": false,
  "async_db_initialized": true,
  "async_db_pool": "<asyncpg.pool.Pool object at 0x0000020164125E40>"
}
```

### Browser 테스트
- Backend (localhost:8000): 실제 DB 데이터 정상 반환 ✅
- Frontend (localhost:3000): Kanban 보드 페이지 로드 성공

![Browser Test Recording](file:///c:/Users/user/Documents/GitHub/UDO-Development-Platform/claudedocs/completion/2025-12-23-kanban-verification.webp)

## 결론
✅ Backend 의존성 문제 해결 완료 - 실제 DB 데이터 반환

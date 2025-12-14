# Database Migrations

PostgreSQL 데이터베이스 마이그레이션 시스템

## 📋 개요

이 디렉토리에는 UDO Development Platform의 PostgreSQL 데이터베이스 스키마 마이그레이션 파일들이 포함되어 있습니다.

## 🗂️ 파일 구조

```
migrations/
├── README.md                           # 이 파일
├── run_migration.py                    # 마이그레이션 실행 스크립트
├── 001_initial_schema.sql              # 초기 스키마
├── 001_initial_schema_rollback.sql     # 초기 스키마 롤백
└── 002_xxx.sql                         # 향후 마이그레이션 파일들
```

## 🎯 데이터베이스 스키마

### 7개 핵심 테이블

1. **projects** - 프로젝트 정보 및 설정
2. **project_contexts** - 프로젝트 컨텍스트 자동 로딩
3. **task_history** - 프롬프트/코드 히스토리 관리
4. **version_history** - Git 커밋 히스토리 캐시
5. **kanban_boards** - 작업 관리 보드
6. **kanban_cards** - 칸반 카드
7. **quality_metrics** - 품질 지표 추적

### 추가 기능

- **Triggers**: 자동 타임스탬프 업데이트
- **Views**: active_projects, project_summary
- **Indexes**: 성능 최적화를 위한 인덱스
- **Full-text Search**: pg_trgm 확장을 사용한 검색

## 🚀 사용 방법

### 1. PostgreSQL 설치 및 설정

```bash
# Windows (Chocolatey)
choco install postgresql

# macOS (Homebrew)
brew install postgresql

# Linux (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib
```

### 2. 데이터베이스 생성

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE udo_dev;

# 사용자 생성 (선택사항)
CREATE USER udo_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE udo_dev TO udo_user;
```

### 3. 환경 변수 설정

`.env` 파일 생성 (backend 디렉토리에):

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=udo_dev
DB_USER=postgres
DB_PASSWORD=your_password_here
```

또는 `.env.example` 파일을 복사:

```bash
cp backend/.env.example backend/.env
# 그 다음 .env 파일을 편집하여 비밀번호 설정
```

### 4. 마이그레이션 실행

#### Dry Run (실행 예정 마이그레이션 확인)

```bash
cd backend/migrations
python run_migration.py --dry-run
```

#### 실제 마이그레이션 실행

```bash
python run_migration.py
```

#### 커스텀 데이터베이스 설정

```bash
python run_migration.py --host localhost --port 5432 --database udo_dev --user postgres --password your_password
```

### 5. 마이그레이션 롤백

```bash
python run_migration.py --rollback 001_initial_schema
```

## 📊 마이그레이션 추적

마이그레이션 시스템은 자동으로 `schema_migrations` 테이블을 생성하여 실행된 마이그레이션을 추적합니다:

```sql
SELECT * FROM schema_migrations ORDER BY executed_at DESC;
```

결과:
```
 version           | filename                    | executed_at         | success
-------------------+-----------------------------+---------------------+---------
 001_initial_schema| 001_initial_schema.sql      | 2025-11-17 10:00:00 | true
```

## 🔧 새 마이그레이션 추가

### 명명 규칙

```
{number}_{description}.sql
{number}_{description}_rollback.sql
```

예시:
```
002_add_user_roles.sql
002_add_user_roles_rollback.sql
```

### 마이그레이션 파일 템플릿

```sql
-- ============================================================
-- Description: Add user roles table
-- Version: 1.0.0
-- Date: 2025-11-18
-- ============================================================

CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    permissions JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_roles_name ON user_roles(name);
```

### 롤백 파일 템플릿

```sql
-- ============================================================
-- Description: Rollback user roles table
-- ============================================================

DROP TABLE IF EXISTS user_roles CASCADE;
```

## 🛡️ 안전 수칙

### 프로덕션 환경

1. **항상 백업 먼저!**
   ```bash
   pg_dump udo_prod > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Dry-run 먼저 실행**
   ```bash
   python run_migration.py --dry-run
   ```

3. **오프피크 시간에 실행**
   - 트래픽이 적은 시간대 선택
   - 사용자에게 사전 공지

4. **롤백 계획 준비**
   - 롤백 스크립트 테스트
   - 복구 절차 문서화

### 개발 환경

1. **로컬에서 먼저 테스트**
2. **Git 커밋 전 마이그레이션 검증**
3. **팀원과 스키마 변경 공유**

## 📈 데이터베이스 상태 확인

### 테이블 목록

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

### 테이블 크기

```sql
SELECT
    table_name,
    pg_size_pretty(pg_total_relation_size(quote_ident(table_name)::regclass)) AS size
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(quote_ident(table_name)::regclass) DESC;
```

### 인덱스 사용률

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## 🐛 문제 해결

### 연결 실패

```
Error: could not connect to server
```

**해결**:
1. PostgreSQL 서비스 실행 확인
   ```bash
   # Windows
   net start postgresql

   # macOS/Linux
   sudo service postgresql start
   ```

2. 연결 정보 확인 (.env 파일)
3. 방화벽 설정 확인

### 권한 오류

```
Error: permission denied for table
```

**해결**:
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
```

### 마이그레이션 실패

```
Error: migration failed
```

**해결**:
1. 에러 메시지 확인
2. `schema_migrations` 테이블에서 실패한 마이그레이션 확인
3. 실패한 마이그레이션 수동 삭제:
   ```sql
   DELETE FROM schema_migrations WHERE version = 'xxx' AND success = false;
   ```
4. SQL 파일 수정 후 재실행

## 📚 추가 리소스

- [PostgreSQL 공식 문서](https://www.postgresql.org/docs/)
- [Psycopg2 문서](https://www.psycopg.org/docs/)
- [Database Migration Best Practices](https://www.postgresql.org/docs/current/ddl-alter.html)

## ✅ 체크리스트

마이그레이션 실행 전:

- [ ] PostgreSQL 설치 및 실행 확인
- [ ] 데이터베이스 생성 완료
- [ ] .env 파일 설정 완료
- [ ] psycopg2-binary 설치 (`pip install -r requirements.txt`)
- [ ] Dry-run 실행 및 확인
- [ ] 백업 완료 (프로덕션의 경우)
- [ ] 롤백 스크립트 준비

마이그레이션 실행 후:

- [ ] 마이그레이션 성공 확인
- [ ] 테이블 생성 확인
- [ ] 인덱스 확인
- [ ] 데이터 무결성 검증
- [ ] 애플리케이션 연결 테스트

---

**Last Updated**: 2025-11-17
**Version**: 1.0.0
**Status**: Production Ready

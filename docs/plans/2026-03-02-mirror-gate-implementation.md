# MirrorGate Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a full-featured testing platform with Mock service, API automation, and UI automation capabilities.

**Architecture:** Monolithic layered architecture with Vue 3 frontend and FastAPI backend, using MySQL for persistence and Redis for caching.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, Vue 3, Element Plus, TypeScript, MySQL 8.0, Redis, Docker Compose

---

## Phase 1: Project Skeleton

### Task 1: Backend Directory Structure

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/requirements.txt`
- Create: `backend/Dockerfile`
- Create: `backend/.env.example`

**Step 1: Create backend directory structure**

```bash
mkdir -p backend/app/{api/v1,models,schemas,services,core,utils}
mkdir -p backend/alembic/versions
mkdir -p backend/tests
```

**Step 2: Create requirements.txt**

```text
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pymysql==1.1.0
alembic==1.13.1
pydantic==2.5.3
pydantic-settings==2.1.0
python-dotenv==1.0.0
redis==5.0.1
httpx==0.26.0
pytest==7.4.4
pytest-asyncio==0.23.3
```

**Step 3: Create config.py**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "MirrorGate"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_DATABASE: str = "mirror_gate"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @property
    def database_url(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

**Step 4: Create database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 5: Create main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}
```

**Step 6: Create __init__.py files**

```bash
touch backend/app/__init__.py
touch backend/app/api/__init__.py
touch backend/app/api/v1/__init__.py
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/services/__init__.py
touch backend/app/core/__init__.py
touch backend/app/utils/__init__.py
```

**Step 7: Create Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 8: Create .env.example**

```text
DEBUG=True
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=mirror_gate
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

**Step 9: Commit**

```bash
git add backend/
git commit -m "feat: add backend project skeleton"
```

---

### Task 2: Frontend Directory Structure

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/Dockerfile`

**Step 1: Create frontend directory structure**

```bash
mkdir -p frontend/src/{api,views,components,stores,router,utils,assets}
```

**Step 2: Create package.json**

```json
{
  "name": "mirror-gate-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "element-plus": "^2.5.0",
    "axios": "^1.6.5"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vue-tsc": "^1.8.0"
  }
}
```

**Step 3: Create vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

**Step 4: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Step 5: Create index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>MirrorGate</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

**Step 6: Create main.ts**

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
```

**Step 7: Create App.vue**

```vue
<template>
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
import zhCn from 'element-plus/es/locale/lang/zh-cn'
</script>

<style>
#app {
  height: 100vh;
}
</style>
```

**Step 8: Create router/index.ts**

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue')
    },
    {
      path: '/mock',
      name: 'Mock',
      component: () => import('@/views/mock/index.vue')
    },
    {
      path: '/api-test',
      name: 'ApiTest',
      component: () => import('@/views/api-test/index.vue')
    },
    {
      path: '/ui-test',
      name: 'UiTest',
      component: () => import('@/views/ui-test/index.vue')
    }
  ]
})

export default router
```

**Step 9: Create Dockerfile**

```dockerfile
FROM node:20-alpine as builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**Step 10: Commit**

```bash
git add frontend/
git commit -m "feat: add frontend project skeleton"
```

---

### Task 3: Docker Compose Configuration

**Files:**
- Create: `docker-compose.yml`
- Create: `docker-compose.dev.yml`
- Create: `frontend/nginx.conf`

**Step 1: Create docker-compose.yml**

```yaml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - MYSQL_USER=root
      - MYSQL_PASSWORD=${MYSQL_PASSWORD:-password}
      - MYSQL_DATABASE=mirror_gate
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - mysql
      - redis

  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_PASSWORD:-password}
      - MYSQL_DATABASE=mirror_gate
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

**Step 2: Create docker-compose.dev.yml**

```yaml
version: '3.8'

services:
  backend:
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    command: npm run dev
```

**Step 3: Create frontend/nginx.conf**

```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Step 4: Commit**

```bash
git add docker-compose.yml docker-compose.dev.yml frontend/nginx.conf
git commit -m "feat: add docker compose configuration"
```

---

## Phase 2: Mock Service

### Task 4: Mock Data Models

**Files:**
- Create: `backend/app/models/mock.py`
- Create: `backend/alembic/versions/001_initial_mock.py`

**Step 1: Write test for MockSuite model**

Create `backend/tests/test_mock_models.py`:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.mock import MockSuite, MockRule, MockResponse, MockWhitelist


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_mock_suite(db_session):
    suite = MockSuite(
        name="test-suite",
        description="Test suite",
        is_enabled=True,
        enable_compare=False,
        created_by="admin"
    )
    db_session.add(suite)
    db_session.commit()

    assert suite.id is not None
    assert suite.name == "test-suite"
    assert suite.is_enabled is True
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/test_mock_models.py -v
```
Expected: FAIL with "cannot import name 'MockSuite'"

**Step 3: Create mock.py model**

```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class MatchType(str, enum.Enum):
    ANY = "any"  # 任一匹配
    ALL = "all"  # 全部匹配


class RuleOperator(str, enum.Enum):
    EQUALS = "equals"
    CONTAINS = "contains"
    NOT_EQUALS = "not_equals"


class WhitelistType(str, enum.Enum):
    CLIENT_ID = "clientId"
    USER_ID = "userId"
    VID = "vid"


class MockSuite(Base):
    __tablename__ = "mock_suites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    is_enabled = Column(Boolean, default=True)
    enable_compare = Column(Boolean, default=False)
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(50))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rules = relationship("MockRule", back_populates="suite", cascade="all, delete-orphan")
    responses = relationship("MockResponse", back_populates="suite", cascade="all, delete-orphan")
    whitelists = relationship("MockWhitelist", back_populates="suite", cascade="all, delete-orphan")


class MockRule(Base):
    __tablename__ = "mock_rules"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("mock_suites.id"), nullable=False)
    field = Column(String(100), nullable=False)  # 匹配字段
    operator = Column(Enum(RuleOperator), default=RuleOperator.EQUALS)
    value = Column(Text, nullable=False)  # 匹配值

    suite = relationship("MockSuite", back_populates="rules")


class MockResponse(Base):
    __tablename__ = "mock_responses"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("mock_suites.id"), nullable=False)
    path = Column(String(255), nullable=False)  # API 路径
    method = Column(String(10), default="GET")
    response_json = Column(Text)  # 响应 JSON
    ab_test_config = Column(Text)  # AB 测试配置
    timeout_ms = Column(Integer, default=0)  # 模拟超时（毫秒）
    empty_response = Column(Boolean, default=False)  # 模拟空响应

    suite = relationship("MockSuite", back_populates="responses")


class MockWhitelist(Base):
    __tablename__ = "mock_whitelists"

    id = Column(Integer, primary_key=True, index=True)
    suite_id = Column(Integer, ForeignKey("mock_suites.id"), nullable=False)
    type = Column(Enum(WhitelistType), nullable=False)
    value = Column(String(255), nullable=False)

    suite = relationship("MockSuite", back_populates="whitelists")
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/test_mock_models.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/models/mock.py backend/tests/test_mock_models.py
git commit -m "feat: add mock data models"
```

---

### Task 5: Mock Schemas

**Files:**
- Create: `backend/app/schemas/mock.py`

**Step 1: Create mock schemas**

```python
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.mock import RuleOperator, WhitelistType, MatchType


# MockRule schemas
class MockRuleBase(BaseModel):
    field: str
    operator: RuleOperator = RuleOperator.EQUALS
    value: str


class MockRuleCreate(MockRuleBase):
    pass


class MockRuleResponse(MockRuleBase):
    id: int
    suite_id: int

    class Config:
        from_attributes = True


# MockResponse schemas
class MockResponseBase(BaseModel):
    path: str
    method: str = "GET"
    response_json: Optional[str] = None
    ab_test_config: Optional[str] = None
    timeout_ms: int = 0
    empty_response: bool = False


class MockResponseCreate(MockResponseBase):
    pass


class MockResponseResponse(MockResponseBase):
    id: int
    suite_id: int

    class Config:
        from_attributes = True


# MockWhitelist schemas
class MockWhitelistBase(BaseModel):
    type: WhitelistType
    value: str


class MockWhitelistCreate(MockWhitelistBase):
    pass


class MockWhitelistResponse(MockWhitelistBase):
    id: int
    suite_id: int

    class Config:
        from_attributes = True


# MockSuite schemas
class MockSuiteBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_enabled: bool = True
    enable_compare: bool = False


class MockSuiteCreate(MockSuiteBase):
    rules: List[MockRuleCreate] = []
    responses: List[MockResponseCreate] = []
    whitelists: List[MockWhitelistCreate] = []
    match_type: MatchType = MatchType.ANY


class MockSuiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_enabled: Optional[bool] = None
    enable_compare: Optional[bool] = None
    rules: Optional[List[MockRuleCreate]] = None
    responses: Optional[List[MockResponseCreate]] = None
    whitelists: Optional[List[MockWhitelistCreate]] = None


class MockSuiteResponse(MockSuiteBase):
    id: int
    created_by: Optional[str]
    created_at: datetime
    updated_by: Optional[str]
    updated_at: datetime
    rules: List[MockRuleResponse] = []
    responses: List[MockResponseResponse] = []
    whitelists: List[MockWhitelistResponse] = []

    class Config:
        from_attributes = True


class MockSuiteListResponse(BaseModel):
    total: int
    items: List[MockSuiteResponse]
```

**Step 2: Commit**

```bash
git add backend/app/schemas/mock.py
git commit -m "feat: add mock pydantic schemas"
```

---

### Task 6: Mock Service API

**Files:**
- Create: `backend/app/services/mock_service.py`
- Create: `backend/app/api/v1/mock.py`

**Step 1: Write test for mock service**

Create `backend/tests/test_mock_service.py`:

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services.mock_service import MockService
from app.schemas.mock import MockSuiteCreate, MockRuleCreate


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_mock_suite(db_session):
    service = MockService(db_session)
    suite_data = MockSuiteCreate(
        name="api-test-suite",
        description="API Test Suite",
        rules=[MockRuleCreate(field="path", value="/api/test")]
    )
    suite = service.create_suite(suite_data, created_by="admin")

    assert suite.id is not None
    assert suite.name == "api-test-suite"
    assert len(suite.rules) == 1
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/test_mock_service.py -v
```
Expected: FAIL

**Step 3: Create mock_service.py**

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.mock import MockSuite, MockRule, MockResponse, MockWhitelist
from app.schemas.mock import (
    MockSuiteCreate,
    MockSuiteUpdate,
    MockSuiteResponse,
    MockRuleCreate,
    MockResponseCreate,
    MockWhitelistCreate
)


class MockService:
    def __init__(self, db: Session):
        self.db = db

    def create_suite(self, suite_data: MockSuiteCreate, created_by: str) -> MockSuite:
        # Check if name exists
        existing = self.db.query(MockSuite).filter(MockSuite.name == suite_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Suite name already exists")

        suite = MockSuite(
            name=suite_data.name,
            description=suite_data.description,
            is_enabled=suite_data.is_enabled,
            enable_compare=suite_data.enable_compare,
            created_by=created_by
        )
        self.db.add(suite)
        self.db.flush()

        # Add rules
        for rule_data in suite_data.rules:
            rule = MockRule(
                suite_id=suite.id,
                field=rule_data.field,
                operator=rule_data.operator,
                value=rule_data.value
            )
            self.db.add(rule)

        # Add responses
        for resp_data in suite_data.responses:
            response = MockResponse(
                suite_id=suite.id,
                path=resp_data.path,
                method=resp_data.method,
                response_json=resp_data.response_json,
                ab_test_config=resp_data.ab_test_config,
                timeout_ms=resp_data.timeout_ms,
                empty_response=resp_data.empty_response
            )
            self.db.add(response)

        # Add whitelists
        for wl_data in suite_data.whitelists:
            whitelist = MockWhitelist(
                suite_id=suite.id,
                type=wl_data.type,
                value=wl_data.value
            )
            self.db.add(whitelist)

        self.db.commit()
        self.db.refresh(suite)
        return suite

    def get_suite(self, suite_id: int) -> Optional[MockSuite]:
        return self.db.query(MockSuite).filter(MockSuite.id == suite_id).first()

    def get_suites(self, skip: int = 0, limit: int = 100) -> List[MockSuite]:
        return self.db.query(MockSuite).offset(skip).limit(limit).all()

    def update_suite(self, suite_id: int, suite_data: MockSuiteUpdate, updated_by: str) -> MockSuite:
        suite = self.get_suite(suite_id)
        if not suite:
            raise HTTPException(status_code=404, detail="Suite not found")

        update_data = suite_data.model_dump(exclude_unset=True)

        # Handle nested updates
        rules_data = update_data.pop("rules", None)
        responses_data = update_data.pop("responses", None)
        whitelists_data = update_data.pop("whitelists", None)

        # Update basic fields
        for key, value in update_data.items():
            setattr(suite, key, value)

        suite.updated_by = updated_by

        # Update rules
        if rules_data is not None:
            self.db.query(MockRule).filter(MockRule.suite_id == suite_id).delete()
            for rule_data in rules_data:
                rule = MockRule(
                    suite_id=suite_id,
                    field=rule_data.field,
                    operator=rule_data.operator,
                    value=rule_data.value
                )
                self.db.add(rule)

        # Update responses
        if responses_data is not None:
            self.db.query(MockResponse).filter(MockResponse.suite_id == suite_id).delete()
            for resp_data in responses_data:
                response = MockResponse(
                    suite_id=suite_id,
                    path=resp_data.path,
                    method=resp_data.method,
                    response_json=resp_data.response_json,
                    ab_test_config=resp_data.ab_test_config,
                    timeout_ms=resp_data.timeout_ms,
                    empty_response=resp_data.empty_response
                )
                self.db.add(response)

        # Update whitelists
        if whitelists_data is not None:
            self.db.query(MockWhitelist).filter(MockWhitelist.suite_id == suite_id).delete()
            for wl_data in whitelists_data:
                whitelist = MockWhitelist(
                    suite_id=suite_id,
                    type=wl_data.type,
                    value=wl_data.value
                )
                self.db.add(whitelist)

        self.db.commit()
        self.db.refresh(suite)
        return suite

    def delete_suite(self, suite_id: int) -> bool:
        suite = self.get_suite(suite_id)
        if not suite:
            raise HTTPException(status_code=404, detail="Suite not found")

        self.db.delete(suite)
        self.db.commit()
        return True

    def copy_suite(self, suite_id: int, new_name: str, created_by: str) -> MockSuite:
        suite = self.get_suite(suite_id)
        if not suite:
            raise HTTPException(status_code=404, detail="Suite not found")

        new_suite = MockSuite(
            name=new_name,
            description=f"Copy of {suite.description}",
            is_enabled=False,
            enable_compare=suite.enable_compare,
            created_by=created_by
        )
        self.db.add(new_suite)
        self.db.flush()

        # Copy rules
        for rule in suite.rules:
            new_rule = MockRule(
                suite_id=new_suite.id,
                field=rule.field,
                operator=rule.operator,
                value=rule.value
            )
            self.db.add(new_rule)

        # Copy responses
        for resp in suite.responses:
            new_resp = MockResponse(
                suite_id=new_suite.id,
                path=resp.path,
                method=resp.method,
                response_json=resp.response_json,
                ab_test_config=resp.ab_test_config,
                timeout_ms=resp.timeout_ms,
                empty_response=resp.empty_response
            )
            self.db.add(new_resp)

        # Copy whitelists
        for wl in suite.whitelists:
            new_wl = MockWhitelist(
                suite_id=new_suite.id,
                type=wl.type,
                value=wl.value
            )
            self.db.add(new_wl)

        self.db.commit()
        self.db.refresh(new_suite)
        return new_suite
```

**Step 4: Run test to verify it passes**

```bash
cd backend && pytest tests/test_mock_service.py -v
```
Expected: PASS

**Step 5: Create API routes**

```python
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.mock_service import MockService
from app.schemas.mock import (
    MockSuiteCreate,
    MockSuiteUpdate,
    MockSuiteResponse,
    MockSuiteListResponse
)

router = APIRouter(prefix="/mock", tags=["Mock"])


@router.post("/suites", response_model=MockSuiteResponse)
def create_suite(
    suite_data: MockSuiteCreate,
    db: Session = Depends(get_db)
):
    service = MockService(db)
    return service.create_suite(suite_data, created_by="system")


@router.get("/suites", response_model=MockSuiteListResponse)
def list_suites(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    service = MockService(db)
    suites = service.get_suites(skip, limit)
    return MockSuiteListResponse(
        total=len(suites),
        items=suites
    )


@router.get("/suites/{suite_id}", response_model=MockSuiteResponse)
def get_suite(
    suite_id: int,
    db: Session = Depends(get_db)
):
    service = MockService(db)
    suite = service.get_suite(suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="Suite not found")
    return suite


@router.put("/suites/{suite_id}", response_model=MockSuiteResponse)
def update_suite(
    suite_id: int,
    suite_data: MockSuiteUpdate,
    db: Session = Depends(get_db)
):
    service = MockService(db)
    return service.update_suite(suite_id, suite_data, updated_by="system")


@router.delete("/suites/{suite_id}")
def delete_suite(
    suite_id: int,
    db: Session = Depends(get_db)
):
    service = MockService(db)
    service.delete_suite(suite_id)
    return {"message": "Suite deleted successfully"}


@router.post("/suites/{suite_id}/copy", response_model=MockSuiteResponse)
def copy_suite(
    suite_id: int,
    new_name: str,
    db: Session = Depends(get_db)
):
    service = MockService(db)
    return service.copy_suite(suite_id, new_name, created_by="system")
```

**Step 6: Register router in main.py**

Add to `backend/app/main.py`:

```python
from app.api.v1 import mock

app.include_router(mock.router, prefix="/api/v1")
```

**Step 7: Commit**

```bash
git add backend/app/services/mock_service.py backend/app/api/v1/mock.py backend/tests/test_mock_service.py
git commit -m "feat: add mock service and API endpoints"
```

---

## Phase 3: Frontend Mock Management

### Task 7: Mock Management Views

**Files:**
- Create: `frontend/src/views/mock/index.vue`
- Create: `frontend/src/views/mock/SuiteEditor.vue`
- Create: `frontend/src/api/mock.ts`

**Step 1: Create API client**

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

export interface MockSuite {
  id: number
  name: string
  description: string
  is_enabled: boolean
  enable_compare: boolean
  created_by: string
  created_at: string
  updated_at: string
  rules: MockRule[]
  responses: MockResponse[]
  whitelists: MockWhitelist[]
}

export interface MockRule {
  id: number
  field: string
  operator: 'equals' | 'contains' | 'not_equals'
  value: string
}

export interface MockResponse {
  id: number
  path: string
  method: string
  response_json: string
  timeout_ms: number
  empty_response: boolean
}

export interface MockWhitelist {
  id: number
  type: 'clientId' | 'userId' | 'vid'
  value: string
}

export const mockApi = {
  getSuites: () => api.get<{ items: MockSuite[] }>('/mock/suites'),
  getSuite: (id: number) => api.get<MockSuite>(`/mock/suites/${id}`),
  createSuite: (data: Partial<MockSuite>) => api.post<MockSuite>('/mock/suites', data),
  updateSuite: (id: number, data: Partial<MockSuite>) => api.put<MockSuite>(`/mock/suites/${id}`, data),
  deleteSuite: (id: number) => api.delete(`/mock/suites/${id}`),
  copySuite: (id: number, newName: string) => api.post<MockSuite>(`/mock/suites/${id}/copy`, null, { params: { new_name: newName } })
}
```

**Step 2: Create mock index view**

```vue
<template>
  <div class="mock-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>Mock 套件管理</span>
          <el-button type="primary" @click="handleCreate">新建套件</el-button>
        </div>
      </template>

      <el-table :data="suites" v-loading="loading">
        <el-table-column prop="name" label="套件名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="is_enabled" label="状态">
          <template #default="{ row }">
            <el-switch v-model="row.is_enabled" @change="handleToggle(row)" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" @click="handleCopy(row)">复制</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <SuiteEditor
      v-if="showEditor"
      :suite="currentSuite"
      @close="handleEditorClose"
      @save="handleSave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { mockApi, MockSuite } from '@/api/mock'
import SuiteEditor from './SuiteEditor.vue'

const suites = ref<MockSuite[]>([])
const loading = ref(false)
const showEditor = ref(false)
const currentSuite = ref<MockSuite | null>(null)

const loadSuites = async () => {
  loading.value = true
  try {
    const { data } = await mockApi.getSuites()
    suites.value = data.items
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  currentSuite.value = null
  showEditor.value = true
}

const handleEdit = (suite: MockSuite) => {
  currentSuite.value = suite
  showEditor.value = true
}

const handleCopy = async (suite: MockSuite) => {
  const { value } = await ElMessageBox.prompt('请输入新套件名称', '复制套件', {
    inputValue: `${suite.name}_copy`
  })
  await mockApi.copySuite(suite.id, value)
  ElMessage.success('复制成功')
  loadSuites()
}

const handleDelete = async (suite: MockSuite) => {
  await ElMessageBox.confirm('确定删除该套件？', '提示')
  await mockApi.deleteSuite(suite.id)
  ElMessage.success('删除成功')
  loadSuites()
}

const handleToggle = async (suite: MockSuite) => {
  await mockApi.updateSuite(suite.id, { is_enabled: suite.is_enabled })
  ElMessage.success('状态更新成功')
}

const handleEditorClose = () => {
  showEditor.value = false
}

const handleSave = () => {
  showEditor.value = false
  loadSuites()
}

onMounted(() => {
  loadSuites()
})
</script>

<style scoped>
.mock-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

**Step 3: Commit**

```bash
git add frontend/src/views/mock/ frontend/src/api/mock.ts
git commit -m "feat: add mock management frontend views"
```

---

## Summary

This implementation plan covers:

1. **Phase 1**: Project skeleton (backend + frontend + Docker)
2. **Phase 2**: Mock service (models, schemas, service, API)
3. **Phase 3**: Frontend mock management views

**Remaining phases** (to be expanded in future plans):
- Phase 4: API Automation module
- Phase 5: UI Automation module
- Phase 6: History comparison feature

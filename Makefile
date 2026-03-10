# MirrorGate Makefile
# 一键开发和部署工具

.PHONY: help dev init-db create-admin verify logs clean test backend frontend

# 默认目标
help:
	@echo "MirrorGate 开发工具"
	@echo ""
	@echo "可用命令:"
	@echo "  make dev          - 一键启动开发环境"
	@echo "  make init-db      - 初始化数据库"
	@echo "  make create-admin - 创建管理员账号"
	@echo "  make verify       - 验证服务健康状态"
	@echo "  make logs         - 查看所有服务日志"
	@echo "  make clean        - 清理所有容器和数据卷"
	@echo "  make test         - 运行所有测试"
	@echo "  make test-e2e     - 运行 E2E 测试"
	@echo "  make test-e2e-ui  - 运行 E2E 测试（UI 模式）"
	@echo "  make test-e2e-headed - 运行 E2E 测试（有头模式）"
	@echo "  make backend      - 启动后端开发服务器"
	@echo "  make frontend     - 启动前端开发服务器"

# 一键启动开发环境（包含所有初始化）
dev: check-docker
	@echo "🚀 启动 MirrorGate 开发环境..."
	@echo ""
	@echo "Step 1: 检查环境变量配置"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "⚠️  已创建 .env 文件，请修改 MYSQL_PASSWORD 后重新运行 make dev"; \
		exit 1; \
	fi
	@echo "✅ 环境变量配置完成"
	@echo ""
	@echo "Step 2: 启动 Docker 服务..."
	docker-compose up -d
	@echo ""
	@echo "Step 3: 等待数据库就绪（10 秒）..."
	sleep 10
	@echo ""
	@echo "Step 4: 初始化数据库..."
	$(MAKE) init-db
	@echo ""
	@echo "Step 5: 创建管理员账号..."
	$(MAKE) create-admin
	@echo ""
	@echo "✅ 开发环境启动完成!"
	@echo ""
	@echo "访问地址:"
	@echo "  前端界面：http://localhost"
	@echo "  API 文档：http://localhost:8000/docs"
	@echo "  ReDoc 文档：http://localhost:8000/redoc"
	@echo ""
	@echo "管理员账号:"
	@echo "  用户名：admin"
	@echo "  密码：admin123"
	@echo ""
	@echo "运行 'make verify' 验证服务状态"

# 初始化数据库
init-db:
	@echo "📦 初始化数据库..."
	@docker-compose exec -T backend python init_db.py || \
		docker-compose exec -T backend alembic upgrade head
	@echo "✅ 数据库初始化完成"

# 创建管理员账号
create-admin:
	@echo "👤 创建管理员账号..."
	@docker-compose exec -T backend python create_admin.py
	@echo "✅ 管理员账号创建完成"
	@echo "  用户名：admin"
	@echo "  密码：admin123"

# 验证服务健康状态
verify:
	@echo "🔍 验证服务健康状态..."
	@echo ""
	@echo "检查 Docker 容器状态:"
	@docker-compose ps
	@echo ""
	@echo "检查后端健康:"
	@curl -sf http://localhost:8000/health && echo " ✅ 后端健康" || echo " ❌ 后端异常"
	@echo ""
	@echo "检查前端可访问:"
	@curl -sf http://localhost > /dev/null && echo " ✅ 前端可访问" || echo " ❌ 前端异常"
	@echo ""
	@echo "检查数据库连接:"
	@docker-compose exec -T backend python -c "from app.database import SessionLocal; SessionLocal().close(); print('✅ 数据库连接正常')" 2>/dev/null || echo " ❌ 数据库连接失败"
	@echo ""
	@echo "检查 Redis 连接:"
	@docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG && echo " ✅ Redis 连接正常" || echo " ❌ Redis 连接失败"
	@echo ""
	@echo "所有检查完成!"

# 查看所有服务日志
logs:
	docker-compose logs -f

# 查看特定服务日志
logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-mysql:
	docker-compose logs -f mysql

logs-redis:
	docker-compose logs -f redis

# 清理所有容器和数据卷
clean:
	@echo "🧹 清理开发环境..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ 清理完成"

# 运行所有测试
test: test-backend test-frontend test-e2e

test-backend:
	@echo "🧪 运行后端测试..."
	cd backend && pytest tests/ -v --cov=app --cov-report=term-missing

test-frontend:
	@echo "🧪 运行前端测试..."
	cd frontend && npm run test

test-e2e:
	@echo "🧪 运行 E2E 测试..."
	cd frontend && npx playwright install chromium && npx playwright test

test-e2e-ui:
	@echo "🎨 运行 E2E 测试（UI 模式）..."
	cd frontend && npx playwright test --ui

test-e2e-headed:
	@echo "🎭 运行 E2E 测试（有头模式）..."
	cd frontend && npx playwright test --headed

# 启动后端开发服务器
backend:
	@echo "🐍 启动后端开发服务器..."
	cd backend && \
	source venv/bin/activate 2>/dev/null || python -m venv venv && source venv/bin/activate && \
	pip install -r requirements.txt -q && \
	uvicorn app.main:app --reload --port 8000

# 启动前端开发服务器
frontend:
	@echo "🎨 启动前端开发服务器..."
	cd frontend && \
	if [ ! -d node_modules ]; then npm install; fi && \
	npm run dev

# 检查 Docker 是否安装
check-docker:
	@command -v docker >/dev/null 2>&1 || (echo "❌ Docker 未安装，请先安装 Docker: https://docs.docker.com/get-docker/" && exit 1)
	@command -v docker-compose >/dev/null 2>&1 || (echo "❌ Docker Compose 未安装，请先安装 Docker Compose" && exit 1)
	@echo "✅ Docker 环境检查通过"

# 重置管理员密码
reset-admin-password:
	@echo "🔑 重置管理员密码..."
	@docker-compose exec -T backend python -c "\
from app.database import SessionLocal; \
from app.models.user import User; \
from passlib.context import CryptContext; \
db = SessionLocal(); \
admin = db.query(User).filter(User.username == 'admin').first(); \
ctx = CryptContext(schemes=['bcrypt'], deprecated='auto'); \
admin.password_hash = ctx.hash('admin123'); \
db.commit(); \
print('管理员密码已重置为：admin123')"

# 备份数据库
backup-db:
	@echo "💾 备份数据库..."
	@mkdir -p backups
	docker-compose exec mysql mysqldump -u root -p$${MYSQL_PASSWORD} mirror_gate > backups/mysql-backup-$$(date +%Y%m%d-%H%M%S).sql
	@echo "✅ 数据库备份完成：backups/"

# 清理重复分组
clean-duplicate-groups:
	@echo "🧹 清理重复分组数据..."
	docker-compose cp backend/clean_duplicate_groups.py backend:/app/clean_duplicate_groups.py
	docker-compose exec -T backend python clean_duplicate_groups.py
	@echo "✅ 清理完成"

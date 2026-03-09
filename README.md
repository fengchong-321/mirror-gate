# Claude Code Configuration

个人 Claude Code 配置仓库，包含自定义 skills、rules、commands 和 agents。

## 目录结构

```
.claude/
├── CLAUDE.md              # 全局指令和项目上下文
├── settings.json          # Claude Code 设置
├── README.md              # 本文件
│
├── skills/                # 技能模块
│   ├── search-first/      # 编码前研究流程 (优先使用 context7)
│   ├── fetch-docs/        # 快速文档获取
│   ├── tdd-workflow/      # TDD 开发流程
│   ├── python-patterns/   # Python 最佳实践
│   ├── golang-patterns/   # Go 最佳实践
│   └── ...                # 更多技能
│
├── rules/                 # 编码规则
│   ├── common/            # 通用规则
│   │   ├── coding-style.md
│   │   ├── testing.md
│   │   ├── security.md
│   │   └── ...
│   ├── python/            # Python 特定规则
│   ├── golang/            # Go 特定规则
│   ├── typescript/        # TypeScript 特定规则
│   └── swift/             # Swift 特定规则
│
├── commands/              # 自定义命令
│   ├── plan.md            # /plan - 实现计划
│   ├── tdd.md             # /tdd - TDD 工作流
│   ├── code-review.md     # /code-review - 代码审查
│   └── ...
│
├── agents/                # 子代理定义
│   ├── planner.md         # 计划代理
│   ├── code-reviewer.md   # 代码审查代理
│   ├── tdd-guide.md       # TDD 指导代理
│   └── ...
│
└── hooks/                 # 钩子脚本
    ├── hooks.json         # 钩子配置
    └── scripts/           # 钩子脚本
```

## 核心功能

### Skills (技能)

| 技能 | 描述 |
|------|------|
| `search-first` | 编码前研究流程，优先使用 context7 获取库文档 |
| `fetch-docs` | 快速文档获取，三级降级策略 |
| `tdd-workflow` | 测试驱动开发流程，80%+ 覆盖率要求 |
| `python-patterns` | Python 最佳实践和代码模式 |
| `golang-patterns` | Go 惯用模式和最佳实践 |
| `security-review` | 安全审查检查清单 |

### Commands (命令)

| 命令 | 描述 |
|------|------|
| `/plan` | 创建实现计划，等待用户确认 |
| `/tdd` | TDD 工作流，测试先行 |
| `/code-review` | 代码审查 |
| `/build-fix` | 修复构建错误 |
| `/e2e` | E2E 测试 |

### Rules (规则)

- **通用规则**: 编码风格、测试要求、安全指南
- **语言规则**: Python/Go/TypeScript/Swift 特定规则
- **覆盖**: 测试覆盖率 80%+、无硬编码密钥、不可变数据

## 文档获取流程

更新后的 `search-first` 技能优先使用 context7：

```
1. NEED ANALYSIS       - 定义需求
2. CONTEXT7 (首选)     - resolve-library-id → query-docs
   ↓ 没找到
3. PARALLEL SEARCH     - npm/PyPI/MCP/GitHub
4. EVALUATE            - 评估候选方案
5. DECIDE              - Adopt/Extend/Build
6. IMPLEMENT           - 实现
```

### Context7 常用库 ID

| 库 | Library ID |
|----|------------|
| React | `/websites/react_dev` |
| Next.js | `/vercel/next.js` |
| FastAPI | `/websites/fastapi_tiangolo` |
| Django | `/django/django` |
| Go | `/golang/go` |
| PostgreSQL | `/postgres/postgres` |

## MCP 服务

配置的 MCP 服务：

| 服务 | 用途 |
|------|------|
| context7 | 获取编程库最新文档 |
| web-search-prime | 网页搜索 |
| web-reader | 网页内容抓取 |
| zread | GitHub 仓库读取 |

## 安装

将此仓库克隆到 `~/.claude` 目录：

```bash
git clone <repo-url> ~/.claude
```

## 更新

```bash
cd ~/.claude && git pull
```

## 关联项目

- [mirror-gate](https://github.com/fengchong-321/mirror-gate) - 主要开发项目

## 许可证

MIT

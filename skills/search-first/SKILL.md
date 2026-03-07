---
name: search-first
description: Research-before-coding workflow. Search for existing tools, libraries, and patterns before writing custom code. Invokes the researcher agent.
origin: ECC
---

# /search-first — Research Before You Code

Systematizes the "search for existing solutions before implementing" workflow.

## Trigger

Use this skill when:
- Starting a new feature that likely has existing solutions
- Adding a dependency or integration
- The user asks "add X functionality" and you're about to write code
- Before creating a new utility, helper, or abstraction

## Workflow

```
┌─────────────────────────────────────────────┐
│  1. NEED ANALYSIS                           │
│     Define what functionality is needed      │
│     Identify language/framework constraints  │
├─────────────────────────────────────────────┤
│  2. CONTEXT7 (首选 - 查库文档)               │
│     ┌──────────────────────────────────┐    │
│     │  resolve-library-id → query-docs │    │
│     │  获取主流库的官方文档和代码示例      │    │
│     └──────────────────────────────────┘    │
│              ↓ 没找到或不适用                 │
├─────────────────────────────────────────────┤
│  3. PARALLEL SEARCH (researcher agent)      │
│     ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│     │  npm /   │ │  MCP /   │ │  GitHub / │  │
│     │  PyPI    │ │  Skills  │ │  Web      │  │
│     └──────────┘ └──────────┘ └──────────┘  │
├─────────────────────────────────────────────┤
│  4. EVALUATE                                │
│     Score candidates (functionality, maint, │
│     community, docs, license, deps)         │
├─────────────────────────────────────────────┤
│  5. DECIDE                                  │
│     ┌─────────┐  ┌──────────┐  ┌─────────┐  │
│     │  Adopt  │  │  Extend  │  │  Build   │  │
│     │ as-is   │  │  /Wrap   │  │  Custom  │  │
│     └─────────┘  └──────────┘  └─────────┘  │
├─────────────────────────────────────────────┤
│  6. IMPLEMENT                               │
│     Install package / Configure MCP /       │
│     Write minimal custom code               │
└─────────────────────────────────────────────┘
```

## Step 2: Context7 (新增 - 优先步骤)

**触发条件**：需要查询编程库/框架的文档、API、用法时

**调用方式**：
```
1. mcp__context7__resolve-library-id(libraryName="库名", query="查询意图")
   → 返回 libraryId (如 "/websites/react_dev")

2. mcp__context7__query-docs(libraryId="/websites/react_dev", query="具体问题")
   → 返回官方文档和代码示例
```

**常用库 ID 参考**：
| 库 | Library ID |
|----|------------|
| React | `/websites/react_dev` |
| Next.js | `/vercel/next.js` |
| Vue | `/vuejs/docs` |
| Python | `/python/cpython` |
| FastAPI | `/fastapi/fastapi` |
| Django | `/django/django` |
| Go | `/golang/go` |
| PostgreSQL | `/postgres/postgres` |
| Supabase | `/supabase/supabase` |
| Tailwind CSS | `/tailwindlabs/tailwindcss` |
| Prisma | `/prisma/prisma` |

**何时跳过 context7**：
- 查询非编程库内容（如配置文件、部署方案）
- 小众库/私有库（context7 没有）
- 需要最新 GitHub issue/讨论

## Decision Matrix

| Signal | Action |
|--------|--------|
| Exact match, well-maintained, MIT/Apache | **Adopt** — install and use directly |
| Partial match, good foundation | **Extend** — install + write thin wrapper |
| Multiple weak matches | **Compose** — combine 2-3 small packages |
| Nothing suitable found | **Build** — write custom, but informed by research |

## How to Use

### Quick Mode (inline)

Before writing a utility or adding functionality, mentally run through:

1. **Is this a library/framework question?** → **context7 first** (resolve-library-id → query-docs)
2. Is this a common problem? → Search npm/PyPI
3. Is there an MCP for this? → Check `~/.claude/settings.json` and search
4. Is there a skill for this? → Check `~/.claude/skills/`
5. Is there a GitHub template? → Search GitHub

### Full Mode (agent)

For non-trivial functionality, launch the researcher agent:

```
Task(subagent_type="general-purpose", prompt="
  Research existing tools for: [DESCRIPTION]
  Language/framework: [LANG]
  Constraints: [ANY]

  Search: npm/PyPI, MCP servers, Claude Code skills, GitHub
  Return: Structured comparison with recommendation
")
```

## Search Shortcuts by Category

### Development Tooling
- Linting → `eslint`, `ruff`, `textlint`, `markdownlint`
- Formatting → `prettier`, `black`, `gofmt`
- Testing → `jest`, `pytest`, `go test`
- Pre-commit → `husky`, `lint-staged`, `pre-commit`

### AI/LLM Integration
- **任何库/框架文档** → **context7 (首选)**: `mcp__context7__resolve-library-id` → `mcp__context7__query-docs`
- Claude SDK → Context7 for latest docs
- Prompt management → Check MCP servers
- Document processing → `unstructured`, `pdfplumber`, `mammoth`

### Data & APIs
- HTTP clients → `httpx` (Python), `ky`/`got` (Node)
- Validation → `zod` (TS), `pydantic` (Python)
- Database → Check for MCP servers first

### Content & Publishing
- Markdown processing → `remark`, `unified`, `markdown-it`
- Image optimization → `sharp`, `imagemin`

## Integration Points

### With planner agent
The planner should invoke researcher before Phase 1 (Architecture Review):
- Researcher identifies available tools
- Planner incorporates them into the implementation plan
- Avoids "reinventing the wheel" in the plan

### With architect agent
The architect should consult researcher for:
- Technology stack decisions
- Integration pattern discovery
- Existing reference architectures

### With iterative-retrieval skill
Combine for progressive discovery:
- Cycle 1: Broad search (npm, PyPI, MCP)
- Cycle 2: Evaluate top candidates in detail
- Cycle 3: Test compatibility with project constraints

## Examples

### Example 1: "Add dead link checking"
```
Need: Check markdown files for broken links
Search: npm "markdown dead link checker"
Found: textlint-rule-no-dead-link (score: 9/10)
Action: ADOPT — npm install textlint-rule-no-dead-link
Result: Zero custom code, battle-tested solution
```

### Example 2: "Add HTTP client wrapper"
```
Need: Resilient HTTP client with retries and timeout handling
Search: npm "http client retry", PyPI "httpx retry"
Found: got (Node) with retry plugin, httpx (Python) with built-in retry
Action: ADOPT — use got/httpx directly with retry config
Result: Zero custom code, production-proven libraries
```

### Example 3: "Add config file linter"
```
Need: Validate project config files against a schema
Search: npm "config linter schema", "json schema validator cli"
Found: ajv-cli (score: 8/10)
Action: ADOPT + EXTEND — install ajv-cli, write project-specific schema
Result: 1 package + 1 schema file, no custom validation logic
```

## Anti-Patterns

- **Jumping to code**: Writing a utility without checking if one exists
- **Ignoring MCP**: Not checking if an MCP server already provides the capability
- **Over-customizing**: Wrapping a library so heavily it loses its benefits
- **Dependency bloat**: Installing a massive package for one small feature

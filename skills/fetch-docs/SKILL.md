---
name: fetch-docs
description: 获取编程库和框架的最新文档。优先使用 context7，失败时自动降级到网页搜索。Use when the user asks about library documentation, API references, code examples, or how to use a specific library/framework. Triggers on queries like "查下 React 文档", "FastAPI 怎么用", "查下某个库的用法".
---

# 文档获取流程

按优先级依次尝试以下方法，直到成功获取文档：

## 流程图

```
用户查询 → context7 → 成功 → 返回结果
              ↓ 失败
         web-search-prime → 找到官方文档 → web-reader → 返回结果
              ↓ 找不到
         WebSearch + WebFetch → 返回结果
```

## Step 1: context7 (首选)

适用场景：主流编程库和框架

```
1. 调用 mcp__context7__resolve-library-id 获取库 ID
2. 调用 mcp__context7__query-docs 查询具体问题
```

示例：
```
mcp__context7__resolve-library-id(libraryName="react", query="hooks")
→ 得到 libraryId: "/websites/react_dev"

mcp__context7__query-docs(libraryId="/websites/react_dev", query="useEffect cleanup")
```

## Step 2: web-search-prime + web-reader (降级方案)

适用场景：context7 没有的库，或需要官方文档

```
1. mcp__web-search-prime__web_search_prime 搜索
2. mcp__web-reader__webReader 读取官方文档页面
```

搜索技巧：
- 添加 "official documentation" 或 "官方文档" 关键词
- 优先选择官方网站域名

## Step 3: WebSearch + WebFetch (最终降级)

适用场景：以上方法都失败时

```
1. WebSearch 搜索
2. WebFetch 抓取页面内容
```

## 常用库的 context7 ID 参考

| 库名 | Library ID |
|------|------------|
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

## 使用示例

**用户**: "查下 React useEffect 怎么用"

**执行**:
1. context7 已有 React，直接查询：
   ```
   mcp__context7__query-docs(
     libraryId="/websites/react_dev",
     query="useEffect hook usage and cleanup"
   )
   ```

**用户**: "查下某个小众库 xxx 的文档"

**执行**:
1. 先尝试 context7 resolve-library-id
2. 如果找不到，用 web-search-prime 搜索 "xxx library documentation"
3. 用 web-reader 读取官方文档页面

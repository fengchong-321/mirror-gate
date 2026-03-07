# 添加知识点到个人知识库

将用户提供的主题搜索、整理并记录到 `~/knowledge-base` 知识库中。

## 参数

- 主题: $ARGUMENTS

## 执行流程

### 1. 确认主题和分类

如果用户没有指定分类，询问用户选择：
- `programming` - 编程语言、框架、算法
- `tools` - 开发工具、CLI、配置
- `concepts` - 概念、原理、设计模式
- `snippets` - 代码片段、常用模板

### 2. 搜索信息

使用 WebSearch 工具搜索相关内容，获取准确、最新的信息。

### 3. 整理知识点

按照以下模板格式整理：

```markdown
# {标题}

> 标签: #{tag1} #{tag2} #{tag3}
> 创建时间: {当前日期 YYYY-MM-DD}
> 来源: {参考链接}

## 概述

{1-2句话摘要}

## 详细内容

{分章节详细说明，包含代码示例、表格等}

## 相关知识点

- [[{相关知识点名称}]]

---
*采集自 Claude Code 对话*
```

### 4. 写入文件

- 文件路径: `~/knowledge-base/{分类}/{文件名}.md`
- 文件名使用英文小写 + 连字符，如 `skill-vs-mcp.md`

### 5. 更新索引

更新 `~/knowledge-base/README.md` 的知识索引表格，新增一行记录。

### 6. Git 提交推送

```bash
cd ~/knowledge-base
git add .
git commit -m "Add: {知识点标题}"
git push
```

### 7. 告知用户

完成后告诉用户：
- 记录了什么内容（标题和核心要点）
- 文件位置
- GitHub 链接

## 示例用法

```
/add-knowledge React Hooks 最佳实践
```

```
/add-knowledge 数据库索引原理 -c concepts
```

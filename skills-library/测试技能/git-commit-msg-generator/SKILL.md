---
name: git-commit-msg-generator
description: "This skill should be used when the user asks to 'generate a commit message', 'git commit', 'push to remote', 'commit and push', 'help me commit', or '生成提交信息', '提交代码', '推送到云端', '帮我提交'. Automates the Git staging → commit message generation → user confirmation → push workflow."
---

# Git 暂存区生成提交并推送云端

## Overview

Automate the Git commit workflow: check staging area → generate standardized Chinese commit message → user confirmation → commit and push. Eliminates repetitive manual commit message writing and ensures consistent format.

> 注意：该技能不需要遵循 AGENT.md 规范文件。

## Checklist

Complete the following steps in order:

1. Activate terminal — run `pwd` (macOS/Linux) or `dir` (Windows)
2. Check staging area — run `git diff --cached`
3. Auto-stage if empty — run `git add .` if staging area is empty
4. Generate commit message — analyze diff and produce formatted message
5. Confirm with user — show message and ask for yes/no confirmation
6. Commit and push — run `git commit` then `git push` on confirmation
7. Report result — summarize the outcome to the user

## Process

**Step 1: Activate terminal**

Run `pwd` on macOS/Linux or `dir` on Windows before any other command. This activates the terminal port and avoids potential execution bugs.

**Step 2: Check staging area**

Run `git diff --cached` to check for staged changes.

- If staging area is empty, run `git add .` to stage all changes
- If still empty after `git add`, stop and inform the user there are no changes to commit

**Step 3: Generate commit message**

Analyze the staged diff and generate a commit message following this format:

```
类型(范围): 简要描述

变更说明1

变更说明2

[日期] YYYYMMDD
```

Commit types:

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 |
| `refactor` | 重构 |
| `style` | 格式 |
| `docs` | 文档 |
| `test` | 测试 |
| `chore` | 工具变动 |

For detailed examples and edge cases, see `references/commit-format.md`.

**Step 4: Confirm with user**

Display the generated commit message and ask: "是否使用此提交信息进行提交？"

- Use an interactive yes/no tool if available
- If user declines, regenerate based on their feedback

**Step 5: Commit and push**

On confirmation, run:

```bash
git commit -m "提交信息"
git push
```

**Step 6: Report result**

Report success or failure with details (branch name, commit hash, push status).

## Key Principles

- User confirmation required before every commit — never auto-commit
- Auto-stage when staging area is empty to reduce friction
- Report each step's outcome transparently
- Keep commit messages in Chinese, following the format strictly

## Additional Resources

### Reference Files

- **`references/commit-format.md`** — Commit message format spec, examples, and edge cases

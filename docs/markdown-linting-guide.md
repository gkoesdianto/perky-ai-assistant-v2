# Markdown Linting Guide

## Overview

This guide explains how to handle Markdown linting warnings and maintain consistent documentation formatting.

## Common Markdown Lint Rules

### MD022 - Headings should be surrounded by blank lines

**Before:**

```markdown
Some text
## Heading
Next paragraph
```

**After:**

```markdown
Some text

## Heading

Next paragraph
```

### MD031 - Fenced code blocks should be surrounded by blank lines

**Before:**

```markdown
Some text
```python
code here
```

Next text

```text

**After:**

```markdown
Some text

```python
code here
```

Next text

```text

### MD032 - Lists should be surrounded by blank lines

**Before:**

```markdown
Some text
- List item 1
- List item 2
Next text
```

**After:**

```markdown
Some text

- List item 1
- List item 2

Next text
```

### MD040 - Fenced code blocks should have a language specified

**Before:**

```markdown
```text
code here
```

```text

**After:**

```markdown
```python
code here
```

```text

### MD034 - No bare URLs

URLs should be enclosed in angle brackets or used as proper links.

**Before:**

```markdown
Visit http://example.com for more info
```

**After:**

```markdown
Visit <http://example.com> for more info
OR
Visit [our website](http://example.com) for more info
```

### MD047 - Files should end with a single newline character

Ensure your file ends with exactly one newline character (Unix standard).

## Setup Instructions

### 1. Install markdownlint CLI

```bash
npm install -g markdownlint-cli
```

### 2. VS Code Extension

Install the markdownlint extension for real-time linting:

```bash
code --install-extension DavidAnson.vscode-markdownlint
```

### 3. Pre-commit Hooks

Install pre-commit and configure hooks:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hook scripts
pre-commit install

# Run against all files (first time)
pre-commit run --all-files
```

## Usage

### Manual Linting

```bash
# Check all Markdown files
markdownlint "**/*.md"

# Auto-fix issues
markdownlint "**/*.md" --fix

# Check specific file
markdownlint workflow-sprint-1.1.md

# Fix specific file
markdownlint workflow-sprint-1.1.md --fix
```

### VS Code Commands

1. **Quick Fix All**: `Cmd/Ctrl + Shift + P` → "markdownlint: Fix all supported document issues"
2. **Format Document**: `Shift + Alt + F` (with markdownlint formatter configured)

### Configuration

The `.markdownlint.json` file configures the linting rules:

```json
{
  "MD022": { "lines_above": 1, "lines_below": 1 },
  "MD031": { "list_items": false },
  "MD040": { "allowed_languages": ["", "text", "bash", "python"] }
}
```

## Best Practices

1. **Consistent Formatting**: Always add blank lines around headings, code blocks, and lists
2. **Language Specification**: Always specify the language for code blocks
3. **File Endings**: Ensure files end with a single newline
4. **Automation**: Use pre-commit hooks to catch issues before committing
5. **Editor Integration**: Configure your editor to format on save

## Troubleshooting

### Issue: Too many warnings

Solution: Run `markdownlint --fix` to auto-fix most issues

### Issue: VS Code not showing warnings

Solution: Ensure the markdownlint extension is enabled and the workspace is trusted

### Issue: Pre-commit hooks failing

Solution: Run `pre-commit run --all-files` to fix issues before committing

## Quick Reference

| Rule | Description | Fix |
|------|-------------|-----|
| MD022 | Missing blank lines around headings | Add blank lines before/after |
| MD031 | Missing blank lines around code blocks | Add blank lines before/after |
| MD032 | Missing blank lines around lists | Add blank lines before/after |
| MD034 | Bare URL used | Wrap in angle brackets `<URL>` |
| MD040 | No language specified for code block | Add language after ``` |
| MD047 | No trailing newline | Add single newline at end |

## Additional Resources

- [Markdownlint Rules Documentation](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md)
- [CommonMark Specification](https://commonmark.org/)
- [VS Code Markdown Support](https://code.visualstudio.com/docs/languages/markdown)

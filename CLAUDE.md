# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a macOS-based automated system that monitors preprint platforms (arXiv, bioRxiv, medRxiv, SSRN) for research papers related to "AI Agents for Scientific Research," filters them using AI, generates Chinese summaries, and sends them to Feishu (Lark) via OpenClaw Gateway.

## Development Commands

### Running the System

```bash
# Fetch and process papers from configured platforms
python3 src/main.py fetch

# Send the briefing to Feishu
python3 src/main.py send

# Test message formatting (doesn't send)
python3 src/main.py test

# View statistics
python3 src/main.py stats

# Clean up old data
python3 src/main.py cleanup
```

### Date-Specific Operations

```bash
# Fetch papers for a specific date
python3 src/main.py fetch --date 2026-02-20

# Send briefing for a specific date
python3 src/main.py send --date 2026-02-20
```

### Testing

```bash
# Run individual test files in project root
python3 test_summarizer.py       # Test summarizer functionality
python3 test_skill.py            # Test skill integration
python3 test_pdf_*.py            # Test PDF processing variants
```

### Service Management (macOS launchd)

```bash
# Check service status
launchctl list | grep research.briefing

# Load/unload services
launchctl load ~/Library/LaunchAgents/com.research.briefing.fetch.plist
launchctl load ~/Library/LaunchAgents/com.research.briefing.send.plist
```

## Architecture

### Core Flow

```
launchd (scheduler) → Shell Scripts → Python Main → Fetchers → AI Filter → Summarizer → Storage → Formatter → OpenClaw Gateway → Feishu
```

### Key Components

**Entry Point**: `src/main.py`
- `ResearchBriefingSystem` class orchestrates the workflow
- Commands: fetch, send, test, cleanup, stats

**Fetchers** (`src/fetchers/`):
- `base.py`: Abstract base class
- `arxiv_fetcher.py`: RSS-based, with pagination support
- `biorxiv_fetcher.py`: API-based for bioRxiv/medRxiv
- Each implements `fetch_papers(date, limit)` returning paper dictionaries

**Processors** (`src/processors/`):
- `ai_filter.py`: Claude Code CLI-based relevance filtering
- `embedding_filter.py`: OpenAI/Zhipu AI embedding-based filtering
- `summarizer.py`: Paper summarization using custom skill
- Supports multiple filtering modes: hybrid, keywords-only, embedding-only, Claude-only

**Storage** (`src/utils/storage.py`):
- SQLite database at `data/briefings.db`
- Tables: `briefings`, `processed_papers`
- Automatic cleanup (90-day retention), VACUUM, REINDEX

**Formatter** (`src/formatters/feishu_formatter.py`):
- Formats briefing messages for Feishu

### Custom Skill Integration

**`skills/paper-summarizer/SKILL.md`**: Specialized paper summarization skill
- YAML frontmatter with metadata
- Extracts: research problem, methods, results (with quantitative data), applications
- Used by `summarizer.py` via Claude Code CLI skill invocation
- Root-level `paper-summarizer.skill` is a ZIP archive

## Configuration

**`config.yaml`**: Main configuration
- Platform settings (categories, API URLs, batch sizes)
- AI filtering mode and parameters
- Summarizer settings (timeout, skill path)
- OpenClaw integration
- Storage options

**`.env`**: Environment variables (create manually)
- `OPENCLAW_GATEWAY_TOKEN`: OpenClaw Gateway token
- `OPENCLAW_FEISHI_TARGET`: Feishu target ID
- `ZHIPU_API_KEY`: Zhipu AI API key for embeddings

## Important Architecture Notes

1. **Claude Code CLI Integration**: The system uses Claude Code CLI (not direct Anthropic API calls) for AI filtering and summarization. This is invoked via shell commands in `src/processors/ai_filter.py` and `src/processors/summarizer.py`.

2. **Multi-Filter Strategy**: Papers go through a staged filtering process:
   - Keyword matching (initial filter)
   - Embedding similarity (if enabled)
   - Claude CLI relevance judgment (final filter)

3. **De-duplication**: `processed_papers` table tracks papers by DOI to prevent reprocessing.

4. **Skill-based Summarization**: The summarizer uses the custom `paper-summarizer` skill via Claude Code CLI's skill system, not inline prompts.

5. **Error Handling**: Failures during fetch/summarize don't stop the entire process. The system continues with remaining papers and logs errors.

6. **Scheduled Execution**: macOS launchd services handle daily automation with wake-at-time support (5:55 AM for 6:00 AM execution).

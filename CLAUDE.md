# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an automated system that monitors preprint platforms (arXiv, bioRxiv, medRxiv) for research papers related to "AI Agents for Scientific Research," filters them using AI, and generates Chinese summaries saved to local files.

## Development Commands

### Running the System

```bash
# Complete workflow: fetch → filter → summarize → generate output files
python3 src/main.py run

# Fetch and process papers only (saves to database, no output)
python3 src/main.py fetch

# View statistics
python3 src/main.py stats

# Test message formatting (doesn't send)
python3 src/main.py test

# View statistics
python3 src/main.py stats

# Clean up old data
python3 src/main.py cleanup
```

### Date-Specific Operations

```bash
# Run complete workflow for a specific date
python3 src/main.py run --date 2026-02-20

# Fetch papers for a specific date
python3 src/main.py fetch --date 2026-02-20

# Send briefing for a specific date
python3 src/main.py send --date 2026-02-20
```

### Service Management

No scheduled tasks configured. Run manually with `python3 src/main.py run`.

### Viewing Logs

```bash
# View today's log
tail -f logs/research_briefing_$(date +%Y-%m-%d).log

# View all recent logs
tail -f logs/*.log
```

## Architecture

### Core Flow

```
Python Main → Fetchers → AI Filter → PDF Download → Summarizer → Storage → Formatter → Output Files
```

### Key Components

**Entry Point**: `src/main.py`
- `ResearchBriefingSystem` class orchestrates the workflow
- Commands: `run`, `fetch`, `send`, `test`, `cleanup`, `stats`
- `run` command generates output files to `data/briefings/output/`
- `fetch` command processes and saves to database only

**Fetchers** (`src/fetchers/`):
- `base.py`: Abstract base class with paper normalization
- `arxiv_fetcher.py`: Atom/RSS API with pagination support (batch_size=100)
- `biorxiv_fetcher.py`: bioRxiv/medRxiv public API
- Each implements `fetch_papers(date, limit)` returning paper dictionaries

**Processors** (`src/processors/`):
- `ai_filter.py`: Multi-stage filtering (keywords → Claude CLI with paper-relevance-judge skill)
- `embedding_filter.py`: OpenAI embedding-based semantic filtering
- `zhipu_embedding_filter.py`: Zhipu AI embedding filtering
- `summarizer.py`: Paper summarization using paper-summarizer skill with PDF support
- Filtering modes: `hybrid`, `keywords`, `embedding`, `claude`

**Storage** (`src/utils/storage.py`):
- SQLite database at `data/briefings.db`
- Tables: `briefings` (date-indexed), `processed_papers` (DOI-based deduplication)
- Automatic cleanup (90-day retention), VACUUM, REINDEX

**Formatter** (`src/formatters/feishu_formatter.py`):
- Formats briefing messages
- Supports markdown-style formatting

**PDF Downloader** (`src/utils/pdf_downloader.py`):
- Downloads PDFs from arXiv, bioRxiv, medRxiv
- Extracts text using PyMuPDF4LLM (Markdown-optimized)
- Auto-cleanup after processing

### Custom Skills

**`skills/paper-relevance-judge/SKILL.md`**:
- Judges if a paper is related to "AI Agents for Scientific Research"
- Outputs: Decision (YES/NO), Reasoning, Confidence
- Used by `ai_filter.py` for relevance filtering

**`skills/paper-summarizer/SKILL.md`**:
- Specialized paper summarization skill
- Extracts: research problem, methods, results (with quantitative data), applications
- Used by `summarizer.py` via Claude Code CLI
- Reference examples in `skills/paper-summarizer/references/EXAMPLES.md`

## Configuration

**`config.yaml`**: Main configuration

```yaml
# Platform settings
platforms:
  arxiv:
    categories: [cs.AI, cs.CL, cs.LG, cs.NE, cs.CR, cs.CV]
    batch_size: 100
  biorxiv:
    sections: [bioinformatics]
  medrxiv:
    sections: [health-informatics]

# AI filtering
ai_filter:
  mode: "hybrid"              # hybrid | keywords | embedding | claude
  max_workers: 2              # Parallel threads (keep ≤2 to avoid errors)
  max_summary_papers: 10      # Max papers in final briefing

# PDF download
pdf_download:
  enabled: true
  max_text_length: 30000
  auto_cleanup: true

# Summarizer
summarizer:
  single_paper_timeout: 600   # 10 minutes per paper
  skill_path: "skills/paper-summarizer/SKILL.md"
```

**`.env`**: Environment variables (create manually)
- `ZHIPU_API_KEY`: Zhipu AI API key for embeddings (optional)

## Important Architecture Notes

1. **Claude Code CLI Integration**: The system uses Claude Code CLI (not direct Anthropic API calls) for AI filtering and summarization. Invoked via `subprocess` in `ai_filter.py` and `summarizer.py`.

2. **Multi-Stage Filtering**:
   ```
   Keywords (fast) → Embedding (semantic) → Claude CLI (precise)
   ```
   - Keyword matching filters ~80% of papers quickly
   - Remaining papers go through Claude CLI with paper-relevance-judge skill

3. **Parallel Processing**: Uses `ThreadPoolExecutor` for concurrent AI calls. **Keep `max_workers ≤ 2`** to avoid "Execution error" from Claude CLI resource contention.

4. **De-duplication**: `processed_papers` table tracks papers by DOI to prevent reprocessing across runs.

5. **PDF Processing**: Downloads PDFs, extracts text with PyMuPDF4LLM, uses full text for summarization (not just abstract). Auto-deletes PDFs after processing.

6. **Output Files**:
   - `data/briefings/briefings/YYYY-MM-DD.json` - Full briefing data (JSON)
   - `data/briefings/output/YYYY-MM-DD.txt` - Formatted text output (from `run` command)
   - `logs/research_briefing_YYYY-MM-DD.log` - Daily log file

7. **Error Handling**: Individual paper failures don't stop the process. System continues and logs errors.

8. **Manual Execution**: Run `python3 src/main.py run` manually to generate briefings.

## Project Structure

```
research-daily-briefing/
├── config.yaml                     # Main configuration
├── .env                            # Environment variables
├── src/
│   ├── main.py                     # Entry point
│   ├── fetchers/                   # Paper fetchers
│   │   ├── base.py
│   │   ├── arxiv_fetcher.py
│   │   └── biorxiv_fetcher.py
│   ├── processors/                 # AI processing
│   │   ├── ai_filter.py
│   │   ├── embedding_filter.py
│   │   ├── zhipu_embedding_filter.py
│   │   └── summarizer.py
│   ├── formatters/
│   │   └── feishu_formatter.py
│   └── utils/
│       ├── logger.py
│       ├── storage.py
│       └── pdf_downloader.py
├── skills/                         # Claude Code Skills
│   ├── paper-relevance-judge/
│   │   └── SKILL.md
│   └── paper-summarizer/
│       ├── SKILL.md
│       ├── skill.json
│       └── references/EXAMPLES.md
├── data/                           # Runtime data (git-ignored)
│   ├── briefings/
│   │   ├── briefings/              # JSON files
│   │   └── output/                 # TXT files
│   ├── papers/                     # Temporary PDF storage
│   └── briefings.db                # SQLite database
└── logs/                           # Log files
```

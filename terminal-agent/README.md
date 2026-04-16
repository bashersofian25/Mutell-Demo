# PoS Terminal Recording Agent

A lightweight Python agent that runs on Point-of-Sale terminals to capture customer-agent text interactions during configurable time windows (slots) and submit them to the Mutell API.

## Status

**Implementation pending.** This directory contains the scaffold only. All source files are placeholders.

## Overview

The terminal agent:

1. Accumulates interaction text during a configurable slot duration (e.g., 5 minutes)
2. POSTs the recorded slot to the backend API at the end of each window
3. Retries failed submissions with exponential backoff
4. Buffers failed uploads to local disk for recovery
5. Syncs configuration from API responses

## Configuration

Environment variables (see `.env.example`):

- `API_BASE_URL` — Backend API base URL
- `API_KEY` — Terminal-specific API key
- `SLOT_DURATION_SECS` — Recording window duration (default: 300)
- `RETRY_ATTEMPTS` — Max retry attempts for failed uploads (default: 3)
- `RETRY_BACKOFF_SECS` — Seconds between retries (default: 5)

## Quick Start

```bash
# Install dependencies
pip install -e .

# Set environment variables
cp .env.example .env

# Run the agent
python -m src.main
```

## Docker

```bash
docker build -t mutell-terminal-agent .
docker run --env-file .env mutell-terminal-agent
```

## Architecture

```
config/settings.py     — Configuration loader from env vars
src/main.py            — Entry point, orchestrates the recording loop
src/recorder.py        — Text accumulation logic during a slot window
src/slot.py            — Slot data model
src/uploader.py        — HTTP POST to API
src/retry.py           — Retry + backoff logic
src/buffer.py          — Local disk buffer for failed uploads
src/sync.py            — Config sync from API response
```

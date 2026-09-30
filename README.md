# Claude Sonnet 5.5 Developer Guide: between_tools, Effort & 5 Breaking Changes


Companion code for the **Technical Potpourri** YouTube video *"Claude Sonnet 5.5 Developer Guide: between_tools, Effort & 5 Breaking Changes"* (host: Sudipta Deb).

YouTube Video Link: 

The video walks through migrating a Sonnet 5 codebase to `claude-sonnet-5-5`: the five breaking changes (plus one silent one), and a data-driven way to route work between Sonnet 5.5 and Opus 5.5. Each script here maps to one scene of the demo.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install --upgrade anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
python -c "import anthropic; print(anthropic.__version__)"
```

## Scripts

| File | Video scene | What it shows | Runnable? |
|---|---|---|---|
| [01_Error.py](01_Error.py) | Hook | Reproduces the `400` when `thinking: {"type": "disabled"}` is sent to Sonnet 5.5. Run with `--fix` to use `between_tools` instead. | Yes |
| [02_first_call.py](02_first_call.py) | Demo 2 — First request | Minimal Sonnet 5.5 call: no date suffix, no `thinking` field (adaptive by default), `effort` instead of temperature, and reading the response by block type rather than `content[0]`. | Yes |
| [03_model_effort_sweep.py](03_model_effort_sweep.py) | Demo 3 — Sonnet vs Opus | Runs one Apex/SOQL-in-a-loop prompt across both models and four effort levels (`low`/`medium`/`high`/`xhigh`), streaming each call, and prints time, output tokens and cost. Answers are saved to [answers/](answers/) for side-by-side quality review. | Yes (makes 8 API calls; `xhigh` can be slow and costly) |
| [01_break_fixes.py](01_break_fixes.py) | Demo 4 — Breaking change #1 | Before/after for `disabled` → `between_tools`, plus the `adaptive` + `xhigh` alternative. | Snippet |
| [02_break_fixes.py](02_break_fixes.py) | Demo 5 — Breaking change #2 | Forced `tool_choice` (`any` / `tool`) is now a 400. Shows `strict: True` tool schema with `tool_choice: auto` and directing tool use in the prompt. | Snippet |
| [03_break_fixes.py](03_break_fixes.py) | Demo 6 — Breaking change #3 | Minimal agent tool loop. Appends the whole assistant turn (thinking blocks included, unchanged) to keep history append-only, and prints `between_tools` progress notes that arrive as thinking blocks (the silent change). | Yes |
| [04_break_fixes.py](04_break_fixes.py) | Demo 7 — Refusals | Handles `stop_reason == "refusal"`, reads `stop_details.category`, and falls back client-side to `claude-sonnet-5` for `cyber` / `frontier_llm`. | Yes |

## The breaking changes, in one place

1. **`thinking: disabled` → `between_tools`** — works at `low` / `medium` / `high` only; `xhigh` / `max` return 400. Need `xhigh`? Omit the `thinking` field (adaptive).
2. **Forced tool use removed** — `tool_choice` accepts only `auto` or `none`. Use `strict: true` tools and say in the prompt when to use them.
3. **Append-only conversations** — pass assistant `content` (including thinking blocks) back untouched; editing earlier history and replaying signed thinking blocks can 400.
4. **Computer use / advisor pairings** — move to the new computer-use toolset and check advisor pairings (covered in the video's takeaways, no script).
5. **Non-default `temperature` is a 400** — use `effort` instead (see `02_first_call.py`).
6. **Silent change** — with `between_tools`, progress notes between tool calls come back as thinking blocks, so code that only prints `text` blocks will appear to go quiet.

Also new: Sonnet 5.5 can **refuse** (HTTP 200, `stop_reason: "refusal"`), which is handled in `04_break_fixes.py`.

## Quick migration grep

Before flipping the model ID, search your code for:

```bash
grep -rnE 'disabled|tool_choice|content\[0\]|computer_20251124' .
```

## Notes

- `PRICES` in the sweep script is USD per token (Sonnet 5.5: $2 in / $10 out per million; Opus 5.5: $4 / $20). Update it if pricing changes.
- Default `effort` is `high` on the Claude API and `medium` in the Claude apps and Claude Code; levels are recalibrated versus Sonnet 5, so re-run the sweep on your own prompts.
- Thinking tokens count against `max_tokens` and are billed as output tokens.
- `stop_details.category` attribute access should be confirmed against your installed SDK version.
- Server-side fallback (`fallbacks: "default"`) is a beta and is not demoed; the client-side retry here is the portable version.

import sys
import anthropic

RED, GREEN, BOLD, DIM, RESET = "\033[31m", "\033[32m", "\033[1m", "\033[2m", "\033[0m"

client = anthropic.Anthropic()
fix = "--fix" in sys.argv

request = dict(
    model="claude-sonnet-5-5",   # the only line we changed from Sonnet 5
    max_tokens=1024,
    messages=[{"role": "user", "content": "Classify this ticket: 'My invoice is wrong'"}],
)

if fix:
    request["thinking"] = {"type": "between_tools"}   # lowest setting on Sonnet 5.5
    request["output_config"] = {"effort": "low"}       # between_tools: low/medium/high only
else:
    request["thinking"] = {"type": "disabled"}          # worked on Sonnet 5

print(f"{DIM}→ model={request['model']}  thinking={request['thinking']}{RESET}\n")

try:
    response = client.messages.create(**request)
except anthropic.BadRequestError as e:
    # e.body is the parsed JSON error: {"type": "error", "error": {"type": ..., "message": ...}}
    err = (e.body or {}).get("error", {}) if isinstance(e.body, dict) else {}
    print(f"{RED}{BOLD}{e.status_code} — {err.get('type', 'invalid_request_error')}{RESET}")
    message = err.get("message", str(e))
    # Split so the fix hint sits on its own line for the [zoom in]
    for part in message.replace(". Use", ".\nUse").splitlines():
        print(f"{RED}{part}{RESET}")
    sys.exit(1)

print(f"{GREEN}{BOLD}200 — {response.stop_reason}{RESET}")
for block in response.content:          # read by type, never content[0]
    if block.type == "text":
        print(block.text)
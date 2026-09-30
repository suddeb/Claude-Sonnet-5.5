import anthropic
client = anthropic.Anthropic()

def ask(model: str, prompt: str):
    return client.messages.create(
        model=model,
        max_tokens=4096,
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": prompt}],
    )

prompt = "Review this Apex class for security issues and suggest fixes: ..."
response = ask("claude-sonnet-5-5", prompt)
if response.stop_reason == "refusal":
    category = response.stop_details.category      # cyber | bio | frontier_llm | ...
    print("Refused:", category)
    if category in ("cyber", "frontier_llm"):
        response = ask("claude-sonnet-5", prompt)  # same fallback target Anthropic uses

for block in response.content:
    if block.type == "text":
        print(block.text)

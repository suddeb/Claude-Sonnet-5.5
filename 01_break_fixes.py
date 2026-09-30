# BEFORE — Sonnet 5 (400 on Sonnet 5.5)

client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    thinking={"type": "disabled"},           # ❌ 400 on 5.5
    messages=[{"role": "user", "content": "Classify: 'My invoice is wrong'"}],

)

# AFTER — Sonnet 5.5

client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=2048,                         # thinking-free, but leave headroom
    thinking={"type": "between_tools"},      # ✅ lowest setting: no up-front thinking
    output_config={"effort": "low"},         # between_tools: low / medium / high only
    messages=[{"role": "user", "content": "Classify: 'My invoice is wrong'"}],
)

client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=64000,                     # leave plenty of room for thinking
    thinking={"type": "adaptive"},
    output_config={"effort": "xhigh"},
    messages=[...],
)

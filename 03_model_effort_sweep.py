import os
import time
import anthropic
client = anthropic.Anthropic()

# USD per token: (input, output)
PRICES = {
    "claude-sonnet-5-5": (2 / 1_000_000, 10 / 1_000_000),
    "claude-opus-5-5":   (4 / 1_000_000, 20 / 1_000_000),
}

EFFORTS = ["low", "medium", "high", "xhigh"]
PROMPT = (
    "An Apex trigger on Case runs a SOQL query inside a for-loop. Explain the "
    "governor-limit risk in max 150 words, then give a bulkified rewrite."
)

os.makedirs("answers", exist_ok=True)
print(f"{'model':<19}{'effort':<8}{'secs':>7}{'out_tok':>9}{'cost_usd':>11}")

for model, (p_in, p_out) in PRICES.items():
    for effort in EFFORTS:
        start = time.perf_counter()
        with client.messages.stream(       # streaming: long runs stay safe
            model=model,
            max_tokens=32000,              # generous: xhigh thinks a lot
            output_config={"effort": effort},
            messages=[{"role": "user", "content": PROMPT}],
        ) as stream:
            r = stream.get_final_message()

        secs = time.perf_counter() - start
        cost = r.usage.input_tokens * p_in + r.usage.output_tokens * p_out

        print(f"{model:<19}{effort:<8}{secs:>7.1f}"
              f"{r.usage.output_tokens:>9}{cost:>11.4f}")

        # Save the visible answer so you can judge quality side by side
        text = "\n".join(b.text for b in r.content if b.type == "text")

        with open(f"answers/{model}_{effort}.md", "w") as f:
            f.write(text)

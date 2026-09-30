import anthropic
client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-5-5",           # no date suffix
    max_tokens=4096,                     # covers thinking + visible text
    output_config={"effort": "medium"},  # thinking depth; API default is "high"
    messages=[{
        "role": "user",
        "content": "Explain the trade-offs of event-driven vs request/response "
                   "integration for a CRM in 5 bullet points.",
    }],
)
print("Stop reason:", response.stop_reason)

# Read by block type — never assume content[0] is text
# If your code says response.content[0].text — stop. The first block can be a thinking block, and that line breaks.
# Always loop over blocks and filter by type
for block in response.content:
    if block.type == "text":
        print(block.text)
        
print("\nUsage:", response.usage)

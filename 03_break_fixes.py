import anthropic
client = anthropic.Anthropic()

def obj(props, required):
    return {"type": "object", "properties": props,
            "required": required, "additionalProperties": False}

tools = [
    {
        "name": "get_open_cases",
        "description": "List open support cases for an account.",
        "strict": True,
        "input_schema": obj({"account": {"type": "string"}}, ["account"]),
    },
    {
        "name": "create_case",
        "description": "Create a support case in the CRM.",
        "strict": True,
        "input_schema": obj(
            {"subject": {"type": "string"},
             "priority": {"type": "string", "enum": ["Low", "Medium", "High"]}},
            ["subject", "priority"],
        ),
    },
]

def run_tool(name, args):
    # Stand-in for a real SOQL query or MCP tool call
    if name == "get_open_cases":
        return f"2 open cases for {args['account']}: 'Login timeout' (High), 'Report export' (Low)"

    if name == "create_case":
        return f"Case created: {args['subject']} ({args['priority']})"

    return "unknown tool"

messages = [{
    "role": "user",
    "content": "Acme says checkout is down for every user. Check their open cases "
               "first, then log a High-priority case if one isn't already there. "
               "Use the tools.",
}]

while True:
    response = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=8000,
        thinking={"type": "between_tools"},   # progress notes come back without `display`
        output_config={"effort": "medium"},
        tools=tools,
        messages=messages,
    )

    # ✅ Append the WHOLE assistant turn, thinking blocks included — don't filter or rebuild

    messages.append({"role": "assistant", "content": response.content})
    tool_results = []
    for block in response.content:
        if block.type == "thinking" and block.thinking:
            print("[progress]", block.thinking)         # text between tool calls
        elif block.type == "text":
            print(block.text)
        elif block.type == "tool_use":
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": run_tool(block.name, block.input),
            })

    if not tool_results:
        break

    messages.append({"role": "user", "content": tool_results})

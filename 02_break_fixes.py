case_tool = {
    "name": "create_case",
    "description": "Create a support case in the CRM.",
    "strict": True,  # This will guarantee that when Claude calls it, the input matches your schema
    "input_schema": {
        "type": "object",
        "properties": {
            "subject":  {"type": "string"},
            "priority": {"type": "string", "enum": ["Low", "Medium", "High"]},
        },
        "required": ["subject", "priority"],
        "additionalProperties": False,   # required on every object for strict tools
    },
}

# BEFORE — Sonnet 5:  tool_choice={"type": "tool", "name": "create_case"}  # ❌ 400 on 5.5
# tool_choice type any or type tool now returns a 400. Only auto and none are allowed.

# AFTER — Sonnet 5.5
response = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=4096,
    tools=[case_tool],
    tool_choice={"type": "auto"},        # ✅ only "auto" or "none" are accepted
    messages=[{
        "role": "user",
        "content": "Customer says checkout is down for all users. "
                   "Use the create_case tool.",  # direct it in the prompt instead
    }],
)

# The replacement is strict tool use. 
# Mark the tool strict: true, which guarantees that 
# when Claude calls it, the input matches your schema. 
# And tell it in the prompt when to use the tool. 
# If what you really wanted was guaranteed JSON rather than a tool call, use structured outputs instead.

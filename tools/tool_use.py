import json
from tools.datetime_tool import get_current_datetime
from tools.batch_tool import run_batch

def run_tool(tool_name, tool_input):
    # list of available Tools to run 
    if tool_name == "get_current_datetime":
        return get_current_datetime(**tool_input)
    elif tool_name == "batch_tool":
        return run_batch(**tool_input)
    '''
    elif tool_name == "another_tool":
        return another_tool(**tool_input)
    # Add more tools as needed
    # '''


def run_tools(message):
    #Input calls
    tool_requests = [
        block for block in message.content if block.type == "tool_use"
    ]
    # Output result from calls
    tool_result_blocks = []

    for tool_request in tool_requests:
        try:
            tool_output = run_tool(tool_request.name, tool_request.input)
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": json.dumps(tool_output),
                "is_error": False,
            }
        except Exception as e:
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": f"Error: {e}",
                "is_error": True,
            }

        tool_result_blocks.append(tool_result_block)

    return tool_result_blocks
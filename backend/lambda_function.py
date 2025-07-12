import json
from app.agents import graph

def lambda_handler(event, context):
    """
    AWS Lambda entry point for the multi-agent research platform.
    Expects event['task'] as input.
    Returns agent outputs in a structured JSON response.
    """
    task = event.get('task')
    if not task:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing 'task' in request"})
        }
    try:
        # Initial state for the graph
        state = {"task": task, "research_data": [], "analysis": "", "report": ""}
        result = graph.invoke(state)
        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Internal server error: {str(e)}"})
        }
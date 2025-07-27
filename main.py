import functions_framework
from vertexai.preview import reasoning_engines
import vertexai
from vertexai import agent_engines
import uuid
import json
import re

PROJECT_ID = "sahayakai-466115"
LOCATION = "us-east4"
STAGING_BUCKET = "gs://sahayak-conversation-agent"

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

def extract_json_from_markdown(text):
    pattern = r"```json\s*(\{.*?\})\s*```"
    match = re.search(pattern, text, re.DOTALL)
    
    if not match:
        raise ValueError("No JSON code block found in the Markdown.")
    
    json_str = match.group(1)
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

@functions_framework.http
def answer_from_textbook(request):
    # For more information about CORS and CORS preflight requests, see:
    # https://developer.mozilla.org/en-US/docs/Glossary/Preflight_request

    # Set CORS headers for the preflight request
    if request.method == "OPTIONS":
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600",
        }

        return ("", 204, headers)

    # Set CORS headers for the main request
    headers = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
    prompt = None
    try:
        request_json = request.get_json(silent=True)
        print(f"Request JSON: {request_json}")
        user_query = request_json.get("user_query", "")
        language = request_json.get("language", "")
        prompt = f"{user_query}. **Answer must be in {language}**"
    except Exception as e:
        return (f"Invalid request body: {e}", 400, headers)
    agent = agent_engines.get('projects/sahayakai-466115/locations/us-east4/reasoningEngines/5221220080494313472')    
    print(agent.operation_schemas())
    print(f"Using agent: {agent.name}")
    
    user_id = str(uuid.uuid4())
    session = agent.create_session(user_id=user_id)
    print(session)
    print(str(session))
    events = []
    print(prompt)
    print("Calling agents")
    for event in agent.stream_query(
        user_id=user_id,
        message=prompt,
    ): events.append(event)
    print(len(events))
    response_event = events[-1]
    print(response_event)
    response_text = response_event['content']['parts'][0]['text']
    print(response_text)
    response_json = extract_json_from_markdown(response_text)
    print(response_json)

    return (response_json, 200, headers)
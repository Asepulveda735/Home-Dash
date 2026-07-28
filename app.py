from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv
import requests
import os
import json
import anthropic
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



# Load environment variables from .env
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
OWM_API_KEY = os.getenv("OWM_API_KEY")
CTA_API_KEY = os.getenv("CTA_API_KEY")  # or whatever transit key you got
OBSIDIAN_API_KEY = os.getenv("OBSIDIAN_API_KEY")
OBSIDIAN_PORT = os.getenv("OBSIDIAN_PORT", "27124")
OBSIDIAN_BASE_URL = f"https://127.0.0.1:{OBSIDIAN_PORT}"
OBSIDIAN_HEADERS = {
    "Authorization": f"Bearer {OBSIDIAN_API_KEY}",
    "Content-Type": "text/markdown"
}


app = Flask(__name__)

from flask import render_template

def read_note(filename):
    response = requests.get(f"{OBSIDIAN_BASE_URL}/vault/{filename}", headers=OBSIDIAN_HEADERS, verify=False)
    print("Read status:", response.status_code)
    print("Read body:", repr(response.text))
    print("Headers sent:", OBSIDIAN_HEADERS)
    return response.text

def write_note(filename, content):
    response = requests.put(f"{OBSIDIAN_BASE_URL}/vault/{filename}", headers=OBSIDIAN_HEADERS, data=content, verify=False)
    return response.text

def update_memory(user_text, action_taken, memory_update=None):
    memory = read_note("memory.md")
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # always log the interaction
    log_entry = f"- [{timestamp}] '{user_text}' → {action_taken}\n"
    
    # if Claude learned something new, add it to preferences
    if memory_update:
        # find the Preferences section and append to it
        if "## Preferences" in memory:
            memory = memory.replace(
                "## Preferences",
                f"## Preferences\n- {memory_update}"
            )
        else:
            memory += f"\n## Preferences\n- {memory_update}\n"
    
    # append to conversation history
    if "## Conversation History" in memory:
        memory += log_entry
    else:
        memory += f"\n## Conversation History\n{log_entry}"
    
    write_note("memory.md", memory)

@app.route("/dashboard")
def dashboard():
    return render_template("index.html")

@app.route("/")
def home():
    return "Dashboard backend is running."


@app.route("/api/weather")
def get_weather():
    # TODO:
    params = {
        "q": "Wheeling,IL,US",
        "appid": OWM_API_KEY,
        "units": "imperial"
}
    response = requests.get("https://api.openweathermap.org/data/2.5/weather", params=params)
    response_json = response.json()
    return jsonify(response_json)
    pass


@app.route("/api/transit")
def get_transit():
    # TODO:
    params = {
        "key": CTA_API_KEY,
        "mapid": "41220",#fullerton stop ID
        "outputType": "JSON"
}
    response = requests.get("http://lapi.transitchicago.com/api/1.0/ttarrivals.aspx", params=params)
    response_json = response.json()
    return jsonify(response_json)
    pass

@app.route("/api/todos", methods=["GET"])
def get_todos():
    # Step 1: read the note (returns raw markdown as a string)
    content = read_note("todos.md")

    # Step 2: split into individual lines
    lines = content.split("\n")

    # Step 3: filter and parse
    # hint: not every line will start with "- [ ]" or "- [x]"
    # you only want lines that DO start with one of those
    todos = []
    for line in lines:
        if line.startswith("- [ ]") or line.startswith("- [x]"):
            # TODO: strip the prefix and append just the task text to todos
            todo = line.replace("- [ ] ", "").replace("- [x] ", "").strip()
            todos.append(todo)

    # Step 4: return as JSON
    return jsonify(todos)


@app.route("/api/todos", methods=["POST"])
def add_todo():
    text = request.json.get("text")
    content = read_note("todos.md")
    
    # ensure content ends with a newline before appending
    if content and not content.endswith("\n"):
        content += "\n"
    
    new_content = content + f"- [ ] {text}\n"
    write_note("todos.md", new_content)
    return jsonify({"status": "ok"})


@app.route("/api/todos/<item>", methods=["DELETE"])
def delete_todo(item):
    # Step 1: read current todos.md content
    content = read_note("todos.md")

    # Step 2: split into lines
    lines = content.split("\n")

    # Step 3: filter out the line containing item
    filtered_lines = [line for line in lines if item not in line]

    # Step 4: join remaining lines back together
    new_content = "\n".join(filtered_lines)

    # Step 5: write back
    write_note("todos.md", new_content)

    # Step 6: return success
    return jsonify({"status": "ok"})


@app.route("/api/bucketlist", methods=["GET"])
def get_bucketlist():
    # Step 1: read the note (returns raw markdown as a string)
    content = read_note("bucketlist.md")

    # Step 2: split into individual lines
    lines = content.split("\n")

    bucketlist = []
    for line in lines:
        if line.startswith("- [ ]") or line.startswith("- [x]"):
            # TODO: strip the prefix and append just the task text to todos
            todo = line.replace("- [ ] ", "").replace("- [x] ", "").strip()
            bucketlist.append(todo)

    # Step 4: return as JSON
    return jsonify(bucketlist)

@app.route("/api/bucketlist", methods=["POST"])
def add_bucketlist_item():
    text = request.json.get("text")
    content = read_note("bucketlist.md")
    
    # ensure content ends with a newline before appending
    if content and not content.endswith("\n"):
        content += "\n"
    
    new_content = content + f"- [ ] {text}\n"
    write_note("bucketlist.md", new_content)
    return jsonify({"status": "ok"})


@app.route("/api/bucketlist/<item>", methods=["DELETE"])
def delete_bucketlist_item(item):
    # Step 1: read current bucketlist.md content
    content = read_note("bucketlist.md")

    # Step 2: split into lines
    lines = content.split("\n")

    # Step 3: filter out the line containing item
    filtered_lines = [line for line in lines if item not in line]

    # Step 4: join remaining lines back together
    new_content = "\n".join(filtered_lines)

    # Step 5: write back
    write_note("bucketlist.md", new_content)

    # Step 6: return success
    return jsonify({"status": "ok"})

@app.route("/api/voice", methods=["POST"])
def voice_command():
    text = request.json.get("text")

    # Step 1: gather context from Obsidian
    
    # Step 1: gather context from Obsiddon
    todos = read_note("todos.md")
    bucketlist = read_note("bucketlist.md")
    memory = read_note("memory.md")

    # Step 2: system prompt now includes memory
    system_prompt = f"""You are Hubert, a personal AI assistant living on Ale's home dashboard. You are witty, warm, and helpful — like Jarvis from Iron Man but more casual and friendly. You know Ale well and get to know them better over time.

    ## What you know about Ale:
    {memory}

    ## Ale's current todos:
    {todos}

    ## Ale's current bucket list:
    {bucketlist}

    ## Your personality:
    - You're conversational and natural, not robotic
    - You remember past conversations and reference them naturally
    - You notice patterns and make proactive recommendations
    - You're concise but warm — no unnecessary filler
    - You occasionally make light jokes or observations
    - You address Ale by BossMan sometimes

    ## Your capabilities:
    - Manage todos and bucket list
    - Answer questions conversationally
    - Make recommendations based on known preferences
    - Notice patterns ("You've added a lot of food places to your bucket list — into trying new restaurants?")
    - Using previously learned information to answer questions and make recommendations

    ## Response format:
    Always respond with valid JSON and nothing else:

    For actions:
    {{"action": "add_todo", "text": "item", "response": "confirmation message in your voice", "memory_update": "optional insight about Ale worth remembering"}}
    {{"action": "delete_todo", "text": "item", "response": "confirmation message", "memory_update": null}}
    {{"action": "add_bucket", "text": "item", "response": "confirmation message", "memory_update": "optional insight"}}
    {{"action": "delete_bucket", "text": "item", "response": "confirmation message", "memory_update": null}}

    For conversation:
    {{"action": "none", "response": "your conversational response", "memory_update": "optional insight worth remembering"}}

    The memory_update field should only be filled when you learn something genuinely useful about Ale's preferences, habits, or interests. Not every interaction needs one."""

    # Step 3: call Claude
    # TODO: use claude_client.messages.create() to send the voice command
    # model: "claude-sonnet-4-6"
    # max_tokens: 256
    # messages: [{"role": "user", "content": text}]
    # system: system_prompt
    response = claude_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system=system_prompt,
        messages=[
            {"role": "user", "content": text}
        ]
    )

    # Step 4: parse Claude's response as JSON
    # TODO: parse the response text as JSON
    try:
        action_data = response.content[0].text  # Assuming the response is in the first message
        action_json = json.loads(action_data)
    except Exception as e:
        return jsonify({"error": "Failed to parse Claude's response as JSON", "details": str(e)}), 400

    # Step 5: execute the action
    # TODO: based on action field, call the right function
    # add_todo → read note, append, write note
    # delete_todo → read note, filter, write note
    # none → just return the response text
    action = action_json.get("action")
    memory_update = action_json.get("memory_update")
    response_text = action_json.get("response", "Done.")

    if action == "add_todo":
        text = action_json.get("text")
        content = read_note("todos.md")
        if content and not content.endswith("\n"):
            content += "\n"
        new_content = content + f"- [ ] {text}\n"
        write_note("todos.md", new_content)
        update_memory(user_text=request.json.get("text"), action_taken=f"added '{text}' to todos", memory_update=memory_update)
        renderTodos()
        return jsonify({"response": response_text})

    elif action == "delete_todo":
        text = action_json.get("text")
        content = read_note("todos.md")
        lines = content.split("\n")
        filtered_lines = [line for line in lines if text.lower() not in line.lower()]
        new_content = "\n".join(filtered_lines)
        write_note("todos.md", new_content)
        update_memory(user_text=request.json.get("text"), action_taken=f"deleted '{text}' from todos", memory_update=memory_update)
        return jsonify({"response": response_text})

    elif action == "add_bucket":
        text = action_json.get("text")
        content = read_note("bucketlist.md")
        if content and not content.endswith("\n"):
            content += "\n"
        new_content = content + f"- [ ] {text}\n"
        write_note("bucketlist.md", new_content)
        update_memory(user_text=request.json.get("text"), action_taken=f"added '{text}' to bucket list", memory_update=memory_update)
        return jsonify({"response": response_text})

    elif action == "delete_bucket":
        text = action_json.get("text")
        content = read_note("bucketlist.md")
        lines = content.split("\n")
        filtered_lines = [line for line in lines if text.lower() not in line.lower()]
        new_content = "\n".join(filtered_lines)
        write_note("bucketlist.md", new_content)
        update_memory(user_text=request.json.get("text"), action_taken=f"deleted '{text}' from bucket list", memory_update=memory_update)
        return jsonify({"response": response_text})

    response_text = action_json.get("response", "I'm not sure how to help with that.")
    update_memory(user_text=request.json.get("text"), action_taken="conversational response", memory_update=memory_update)
    return jsonify({"response": response_text})

if __name__ == "__main__":
    app.run(debug=True)
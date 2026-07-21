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


    # 1. Build the request URL using OWM_API_KEY and a city (e.g. "Wheeling,IL,US")
    # 2. Call it with requests.get()
    # 3. Convert the response to JSON with .json()
    # 4. Return it using jsonify()
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


    # 1. Build the request URL using CTA_API_KEY and a stop/route ID
    # 2. Call it with requests.get()
    # 3. Convert the response to JSON with .json()
    # 4. Return it using jsonify()
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

    # Step 3: filter and parse
    # hint: not every line will start with "- [ ]" or "- [x]"
    # you only want lines that DO start with one of those
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
    todos = read_note("todos.md")
    bucketlist = read_note("bucketlist.md")

    # Step 2: build a system prompt telling Claude what it can do
    system_prompt = f"""You are a smart home dashboard assistant. 
You help manage todos and bucket list items stored in Obsidian.

Current todos:
{todos}

Current bucket list:
{bucketlist}

When the user wants to add or remove items, respond with a JSON action like:
{{"action": "add_todo", "text": "item text"}}
{{"action": "delete_todo", "text": "item text"}}
{{"action": "add_bucket", "text": "item text"}}
{{"action": "delete_bucket", "text": "item text"}}
{{"action": "none", "response": "your conversational response here"}}

Always respond with valid JSON and nothing else."""

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
    if action == "add_todo":
        text = action_json.get("text")
        content = read_note("todos.md")
        if content and not content.endswith("\n"):
            content += "\n"
        new_content = content + f"- [ ] {text}\n"
        write_note("todos.md", new_content)
        return jsonify({"status": "ok", "action": "add_todo", "text": text})
    elif action == "delete_todo":
        text = action_json.get("text")
        content = read_note("todos.md")
        lines = content.split("\n")
        filtered_lines = [line for line in lines if text not in line]
        new_content = "\n".join(filtered_lines)
        write_note("todos.md", new_content)
        return jsonify({"status": "ok", "action": "delete_todo", "text": text})
    elif action == "add_bucket":    
        text = action_json.get("text")
        content = read_note("bucketlist.md")
        if content and not content.endswith("\n"):
            content += "\n"
        new_content = content + f"- [ ] {text}\n"
        write_note("bucketlist.md", new_content)
        return jsonify({"status": "ok", "action": "add_bucket", "text": text})
    elif action == "delete_bucket":
        text = action_json.get("text")
        content = read_note("bucketlist.md")
        lines = content.split("\n")
        filtered_lines = [line for line in lines if text not in line]
        new_content = "\n".join(filtered_lines)
        write_note("bucketlist.md", new_content)
        return jsonify({"status": "ok", "action": "delete_bucket", "text": text})
    
    return jsonify({"response": action_json.get("response", "I'm not sure how to help with that.")})


if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, jsonify
from dotenv import load_dotenv
import requests
import os
from flask import Flask, jsonify, request
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



# Load environment variables from .env
load_dotenv()

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
    print("Voice command received:", text)
    # Phase 3 will process this with Claude
    # For now just echo it back
    return jsonify({"response": f"You said: {text}"})

if __name__ == "__main__":
    app.run(debug=True)
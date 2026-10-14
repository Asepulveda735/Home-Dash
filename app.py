from datetime import datetime
from flask import Flask, jsonify, request, render_template, send_from_directory
from dotenv import load_dotenv
from flask_socketio import SocketIO
import requests
import os
import json
import base64
import psutil
import socket
import time
import robin_stocks.robinhood as r
import glob

# Load environment variables from .env
load_dotenv()
OWM_API_KEY = os.getenv("OWM_API_KEY")
ROBINHOOD_EMAIL = os.getenv("ROBINHOOD_EMAIL")
ROBINHOOD_PASSWORD = os.getenv("ROBINHOOD_PASSWORD")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")
CTA_API_KEY = os.getenv("CTA_API_KEY")  # or whatever transit key you got
r.login(ROBINHOOD_EMAIL, ROBINHOOD_PASSWORD)
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

def read_note(filename):
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
        response = requests.get(url, headers=GITHUB_HEADERS)
        if response.status_code == 200:
            content = base64.b64decode(response.json()["content"]).decode("utf-8")
            return content
        return ""
    except Exception as e:
        print(f"Error reading {filename}:", e)
        return ""

def write_note(filename, content):
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
        # get current SHA (needed for updates)
        get_response = requests.get(url, headers=GITHUB_HEADERS)
        sha = get_response.json().get("sha") if get_response.status_code == 200 else None

        payload = {
            "message": f"Hubert update: {filename}",
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8")
        }
        if sha:
            payload["sha"] = sha

        requests.put(url, headers=GITHUB_HEADERS, json=payload)
    except Exception as e:
        print(f"Error writing {filename}:", e)

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
    #TODO:
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

    # Step 1: gather context from notes
    todos = read_note("todos.md")
    bucketlist = read_note("bucketlist.md")
    memory = read_note("memory.md")
    calendar = read_note("calendar.md")

    # Step 2: system prompt now includes memory
    system_prompt = f"""You are Hubert, a personal AI assistant living on Ale's home dashboard. You are witty, warm, and helpful — like Jarvis from Iron Man but more casual and friendly. You know Ale well and get to know them better over time.

    ## What you know about Ale:
    {memory}

    ## Ale's current todos:
    {todos}

    ## Ale's current bucket list:
    {bucketlist}

    ## Ale's upcoming calendar events:
    {calendar}

    ## Your personality:
    - You're conversational and natural, not robotic
    - You remember past conversations and reference them naturally
    - You notice patterns and make proactive recommendations
    - You're concise but warm — no unnecessary filler
    - You occasionally make light jokes or observations
    - You address Ale by BossMan sometimes

    ## Your capabilities:
    - Manage todos and bucket list
    - Add and delete calendar events
    - Answer questions conversationally
    - Make recommendations based on known preferences
    - Notice patterns ("You've added a lot of food places to your bucket list — into trying new restaurants?")

    ## Response format:
    Always respond with valid JSON and nothing else:

    For actions:
    {{"action": "add_todo", "text": "item", "response": "confirmation", "memory_update": null}}
    {{"action": "delete_todo", "text": "item", "response": "confirmation", "memory_update": null}}
    {{"action": "add_bucket", "text": "item", "response": "confirmation", "memory_update": null}}
    {{"action": "delete_bucket", "text": "item", "response": "confirmation", "memory_update": null}}
    {{"action": "add_event", "date": "YYYY-MM-DD", "time": "HH:MM", "title": "event title", "response": "confirmation", "memory_update": null}}
    {{"action": "delete_event", "title": "event title", "response": "confirmation", "memory_update": null}}
    {{"action": "none", "response": "your conversational response", "memory_update": null}}

    For conversation:
    {{"action": "none", "response": "your conversational response", "memory_update": "optional insight worth remembering"}}

    For add_event, infer the date from context. Today is {datetime.now().strftime('%Y-%m-%d')}. If Ale says 'tomorrow' calculate it correctly. Time defaults to 09:00 if not specified.

    The memory_update field should only be filled when you learn something genuinely useful about Ale's preferences, habits, or interests. Not every interaction needs one."""

    # Step 3: call Ollama
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama3.2",
        "prompt": f"{system_prompt}\n\nUser: {text}",
        "stream": False
    })
    # Step 4: parse response as JSON
    try:
        action_data = response.json()["response"]
        action_data = action_data.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        action_json = json.loads(action_data)
    except Exception as e:
        return jsonify({"error": "Failed to parse response as JSON", "details": str(e)}), 400

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
        socketio.emit('dashboard_update', {'type': 'todos'})
        update_memory(user_text=request.json.get("text"), action_taken=f"added '{text}' to todos", memory_update=memory_update)
        return jsonify({"response": response_text})

    elif action == "delete_todo":
        text = action_json.get("text")
        content = read_note("todos.md")
        lines = content.split("\n")
        filtered_lines = [line for line in lines if text.lower() not in line.lower()]
        new_content = "\n".join(filtered_lines)
        write_note("todos.md", new_content)
        socketio.emit('dashboard_update', {'type': 'todos'})
        update_memory(user_text=request.json.get("text"), action_taken=f"deleted '{text}' from todos", memory_update=memory_update)
        return jsonify({"response": response_text})

    elif action == "add_bucket":
        text = action_json.get("text")
        content = read_note("bucketlist.md")
        if content and not content.endswith("\n"):
            content += "\n"
        new_content = content + f"- [ ] {text}\n"
        write_note("bucketlist.md", new_content)
        socketio.emit('dashboard_update', {'type': 'bucketlist'})
        update_memory(user_text=request.json.get("text"), action_taken=f"added '{text}' to bucket list", memory_update=memory_update)
        return jsonify({"response": response_text})

    elif action == "delete_bucket":
        text = action_json.get("text")
        content = read_note("bucketlist.md")
        lines = content.split("\n")
        filtered_lines = [line for line in lines if text.lower() not in line.lower()]
        new_content = "\n".join(filtered_lines)
        write_note("bucketlist.md", new_content)
        socketio.emit('dashboard_update', {'type': 'bucketlist'})
        update_memory(user_text=request.json.get("text"), action_taken=f"deleted '{text}' from bucket list", memory_update=memory_update)
        return jsonify({"response": response_text})
    
    elif action == "add_event":
        date = action_json.get("date")
        time = action_json.get("time", "09:00")
        title = action_json.get("title")
        content = read_note("calendar.md")
        if content and not content.endswith("\n"):
            content += "\n"
        new_line = f"{date} {time} | {title}\n"
        write_note("calendar.md", content + new_line)
        socketio.emit('dashboard_update', {'type': 'calendar'})
        update_memory(user_text=request.json.get("text"), action_taken=f"added event '{title}' on {date} at {time}", memory_update=memory_update)
        return jsonify({"response": response_text})

    elif action == "delete_event":
        title = action_json.get("title")
        content = read_note("calendar.md")
        lines = content.split("\n")
        filtered = [line for line in lines if title.lower() not in line.lower()]
        write_note("calendar.md", "\n".join(filtered))
        socketio.emit('dashboard_update', {'type': 'calendar'})
        update_memory(user_text=request.json.get("text"), action_taken=f"deleted event '{title}'", memory_update=memory_update)
        return jsonify({"response": response_text})

    response_text = action_json.get("response", "I'm not sure how to help with that.")
    update_memory(user_text=request.json.get("text"), action_taken="conversational response", memory_update=memory_update)
    return jsonify({"response": response_text})

@app.route("/api/crypto")
def get_crypto():
    ids = "bitcoin,ethereum"
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ids,
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    response = requests.get(url, params=params)
    return jsonify(response.json())

@app.route("/api/markets")
def get_markets():
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": "SPY",
        "apikey": ALPHA_VANTAGE_KEY
    }
    response = requests.get(url, params=params)
    return jsonify(response.json())

@app.route("/api/events", methods=["GET"])
def get_events():
    content = read_note("calendar.md")
    events = []
    for line in content.split("\n"):
        if "|" in line and line.strip() and not line.startswith("#"):
            parts = line.strip().split(" | ", 1)
            if len(parts) == 2:
                datetime_str = parts[0].strip()
                title = parts[1].strip()
                events.append({"datetime": datetime_str, "title": title})
    events.sort(key=lambda e: e["datetime"])
    return jsonify(events)
#Calander
@app.route("/api/events", methods=["POST"])
def add_event():
    date = request.json.get("date")
    time = request.json.get("time")
    title = request.json.get("title")
    content = read_note("calendar.md")
    if content and not content.endswith("\n"):
        content += "\n"
    new_line = f"{date} {time} | {title}\n"
    write_note("calendar.md", content + new_line)
    socketio.emit('dashboard_update', {'type': 'calendar'})
    return jsonify({"status": "ok"})
@app.route("/api/events/<path:event_id>", methods=["DELETE"])
def delete_event(event_id):
    content = read_note("calendar.md")
    lines = content.split("\n")
    filtered = [line for line in lines if event_id not in line]
    write_note("calendar.md", "\n".join(filtered))
    socketio.emit('dashboard_update', {'type': 'calendar'})
    return jsonify({"status": "ok"})


#robinhood
@app.route("/api/portfolio")
def get_portfolio():
    try:
        # total portfolio value
        portfolio = r.profiles.load_portfolio_profile()
        total_value = float(portfolio['equity'])
        prev_close = float(portfolio['adjusted_equity_previous_close'])
        daily_change = total_value - prev_close
        daily_change_pct = (daily_change / prev_close) * 100

        # individual stock positions
        positions = r.account.get_open_stock_positions()
        stocks = []
        for position in positions:
            instrument = r.stocks.get_instrument_by_url(position['instrument'])
            quote = r.stocks.get_latest_price(instrument['symbol'])[0]
            quantity = float(position['quantity'])
            avg_cost = float(position['average_buy_price'])
            current_price = float(quote)
            total = quantity * current_price
            gain = total - (quantity * avg_cost)
            stocks.append({
                "symbol": instrument['symbol'],
                "quantity": quantity,
                "avg_cost": avg_cost,
                "current_price": current_price,
                "total_value": round(total, 2),
                "gain_loss": round(gain, 2)
            })

        # crypto holdings
        crypto_positions = r.crypto.get_crypto_positions()
        crypto = []
        for position in crypto_positions:
            quantity = float(position['quantity_available'])
            if quantity > 0:
                symbol = position['currency']['code']
                quote = r.crypto.get_crypto_quote(symbol)
                current_price = float(quote['mark_price'])
                cost_basis = float(position['cost_bases'][0]['direct_cost_basis']) if position['cost_bases'] else 0
                total = quantity * current_price
                gain = total - cost_basis
                crypto.append({
                    "symbol": symbol,
                    "quantity": quantity,
                    "current_price": current_price,
                    "total_value": round(total, 2),
                    "gain_loss": round(gain, 2)
                })

        # buying power
        account = r.profiles.load_account_profile()
        buying_power = float(account['buying_power'])

        return jsonify({
            "total_value": round(total_value, 2),
            "daily_change": round(daily_change, 2),
            "daily_change_pct": round(daily_change_pct, 2),
            "buying_power": round(buying_power, 2),
            "stocks": stocks,
            "crypto": crypto
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/system")
def get_system():
    cpu_percent = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime_seconds = time.time() - psutil.boot_time()
    uptime_hours = int(uptime_seconds // 3600)
    uptime_minutes = int((uptime_seconds % 3600) // 60)

    try:
        temp = psutil.sensors_temperatures()
        cpu_temp = temp['cpu_thermal'][0].current if 'cpu_thermal' in temp else None
    except:
        cpu_temp = None

    try:
        ip = socket.gethostbyname(socket.gethostname())
    except:
        ip = "unknown"

    return jsonify({
        "cpu_percent": cpu_percent,
        "cpu_temp": round(cpu_temp, 1) if cpu_temp else None,
        "ram_percent": ram.percent,
        "ram_used": round(ram.used / 1024 / 1024 / 1024, 2),
        "ram_total": round(ram.total / 1024 / 1024 / 1024, 2),
        "disk_percent": disk.percent,
        "disk_used": round(disk.used / 1024 / 1024 / 1024, 1),
        "disk_total": round(disk.total / 1024 / 1024 / 1024, 1),
        "uptime": f"{uptime_hours}h {uptime_minutes}m",
        "ip": ip
    })

@app.route("/api/speak", methods=["POST"])
def speak():
    text = request.json.get("text")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True
        }
    }


    
    response = requests.post(url, headers=headers, json=payload)
    print("ElevenLabs status:", response.status_code)
    print("ElevenLabs response:", response.text[:300])
    
    if response.status_code == 200:
        audio_data = base64.b64encode(response.content).decode('utf-8')
        return jsonify({"audio": audio_data})
    else:
        return jsonify({"error": "TTS failed", "details": response.text}), 500


PHOTOS_DIR = os.path.join(os.path.dirname(__file__), 'static', 'photos')
@app.route("/api/photos")
def get_photos():
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']
    photos = []
    for ext in extensions:
        photos.extend(glob.glob(os.path.join(PHOTOS_DIR, ext)))
    photos = sorted([os.path.basename(p) for p in photos])
    return jsonify(photos)

@app.route('/photos/<filename>')
def serve_photo(filename):
    return send_from_directory(PHOTOS_DIR, filename)

if __name__ == "__main__":
    socketio.run(app, debug=os.getenv("FLASK_DEBUG") == "1")
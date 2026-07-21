// ---- Weather ----
async function loadWeather() {
    const response = await fetch('/api/weather');
    const data = await response.json();

    const temp = data.main.temp;
    const description = data.weather[0].description;
    const weatherMessage = `It's currently ${temp}°F with ${description}.`;

    document.getElementById('weather-info').textContent = weatherMessage;
}

// ---- Transit ----
async function loadTransit() {
    const response = await fetch('/api/transit');
    const data = await response.json();

    const arrivals = data.ctatt.eta;
    const transitMessage = arrivals.slice(0, 4).map(arrival => {
        const time = new Date(arrival.arrT).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
        return `${arrival.rt} Line to ${arrival.destNm}: ${time}`;
    }).join('<br>');

    document.getElementById('transit-info').innerHTML = transitMessage;
}

// ---- To-Do List ----
async function renderTodos() {
    const response = await fetch('/api/todos');
    const todos = await response.json();

    const list = document.getElementById('todo-list');
    list.innerHTML = '';

    todos.forEach(task => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${task}</span> <button onclick="deleteTodo('${encodeURIComponent(task)}')">✕</button>`;
        list.appendChild(li);
    });
}

async function addTodo() {
    const input = document.getElementById('todo-input');
    const value = input.value.trim();
    if (value === '') return;

    await fetch('/api/todos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: value })
    });

    input.value = '';
    renderTodos();
}

async function deleteTodo(item) {
    await fetch(`/api/todos/${item}`, { method: 'DELETE' });
    renderTodos();
}

// ---- Bucket List ----
async function renderBucketList() {
    const response = await fetch('/api/bucketlist');
    const items = await response.json();

    const list = document.getElementById('bucketlist-list');
    list.innerHTML = '';

    items.forEach(goal => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${goal}</span> <button onclick="deleteBucketItem('${encodeURIComponent(goal)}')">✕</button>`;
        list.appendChild(li);
    });
}

async function addBucketItem() {
    const input = document.getElementById('bucketlist-input');
    const value = input.value.trim();
    if (value === '') return;

    await fetch('/api/bucketlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: value })
    });

    input.value = '';
    renderBucketList();
}

async function deleteBucketItem(item) {
    await fetch(`/api/bucketlist/${item}`, { method: 'DELETE' });
    renderBucketList();
}


// ---- Voice Assistant ----
function startListening() {
    const recognition = new webkitSpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    document.getElementById('voice-status').textContent = 'Listening...';
    document.getElementById('mic-button').textContent = '🔴 Listening...';

    recognition.onresult = async function(event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById('voice-status').textContent = `Heard: "${transcript}"`;

        const response = await fetch('/api/voice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: transcript })
        });

        const data = await response.json();
        document.getElementById('voice-response').textContent = data.response;
    };

    recognition.onerror = function(event) {
        document.getElementById('voice-status').textContent = 'Error: ' + event.error;
        document.getElementById('mic-button').textContent = '🎤 Tap to Speak';
    };

    recognition.onend = function() {
        document.getElementById('mic-button').textContent = '🎤 Tap to Speak';
    };

    recognition.start();
}

// ---- Initial load ----
loadWeather();
loadTransit();
renderTodos();
renderBucketList();

// ---- Auto refresh ----
setInterval(loadWeather, 60000);
setInterval(loadTransit, 30000);
setInterval(renderTodos, 30000);
setInterval(renderBucketList, 30000);
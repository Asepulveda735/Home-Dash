// ---- WebSockets ----
const socket = io();

socket.on('dashboard_update', function(data) {
    if (data.type === 'todos') {
        renderTodos();
    }
    if (data.type === 'bucketlist') {
        renderBucketList();
    }
    if (data.type === 'all') {
        renderTodos();
        renderBucketList();
    }
});
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
// ---- Clock ----
function updateClock() {
    const now = new Date();
    const time = now.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    const date = now.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }).toUpperCase();
    document.getElementById('clock').textContent = time;
    document.getElementById('date-display').textContent = date;
}
updateClock();
setInterval(updateClock, 1000);

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

        if (data.response) {
            const utterance = new SpeechSynthesisUtterance(data.response);
            utterance.rate = 0.88;
            utterance.pitch = 0.85;
            utterance.volume = 1.0;

            const voices = window.speechSynthesis.getVoices();
            const preferred = voices.find(v => v.name.includes('Daniel')) 
                || voices.find(v => v.name.includes('Google UK English Male'))
                || voices.find(v => v.lang === 'en-GB')
                || voices.find(v => v.lang.startsWith('en'));

            if (preferred) utterance.voice = preferred;
            window.speechSynthesis.speak(utterance);
        }
        if (data.action && data.action !== 'none') {
            renderTodos();
            renderBucketList();
        }
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


// ---- Page navigation ----
let currentPage = 0;
const totalPages = 3;
let touchStartX = 0;

function goToPage(index) {
    // TODO:
    // 1. clamp index between 0 and totalPages - 1
    index = Math.max(0, Math.min(index, totalPages - 1));
    // 2. set currentPage = index
    currentPage = index;
    // 3. move .pages-wrapper with transform: translateX(-{index * 100}vw)
    document.querySelector('.pages-wrapper').style.transform = `translateX(-${index * 100}vw)`;
    // 4. update dots — remove 'active' from all, add to the current one
    document.querySelectorAll('.dot').forEach((dot, i) => {
        dot.classList.toggle('active', i === index);
    });
}

// Touch swipe detection
document.addEventListener('touchstart', e => {
    touchStartX = e.touches[0].clientX;
});

document.addEventListener('touchend', e => {
    const diff = touchStartX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) {
        if (diff > 0) goToPage(currentPage + 1); // swipe left
        else goToPage(currentPage - 1);           // swipe right
    }
});

// ---- Markets ----
async function loadMarkets() {
    // crypto
    const cryptoRes = await fetch('/api/crypto');
    const crypto = await cryptoRes.json();

    const btcChange = crypto.bitcoin.usd_24h_change.toFixed(2);
    const ethChange = crypto.ethereum.usd_24h_change.toFixed(2);

    document.getElementById('btc-price').className = 'price-value';
    document.getElementById('btc-price').textContent = `$${crypto.bitcoin.usd.toLocaleString()}`;
    document.getElementById('btc-change').className = btcChange >= 0 ? 'change-up' : 'change-down';
    document.getElementById('btc-change').textContent = `${btcChange >= 0 ? '▲' : '▼'} ${Math.abs(btcChange)}% 24h`;

    document.getElementById('eth-price').className = 'price-value';
    document.getElementById('eth-price').textContent = `$${crypto.ethereum.usd.toLocaleString()}`;
    document.getElementById('eth-change').className = ethChange >= 0 ? 'change-up' : 'change-down';
    document.getElementById('eth-change').textContent = `${ethChange >= 0 ? '▲' : '▼'} ${Math.abs(ethChange)}% 24h`;

    // S&P 500
    const spyRes = await fetch('/api/markets');
    const spy = spyRes.ok ? await spyRes.json() : null;

    if (spy && spy['Global Quote']) {
        const quote = spy['Global Quote'];
        const price = parseFloat(quote['05. price']).toFixed(2);
        const change = parseFloat(quote['09. change']).toFixed(2);
        const changePct = quote['10. change percent'];
        const open = parseFloat(quote['02. open']).toFixed(2);
        const high = parseFloat(quote['03. high']).toFixed(2);
        const low = parseFloat(quote['04. low']).toFixed(2);
        const vol = parseInt(quote['06. volume']).toLocaleString();

        document.getElementById('spy-price').className = 'price-value';
        document.getElementById('spy-price').textContent = `$${parseFloat(price).toLocaleString()}`;
        document.getElementById('spy-change').className = change >= 0 ? 'change-up' : 'change-down';
        document.getElementById('spy-change').textContent = `${change >= 0 ? '▲' : '▼'} $${Math.abs(change)} (${changePct}) today`;
        document.getElementById('spy-open').textContent = `OPEN · $${open}`;
        document.getElementById('spy-high').textContent = `HIGH · $${high}`;
        document.getElementById('spy-low').textContent = `LOW · $${low}`;
        document.getElementById('spy-vol').textContent = `VOL · ${vol}`;
}
}

loadMarkets();
setInterval(loadMarkets, 60000);



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
async function loadWeather() {
    const response = await fetch('/api/weather');
    const data = await response.json();

    const temp = data.main.temp;
    const description = data.weather[0].description;
    const weatherMessage = `It's currently ${temp}°F with ${description}.`;

    document.getElementById('weather-info').textContent = weatherMessage;
}

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

loadWeather();
loadTransit();
setInterval(loadWeather, 60000); // Refresh weather every 60 seconds
setInterval(loadTransit, 30000); // Refresh transit every 30 seconds

// ---- To-Do List ----
function getTodos() {
    return JSON.parse(localStorage.getItem('todos')) || [];
}

function saveTodos(todos) {
    localStorage.setItem('todos', JSON.stringify(todos));
}

function renderTodos() {
    const todos = getTodos();
    const list = document.getElementById('todo-list');
    list.innerHTML = '';

    todos.forEach((task, index) => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${task}</span> <button onclick="deleteTodo(${index})">✕</button>`;
        list.appendChild(li);
    });
}

function addTodo() {
    const input = document.getElementById('todo-input');
    const value = input.value.trim();
    if (value === '') return;

    const todos = getTodos();
    todos.push(value);
    saveTodos(todos);
    input.value = '';
    renderTodos();
}

function deleteTodo(index) {
    const todos = getTodos();
    todos.splice(index, 1);
    saveTodos(todos);
    renderTodos();
}

// ---- Bucket List ----
function getBucketList() {
    return JSON.parse(localStorage.getItem('bucketlist')) || [];
}

function saveBucketList(items) {
    localStorage.setItem('bucketlist', JSON.stringify(items));
}

function renderBucketList() {
    const items = getBucketList();
    const list = document.getElementById('bucketlist-list');
    list.innerHTML = '';

    items.forEach((goal, index) => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${goal}</span> <button onclick="deleteBucketItem(${index})">✕</button>`;
        list.appendChild(li);
    });
}

function addBucketItem() {
    const input = document.getElementById('bucketlist-input');
    const value = input.value.trim();
    if (value === '') return;

    const items = getBucketList();
    items.push(value);
    saveBucketList(items);
    input.value = '';
    renderBucketList();
}

function deleteBucketItem(index) {
    const items = getBucketList();
    items.splice(index, 1);
    saveBucketList(items);
    renderBucketList();
}

// ---- Initial render on page load ----
renderTodos();
renderBucketList();
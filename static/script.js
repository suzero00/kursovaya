const API_URL = window.location.origin;
let currentUser = null;
let selectedMovieCard = null;
let selectedSessionCard = null;

function saveUser(user) {
    currentUser = user;
    localStorage.setItem("currentUser", JSON.stringify(user));

    const userInfo = document.getElementById("user-info");
    userInfo.innerText = user.username + (user.is_admin ? " (админ)" : "");

    document.getElementById("btn-login").style.display = "none";
    document.getElementById("btn-register").style.display = "none";
    document.getElementById("btn-logout").style.display = "inline-block";

    if (user.is_admin) {
        document.getElementById("admin-panel").style.display = "block";
        loadAdminSessions();
    } else {
        document.getElementById("admin-panel").style.display = "none";
    }
}

function logout() {
    localStorage.removeItem("currentUser");
    currentUser = null;
    selectedMovieCard = null;
    selectedSessionCard = null;

    document.getElementById("user-info").innerText = "Гость";
    document.getElementById("btn-login").style.display = "inline-block";
    document.getElementById("btn-register").style.display = "inline-block";
    document.getElementById("btn-logout").style.display = "none";

    document.getElementById("movies").innerHTML = "";
    document.getElementById("sessions").innerHTML = "";
    document.getElementById("seats").innerHTML = "";
    document.getElementById("admin-sessions").innerHTML = "";
    document.getElementById("admin-panel").style.display = "none";
}

function loadUserFromLocal() {
    const user = JSON.parse(localStorage.getItem("currentUser"));
    if (user) saveUser(user);
}

async function registerUser(username, password) {
    const res = await fetch(`${API_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (res.ok) {
        alert("Регистрация выполнена!");
        location.href = "/login";
    } else {
        alert(data.detail);
    }
}

async function loginUser(username, password) {
    const res = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({username,password})
    });
    const data = await res.json();
    if (res.ok) {
        saveUser(data);
        location.href = "/";
    } else {
        alert(data.detail);
    }
}

async function loadMovies() {
    const res = await fetch(`${API_URL}/movies`);
    const movies = await res.json();
    const container = document.getElementById("movies");
    container.innerHTML = "";

    movies.forEach(movie => {
    const card = document.createElement("div");
    card.className = "card";

    const genres = movie.genres.join(", ");

    card.innerHTML = `
        <img src="${movie.image_url}" alt="${movie.title}" class="movie-poster" />
        <h3>${movie.title}</h3>
        <p class="movie-genres"><strong>Жанры:</strong> ${genres}</p>
        <p class="movie-description">${movie.description}</p>
    `;

    card.onclick = () => {
        if (selectedMovieCard) selectedMovieCard.classList.remove("active");
        card.classList.add("active");
        selectedMovieCard = card;

        loadSessions(movie.id);
        document.getElementById("seats").innerHTML = "";
        selectedSessionCard = null;
    };

    container.appendChild(card);
});
}

async function loadSessions(movieId) {
    const res = await fetch(`${API_URL}/sessions/${movieId}`);
    const sessions = await res.json();
    const container = document.getElementById("sessions");
    container.innerHTML = "<h2>Выберите сеанс:</h2>";

    sessions.forEach(session => {
        const card = document.createElement("div");
        card.className = "card session-card";
        card.innerHTML = `<h3>${session.time}</h3><p>Зал: ${session.hall_id}</p>`;

        card.onclick = () => {
            if (selectedSessionCard) selectedSessionCard.classList.remove("active");
            card.classList.add("active");
            selectedSessionCard = card;

            showSeats(session);
        };

        container.appendChild(card);
    });

    if (currentUser?.is_admin) loadAdminSessions();
}

function showSeats(session) {
    if (!currentUser) {
        alert("Войдите в аккаунт");
        return;
    }

    const container = document.getElementById("seats");
    container.innerHTML = `<h2>Места (${session.time})</h2>`;

    for (let i = 1; i <= 10; i++) {
        const seat = document.createElement("div");
        seat.className = "seat free";
        seat.innerText = i;

        const bookedIndex = session.seats_booked.findIndex(s => s.startsWith(i + "_"));
        if (bookedIndex !== -1) {
            const username = session.seats_booked[bookedIndex].split("_")[1];
            seat.className = username === currentUser.username ? "seat my-booked" : "seat booked";
        }

        seat.onclick = async () => {
            if (seat.classList.contains("booked")) return;

            const isMySeat = seat.classList.contains("my-booked");
            if (!confirm(`Вы уверены, что хотите ${isMySeat ? "отменить" : "забронировать"} место №${i}?`)) return;
            const action = isMySeat ? "/cancel" : "/book";

            const res = await fetch(`${API_URL}${action}`, {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({
                    session_id: session.id,
                    seat_number: i,
                    username: currentUser.username
                })
            });
            const data = await res.json();
            if (!res.ok) return alert(data.detail);

            seat.className = isMySeat ? "seat free" : "seat my-booked";
            if (isMySeat) {
                session.seats_booked = session.seats_booked.filter(s => s !== `${i}_${currentUser.username}`);
            } else {
                session.seats_booked.push(`${i}_${currentUser.username}`);
            }

            if (currentUser.is_admin) loadAdminSessions();
        };

        container.appendChild(seat);
    }
}

async function loadAdminSessions() {
    if (!currentUser?.is_admin) return;

    const container = document.getElementById("admin-sessions");
    container.innerHTML = "";

    const movies = await (await fetch(`${API_URL}/movies`)).json();
    for (const movie of movies) {
        const sessions = await (await fetch(`${API_URL}/sessions/${movie.id}`)).json();
        sessions.forEach(session => {
            const row = document.createElement("div");
            row.className = "admin-session";
            row.innerHTML = `
                <span>${movie.title} — ${session.time}</span>
                <div>
                    <button onclick="editSession(${session.id})">Изменить</button>
                    <button onclick="deleteSession(${session.id})">Удалить</button>
                    <button onclick="clearBookings(${session.id})">Очистить брони</button>
                </div>
            `;
            container.appendChild(row);
        });
    }
}

async function editSession(sessionId){
    const newTime = prompt("Введите новое время:");
    if (!newTime) return;
    const res = await fetch(`${API_URL}/sessions/${sessionId}/edit?username=${currentUser.username}&time=${newTime}`, {method:"PUT"});
    const data = await res.json();
    alert(data.message || data.detail);
    loadMovies();
}

async function deleteSession(sessionId){
    if (!confirm("Удалить сеанс?")) return;
    const res = await fetch(`${API_URL}/sessions/${sessionId}?username=${currentUser.username}`, {method:"DELETE"});
    const data = await res.json();
    alert(data.message || data.detail);
    loadMovies();
}

async function clearBookings(sessionId){
    if(!confirm("Очистить все брони?")) return;
    const movies = await (await fetch(`${API_URL}/movies`)).json();
    for(const movie of movies){
        const sessions = await (await fetch(`${API_URL}/sessions/${movie.id}`)).json();
        const session = sessions.find(s => s.id === sessionId);
        if (!session) continue;
        for(const seatStr of session.seats_booked){
            const [seat, user] = seatStr.split("_");
            await fetch(`${API_URL}/sessions/${sessionId}/booking?seat_number=${seat}&username=${user}&admin_username=${currentUser.username}`, {method:"DELETE"});
        }
    }
    alert("Очищено!");
    loadMovies();
}

window.onload = () => {
    loadUserFromLocal();
    if (document.getElementById("movies")) loadMovies();
    const logoutBtn = document.getElementById("btn-logout");
    if (logoutBtn) logoutBtn.onclick = logout;
};

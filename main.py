from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class User(BaseModel):
    username: str
    password: str
    is_admin: bool = False

class CinemaHall(BaseModel):
    id: int
    name: str
    seats_total: int

class Movie(BaseModel):
    id: int
    title: str
    description: str
    genres: List[str]
    image_url: str

class Session(BaseModel):
    id: int
    movie_id: int
    hall_id: int
    time: str
    seats_booked: List[str] = []

class Booking(BaseModel):
    session_id: int
    seat_number: int
    username: str

users: List[User] = [User(username="admin", password="admin123", is_admin=True)]
halls: List[CinemaHall] = [CinemaHall(id=1, name="Зал 1", seats_total=10)]

movies: List[Movie] = [
    Movie(
        id=1,
        title="Титаник",
        description="История любви на фоне трагедии затонувшего корабля.",
        genres=["Драма", "Романтика", "История"],
        image_url="https://m.media-amazon.com/images/M/MV5BYzYyN2FiZmUtYWYzMy00MzViLWJkZTMtOGY1ZjgzNWMwN2YxXkEyXkFqcGc%40._V1_FMjpg_UX1000_.jpg"
    ),
    Movie(
        id=2,
        title="Интерстеллар",
        description="Команда исследователей отправляется в космос для спасения человечества.",
        genres=["Фантастика", "Приключения", "Драма"],
        image_url="https://film-grab.com/wp-content/uploads/2015/04/35-512.jpg"
    ),
    Movie(
        id=3,
        title="Начало",
        description="Вор, способный проникать в сны, получает необычное задание.",
        genres=["Фантастика", "Боевик", "Триллер"],
        image_url="https://m.media-amazon.com/images/I/81p+xe8cbnL._AC_SY679_.jpg"
    ),
    Movie(
        id=4,
        title="Матрица",
        description="Программист узнаёт, что реальность — это иллюзия.",
        genres=["Фантастика", "Боевик"],
        image_url="https://m.media-amazon.com/images/I/51EG732BV3L.jpg"
    ),
    Movie(
        id=5,
        title="Форрест Гамп",
        description="История жизни простого человека с большим сердцем.",
        genres=["Драма", "Комедия"],
        image_url="https://m.media-amazon.com/images/I/61+9F8N1Z0L._AC_SY679_.jpg"
    ),
    Movie(
        id=6,
        title="Зелёная миля",
        description="Надзиратель тюрьмы сталкивается с настоящим чудом.",
        genres=["Драма", "Фэнтези"],
        image_url="https://m.media-amazon.com/images/I/51NiGlapXlL.jpg"
    ),
    Movie(
        id=7,
        title="Бойцовский клуб",
        description="Офисный работник создаёт подпольный бойцовский клуб.",
        genres=["Драма", "Триллер"],
        image_url="https://m.media-amazon.com/images/I/51v5ZpFyaFL.jpg"
    ),
    Movie(
        id=8,
        title="Гладиатор",
        description="Римский генерал становится гладиатором.",
        genres=["История", "Драма", "Боевик"],
        image_url="https://m.media-amazon.com/images/I/51A9FQ5YF9L.jpg"
    ),
    Movie(
        id=9,
        title="Джокер",
        description="История становления одного из самых известных злодеев.",
        genres=["Драма", "Триллер"],
        image_url="https://m.media-amazon.com/images/I/71xBLRBYOiL._AC_SY679_.jpg"
    ),
    Movie(
        id=10,
        title="Властелин колец: Братство кольца",
        description="Начало великого путешествия по Средиземью.",
        genres=["Фэнтези", "Приключения"],
        image_url="https://m.media-amazon.com/images/I/51Qvs9i5a+L.jpg"
    ),
]

sessions: List[Session] = [
    Session(id=1, movie_id=1, hall_id=1, time="18:00"),
    Session(id=2, movie_id=1, hall_id=1, time="21:00"),
    Session(id=3, movie_id=2, hall_id=1, time="19:00"),
]

@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse("templates/index.html")

@app.get("/login", response_class=HTMLResponse)
def login_page():
    return FileResponse("templates/login.html")

@app.get("/register", response_class=HTMLResponse)
def register_page():
    return FileResponse("templates/register.html")

@app.post("/register")
def register(user: User):
    if any(u.username == user.username for u in users):
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    users.append(user)
    return {"message": f"Пользователь {user.username} зарегистрирован"}

@app.post("/login")
def login(user: User):
    u = next((u for u in users if u.username == user.username and u.password == user.password), None)
    if not u:
        raise HTTPException(status_code=401, detail="Неверные имя пользователя или пароль")
    return {"username": u.username, "is_admin": u.is_admin}

@app.post("/book")
def book_seat(booking: Booking):
    session = next((s for s in sessions if s.id == booking.session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Сеанс не найден")
    hall = next((h for h in halls if h.id == session.hall_id), None)
    if booking.seat_number < 1 or booking.seat_number > hall.seats_total:
        raise HTTPException(status_code=400, detail="Неверный номер места")
    if any(s.startswith(f"{booking.seat_number}_") for s in session.seats_booked):
        raise HTTPException(status_code=400, detail="Место уже забронировано")
    session.seats_booked.append(f"{booking.seat_number}_{booking.username}")
    return {"message": f"Место {booking.seat_number} забронировано пользователем {booking.username}"}

@app.post("/cancel")
def cancel_booking(booking: Booking):
    session = next((s for s in sessions if s.id == booking.session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Сеанс не найден")
    seat_str = f"{booking.seat_number}_{booking.username}"
    if seat_str not in session.seats_booked:
        raise HTTPException(status_code=400, detail="Вы не бронировали это место")
    session.seats_booked.remove(seat_str)
    return {"message": f"Бронь места {booking.seat_number} отменена пользователем {booking.username}"}

@app.put("/sessions/{session_id}/edit")
def edit_session(session_id: int, time: str, username: str):
    user = next((u for u in users if u.username == username), None)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    session = next((s for s in sessions if s.id == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Сеанс не найден")
    session.time = time
    return {"message": f"Сеанс {session_id} обновлён, новое время {time}"}

@app.delete("/sessions/{session_id}")
def delete_session(session_id: int, username: str):
    user = next((u for u in users if u.username == username), None)
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    global sessions
    sessions = [s for s in sessions if s.id != session_id]
    return {"message": f"Сеанс {session_id} удалён"}

@app.delete("/sessions/{session_id}/booking")
def delete_booking(session_id: int, seat_number: int, username: str, admin_username: str):
    admin = next((u for u in users if u.username == admin_username), None)
    if not admin or not admin.is_admin:
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    session = next((s for s in sessions if s.id == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Сеанс не найден")
    seat_str = f"{seat_number}_{username}"
    if seat_str in session.seats_booked:
        session.seats_booked.remove(seat_str)
        return {"message": f"Бронь места {seat_number} пользователя {username} удалена"}
    else:
        raise HTTPException(status_code=400, detail="Бронь не найдена")

@app.get("/movies", response_model=List[Movie])
def get_movies():
    return movies

@app.get("/sessions/{movie_id}", response_model=List[Session])
def get_sessions(movie_id: int):
    return [s for s in sessions if s.movie_id == movie_id]

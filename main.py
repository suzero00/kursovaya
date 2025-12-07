from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

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
movies: List[Movie] = [Movie(id=1, title="Титаник"), Movie(id=2, title="Интерстеллар")]
sessions: List[Session] = [
    Session(id=1, movie_id=1, hall_id=1, time="18:00"),
    Session(id=2, movie_id=1, hall_id=1, time="21:00"),
    Session(id=3, movie_id=2, hall_id=1, time="19:00"),
]

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

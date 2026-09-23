# Real-Time Multi-Room Chat Application

A full-stack chat platform built with **Angular (Material UI)**, **Flask (Socket.IO)**, **PostgreSQL**, and **Apache Cassandra**.

---

## Port Numbers at a Glance

| Service | Port | URL / Connection |
| :--- | :--- | :--- |
| **Frontend** | `4200` | [http://localhost:4200](http://localhost:4200) |
| **Backend** | `5000` | [http://localhost:5000](http://localhost:5000) |
| **PostgreSQL** | `5432` | `localhost:5432` |
| **Cassandra** | `9042` | `localhost:9042` |

---

## Prerequisites and Required Dependencies

To run the project, make sure you have the following installed:

- **Docker & Docker Compose** (easiest way to run the entire app or just the databases)
- **Python 3.14+** and **uv** 
- **Node.js (v20+ or v22+)** and **npm**

---

## Required Environment Variables & Configuration

The application reads configuration from a root `.env` file. A ready-to-use template is included in `.env.example`.

Create your `.env` file by copying the template:

```bash
cp .env.example .env
```

Here is what each variable does:

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `SECRET_KEY` | Flask secret key for sessions | Pre-filled in `.env.example` |
| `JWT_SECRET_KEY` | Key used to sign JWT auth tokens | Pre-filled in `.env.example` |
| `POSTGRES_PASSWORD` | Password for PostgreSQL user `user` | `password` |
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql+psycopg://user:password@localhost:5432/reatimechat_db` |
| `CORS_ORIGINS` | Allowed frontend origins | `http://localhost:4200,http://localhost:3000` |
| `CASSANDRA_HOSTS` | Cassandra host | `localhost` (or `cassandra` in Docker) |
| `CASSANDRA_PORT` | Cassandra port | `9042` |
| `CASSANDRA_KEYSPACE` | Keyspace name for chat history | `chat` |

---

## Quick Start with Docker (Recommended)

The fastest way to test the entire application is with Docker Compose:

```bash
# 1. Copy the environment file
cp .env.example .env

# 2. Build and start all services (Postgres, Cassandra, Flask, Angular)
docker compose up --build -d
```

Once running:
- Open your browser to **[http://localhost:4200](http://localhost:4200)** to use the chat app.
- Check backend health at **[http://localhost:5000/api/health](http://localhost:5000/api/health)**.

To check backend logs:
```bash
docker compose logs -f backend
```

To stop everything:
```bash
docker compose down
```

---

## Database Setup & Configuration

We use two databases tailored to different workloads:

### 1. PostgreSQL (Relational Data)
PostgreSQL stores structured data with strict relational integrity:
- **`users`**: User profiles with `bcrypt`-hashed passwords.
- **`rooms`**: Chat room details and ownership.
- **`room_memberships`**: Composite key `(room_id, user_id)` ensuring a user can't join a room twice, and non-members can't read or send messages in private rooms.

**Database Migrations:**
Migrations run automatically on startup. To run or inspect them manually:
```bash
cd chat-backend
uv run flask --app "app:create_app()" db upgrade
```

### 2. Apache Cassandra (Time-Series Messages)
Cassandra handles chat messages because chat history is append-only and write-intensive:
- **Keyspace**: `chat`
- **Table**: `messages`
- **Partition Key**: `room_id` — All messages for a room are stored on the same partition.
- **Clustering Key**: `message_id` (`TIMEUUID DESC`) — Messages are ordered by time so recent history loads instantly.

---

## Backend Setup and How to Run the Backend

If you want to run the Flask backend directly on your computer:

```bash
# 1. Make sure databases are running
docker compose up -d db cassandra

# 2. Navigate to backend directory and configure env
cd chat-backend
cp .env.example .env

# 3. Install Python dependencies
uv sync

# 4. Start the server (runs migrations automatically)
uv run run.py
```

The backend server will start on **`http://127.0.0.1:5000`**.

---

## Frontend Setup and How to Run the Angular Application

To run the Angular frontend on your computer:

```bash
cd chat-frontend

# 1. Install Node dependencies
npm install

# 2. Start the development server
npm start
```

The Angular app will open on **`http://localhost:4200`**. 

> **Note:** The dev server uses `proxy.conf.json` to automatically forward all `/api/*` and `/socket.io/*` requests to the Flask server on port 5000, avoiding CORS issues during local development.

---

## WebSocket Connection Configuration

Real-time messaging, typing indicators, and user presence are handled by **Flask-SocketIO** (server) and **socket.io-client** (frontend).

- **Path**: `/socket.io`
- **Authentication**: JWT token sent during the initial handshake:
  ```typescript
  io({
    path: '/socket.io',
    auth: { token: jwtToken },
    transports: ['polling', 'websocket']
  });
  ```

### Supported WebSocket Events

| Event Name | Direction | Purpose |
| :--- | :--- | :--- |
| `join_room` | Client &rarr; Server | Subscribes client to a room channel (verifies membership first). |
| `leave_room` | Client &rarr; Server | Unsubscribes client from a room channel. |
| `send_message` | Client &rarr; Server | Persists message to Cassandra and broadcasts it to the room. |
| `typing` | Client &rarr; Server | Sends ephemeral typing state (`isTyping: true/false`). |
| `receive_message` | Server &rarr; Client | Delivers new messages to all active room subscribers. |
| `user_joined` | Server &rarr; Client | Notifies room subscribers when someone enters. |
| `user_left` | Server &rarr; Client | Notifies room subscribers when someone leaves. |
| `user_typing` | Server &rarr; Client | Broadcasts who is currently typing. |

---

## Instructions for Running the Unit Tests

### 1. Backend Tests (Pytest)
Run the backend test suite:
```bash
cd chat-backend
uv run pytest -v
```

**What is tested:**
- `test_auth.py`: Registration, duplicate user checks, login, JWT validation, and bcrypt password hashing.
- `test_rooms.py`: Room creation, room listing, member joins/leaves, and membership access authorization.
- `test_chat.py`: Message history loading via REST, WebSocket connection, live message broadcasting, and typing events.
- `test_health.py`: Basic API health check.

### 2. Frontend Tests (Angular / Vitest)
Run the frontend unit tests:
```bash
cd chat-frontend
npm test -- --watch=false
```

**What is tested:**
- `login.spec.ts`: Login and registration form rendering, input validation, and submission.
- `chat-room.spec.ts`: Chat room loading, message timeline display, sending messages, and active user list.
- `auth.service.spec.ts`: Authentication requests and token management.
- `room.service.spec.ts`: Room fetching, creating, and joining.
- `websocket.service.spec.ts`: WebSocket connection lifecycle and event subscriptions.
- `app.spec.ts` & `message.service.spec.ts`: Application creation and service instantiation.

---

## Any Additional Steps Required to Run the Application Successfully

To verify multi-user real-time chat with two people:

1. Open **[http://localhost:4200](http://localhost:4200)** in your primary browser window and register **User 1**.
2. Open **[http://localhost:4200](http://localhost:4200)** in an **Incognito / Private window** and register **User 2**.
3. In User 1's window, create a new room (e.g., *"Team Chat"*). User 1 is automatically joined.
4. In User 2's window, find *"Team Chat"* in the list, click **Join Room**, and open the chat.
5. You can now test:
   - **Active Participants List**: Both users appear in the participants sidebar with an online indicator.
   - **Live Messaging**: Messages sent from one window appear instantly in the other with a `NEW` badge.
   - **Typing Indicators**: Start typing in one window; the other window shows `"... is typing..."`.
   - **Message Persistence**: Refresh either browser window to confirm messages rehydrate from Cassandra.

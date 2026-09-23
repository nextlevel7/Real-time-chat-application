from datetime import UTC, datetime
from uuid import UUID, uuid1

from cassandra.cluster import Cluster
from flask import current_app

_CLUSTER = None
_SESSION = None
_CASSANDRA_FAILED = False

# In-memory store for tests and local fallback when Cassandra is unreachable
_FALLBACK_MESSAGES: dict[UUID, list[dict]] = {}


def get_cassandra_session():
    """Lazily connect to Cassandra cluster and keyspace.

    Falls back to an in-memory store if Cassandra is unavailable or if app is in TESTING mode.
    """
    global _CLUSTER, _SESSION, _CASSANDRA_FAILED
    if current_app.config.get("TESTING") or _CASSANDRA_FAILED:
        return None

    if _SESSION is not None:
        return _SESSION

    try:
        hosts = current_app.config.get("CASSANDRA_HOSTS", ["localhost"])
        port = current_app.config.get("CASSANDRA_PORT", 9042)
        keyspace = current_app.config.get("CASSANDRA_KEYSPACE", "chat")

        cluster = Cluster(contact_points=hosts, port=port, connect_timeout=3)
        session = cluster.connect()
        session.execute(
            f"CREATE KEYSPACE IF NOT EXISTS {keyspace} "
            "WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};"
        )
        session.set_keyspace(keyspace)
        session.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                room_id uuid,
                message_id timeuuid,
                sender_id uuid,
                sender_username text,
                content text,
                created_at timestamp,
                PRIMARY KEY (room_id, message_id)
            ) WITH CLUSTERING ORDER BY (message_id DESC);
            """
        )
        _CLUSTER = cluster
        _SESSION = session
        return _SESSION
    except Exception as exc:  # noqa: BLE001 - Graceful degradation to in-memory store
        _CASSANDRA_FAILED = True
        current_app.logger.warning(
            f"Could not connect to Cassandra: {exc}. Using in-memory fallback for messages."
        )
        return None


def save_message(
    room_id: UUID, sender_id: UUID, sender_username: str, content: str
) -> dict:
    """Save a chat message with a TIMEUUID primary key."""
    message_id = uuid1()
    created_at = datetime.now(UTC)

    msg = {
        "id": str(message_id),
        "roomId": str(room_id),
        "senderId": str(sender_id),
        "senderUsername": sender_username,
        "content": content,
        "createdAt": created_at.isoformat(),
    }

    session = get_cassandra_session()
    if session is not None:
        session.execute(
            """
            INSERT INTO messages (room_id, message_id, sender_id, sender_username, content, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (room_id, message_id, sender_id, sender_username, content, created_at),
        )
    else:
        if room_id not in _FALLBACK_MESSAGES:
            _FALLBACK_MESSAGES[room_id] = []
        _FALLBACK_MESSAGES[room_id].append(msg)

    return msg


def get_messages(room_id: UUID, limit: int = 50) -> list[dict]:
    """Retrieve recent messages for a room in chronological order."""
    session = get_cassandra_session()
    if session is not None:
        rows = session.execute(
            """
            SELECT room_id, message_id, sender_id, sender_username, content, created_at
            FROM messages
            WHERE room_id = %s
            LIMIT %s
            """,
            (room_id, limit),
        )
        messages = [
            {
                "id": str(row.message_id),
                "roomId": str(row.room_id),
                "senderId": str(row.sender_id),
                "senderUsername": row.sender_username,
                "content": row.content,
                "createdAt": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
        messages.reverse()
        return messages
    else:
        room_msgs = _FALLBACK_MESSAGES.get(room_id, [])
        return room_msgs[-limit:]


def clear_test_messages() -> None:
    """Clear in-memory fallback store between tests."""
    _FALLBACK_MESSAGES.clear()

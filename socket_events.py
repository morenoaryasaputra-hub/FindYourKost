from flask import session

from flask_socketio import emit
from flask_socketio import join_room
from flask_socketio import leave_room

from extensions import socketio
from extensions import get_db


@socketio.on("join")
def on_join(data):

    room = str(data["room"])

    join_room(room)

    emit(
        "status",
        {
            "msg": "joined"
        },
        room=room
    )


@socketio.on("leave")
def on_leave(data):

    room = str(data["room"])

    leave_room(room)


@socketio.on("send_message")
def send_message(data):

    room = str(data["room"])

    pesan = data["message"]

    sender_id = session.get("user_id")

    conn = get_db()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO chat_message
        (
            room_id,
            sender_id,
            pesan
        )
        VALUES
        (
            %s,
            %s,
            %s
        )
        """,
        (
            room,
            sender_id,
            pesan
        )
    )

    conn.commit()

    cursor.close()

    conn.close()

    emit(
        "receive_message",
        {
            "sender_id": sender_id,
            "message": pesan
        },
        room=room
    )
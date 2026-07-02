from flask import session

from flask_socketio import join_room
from flask_socketio import leave_room

from extensions import socketio
from extensions import get_db


@socketio.on("join")
def join(data):

    room = str(data["room"])

    print("JOIN ROOM:", room)

    join_room(room)


@socketio.on("leave")
def leave(data):

    room = str(data["room"])

    leave_room(room)


@socketio.on("send_message")
def send_message(data):

    room = str(data["room"])

    pesan = data["message"]

    sender = session["user_id"]

    print("SEND:", room, sender, pesan)

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
            sender,
            pesan
        )
    )

    conn.commit()

    cursor.close()

    conn.close()

    socketio.emit(

        "receive_message",

        {

            "sender_id": sender,

            "message": pesan

        },
        to=room,
        namespace="/"

    )

    print("EMIT:", room)
from flask import Blueprint, render_template, session, redirect, request
from extensions import get_db

chat_bp = Blueprint(
    "chat",
    __name__
)

#-------------------------#
# CHAT
#-------------------------#

@chat_bp.route("/chat")
def chat():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    # daftar room milik user

    cursor.execute("""
        SELECT
            cr.id,

            u.nama,

            u.foto_profil,

            k.nama_kost,

            (
                SELECT pesan
                FROM chat_message
                WHERE room_id=cr.id
                ORDER BY waktu_kirim DESC
                LIMIT 1
            ) last_message,

            (
                SELECT waktu_kirim
                FROM chat_message
                WHERE room_id=cr.id
                ORDER BY waktu_kirim DESC
                LIMIT 1
            ) last_time

        FROM chat_room cr

        JOIN users u
        ON u.id = cr.pemilik_id

        JOIN kost k
        ON k.id = cr.kost_id

        WHERE cr.penyewa_id=%s

        ORDER BY last_time DESC

    """, (session["user_id"],))

    rooms = cursor.fetchall()

    active_room = None
    messages = []

    if rooms:

        active_room = rooms[0][0]

        cursor.execute("""

            SELECT

                cm.id,
                cm.sender_id,
                cm.pesan,
                cm.waktu_kirim,
                u.nama

            FROM chat_message cm

            JOIN users u
            ON u.id = cm.sender_id

            WHERE room_id=%s

            ORDER BY waktu_kirim

        """, (active_room,))

        messages = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "chat/chat.html",
        rooms=rooms,
        messages=messages,
        active_room=active_room
    )

#-------------------------#
# CHAT ROOM
#-------------------------#

@chat_bp.route("/chat/<int:room_id>")
def open_room(room_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            cr.id,
            u.nama,
            u.foto_profil,
            k.nama_kost,

            (
                SELECT pesan
                FROM chat_message
                WHERE room_id=cr.id
                ORDER BY waktu_kirim DESC
                LIMIT 1
            ) last_message,

            (
                SELECT waktu_kirim
                FROM chat_message
                WHERE room_id=cr.id
                ORDER BY waktu_kirim DESC
                LIMIT 1
            ) last_time

        FROM chat_room cr

        JOIN users u
        ON u.id=cr.pemilik_id

        JOIN kost k
        ON k.id=cr.kost_id

        WHERE cr.penyewa_id=%s

        ORDER BY last_time DESC

    """, (session["user_id"],))

    rooms = cursor.fetchall()

    cursor.execute("""

        SELECT

            cm.id,
            cm.sender_id,
            cm.pesan,
            cm.waktu_kirim,
            u.nama

        FROM chat_message cm

        JOIN users u
        ON u.id=cm.sender_id

        WHERE room_id=%s

        ORDER BY waktu_kirim

    """, (room_id,))

    messages = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "chat/chat.html",
        rooms=rooms,
        messages=messages,
        active_room=room_id
    )

#-------------------------#
# SEND MESSAGE
#-------------------------#

@chat_bp.route("/chat/send", methods=["POST"])
def send_message():

    if "user_id" not in session:
        return redirect("/login")

    room_id = request.form["room_id"]
    pesan = request.form["pesan"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""

        INSERT INTO chat_message(

            room_id,
            sender_id,
            pesan

        )

        VALUES(%s,%s,%s)

    """, (

        room_id,
        session["user_id"],
        pesan

    ))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(f"/chat/{room_id}")

@chat_bp.route("/chat/create/<int:kost_id>")
def create_chat(kost_id):

    if "user_id" not in session:

        return redirect("/login")

    conn = get_db()

    cursor = conn.cursor()

    # Ambil pemilik kos

    cursor.execute(
        """
        SELECT pemilik_id
        FROM kost
        WHERE id=%s
        """,
        (kost_id,)
    )

    kost = cursor.fetchone()

    if not kost:

        cursor.close()
        conn.close()

        return redirect("/")

    pemilik_id = kost[0]

    # Cek apakah room sudah ada

    cursor.execute(
        """
        SELECT id
        FROM chat_room
        WHERE

        penyewa_id=%s
        AND pemilik_id=%s
        AND kost_id=%s
        """,
        (
            session["user_id"],
            pemilik_id,
            kost_id
        )
    )

    room = cursor.fetchone()

    if room:

        room_id = room[0]

    else:

        cursor.execute(
            """
            INSERT INTO chat_room
            (
                penyewa_id,
                pemilik_id,
                kost_id
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
            """,
            (
                session["user_id"],
                pemilik_id,
                kost_id
            )
        )

        conn.commit()

        room_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return redirect(
        f"/chat/{room_id}"
    )
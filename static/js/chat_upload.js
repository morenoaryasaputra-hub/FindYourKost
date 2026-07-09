// js/chat_upload.js
document.getElementById('file-input').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;

    const roomId = document.getElementById("room_id").value;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('room_id', roomId);

    // Kirim ke backend (route /chat/upload yang tadi sudah kita buat)
    fetch('/chat/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if(data.success) {
            // Beritahu socket agar pesan muncul di layar tanpa reload
           // Di dalam success callback upload:
    socket.emit("send_message", {
    room: roomId,
    message: "FILE_UPLOADED", // Penanda ini adalah file
    file_path: data.file_path,
    file_type: file.type // contoh: image/png, video/mp4
    });
        } else {
            alert("Error: " + data.error);
        }
    })
    .catch(err => console.error("Upload error:", err));
});

// ... di dalam fetch().then() ...
if(data.success) {
    // KITA KIRIM PESAN KOSONG SAJA, BIARKAN FRONTEND YANG ME-RENDER DARI file_path
    socket.emit("send_message", {
        room: roomId,
        message: "", // Kosongkan, nanti di-render oleh chat.html
        file_path: data.file_path,
        file_type: file.type
    });
}
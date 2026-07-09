// static/js/payment.js
function payNow(amount) {
    // 1. Minta token ke backend kita
    fetch('/create-transaction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: amount })
    })
    .then(response => response.json())
    .then(data => {
        // 2. Tampilkan popup Midtrans
        window.snap.pay(data.token, {
            onSuccess: function(result){
                alert("Pembayaran Berhasil! Terima kasih.");
                // Bisa redirect ke halaman pembayaran.html
                window.location.href = "/pembayaran"; 
            },
            onPending: function(result){
                alert("Menunggu pembayaran...");
            },
            onError: function(result){
                alert("Pembayaran Gagal!");
            }
        });
    })
    .catch(err => console.error(err));
}
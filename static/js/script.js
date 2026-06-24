document.addEventListener('DOMContentLoaded', function() {
    
    // Cek apakah elemen grafik ada di halaman ini
    const canvas = document.getElementById('revenueChart');
    
    if (canvas) {
        const ctx = canvas.getContext('2d');
        const revenueChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun'],
                datasets: [
                    {
                        label: 'Pendapatan 2026',
                        data: [40, 55, 45, 70, 60, 82.4],
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { display: false },
                    x: { grid: { display: false } }
                }
            }
        });
    }
});
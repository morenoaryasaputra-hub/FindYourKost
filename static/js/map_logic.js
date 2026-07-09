document.addEventListener("DOMContentLoaded", function() {
    // API Key diinject langsung dari Flask agar aman
    const API_KEY = document.getElementById("geoapify_key_holder").value;
    
    const regionCoords = {
        "Salatiga": [-7.3305, 110.5084], "Tuntang": [-7.2700, 110.4550], 
        "Bawen": [-7.2400, 110.4250], "Ambarawa": [-7.2600, 110.3950],
        "Tengaran": [-7.3850, 110.5350], "Suruh": [-7.3600, 110.5850],
        "Pabelan": [-7.2900, 110.5650], "Beringin": [-7.2450, 110.5500], 
        "Banyubiru": [-7.2950, 110.4000]
    };

    // Inisialisasi Map
    const map = L.map('mapPicker').setView([-7.3305, 110.5084], 15);
    L.tileLayer(`https://maps.geoapify.com/v1/tile/osm-bright/{z}/{x}/{y}.png?apiKey=${API_KEY}`, {
        attribution: "© Geoapify", maxZoom: 19
    }).addTo(map);

    let marker = L.marker([-7.3305, 110.5084], { draggable: true }).addTo(map);

    async function updateData(lat, lng) {
        document.getElementById("latInput").value = lat;
        document.getElementById("lngInput").value = lng;
        const wrapper = document.getElementById("wrapperFasilitas");
        
        // Fetch Alamat (Reverse Geocoding)
        try {
            const geoResp = await fetch(`https://api.geoapify.com/v1/geocode/reverse?lat=${lat}&lon=${lng}&apiKey=${API_KEY}`);
            const geoData = await geoResp.json();
            if(geoData.features.length > 0) {
                document.getElementById("alamatInput").value = geoData.features[0].properties.formatted;
            }
            
            // Fetch Fasilitas (Kategori luas supaya tidak kosong)
            const cat = "commercial,education,catering,service,tourism,leisure";
            const pResp = await fetch(`https://api.geoapify.com/v2/places?categories=${cat}&filter=circle:${lng},${lat},2000&limit=15&apiKey=${API_KEY}`);
            const pData = await pResp.json();
            
            wrapper.innerHTML = ""; // Bersihkan
            pData.features.forEach(f => {
                const p = f.properties;
                if(p.name) {
                    wrapper.innerHTML += `
                    <div class="fasilitas-item" style="padding:8px; border-bottom:1px solid #eee;">
                        <i class="fas fa-map-marker-alt text-danger"></i> <strong>${p.name}</strong><br>
                        <small class="text-muted">${Math.round(p.distance)} meter</small>
                    </div>`;
                }
            });
        } catch(e) {
            wrapper.innerHTML = "Gagal memuat fasilitas.";
        }
    }

    // Dropdown Logic
    document.getElementById("wilayahSelect").addEventListener("change", function() {
        const c = regionCoords[this.value];
        if(c) {
            map.setView(c, 15);
            marker.setLatLng(c);
            updateData(c[0], c[1]);
        }
    });

    marker.on('dragend', () => updateData(marker.getLatLng().lat, marker.getLatLng().lng));
});
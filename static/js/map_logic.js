document.addEventListener("DOMContentLoaded", function() {
    // 1. Ambil API Key dari hidden input HTML yang dikirim Flask
    const keyHolder = document.getElementById("geoapify_key_holder");
    const API_KEY = keyHolder ? keyHolder.value : "b5ebf0b5ae1047cc8ea72c255a6c3b1a"; // Fallback aman jika kosong
    
    // Koordinat Daerah Salatiga & Sekitarnya
    const regionCoords = {
        "Salatiga": [-7.3305, 110.5084], "Tuntang": [-7.2700, 110.4550], 
        "Bawen": [-7.2400, 110.4250], "Ambarawa": [-7.2600, 110.3950],
        "Tengaran": [-7.3850, 110.5350], "Suruh": [-7.3600, 110.5850],
        "Pabelan": [-7.2900, 110.5650], "Beringin": [-7.2450, 110.5500], 
        "Banyubiru": [-7.2950, 110.4000]
    };

    // Ambil data koordinat awal (berguna untuk halaman Edit Kos agar tidak lompat balik)
    let initialLat = parseFloat(document.getElementById("latInput").value) || -7.3305;
    let initialLng = parseFloat(document.getElementById("lngInput").value) || 110.5084;

    // Inisialisasi Peta Leaflet
    const map = L.map('mapPicker').setView([initialLat, initialLng], 15);
    L.tileLayer(`https://maps.geoapify.com/v1/tile/osm-bright/{z}/{x}/{y}.png?apiKey=${API_KEY}`, {
        attribution: "© Geoapify", maxZoom: 19
    }).addTo(map);

    let marker = L.marker([initialLat, initialLng], { draggable: true }).addTo(map);
    let markersFasilitas = []; // Menyimpan marker fasilitas umum sekitar jika dibutuhkan

    // ========================================================
    // FUNGSI FOKUS 2: KLIK LIST FASILITAS -> MAP TERBANG (IDE KAMU)
    // ========================================================
    window.terbangKeFasilitas = function(lat, lng, nama) {
        map.flyTo([lat, lng], 17, { animate: true, duration: 1.5 }); // Kamera meluncur ke koordinat objek
        L.popup()
            .setLatLng([lat, lng])
            .setContent(`<div class="text-center p-1"><strong class="text-primary d-block mb-1">${nama}</strong><small class="text-muted">Fasilitas Sekitar Kos</small></div>`)
            .openOn(map);
    };

    // Tombol opsional untuk mengembalikan fokus kamera ke posisi Pin Kos utama
    window.kembaliKeKos = function() {
        let lat = parseFloat(document.getElementById("latInput").value);
        let lng = parseFloat(document.getElementById("lngInput").value);
        map.flyTo([lat, lng], 15);
        map.closePopup();
    };

    // ========================================================
    // FUNGSI FOKUS 1: AMBIL LOKASI UTAMA & TEMUKAN FASILITAS SEKITAR
    // ========================================================
    async function updateData(lat, lng, isInit = false) {
        document.getElementById("latInput").value = lat;
        document.getElementById("lngInput").value = lng;
        const wrapper = document.getElementById("wrapperFasilitas");
        
        // Buat tombol kembali ke kos selalu stand-by di atas list fasilitas
        let baseHtml = `
            <div class="mb-3 sticky-top bg-light pb-2 pt-1">
                <button type="button" class="btn btn-outline-primary btn-sm w-100 fw-bold shadow-sm" onclick="kembaliKeKos()">
                    <i class="fas fa-crosshairs me-2"></i> Fokus ke Lokasi Kos
                </button>
            </div>
        `;
        wrapper.innerHTML = baseHtml + '<div class="text-center py-4"><i class="fas fa-spinner fa-spin text-primary"></i> Melacak satelit...</div>';

        try {
            // A. REVERSE GEOCODING (Ubah Koordinat jadi Teks Alamat Jalan)
            if(!isInit || !document.getElementById("alamatInput").value.trim()) {
                const geoResp = await fetch(`https://api.geoapify.com/v1/geocode/reverse?lat=${lat}&lon=${lng}&apiKey=${API_KEY}`);
                const geoData = await geoResp.json();
                if(geoData.features && geoData.features.length > 0) {
                    document.getElementById("alamatInput").value = geoData.features[0].properties.formatted;
                }
            }
            
            // B. PLACES API (Diperluas Kategori & Di-Fix agar tidak Bad Request 400)
            const cat = "commercial.supermarket,commercial.convenience,education.university,catering.restaurant,catering.cafe,service.financial.atm";
            const pResp = await fetch(`https://api.geoapify.com/v2/places?categories=${cat}&filter=circle:${lng},${lat},2000&bias=proximity:${lng},${lat}&limit=15&apiKey=${API_KEY}`);
            const pData = await pResp.json();
            
            let listHtml = "";
            if(pData.features && pData.features.length > 0) {
                pData.features.forEach(f => {
                    const p = f.properties;
                    if(p.name && p.lat && p.lon) {
                        let iconClass = "fa-map-marker-alt text-secondary";
                        let cats = p.categories || [];
                        
                        // Deteksi rumpun kategori agar ikon bervariasi cantik
                        if(cats.some(c => c.includes("education"))) iconClass = "fa-graduation-cap text-primary";
                        else if(cats.some(c => c.includes("commercial"))) iconClass = "fa-shopping-cart text-success";
                        else if(cats.some(c => c.includes("catering"))) iconClass = "fa-utensils text-danger";
                        else if(cats.some(c => c.includes("financial"))) iconClass = "fa-money-bill-wave text-info";

                        let safeName = p.name.replace(/'/g, "\\'"); // Handle string kutip tunggal agar tidak patah

                        // Suntik fungsi klik langsung terbang menggunakan window.terbangKeFasilitas
                        listHtml += `
                        <div class="fasilitas-item d-flex align-items-center py-2 px-2 border-bottom bg-white rounded-3 mb-2 shadow-sm" 
                             style="cursor:pointer; transition: 0.2s;" 
                             onclick="terbangKeFasilitas(${p.lat}, ${p.lon}, '${safeName}')"
                             onmouseover="this.style.backgroundColor='#f1f5f9';" onmouseout="this.style.backgroundColor='#ffffff';">
                            <i class="fas ${iconClass} me-3 fs-6" style="width:20px; text-align:center;"></i>
                            <div class="w-100 d-flex justify-content-between align-items-center">
                                <div>
                                    <strong class="text-dark d-block" style="font-size: 13px;">${p.name}</strong>
                                    <small class="text-muted" style="font-size: 11px;">Klik untuk intip lokasi</small>
                                </div>
                                <span class="badge bg-secondary bg-opacity-10 text-dark border text-xs px-2 py-1 rounded-pill">${Math.round(p.distance)} m</span>
                            </div>
                        </div>`;
                    }
                });
                wrapper.innerHTML = baseHtml + listHtml;
            } else {
                wrapper.innerHTML = baseHtml + '<div class="p-3 text-muted text-center small">Fasilitas umum tidak terdata di radius 2KM dari titik ini.</div>';
            }
        } catch(e) {
            console.error("Maps Connection Error: ", e);
            wrapper.innerHTML = baseHtml + '<div class="p-3 text-danger text-center small">Koneksi satelit Geoapify terputus.</div>';
        }
    }

    // ========================================================
    // FUNGSI FOKUS 3: AUTOCOMPLETE ALAMAT CARI MANUAL (ALA SHOPEE)
    // ========================================================
    const alamatInput = document.getElementById("alamatInput");
    if(alamatInput) {
        // Buka kunci input agar user BISA MENGETIK MANUAL (Bukan cuma dari sistem)
        alamatInput.removeAttribute("readonly");
        alamatInput.placeholder = "Ketik alamat kos Anda di sini (Contoh: Kauman Salatiga)...";

        // Buat kotak melayang (Dropdown) rekomendasi tepat di bawah input alamat
        const sugBox = document.createElement("div");
        sugBox.id = "geo-autocomplete-dropdown";
        sugBox.style.cssText = "position:absolute; background:#fff; border:1px solid #d1d5db; width:100%; z-index:9999; max-height:220px; overflow-y:auto; border-radius:8px; display:none; box-shadow:0 10px 15px -3px rgba(0,0,0,0.1); font-family:inherit;";
        alamatInput.parentNode.style.position = "relative";
        alamatInput.parentNode.appendChild(sugBox);

        // Dengarkan saat user mengetik di kolom alamat
        alamatInput.addEventListener("input", async function() {
            let query = this.value;
            if(query.length < 3) { sugBox.style.display = "none"; return; } // Minimal 3 huruf baru cari

            try {
                // Tembak API Autocomplete Geoapify (Diberikan pembatas bias radius 40KM sekitar Salatiga agar akurat)
                let autocompleteUrl = `https://api.geoapify.com/v1/geocode/autocomplete?text=${encodeURIComponent(query)}&filter=circle:110.5084,-7.3305,40000&apiKey=${API_KEY}`;
                let response = await fetch(autocompleteUrl);
                let result = await response.json();
                
                sugBox.innerHTML = "";
                if(result.features && result.features.length > 0) {
                    sugBox.style.display = "block";
                    result.features.forEach(place => {
                        let info = place.properties;
                        let row = document.createElement("div");
                        row.style.cssText = "padding:10px 14px; cursor:pointer; border-bottom:1px solid #f3f4f6; font-size:13px; text-align:left; transition:0.2s;";
                        row.innerHTML = `<i class="fas fa-map-marker-alt text-muted me-2"></i> <span>${info.formatted}</span>`;
                        
                        // Efek Hover baris list ala Shopee
                        row.onmouseover = function() { this.style.backgroundColor = "#eff6ff"; };
                        row.onmouseout = function() { this.style.backgroundColor = "#ffffff"; };
                        
                        // KETIKA USER KLIK SALAH SATU DAFTAR ALAMAT REKOMENDASI
                        row.addEventListener("click", function() {
                            alamatInput.value = info.formatted; // Isi input kolom dengan alamat lengkap pilihan
                            sugBox.style.display = "none";     // Sembunyikan dropdown shopee
                            
                            let targetLat = info.lat;
                            let targetLon = info.lon;
                            
                            // Terbangkan kamera peta dan pin merah ke alamat yang diketik user tersebut!
                            map.flyTo([targetLat, targetLon], 16);
                            marker.setLatLng([targetLat, targetLon]);
                            
                            // Jalankan reload pencarian fasilitas umum di dekat alamat baru tersebut
                            updateData(targetLat, targetLon, true);
                        });
                        sugBox.appendChild(row);
                    });
                } else { sugBox.style.display = "none"; }
            } catch(err) { console.error("Autocomplete Gagal:", err); }
        });

        // Sembunyikan kotak pencarian shopee jika user mengklik sembarang tempat di luar area input
        document.addEventListener("click", function(e) {
            if(e.target !== alamatInput) { sugBox.style.display = "none"; }
        });
    }

    // ========================================================
    // LOGIKA PENGIKAT EVENT TRIGGER MAPS
    // ========================================================
    // Dropdown wilayah biasa bawaan kamu
    const wilayahSelect = document.getElementById("wilayahSelect");
    if(wilayahSelect) {
        wilayahSelect.addEventListener("change", function() {
            const c = regionCoords[this.value];
            if(c) {
                map.setView(c, 15);
                marker.setLatLng(c);
                updateData(c[0], c[1]);
            }
        });
    }

    // Ketika pin merah digeser manual oleh user
    marker.on('dragend', function() {
        const pos = marker.getLatLng();
        updateData(pos.lat, pos.lng);
    });

    // Ketika bagian area peta diklik sembarang oleh user
    map.on('click', function(e) {
        marker.setLatLng(e.latlng);
        updateData(e.latlng.lat, e.latlng.lng);
    });

    // Pemicu awal saat halaman pertama kali dibuka
    updateData(initialLat, initialLng, true);
});
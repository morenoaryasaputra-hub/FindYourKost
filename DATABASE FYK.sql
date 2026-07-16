CREATE DATABASE IF NOT EXISTS findyourkost;
USE findyourkost;

CREATE TABLE `log_admin` (
  `id` int NOT NULL AUTO_INCREMENT,
  `admin_id` int NOT NULL,
  `kategori` varchar(50) NOT NULL,
  `aksi` varchar(100) NOT NULL,
  `deskripsi` text NOT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin AUTO_INCREMENT=240001;


CREATE TABLE `notifikasi_pemilik` (
  `id` int NOT NULL AUTO_INCREMENT,
  `pemilik_id` int NOT NULL,
  `judul` varchar(100) NOT NULL,
  `pesan` text NOT NULL,
  `ikon` varchar(50) DEFAULT 'fa-bell',
  `warna` varchar(20) DEFAULT 'primary',
  `is_read` tinyint(1) DEFAULT '0',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin AUTO_INCREMENT=120001;


CREATE TABLE `paket_premium` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nama_paket` varchar(50) NOT NULL DEFAULT 'Premium',
  `harga` decimal(12,2) NOT NULL DEFAULT '99000.00',
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin AUTO_INCREMENT=30002;


CREATE TABLE `premium_tiers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `price` int NOT NULL,
  `status` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin AUTO_INCREMENT=30001;


CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nama` varchar(100) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `email` varchar(100) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `google_id` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `no_hp` varchar(20) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `foto_profil` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `role` enum('penyewa','pemilik','admin') COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'penyewa',
  `is_profile_complete` tinyint(1) DEFAULT '0',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `alamat` text COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `tanggal_lahir` date DEFAULT NULL,
  `jenis_kelamin` enum('L','P') COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `foto_ktp` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `is_verified` tinyint(1) DEFAULT '0',
  `pekerjaan` varchar(100) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `instansi` varchar(150) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `is_premium` tinyint(1) DEFAULT '0',
  `nama_bank` varchar(50) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `no_rekening` varchar(50) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `atas_nama_rekening` varchar(100) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `nik` varchar(20) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `nama_ktp` varchar(100) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `is_ktp_verified` tinyint(1) DEFAULT '0',
  `ktp_attempts` int DEFAULT '0',
  `last_ktp_attempt` date DEFAULT NULL,
  `tempat_lahir` varchar(100) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `alamat_ktp` text COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `status_akun` varchar(20) COLLATE utf8mb4_0900_ai_ci DEFAULT 'aktif',
  `alasan_status` text COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `suspend_until` datetime DEFAULT NULL,
  `saldo_dompet` decimal(12,2) DEFAULT '0.00',
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci AUTO_INCREMENT=600001;


CREATE TABLE `banding` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `alasan` text DEFAULT NULL,
  `status` varchar(20) DEFAULT 'pending',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`user_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin AUTO_INCREMENT=300001;


CREATE TABLE `kost` (
  `id` int NOT NULL AUTO_INCREMENT,
  `pemilik_id` int NOT NULL,
  `nama_kost` varchar(150) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `alamat` text COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `deskripsi` text COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `harga` decimal(12,2) NOT NULL,
  `tipe_penghuni` enum('putra','putri','campur') COLLATE utf8mb4_0900_ai_ci DEFAULT 'campur',
  `total_kamar` int NOT NULL DEFAULT '1',
  `sisa_kamar` int DEFAULT '0',
  `latitude` decimal(10,8) DEFAULT NULL,
  `longitude` decimal(11,8) DEFAULT NULL,
  `status_verifikasi` tinyint(1) DEFAULT '0',
  `tier_listing` enum('none','silver','gold','premium') COLLATE utf8mb4_0900_ai_ci DEFAULT 'none',
  `foto_thumbnail` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `status_promosi` tinyint(1) DEFAULT '0',
  `alasan_penolakan` text COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `uang_muka` int DEFAULT '0',
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`pemilik_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`pemilik_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci AUTO_INCREMENT=420001;


CREATE TABLE `laporan` (
  `id` int NOT NULL AUTO_INCREMENT,
  `pelapor_id` int NOT NULL,
  `kost_id` int NOT NULL,
  `alasan` text COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `status` enum('pending','diproses','selesai') COLLATE utf8mb4_0900_ai_ci DEFAULT 'pending',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`pelapor_id`),
  KEY `fk_2` (`kost_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`pelapor_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_2` FOREIGN KEY (`kost_id`) REFERENCES `kost` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci AUTO_INCREMENT=30001;


CREATE TABLE `notifikasi` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `judul` varchar(100) NOT NULL,
  `pesan` text NOT NULL,
  `is_read` tinyint(1) DEFAULT '0',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`user_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;


CREATE TABLE `password_reset_tokens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `token` varchar(255) NOT NULL,
  `expired_at` datetime NOT NULL,
  `is_used` tinyint(1) DEFAULT '0',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`user_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin AUTO_INCREMENT=120001;


CREATE TABLE `payouts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `booking_id` int NOT NULL,
  `pemilik_id` int NOT NULL,
  `jumlah_transfer` decimal(10,2) NOT NULL,
  `status` enum('Pending','Paid') DEFAULT 'Pending',
  `bukti_transfer` varchar(255) DEFAULT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`pemilik_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`pemilik_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;


CREATE TABLE `premium_subscription` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `tier` enum('silver','gold','premium') COLLATE utf8mb4_0900_ai_ci DEFAULT 'silver',
  `tanggal_mulai` date DEFAULT NULL,
  `tanggal_akhir` date DEFAULT NULL,
  `status` enum('aktif','expired') COLLATE utf8mb4_0900_ai_ci DEFAULT 'aktif',
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`user_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `rekening_bank` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `nama_bank` varchar(50) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `nomor_rekening` varchar(50) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `atas_nama` varchar(100) COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `is_utama` tinyint(1) DEFAULT '0',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`user_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `verifikasi_kost` (
  `id` int NOT NULL AUTO_INCREMENT,
  `kost_id` int NOT NULL,
  `admin_id` int NOT NULL,
  `status` enum('pending','diterima','ditolak') COLLATE utf8mb4_0900_ai_ci DEFAULT 'pending',
  `catatan` text COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`kost_id`),
  KEY `fk_2` (`admin_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`kost_id`) REFERENCES `kost` (`id`),
  CONSTRAINT `fk_2` FOREIGN KEY (`admin_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `wishlist` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `kost_id` int NOT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`user_id`),
  KEY `fk_2` (`kost_id`),
  UNIQUE KEY `unique_wishlist` (`user_id`,`kost_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_2` FOREIGN KEY (`kost_id`) REFERENCES `kost` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci AUTO_INCREMENT=300001;


CREATE TABLE `booking` (
  `id` int NOT NULL AUTO_INCREMENT,
  `penyewa_id` int NOT NULL,
  `kost_id` int NOT NULL,
  `tanggal_booking` datetime DEFAULT CURRENT_TIMESTAMP,
  `tanggal_masuk` date DEFAULT NULL,
  `durasi_bulan` int DEFAULT NULL,
  `total_harga` decimal(12,2) DEFAULT NULL,
  `status_booking` varchar(50) COLLATE utf8mb4_0900_ai_ci DEFAULT 'menunggu_dp',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `status_pembayaran` enum('Belum Bayar','Tertunda','Lunas') COLLATE utf8mb4_0900_ai_ci DEFAULT 'Belum Bayar',
  `alasan_tolak` text COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`penyewa_id`),
  KEY `fk_2` (`kost_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`penyewa_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_2` FOREIGN KEY (`kost_id`) REFERENCES `kost` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci AUTO_INCREMENT=330001;


CREATE TABLE `buku_kas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `kost_id` int NOT NULL,
  `jenis_transaksi` enum('pemasukan','pengeluaran') COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `kategori` varchar(50) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `nominal` decimal(12,2) NOT NULL,
  `keterangan` text COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `tanggal_transaksi` date NOT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`kost_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`kost_id`) REFERENCES `kost` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `chat_room` (
  `id` int NOT NULL AUTO_INCREMENT,
  `penyewa_id` int NOT NULL,
  `pemilik_id` int NOT NULL,
  `kost_id` int NOT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`penyewa_id`),
  KEY `fk_2` (`pemilik_id`),
  KEY `fk_3` (`kost_id`),
  KEY `idx_room` (`penyewa_id`,`pemilik_id`,`kost_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`penyewa_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_2` FOREIGN KEY (`pemilik_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_3` FOREIGN KEY (`kost_id`) REFERENCES `kost` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci AUTO_INCREMENT=300001;


CREATE TABLE `escrow` (
  `id` int NOT NULL AUTO_INCREMENT,
  `booking_id` int NOT NULL,
  `admin_id` int DEFAULT NULL,
  `rekening_tujuan_id` int DEFAULT NULL,
  `jumlah_dp` decimal(12,2) DEFAULT NULL,
  `potongan_komisi` decimal(12,2) DEFAULT '0.00',
  `nominal_bersih` decimal(12,2) DEFAULT NULL,
  `status` enum('ditahan','released','refund') COLLATE utf8mb4_0900_ai_ci DEFAULT 'ditahan',
  `bukti_transfer` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `tanggal_release` datetime DEFAULT NULL,
  `tanggal_refund` datetime DEFAULT NULL,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`booking_id`),
  KEY `fk_2` (`admin_id`),
  KEY `fk_3` (`rekening_tujuan_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_2` FOREIGN KEY (`admin_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_3` FOREIGN KEY (`rekening_tujuan_id`) REFERENCES `rekening_bank` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci AUTO_INCREMENT=30001;


CREATE TABLE `foto_kost` (
  `id` int NOT NULL AUTO_INCREMENT,
  `kost_id` int NOT NULL,
  `url_foto` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`kost_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`kost_id`) REFERENCES `kost` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `pembayaran` (
  `id` int NOT NULL AUTO_INCREMENT,
  `booking_id` int NOT NULL,
  `midtrans_order_id` varchar(100) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `jumlah` decimal(12,2) DEFAULT NULL,
  `metode_pembayaran` varchar(100) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `status_pembayaran` enum('pending','success','failed','expired') COLLATE utf8mb4_0900_ai_ci DEFAULT 'pending',
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `snap_token` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `jenis_pembayaran` enum('dp','pelunasan') COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `status_pencairan` varchar(50) COLLATE utf8mb4_0900_ai_ci DEFAULT 'belum_cair',
  `bukti_pencairan` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `tanggal_pencairan` datetime DEFAULT NULL,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`booking_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci AUTO_INCREMENT=360001;


CREATE TABLE `review` (
  `id` int NOT NULL AUTO_INCREMENT,
  `booking_id` int NOT NULL,
  `user_id` int NOT NULL,
  `kost_id` int NOT NULL,
  `rating` int DEFAULT NULL,
  `ulasan` text COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`booking_id`),
  KEY `fk_2` (`user_id`),
  KEY `fk_3` (`kost_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`id`),
  CONSTRAINT `fk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_3` FOREIGN KEY (`kost_id`) REFERENCES `kost` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci AUTO_INCREMENT=30001;


CREATE TABLE `tagihan_penghuni` (
  `id` int NOT NULL AUTO_INCREMENT,
  `booking_id` int NOT NULL,
  `bulan_tagihan` date NOT NULL,
  `nominal` decimal(12,2) NOT NULL,
  `status` enum('belum_bayar','lunas') COLLATE utf8mb4_0900_ai_ci DEFAULT 'belum_bayar',
  `tanggal_jatuh_tempo` date NOT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`booking_id`),
  CONSTRAINT `fk_1` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `chat_message` (
  `id` int NOT NULL AUTO_INCREMENT,
  `room_id` int NOT NULL,
  `sender_id` int NOT NULL,
  `pesan` text COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT '0',
  `waktu_kirim` timestamp DEFAULT CURRENT_TIMESTAMP,
  `file_path` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `is_tagihan` tinyint(1) DEFAULT '0',
  `tagihan_amount` decimal(15,2) DEFAULT NULL,
  PRIMARY KEY (`id`) /*T![clustered_index] CLUSTERED */,
  KEY `fk_1` (`room_id`),
  KEY `fk_2` (`sender_id`),
  KEY `idx_message` (`room_id`,`waktu_kirim`),
  CONSTRAINT `fk_1` FOREIGN KEY (`room_id`) REFERENCES `chat_room` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_2` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci AUTO_INCREMENT=660001;
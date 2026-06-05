# 🏥 Sistem E-Commerce Klinik Makmur Jaya

Sebuah sistem informasi manajemen apotek dan *e-commerce* berbasis Web yang dibangun khusus untuk memenuhi persyaratan Ujian Kompetensi BNSP. Sistem ini menggunakan arsitektur monolitik modern dengan **FastAPI (Python)** sebagai *backend*, **SQLite** sebagai basis data, dan **Jinja2 + TailwindCSS + Alpine.js** sebagai *frontend*.

---

## 🌟 Fitur Utama

### 1. Autentikasi & Keamanan (Modul 1)
- **Role-Based Access Control (RBAC)**: Pemisahan level akses untuk Admin, Apoteker, Kasir, dan Pelanggan.
- **Enkripsi Kuat**: Penyimpanan *password* menggunakan format hashing `bcrypt`.
- **Keamanan Siber**: Proteksi terhadap *SQL Injection* (via SQLAlchemy), *XSS* (via Jinja2 autoescape), dan *CSRF* (via SessionMiddleware).
- **Session Cookie**: Autentikasi UI berjalan lancar dan aman menggunakan `HTTPOnly Cookie` yang memiliki masa kedaluwarsa otomatis.
- **Audit Log**: Seluruh aktivitas krusial (*Login, Checkout, dll.*) tercatat kedalam *Database* dengan informasi stempel waktu (*timestamp*).

### 2. Dashboard Admin & Monitoring (Modul 2)
- **Visualisasi Data**: Statistik penjualan, total pelanggan, dan pesanan terbaru ditampilkan menggunakan integrasi `Chart.js`.
- **Monitor Server**: Pengecekan real-time status RAM, Disk, dan CPU server menggunakan pustaka `psutil`.
- **Export PDF**: Kemampuan mencetak laporan menggunakan *Print API* ke bentuk PDF yang *clean* dan presentabel.

### 3. Manajemen Data Inventaris (Modul 3)
- **Sistem FIFO (First-In, First-Out)**: Pengurangan stok obat secara otomatis dan cerdas yang mengutamakan inventaris dengan tanggal kedaluwarsa (`expiry_date`) terdekat.
- **Transaksional Atomik**: Pengamanan keranjang belanja (*Checkout*), membatalkan seluruh operasi (*rollback*) apabila stok tiba-tiba habis.
- **Fuzzy Search & Autocomplete**: Kueri pencarian obat pintar.
- **Dokumen Rekam Medis**: Fitur unggah foto/PDF Resep Dokter (`Prescription`) ke penyimpanan lokal `/static/uploads`.

### 4. Background Task & Real-time (Modul 4 & 5)
- **Notifikasi WebSockets**: Admin dapat melihat perubahan/peringatan sistem yang muncul sebagai "Toast Pop-up" tanpa perlu melakukan *refresh* halaman.
- **Asynchronous Paralel**: Modul Impor Katalog (*CSV*) masif dijalankan dalam sistem antrean *Thread Pool Background* (agar UI tidak *freeze*).
- **Simulasi Email**: Pengiriman email verifikasi disimulasikan melalui pencatatan *logger server* di latar belakang.

---

## 🛠️ Teknologi yang Digunakan
* **Backend**: Python 3.10+, FastAPI, Uvicorn (Web Server)
* **Database**: SQLite3, SQLAlchemy ORM, Alembic (Migrasi)
* **Frontend**: Jinja2 Templates, Tailwind CSS (via CDN), Alpine.js, Chart.js, Lucide Icons
* **Security**: Passlib (Bcrypt), Python-Jose (JWT), Starlette Sessions

---

## 🚀 Panduan Instalasi & Menjalankan Aplikasi

Jika Anda ingin mendemokan aplikasi ini, ikuti langkah-langkah di bawah:

### Prasyarat
- **Python 3.10** atau lebih baru terpasang di komputer Anda.
- **Git** (opsional).

### 1. Kloning / Unduh Repositori
Buka terminal/Command Prompt dan arahkan ke folder proyek ini.

### 2. Siapkan Lingkungan Virtual (Virtual Environment)
Sangat disarankan menggunakan `venv` agar modul tidak bercampur dengan Python global Anda.
```bash
python -m venv venv

# Aktifkan venv (Windows):
venv\Scripts\activate

# Aktifkan venv (Mac/Linux):
source venv/bin/activate
```

### 3. Pasang Dependensi
```bash
pip install -r requirements.txt
```
> *Catatan: Pastikan kapasitas disk Anda mencukupi. Jika gagal memasang pustaka seperti `pydantic-core` (karena membutuhkan Rust), Anda disarankan untuk membersihkan disk sementara waktu.*

### 4. Migrasi Database Pertama Kali
Buat tabel-tabel SQLite dengan menjalankan *Alembic*:
```bash
alembic upgrade head
```

### 5. (Wajib) Eksekusi Seeder Pengguna
Untuk mendapatkan kredensial awal (Akun Admin, Apoteker, Pelanggan), jalankan *script* penyemaian data bawaan:
```bash
python seed_users.py
```
*Script* ini akan membuat berkas `makmurjaya.db` dan mencetak kombinasi **Email dan Password** ke layar Terminal Anda.

### 6. Jalankan Server Web Asinkron
```bash
uvicorn main:app --reload
```

Aplikasi sekarang dapat diakses melalui browser kesayangan Anda:
* **Halaman Web (Katalog & Dashboard)**: [http://localhost:8000](http://localhost:8000)
* **Dokumentasi API Terbuka (Swagger UI)**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

---

## 📂 Struktur Direktori Proyek

```text
makmurjayamedicines/
├── alembic/              # Berkas migrasi database struktural
├── app/                  # Direktori utama logika perangkat lunak
│   ├── api/              # Rute API REST (auth.py, ws.py, api.py) & Rute HTML (web.py)
│   ├── core/             # Konfigurasi sistem dasar (database.py, security.py)
│   ├── models/           # Entitas SQLAlchemy (models.py)
│   ├── repositories/     # Logika kueri database spesifik (repositories.py)
│   ├── schemas/          # Validasi tipe Pydantic (schemas.py)
│   ├── services/         # Algoritma tingkat tinggi (inventory.py, checkout.py)
│   ├── static/           # Berkas CSS statis dan folder penyimpanan unggahan
│   └── templates/        # Halaman frontend Jinja2 HTML (UI K-24)
├── docs/BNSP/            # (ERD, UAT, Skalabilitas, Risiko)
├── main.py               # Titik masuk eksekusi FastAPI
├── requirements.txt      # Daftar modul Python
├── seed_users.py         # Skrip penghasil akun demo otomatis
└── README.md             # Dokumentasi proyek (berkas ini)
```

---

## 📜 Dokumen BNSP (Phase 10)
Terdapat 5 dokumen teoritis esensial yang ditujukan langsung bagi *Assessor* BNSP, terletak di dalam folder `docs/BNSP/`:
1. `1_erd_schema.md` (Entity Relationship Diagram)
2. `2_arsitektur_skalabilitas.md` (Topologi Jaringan dan Skala Perangkat Keras)
3. `3_analisis_risiko.md` (Manajemen Risiko Siber & Operasional)
4. `4_migrasi_cutover_rollback.md` (Strategi Implementasi *Live-Production*)
5. `5_uat_troubleshooting.md` (Rancangan Tes Klien / User Acceptance Testing)

---
*Didedikasikan oleh Deshi Ardiani untuk Ujian Kompetensi BNSP.*

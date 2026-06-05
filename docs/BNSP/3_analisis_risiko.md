# 3. Analisis Risiko Keamanan & Mitigasi
**Sistem E-Commerce Klinik Makmur Jaya**

Dokumen ini memetakan potensi risiko keamanan informasi dan operasional sistem, beserta langkah-langkah teknis mitigasi yang telah diterapkan pada aplikasi.

## Tabel Pemetaan Risiko

| ID | Kategori | Deskripsi Risiko (Ancaman) | Dampak | Probabilitas | Tingkat Risiko | Mitigasi / Solusi yang Diterapkan di Sistem |
|:---|:---|:---|:---|:---|:---|:---|
| RSK-01 | **Keamanan Data** | *SQL Injection*: Penyerang memanipulasi form input (pencarian, login) untuk mengekstrak atau merusak database. | Tinggi | Menengah | **Tinggi** | Seluruh operasi *database* dipetakan secara ketat menggunakan *Object Relational Mapping* (**SQLAlchemy ORM**) yang secara bawaan melakukan parametrisasi *query* sehingga menghindari injeksi sintaksis SQL mentah. |
| RSK-02 | **Keamanan Web** | *Cross-Site Scripting (XSS)*: Penyerang memasukkan skrip berbahaya (misal via komentar/deskripsi) yang dieksekusi di browser korban. | Menengah | Tinggi | **Tinggi** | Mesin *template* Jinja2 yang digunakan telah memiliki fitur **Autoescape** aktif secara *default*, yang menyaring tag HTML/JS berbahaya menjadi *safe string*. |
| RSK-03 | **Keamanan Web** | *Cross-Site Request Forgery (CSRF)*: Eksploitasi sesi *cookie* pengguna untuk memalsukan permintaan paksa tanpa sadar (misal: merubah profil). | Menengah | Menengah | **Menengah** | Aplikasi menerapkan `SessionMiddleware` untuk meng-*generate* dan mencocokkan `csrf_token` rahasia di dalam *hidden input field* form sebelum memproses instruksi POST (khususnya Login/Order). |
| RSK-04 | **Autentikasi** | *Brute Force / Credential Stuffing*: Pencurian sandi pengguna. | Kritikal | Tinggi | **Kritikal** | 1) Sandi di-*hash* menggunakan algoritma kuat **Bcrypt** (Passlib) dengan fungsi *salting* otomatis.<br>2) Pydantic *Schema* menerapkan *Regex* validasi (minimal 8 karakter, kombinasi huruf kapital dan angka). |
| RSK-05 | **Aksesibilitas** | Akses Tidak Sah terhadap Halaman Admin (Bypass *Role*). | Tinggi | Rendah | **Menengah** | Sistem *backend* diamankan menggunakan **Role-Based Access Control (RBAC)** melalui Dependency Injection (`get_current_admin`), yang selalu memeriksa secara persisten apakah *token JWT* (*bearer/cookie*) benar-benar berelasi dengan `Role` bernilai "Admin". |
| RSK-06 | **Operasional** | Hilangnya Bukti Riwayat (Denial of Action) oleh admin atau staf internal yang korup. | Tinggi | Rendah | **Menengah** | Sistem menanamkan tabel **AuditLog** yang mencatat segala bentuk aksi (`LOGIN_WEB`, `UPLOAD_RESEP`), ID Pengguna, dan stempel waktu (`created_at`) secara mutlak, tidak dapat dihapus melalui UI. |
| RSK-07 | **Integritas Data**| *Race Condition*: Pengurangan stok obat secara bersamaan oleh dua pelanggan (menghasilkan stok minus). | Tinggi | Menengah | **Tinggi** | Transaksi *Checkout* dan pengurangan inventaris dikurung di dalam satu sesi transaksi transaksional atomik. Sistem menerapkan logika FIFO yang akan di-*rollback* (`db.rollback()`) sepenuhnya apabila stok tidak memadai sebelum sempat disimpan (`db.commit()`). |

## Kebijakan Pencadangan Data (Backup Policy)

Karena aplikasi menggunakan **SQLite** (fase awal), kebijakan pencadangannya sangat mudah dan dapat diproses seketika tanpa mematikan layanan (Zero Downtime Backup):

1. **Daily Backup (Harian)**: Menyalin berkas `makmurjaya.db` setiap jam 00:00 ke penyimpanan komputasi lokal lain (misal cron job *scp/rsync*).
2. **Weekly Cloud Archive (Mingguan)**: Mengemas (tar/zip) database harian dan file media di `/static/uploads` untuk dikirimkan secara otomatis ke *Object Storage* atau *Google Drive* menggunakan protokol asinkron.

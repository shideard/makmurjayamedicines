# 5. Dokumen UAT & Panduan Troubleshooting
**Sistem E-Commerce Klinik Makmur Jaya**

Dokumen ini mendefinisikan langkah pengujian terakhir (User Acceptance Testing) bersama klien dan instruksi penyelesaian masalah (Troubleshooting) bagi admin.

## 5.1. User Acceptance Testing (UAT)

UAT dilakukan dengan menandai metrik kelulusan berikut:

| ID Tes | Skenario Pengujian | Hasil yang Diharapkan (Expected Result) | Status |
|:---|:---|:---|:---|
| UAT-01 | Pengujian Login Admin vs Pelanggan | Pengguna dengan *Role* Pelanggan ditolak masuk saat membuka `/admin/dashboard`. Admin berhasil masuk. | [  ] LULUS / [  ] GAGAL |
| UAT-02 | Pembelian Obat dan FIFO Inventory | Saat pelanggan melakukan Checkout 5 item, sistem akan memotong jumlah dari *Inventory Batch* yang `expiry_date`-nya paling dekat. | [  ] LULUS / [  ] GAGAL |
| UAT-03 | Pengunggahan Resep Dokter | File resep (`.jpg` / `.pdf`) berhasil tersimpan di lokal `/static/uploads` dan tautan url-nya tertaut di pesanan. | [  ] LULUS / [  ] GAGAL |
| UAT-04 | Keamanan CSRF pada Formulir | Modifikasi nilai *hidden input* `csrf_token` pada form akan menyebabkan *request* ditolak sistem (400 Bad Request). | [  ] LULUS / [  ] GAGAL |
| UAT-05 | Background Task & Notifikasi | Saat Admin menekan "Cetak Laporan / Import CSV", UI tidak membeku (*freeze*). Setelah tugas asinkron selesai, *Toast Notification* berwarna hijau muncul. | [  ] LULUS / [  ] GAGAL |

*Catatan: Keseluruhan UAT di atas menjadi parameter baku kelulusan sistem dalam pengujian fungsional.*

## 5.2. Panduan Penyelesaian Masalah (Troubleshooting Guide)

Berikut adalah panduan bagi administrator teknis jika menemukan kendala operasional:

### T: Aplikasi Menampilkan `500 Internal Server Error` saat Checkout
* **Penyebab Kemungkinan**: Kegagalan koneksi database SQLite saat proses pengecekan stok persediaan (*Database locked*) akibat tingginya tingkat konkurensi, atau ada *bug* logika komitmen.
* **Solusi/Pengecekan**: Buka berkas `AuditLog` di tabel database. Aplikasi di-*design* agar melakukan otomatis `db.rollback()` jika *commit* gagal. Hubungi *engineer* backend jika *error* berkelanjutan, sistem tidak membiarkan terjadinya data korup.

### T: Notifikasi Toast "Real-time" Tidak Muncul di Dashboard
* **Penyebab Kemungkinan**: Koneksi *WebSocket* terputus, atau *port* WebSocket (`/ws/notifications`) diblokir oleh *Firewall/Antivirus* lokal di jaringan klinik.
* **Solusi/Pengecekan**: 
  1. Buka *Developer Tools* browser (F12) > tab *Network* > pilih filter *WS* (WebSockets). 
  2. Periksa apakah rute *WebSocket* merespons `101 Switching Protocols`. Jika ada pesan *Connection Refused*, periksa status *server backend* (Uvicorn).

### T: Import CSV Tersangkut/Gagal dan Data Tidak Masuk
* **Penyebab Kemungkinan**: Format kolom *header* pada file `.csv` tidak sesuai (*name, slug, price, description*) atau terdapat karakter ilegal/kosong di kolom wajib.
* **Solusi/Pengecekan**:
  Pastikan format dokumen sesuai templat yang direkomendasikan. Sistem menggunakan *Background Tasks* sehingga *error stack-trace* tidak dilempar langsung ke UI. Admin perlu memeriksa jendela *Command Prompt/Terminal* di sisi server untuk melihat keluaran log kegagalan `BackgroundTasks`.

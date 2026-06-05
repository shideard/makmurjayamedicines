# 4. Rencana Migrasi Data, Cutover & Rollback Plan
**Sistem E-Commerce Klinik Makmur Jaya**

Rencana ini menjadi pedoman operasional apabila sistem yang di-*host* saat ini ingin dimigrasikan ke arsitektur produksi/cloud yang lebih besar secara terkendali.

## 4.1. Rencana Migrasi Data

Rencana perpindahan data dari sistem lama (manual/Excel/sistem legacy) menuju sistem baru (Makmur Jaya FastAPI).

1. **Pembersihan Data (Data Cleansing)**: Memastikan format nama obat, kategori, dosis, dan harga yang ada di sistem lama telah dirapikan ke dalam format `.csv` berstandar.
2. **Uji Migrasi Staging**: 
   Aplikasi FastAPI akan menggunakan endpoint yang telah dibuat (`/api/v1/upload/import-csv`) di lingkungan *staging*. Fitur `BackgroundTasks` asinkronus akan memasukkan puluhan ribu rekaman data (*records*) sambil menguji kecepatan *database insert* ke SQLite tanpa membuat UI macet.
3. **Migrasi Data Pengguna**: Akun pegawai lama akan dibuat melalui `seed_users.py` atau endpoint Registrasi agar *password* tersimpan dalam format hash `bcrypt`. Password lama yang berupa teks telanjang (plaintext) tidak boleh langsung di-import.
4. **Verifikasi Data**: Melakukan *fuzzy search* dan menelusuri katalog obat untuk memverifikasi apakah seluruh 2,000 produk obat telah terekam secara valid di database.

## 4.2. Cutover Plan (Transisi Sistem Baru)

Transisi saat sistem berjalan penuh ke sistem yang baru:

1. **Pengumuman Pengguna (H-3)**: Mengabarkan seluruh dokter, staf apotek, dan pelanggan bahwa Makmur Jaya E-Commerce akan melakukan pemeliharaan (downtime cutover) pada malam hari.
2. **Lockdown Sistem Lama (D-Day 23:00)**: Seluruh pencatatan manual dihentikan.
3. **Final Sinkronisasi Data (23:15)**: Import data stok terakhir (final batch) menggunakan fitur Parallel Import CSV di Dashboard Admin.
4. **Go-Live (23:45)**: Perubahan domain DNS diarahkan ke alamat IP server FastAPI produksi.
5. **Sanity Check (00:00)**: Melakukan transaksi palsu/dummy bernilai Rp10,- untuk mengecek proses verifikasi resep dan alur keranjang belanja (`checkout`) hingga `COMPLETED`. Sistem dinyatakan **LIVE**.

## 4.3. Rollback Plan (Rencana Darurat Penarikan Mundur)

Jika saat tahapan *Cutover* ditemukan *bug* kritikal, misalnya pesanan masuk ke database secara ganda (*race condition failure*) yang tidak teratasi dalam *Time Tolerance* (1 jam), maka *Rollback Plan* dilakukan:

1. **Isolasi Database**: Ekspor `makmurjaya.db` yang terinfeksi dan cabut koneksinya dari *Web Server*.
2. **Downgrade DNS**: Mengarahkan kembali DNS domain kembali ke sistem lama/halaman pengumuman *Maintenance*.
3. **Investigasi Log**: Memeriksa tabel `AuditLog` dan *log exception* Uvicorn untuk menganalisis sumber *crash* dari *Backend*.
4. **Reschedule (Penjadwalan Ulang)**: Evaluasi celah keamanan/eror yang terjadi, lalu menunda *Go-Live* pada akhir pekan berikutnya setelah modul tersebut diperbaiki dan lolos tahap pengujian (UAT).

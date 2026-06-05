# 2. Arsitektur Perangkat Keras & Analisis Skalabilitas
**Sistem E-Commerce Klinik Makmur Jaya**

Dokumen ini mendefinisikan topologi sistem (*deployment*) serta strategi penskalaan (*scalability*) seiring bertambahnya beban trafik pasien dan transaksi Klinik Makmur Jaya.

## 2.1. Arsitektur Deployment Saat Ini (Fase Awal)

Pada fase MVP (Minimum Viable Product), arsitektur dibuat berbentuk **Monolitik Tunggal** untuk menekan biaya operasional dan mempercepat *time-to-market*.

* **Framework Utama**: FastAPI (Python 3.10+)
* **Web Server**: Uvicorn (secara asinkronus dengan *workers*)
* **Database**: SQLite (Berkas lokal `makmurjaya.db`)
* **Penyimpanan Berkas**: Direktori lokal (`/static/uploads`)
* **Spesifikasi Server Minimal (VPS)**:
  * CPU: 2 vCPU
  * RAM: 2 GB
  * Storage: 40 GB SSD
  * OS: Ubuntu 22.04 / Debian 11

**Alur Arsitektur (Monolitik):**
`[Klien/Browser]` <--> `[Uvicorn Server + FastAPI App]` <--> `[SQLite Database & File System]`

*Pendekatan ini sangat cukup untuk menangani skala Klinik Makmur Jaya saat ini (150-200 pasien/hari) karena FastAPI memiliki performa I/O asinkronus tingkat tinggi.*

## 2.2. Rencana Skalabilitas (Fase Menengah & Enterprise)

Apabila skala pesanan melonjak drastis, arsitektur SQLite dan File Lokal akan menjadi *bottleneck*. Sistem telah didesain secara berlapis (*Layered Architecture*) agar mudah dinaikkan skalanya (Scale-Up maupun Scale-Out) tanpa merombak logika bisnis utama.

### Langkah Skalabilitas Vertikal (Scale-Up)
1. **Peningkatan Kapasitas Server**: Menambah RAM menjadi 8GB dan CPU menjadi 4/8 Core pada instansi VPS tunggal.
2. **Peningkatan Concurrency**: Mengubah konfigurasi `uvicorn` dengan meningkatkan jumlah *worker* (contoh: `--workers 4`).

### Langkah Skalabilitas Horizontal (Scale-Out)
Jika *Scale-Up* tidak lagi mencukupi, sistem akan dipisahkan menjadi komponen *microservices/distributed*:

1. **Migrasi Database (Penting)**:
   Mengganti koneksi URL SQLAlchemy dari SQLite menjadi **PostgreSQL**. Karena aplikasi sudah menggunakan ORM (SQLAlchemy), migrasi ini hanya mengubah *connection string* tanpa perlu merombak ratusan *query* SQL.
2. **State Server & Queue**:
   Menggunakan **Redis** sebagai penyimpanan sesi, *cache*, dan antrean *Background Tasks* (dapat dikombinasikan dengan Celery/BullMQ) agar *task* pembuatan PDF atau pengiriman email massal dikerjakan oleh *worker server* terpisah.
3. **Penyimpanan Berkas Terdistribusi (Object Storage)**:
   Pemindahan fungsi *upload* lokal (`/static/uploads`) ke layanan Object Storage S3-compatible (AWS S3, MinIO) untuk kemudahan akses dari *multiple app servers*.
4. **Load Balancer**:
   Memasang Nginx atau HAProxy di depan beberapa *node* FastAPI untuk mendistribusikan beban secara merata.

```mermaid
graph TD
    Client[Klien Web / Mobile] --> LB[Load Balancer / Nginx]
    LB --> App1[FastAPI Node 1]
    LB --> App2[FastAPI Node 2]
    LB --> App3[FastAPI Node 3]
    
    App1 --> DB[(PostgreSQL Master)]
    App2 --> DB
    App3 --> DB
    
    App1 --> Redis[(Redis Cache & Queue)]
    App2 --> Redis
    App3 --> Redis
    
    Redis --> Worker[Celery Worker Nodes]
    Worker --> Email[SMTP Service]
    
    App1 --> S3[S3 Object Storage (Uploads)]
    App2 --> S3
    App3 --> S3
```

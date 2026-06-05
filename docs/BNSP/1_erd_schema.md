# 1. Entity Relationship Diagram (ERD) & Skema Database
**Sistem E-Commerce Klinik Makmur Jaya**

Dokumen ini menjelaskan struktur entitas dan relasi basis data yang digunakan dalam Sistem Informasi Manajemen Apotek & E-Commerce Makmur Jaya.

## 1.1. Entity Relationship Diagram (ERD)

Berikut adalah pemetaan visual dari model data menggunakan notasi *Crow's Foot*.

```mermaid
erDiagram
    ROLE ||--o{ USER : "memiliki"
    USER ||--o{ CUSTOMER : "berperan sebagai"
    USER ||--o{ AUDIT_LOG : "melakukan"
    CUSTOMER ||--o{ ORDER : "membuat"
    CUSTOMER ||--o{ PRESCRIPTION : "mengunggah"
    
    CATEGORY ||--o{ MEDICINE : "mengelompokkan"
    SUPPLIER ||--o{ MEDICINE : "memasok"
    MEDICINE ||--o{ INVENTORY_BATCH : "memiliki stok di"
    MEDICINE ||--o{ ORDER_ITEM : "dipesan dalam"
    
    ORDER ||--o{ ORDER_ITEM : "terdiri atas"
    ORDER ||--o| PAYMENT : "dibayar melalui"

    USER {
        string id PK
        string email UK
        string hashed_password
        string name
        string role_id FK
    }
    ROLE {
        string id PK
        string name
    }
    CUSTOMER {
        string id PK
        string user_id FK
        string phone
        string address
    }
    CATEGORY {
        string id PK
        string name
    }
    SUPPLIER {
        string id PK
        string name
        string contact_info
    }
    MEDICINE {
        string id PK
        string name
        string slug UK
        float price
        text description
        text composition
        text dosage
        text side_effects
        string image_url
        string category_id FK
        string supplier_id FK
    }
    INVENTORY_BATCH {
        string id PK
        string medicine_id FK
        int quantity
        date expiry_date
        date received_date
    }
    ORDER {
        string id PK
        string customer_id FK
        float total_amount
        string status
        datetime created_at
    }
    ORDER_ITEM {
        string id PK
        string order_id FK
        string medicine_id FK
        int quantity
        float unit_price
    }
    PAYMENT {
        string id PK
        string order_id FK
        float amount
        string method
        string status
        string receipt_url
        string verified_by_id FK
        datetime created_at
    }
    PRESCRIPTION {
        string id PK
        string customer_id FK
        string doctor_name
        string file_url
        string status
        string notes
        string verified_by_id FK
        datetime created_at
    }
    AUDIT_LOG {
        string id PK
        string user_id FK
        string action
        string entity
        string entity_id
        text details
        string ip_address
        datetime created_at
    }
```

## 1.2. Penjelasan Skema Utama

1. **Modul Autentikasi (`USER`, `ROLE`)**: 
   Sistem Role-Based Access Control (RBAC). `Role` memisahkan akses untuk Admin, Apoteker, Kasir, dan Pelanggan. `User` menyimpan kredensial (ter-hash).
2. **Modul Inventaris (`MEDICINE`, `INVENTORY_BATCH`, `CATEGORY`, `SUPPLIER`)**: 
   Menerapkan sistem FIFO (First-In, First-Out). Satu obat (`MEDICINE`) dapat memiliki banyak tumpukan stok (`INVENTORY_BATCH`) dengan tanggal kedaluwarsa (`expiry_date`) yang berbeda-beda.
3. **Modul Transaksi (`ORDER`, `ORDER_ITEM`, `PAYMENT`)**: 
   Keranjang belanja diproses menjadi `ORDER`. Bukti bayar akan disimpan referensinya di `PAYMENT.receipt_url` dan diverifikasi oleh admin.
4. **Modul Rekam Medis & Audit (`PRESCRIPTION`, `AUDIT_LOG`)**: 
   Resep fisik/digital yang diunggah pelanggan disimpan di `PRESCRIPTION`. Seluruh aktivitas krusial pengguna terekam secara persisten di `AUDIT_LOG`.

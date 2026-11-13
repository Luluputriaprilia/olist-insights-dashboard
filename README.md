# 🛒 Proyek Analisis Data: E-Commerce Public Dataset Olist

## Deskripsi Proyek
Proyek ini bertujuan untuk menganalisis data transaksi E-Commerce Public Dataset dari Olist, sebuah platform e-commerce di Brasil. Analisis dilakukan untuk memahami karakteristik pelanggan melalui segmentasi RFM (Recency, Frequency, Monetary), mengevaluasi hubungan ketepatan waktu pengiriman dengan kepuasan pelanggan, serta mengidentifikasi tren penjualan berdasarkan periode waktu.

Hasil analisis digunakan untuk memperoleh insight bisnis dan memberikan rekomendasi strategis dalam meningkatkan loyalitas pelanggan, kualitas layanan pengiriman, serta performa penjualan.

## Pertanyaan Bisnis
1. Bagaimana segmentasi pelanggan berdasarkan Recency, Frequency, dan Monetary (RFM) menggunakan seluruh periode transaksi yang tersedia pada dataset (September 2016 – Oktober 2018), dan segmen mana yang menyumbang revenue terbesar?

2. Bagaimana perbandingan rata-rata skor ulasan pelanggan antara pesanan yang diterima tepat waktu dan pesanan yang mengalami keterlambatan pengiriman selama periode Januari 2017 – Oktober 2018, dan seberapa besar selisih kepuasan di antara keduanya?

## Struktur Direktori
- `dashboard/`: Berisi aplikasi dashboard Streamlit.
- `data/`: Berisi dataset CSV yang digunakan dalam proses analisis.
- `notebook.ipynb`: Berisi proses pengumpulan data, data wrangling, exploratory data analysis (EDA), visualisasi, dan kesimpulan.
- `requirements.txt`: Berisi daftar library Python yang dibutuhkan untuk menjalankan proyek.
- `README.md`: Dokumentasi proyek dan panduan penggunaan.
- `url.txt`: Berisi tautan dashboard yang telah dipublikasikan (jika melakukan deployment).

## Instalasi dan Persiapan Environment

### 1. Menggunakan Anacond
Buat environment Python baru:

```bash
conda create --name olist-analysis python=3.11
```

Aktifkan environment:

```bash
conda activate olist-analysis
```

Masuk ke direktori utama proyek, kemudian instal seluruh library:

```bash
pip install -r requirements.txt
```

### 2. Menjalankan Dashboard
Pastikan terminal berada di direktori utama proyek, kemudian jalankan:

```bash
streamlit run dashboard/dashboard.py
```

Dashboard akan terbuka melalui browser. Jika tidak terbuka secara otomatis, akses alamat berikut:

```text
http://localhost:8501
```

## Menjalankan Notebook
Buka file `notebook.ipynb` menggunakan Jupyter Notebook, JupyterLab, atau Google Colab untuk melihat keseluruhan proses analisis data, mulai dari pengumpulan data, data wrangling, EDA, visualisasi, hingga kesimpulan dan rekomendasi bisnis.

Pastikan dataset yang digunakan tersedia pada folder `data/`.

## Hasil Analisis
Analisis dilakukan melalui beberapa tahapan utama:

1. Data Wrangling: Mengumpulkan, menilai kualitas, dan membersihkan data sebelum digunakan dalam proses analisis.
2. Exploratory Data Analysis (EDA): Memahami karakteristik dataset melalui statistik deskriptif, distribusi data, dan eksplorasi variabel.
3. RFM Analysis: Mengelompokkan pelanggan berdasarkan Recency, Frequency, dan Monetary untuk mengidentifikasi segmen pelanggan serta kontribusi revenue.
4. Delivery Performance Analysis: Membandingkan rata-rata skor ulasan antara pesanan yang diterima tepat waktu dan pesanan yang terlambat.
5. Data Visualization: Menyajikan hasil analisis melalui visualisasi agar pola dan insight lebih mudah dipahami.

## Ringkasan Insight Bisnis
Berdasarkan hasil analisis, diperoleh beberapa insight utama:
1. Segmentasi Pelanggan (RFM):Segmen At Risk / Churn menyumbang sekitar 85,07% revenue. Hal ini menunjukkan pentingnya strategi mempertahankan pelanggan dan mendorong pembelian ulang. Segmen Loyal Customer juga perlu dipertahankan melalui program loyalitas.

2. Ketepatan Pengiriman dan Kepuasan Pelanggan: Pesanan yang diterima tepat waktu memiliki rata-rata skor ulasan sebesar 4,30/5, sedangkan pesanan yang terlambat memiliki rata-rata skor sebesar 2,57/5. Terdapat selisih sebesar 1,73 poin yang menunjukkan adanya hubungan antara ketepatan pengiriman dan kepuasan pelanggan.

3. Tren Penjualan: Penjualan mencapai puncaknya pada November 2017 dengan 7.544 pesanan dan total nilai transaksi sekitar R$1,19 juta. Kondisi ini dapat menjadi pertimbangan dalam perencanaan strategi penjualan pada periode promosi berikutnya.

## Dashboard
Dashboard interaktif dikembangkan menggunakan Streamlit dan Plotly untuk menyajikan hasil analisis dalam tiga bagian utama:

- Segmentasi Pelanggan (RFM).
- Ketepatan Pengiriman dan Kepuasan Pelanggan.
- Tren Penjualan Bulanan.

Dashboard dirancang agar pengguna dapat mengeksplorasi hasil analisis secara lebih interaktif dan memperoleh gambaran mengenai performa bisnis E-Commerce Olist.
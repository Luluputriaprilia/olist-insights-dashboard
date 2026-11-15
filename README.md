# 🛒 Proyek Analisis Data: E-Commerce Public Dataset Olist

## Deskripsi Proyek

Proyek ini bertujuan untuk menganalisis E-Commerce Public Dataset dari Olist, sebuah platform e-commerce di Brasil. Analisis dilakukan untuk memahami tren transaksi bulanan, mengevaluasi hubungan ketepatan waktu pengiriman dengan kepuasan pelanggan, serta melakukan segmentasi pelanggan menggunakan metode Recency, Frequency, dan Monetary (RFM).

Analisis menggunakan data transaksi berstatus *delivered* dengan periode yang disesuaikan pada masing-masing pertanyaan bisnis. Hasil analisis digunakan untuk memperoleh insight bisnis dan menyusun rekomendasi strategis terkait optimalisasi penjualan, peningkatan kualitas layanan pengiriman, serta strategi retensi pelanggan.

## Pertanyaan Bisnis

1. Bagaimana perkembangan jumlah pesanan berstatus *delivered* dan total nilai pembayaran setiap bulan selama September 2017 hingga Agustus 2018, serta pada bulan apa jumlah pesanan dan nilai pembayaran mencapai nilai tertinggi, sebagai dasar perencanaan strategi promosi dan pengelolaan kapasitas operasional?

2. Bagaimana perbandingan rata-rata skor ulasan pelanggan (skala 1–5) antara pesanan yang diterima tepat waktu dan pesanan yang mengalami keterlambatan selama Januari 2017 hingga Agustus 2018, serta berapa selisih rata-rata skor kedua kelompok tersebut sebagai dasar evaluasi dan penentuan prioritas perbaikan kinerja pengiriman?

3. Bagaimana distribusi jumlah pelanggan, rata-rata Recency, Frequency, dan Monetary, serta kontribusi nilai pembayaran dari setiap segmen pelanggan berdasarkan transaksi berstatus *delivered* selama September 2016 hingga Agustus 2018, sebagai dasar penentuan prioritas strategi retensi dan peningkatan pembelian ulang?

## Struktur Direktori

- `dashboard/`: Berisi aplikasi dashboard Streamlit.
- `data/`: Berisi dataset CSV yang digunakan dalam proses analisis.
- `notebook.ipynb`: Berisi proses pengumpulan data, data wrangling, exploratory data analysis (EDA), visualisasi, kesimpulan, dan rekomendasi bisnis.
- `requirements.txt`: Berisi daftar library Python yang dibutuhkan untuk menjalankan proyek.
- `README.md`: Dokumentasi proyek dan panduan penggunaan.
- `url.txt`: Berisi tautan dashboard yang telah dipublikasikan, jika melakukan deployment.

## Instalasi dan Persiapan Environment

### 1. Menggunakan Anaconda

Buat environment Python baru:

```bash
conda create --name olist-analysis python=3.11
```

Aktifkan environment:

```bash
conda activate olist-analysis
```

Pastikan terminal berada di direktori utama proyek, kemudian instal seluruh library yang dibutuhkan:

```bash
pip install -r requirements.txt
```

### 2. Menjalankan Dashboard

Pastikan dataset CSV yang dibutuhkan telah tersedia pada folder `data/` atau direktori yang telah ditentukan pada kode dashboard.

Masuk ke direktori utama proyek, kemudian jalankan perintah berikut:

```bash
streamlit run dashboard/dashboard.py
```

Dashboard akan terbuka melalui browser. Jika tidak terbuka secara otomatis, akses alamat berikut:

```text
http://localhost:8501
```

## Menjalankan Notebook

Buka file `notebook.ipynb` menggunakan Jupyter Notebook, JupyterLab, atau Google Colab untuk melihat keseluruhan proses analisis data.

Tahapan analisis meliputi:

- Pengumpulan dan pemuatan dataset.
- Data wrangling, termasuk penilaian kualitas dan pembersihan data.
- Exploratory Data Analysis (EDA).
- Analisis tren transaksi bulanan.
- Analisis ketepatan waktu pengiriman dan skor ulasan pelanggan.
- Segmentasi pelanggan menggunakan metode RFM.
- Visualisasi data.
- Kesimpulan dan rekomendasi bisnis.

Pastikan seluruh dataset yang digunakan tersedia pada folder `data/` dan sesuaikan path pemuatan data apabila diperlukan.

## Hasil Analisis

Analisis dilakukan melalui beberapa tahapan utama:

1. **Data Wrangling**  
   Mengumpulkan, memeriksa, dan membersihkan dataset. Tahapan ini mencakup pemeriksaan missing values, duplicate data, tipe data, serta invalid values pada beberapa atribut.

2. **Exploratory Data Analysis (EDA)**  
   Memahami karakteristik data melalui statistik deskriptif, distribusi data, serta eksplorasi hubungan antarvariabel untuk mendukung pertanyaan bisnis.

3. **Monthly Transaction Analysis**  
   Menganalisis perkembangan jumlah pesanan berstatus *delivered* dan total nilai pembayaran setiap bulan selama September 2017 hingga Agustus 2018.

4. **Delivery Performance Analysis**  
   Membandingkan rata-rata skor ulasan pelanggan antara pesanan yang diterima tepat waktu dan pesanan yang mengalami keterlambatan selama Januari 2017 hingga Agustus 2018.

5. **RFM Analysis**  
   Melakukan segmentasi pelanggan berdasarkan Recency, Frequency, dan Monetary dari transaksi berstatus *delivered* selama September 2016 hingga Agustus 2018.

6. **Data Visualization**  
   Menyajikan hasil analisis melalui visualisasi agar pola transaksi, perbedaan kepuasan pelanggan, serta karakteristik segmen pelanggan lebih mudah dipahami.

## Ringkasan Insight Bisnis

Berdasarkan hasil analisis pada notebook, diperoleh beberapa insight utama:

1. **Tren Transaksi Bulanan**  
   Aktivitas transaksi tertinggi terjadi pada November 2017 dengan jumlah pesanan sebanyak **7.289 pesanan** dan total nilai pembayaran sebesar **R$1.153.528,05**. Periode tersebut dapat menjadi pertimbangan dalam perencanaan strategi promosi, persiapan stok, serta pengelolaan kapasitas operasional.

2. **Ketepatan Pengiriman dan Kepuasan Pelanggan**  
   Pesanan yang diterima tepat waktu memiliki rata-rata skor ulasan sebesar **4,30/5**, sedangkan pesanan yang mengalami keterlambatan memiliki rata-rata skor sebesar **2,57/5**. Selisih sebesar **1,73 poin** menunjukkan bahwa pesanan yang diterima tepat waktu cenderung memperoleh penilaian pelanggan yang lebih tinggi. Oleh karena itu, ketepatan pengiriman perlu menjadi salah satu prioritas dalam peningkatan kualitas layanan.

3. **Segmentasi Pelanggan Berdasarkan RFM**  
   Hasil segmentasi RFM terhadap **93.357 pelanggan** menunjukkan bahwa pelanggan terbagi menjadi empat segmen, yaitu Champions, Loyal Customers, Potential Customers, dan Need Attention.

   - **Potential Customers** merupakan segmen terbesar dengan 44.145 pelanggan (47,29%) dan memberikan kontribusi pembayaran terbesar, yaitu **54,48%**. Segmen ini memiliki rata-rata Recency 193,70 hari, Frequency 1,03 transaksi, dan Monetary R$190,34.
   - **Need Attention** terdiri dari 37.124 pelanggan (39,77%) dengan kontribusi pembayaran 17,80%. Segmen ini memiliki rata-rata Recency 341,57 hari, Frequency 1,00 transaksi, dan Monetary R$73,95.
   - **Loyal Customers** berjumlah 12.020 pelanggan (12,88%) dengan kontribusi pembayaran 27,40%. Rata-rata Recency sebesar 81,29 hari, Frequency 1,12 transaksi, dan Monetary R$351,61.
   - **Champions** merupakan segmen terkecil dengan 68 pelanggan (0,07%) dan kontribusi pembayaran 0,31%. Segmen ini memiliki rata-rata Frequency tertinggi sebesar 4,15 transaksi dan Monetary tertinggi sebesar R$708,16, serta rata-rata Recency sebesar 72,26 hari.

   Temuan tersebut menunjukkan bahwa Potential Customers memiliki kontribusi pembayaran terbesar, sedangkan Champions memiliki karakteristik pembelian paling aktif dan nilai transaksi rata-rata tertinggi.

## Rekomendasi Bisnis

Berdasarkan hasil analisis, beberapa rekomendasi yang dapat diterapkan adalah:

1. **Optimalisasi Strategi Penjualan**  
   Memanfaatkan periode transaksi tertinggi, khususnya November 2017, sebagai acuan perencanaan promosi, persiapan stok, dan kapasitas operasional. Selain itu, melakukan monitoring tren transaksi bulanan untuk mengantisipasi penurunan aktivitas penjualan.

2. **Peningkatan Kualitas Pengiriman**  
   Melakukan evaluasi terhadap mitra logistik, meningkatkan komunikasi status pesanan kepada pelanggan, serta memantau ketepatan waktu pengiriman secara berkala untuk meningkatkan kepuasan pelanggan.

3. **Pengembangan Strategi Retensi Pelanggan**
   - **Potential Customers:** Mendorong pembelian ulang melalui voucher, promosi personal, dan rekomendasi produk relevan.
   - **Need Attention:** Melakukan reaktivasi pelanggan melalui penawaran khusus, diskon, atau pengingat promosi.
   - **Loyal Customers:** Mempertahankan loyalitas melalui program reward dan penawaran eksklusif.
   - **Champions:** Memberikan apresiasi melalui program loyalitas eksklusif dan keuntungan tambahan.

4. **Monitoring dan Evaluasi**  
   Melakukan evaluasi secara berkala terhadap jumlah pesanan, nilai pembayaran, ketepatan pengiriman, skor ulasan, serta perubahan segmentasi RFM untuk mengukur efektivitas strategi bisnis.

## Dashboard

Dashboard interaktif dikembangkan menggunakan Streamlit dan Plotly untuk menyajikan hasil analisis dalam tiga bagian utama:

- Tren Transaksi Bulanan: Menampilkan perkembangan jumlah pesanan dan total nilai pembayaran setiap bulan serta periode dengan aktivitas transaksi tertinggi.
- Ketepatan Pengiriman dan Kepuasan Pelanggan: Menampilkan perbandingan rata-rata skor ulasan antara pesanan tepat waktu dan pesanan terlambat.
- Segmentasi Pelanggan (RFM): Menampilkan distribusi pelanggan, karakteristik Recency, Frequency, Monetary, serta kontribusi pembayaran dari setiap segmen pelanggan.

Dashboard dirancang agar pengguna dapat mengeksplorasi hasil analisis secara interaktif dan memperoleh gambaran mengenai performa bisnis E-Commerce Olist.
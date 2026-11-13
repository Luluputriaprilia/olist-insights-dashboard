# ============================================================
# OLIST E-COMMERCE DASHBOARD
# Analisis: RFM, Ketepatan Pengiriman & Kepuasan, Tren Penjualan
# Dataset: main_data.csv dan reviews_data.csv
# ============================================================

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------
# 1. KONFIGURASI HALAMAN
# ------------------------------------------------------------
st.set_page_config(
    page_title="Olist E-Commerce Dashboard",
    page_icon="🛍️",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR_CANDIDATES = [
    BASE_DIR,
    BASE_DIR / "data",
    BASE_DIR.parent,
    BASE_DIR.parent / "data",
]

SEGMENT_ORDER = [
    "Others",
    "New / Recent Customer",
    "Lost / Churn",
    "Champions",
    "At Risk",
    "Loyal Customers",
]

SEGMENT_COLORS = {
    "Others": "#493878",
    "New / Recent Customer": "#49678F",
    "Lost / Churn": "#3B8790",
    "Champions": "#329B83",
    "At Risk": "#80B84A",
    "Loyal Customers": "#A7C957",
}

DELIVERY_COLORS = {
    "Tepat Waktu": "#72B7B2",
    "Terlambat": "#F28E6B",
}

# ------------------------------------------------------------
# 2. MEMUAT DATA
# ------------------------------------------------------------
def find_csv(filename):
    """Mencari file CSV di folder aplikasi atau folder data."""
    for folder in DATA_DIR_CANDIDATES:
        path = folder / filename
        if path.exists():
            return path

    checked = "\n".join(str(folder / filename) for folder in DATA_DIR_CANDIDATES)
    raise FileNotFoundError(
        f"File {filename} tidak ditemukan.\n"
        f"Lokasi yang diperiksa:\n{checked}"
    )

@st.cache_data
def load_data():
    main = pd.read_csv(find_csv("main_data.csv"), low_memory=False)
    reviews = pd.read_csv(find_csv("reviews_data.csv"), low_memory=False)

    required_main = [
        "order_id",
        "customer_unique_id",
        "order_purchase_timestamp",
        "payment_value",
    ]
    required_reviews = [
        "order_id",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "review_score",
    ]

    missing_main = [c for c in required_main if c not in main.columns]
    missing_reviews = [c for c in required_reviews if c not in reviews.columns]

    if missing_main:
        raise ValueError(
            "Kolom berikut tidak ditemukan di main_data.csv: "
            + ", ".join(missing_main)
        )
    if missing_reviews:
        raise ValueError(
            "Kolom berikut tidak ditemukan di reviews_data.csv: "
            + ", ".join(missing_reviews)
        )

    main["order_purchase_timestamp"] = pd.to_datetime(
        main["order_purchase_timestamp"], errors="coerce"
    )
    main["payment_value"] = pd.to_numeric(
        main["payment_value"], errors="coerce"
    )

    for col in [
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]:
        reviews[col] = pd.to_datetime(reviews[col], errors="coerce")

    reviews["review_score"] = pd.to_numeric(
        reviews["review_score"], errors="coerce"
    )

    return main, reviews

# ------------------------------------------------------------
# 3. PENGOLAHAN RFM
#    Aturan scoring mengikuti notebook Google Colab:
#    R = qcut Recency, label 5 sampai 1
#    F = 1 transaksi -> 1, 2 transaksi -> 4, >=3 -> 5
#    M = qcut Monetary, label 1 sampai 5
# ------------------------------------------------------------
@st.cache_data
def prepare_rfm(main_data):
    data = main_data.dropna(
        subset=[
            "order_id",
            "customer_unique_id",
            "order_purchase_timestamp",
            "payment_value",
        ]
    ).copy()

    if data.empty:
        return pd.DataFrame(), pd.DataFrame()

    customer = (
        data.groupby("customer_unique_id")
        .agg(
            last_purchase=("order_purchase_timestamp", "max"),
            Frequency=("order_id", "nunique"),
            Monetary=("payment_value", "sum"),
        )
        .reset_index()
    )

    snapshot_date = (
        data["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    )
    customer["Recency"] = (
        snapshot_date - customer["last_purchase"]
    ).dt.days

    # Scoring R: semakin kecil Recency, semakin tinggi skor.
    customer["R_Score"] = pd.qcut(
        customer["Recency"],
        q=5,
        labels=[5, 4, 3, 2, 1],
    ).astype(int)

    # Scoring F sesuai aturan bisnis pada notebook.
    def freq_score(frequency):
        if frequency >= 3:
            return 5
        elif frequency == 2:
            return 4
        return 1

    customer["F_Score"] = customer["Frequency"].apply(freq_score)

    # Scoring M mengikuti notebook: qcut pada rank Monetary.
    customer["M_Score"] = pd.qcut(
        customer["Monetary"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    customer["RFM_Score"] = (
        customer["R_Score"].astype(str)
        + customer["F_Score"].astype(str)
        + customer["M_Score"].astype(str)
    )

    # Segmentasi persis mengikuti fungsi rfm_segment di notebook.
    def rfm_segment(row):
        r = row["R_Score"]
        f = row["F_Score"]
        m = row["M_Score"]

        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        elif r >= 3 and f >= 4:
            return "Loyal Customers"
        elif r >= 4 and f == 1:
            return "New / Recent Customer"
        elif r <= 2 and f >= 4:
            return "At Risk"
        elif r <= 2 and f == 1 and m <= 2:
            return "Lost / Churn"
        return "Others"

    customer["Segment"] = customer.apply(rfm_segment, axis=1)

    summary = (
        customer.groupby("Segment", observed=False)
        .agg(
            Total_Revenue=("Monetary", "sum"),
            Jumlah_Pelanggan=("customer_unique_id", "count"),
            Avg_Recency=("Recency", "mean"),
            Avg_Frequency=("Frequency", "mean"),
            Avg_Monetary=("Monetary", "mean"),
        )
        .reset_index()
    )

    total_revenue = summary["Total_Revenue"].sum()
    summary["Revenue (%)"] = (
        summary["Total_Revenue"] / total_revenue * 100
        if total_revenue
        else 0
    )

    summary["Segment"] = pd.Categorical(
        summary["Segment"],
        categories=SEGMENT_ORDER,
        ordered=True,
    )
    summary = (
        summary.sort_values("Segment")
        .dropna(subset=["Segment"])
        .reset_index(drop=True)
    )

    return customer, summary

# ------------------------------------------------------------
# 4. PENGOLAHAN PENGIRIMAN DAN ULASAN
#    Periode Januari 2017 sampai Oktober 2018.
# ------------------------------------------------------------
@st.cache_data
def prepare_delivery(reviews_data):
    valid = reviews_data.dropna(
        subset=[
            "order_id",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
            "review_score",
        ]
    ).copy()

    if "order_purchase_timestamp" in valid.columns:
        valid["order_purchase_timestamp"] = pd.to_datetime(
            valid["order_purchase_timestamp"], errors="coerce"
        )
        valid = valid[
            (valid["order_purchase_timestamp"] >= pd.Timestamp("2017-01-01"))
            & (valid["order_purchase_timestamp"] < pd.Timestamp("2018-11-01"))
        ]

    if valid.empty:
        return pd.DataFrame()

    valid["delivery_status"] = (
        valid["order_delivered_customer_date"]
        <= valid["order_estimated_delivery_date"]
    ).map({True: "Tepat Waktu", False: "Terlambat"})

    # Satu baris per pesanan agar tidak terhitung berulang.
    return (
        valid.groupby("order_id", as_index=False)
        .agg(
            delivery_status=("delivery_status", "first"),
            review_score=("review_score", "mean"),
        )
    )

# ------------------------------------------------------------
# 5. PENGOLAHAN TREN PENJUALAN BULANAN
# ------------------------------------------------------------
@st.cache_data
def prepare_monthly_sales(main_data):
    valid = main_data.dropna(
        subset=[
            "order_id",
            "order_purchase_timestamp",
            "payment_value",
        ]
    ).copy()

    if valid.empty:
        return pd.DataFrame()

    valid["month"] = (
        valid["order_purchase_timestamp"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    # Satu tanggal dan satu nilai per order untuk menghindari
    # penghitungan jumlah order berulang.
    order_level = (
        valid.groupby(["order_id", "month"], as_index=False)
        .agg(payment_value=("payment_value", "sum"))
    )

    monthly = (
        order_level.groupby("month", as_index=False)
        .agg(
            total_orders=("order_id", "nunique"),
            total_revenue=("payment_value", "sum"),
        )
        .sort_values("month")
    )
    return monthly

# ------------------------------------------------------------
# 6. GRAFIK INTERAKTIF: KLIK GRAFIK UNTUK PENJELASAN
# ------------------------------------------------------------
def show_chart_with_explanation(fig, key, descriptions):
    event = st.plotly_chart(
        fig,
        use_container_width=True,
        key=key,
        on_select="rerun",
        selection_mode="points",
        config={"displayModeBar": True},
    )

    st.caption(
        "👆 Klik salah satu batang atau titik pada grafik untuk melihat penjelasannya."
    )

    selected_label = None

    try:
        points = event.selection.points
        if points:
            point = points[0]

            # customdata dipakai agar kategori/tanggal dapat dikenali konsisten.
            custom = point.get("customdata")
            if custom is not None:
                if isinstance(custom, (list, tuple)):
                    selected_label = custom[0]
                else:
                    selected_label = custom

            if selected_label is None:
                selected_label = point.get("label")

            if selected_label is None:
                x_value = point.get("x")
                y_value = point.get("y")

                if isinstance(x_value, str):
                    selected_label = x_value
                elif isinstance(y_value, str):
                    selected_label = y_value
                elif x_value is not None:
                    selected_label = x_value
    except Exception:
        selected_label = None

    if selected_label is not None:
        label = str(selected_label)

        explanation = descriptions.get(label)

        if explanation is None:
            # Menangani tanggal yang dikirim Plotly dalam format ISO.
            for category, description in descriptions.items():
                if label.startswith(str(category)):
                    explanation = description
                    break

        st.markdown("**💡 Penjelasan Grafik**")
        if explanation:
            st.info(explanation)
        else:
            st.info(f"Kategori yang dipilih: **{label}**.")
    else:
        st.caption("Penjelasan akan muncul di sini setelah bagian grafik diklik.")

# ------------------------------------------------------------
# 7. STYLE DASHBOARD
# ------------------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
            padding-left: 2.5rem;
            padding-right: 2.5rem;
            max-width: 1600px;
        }
        div[data-testid="stMetric"] {
            background: rgba(128, 128, 128, 0.07);
            border: 1px solid rgba(128, 128, 128, 0.16);
            padding: 13px 15px;
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛍️ Olist E-Commerce Dashboard")
st.write(
    "Dashboard analisis Brazilian E-Commerce Public Dataset by Olist "
    "untuk memahami segmentasi pelanggan, ketepatan pengiriman, "
    "kepuasan pelanggan, dan tren penjualan."
)

# ------------------------------------------------------------
# 8. LOAD DAN VALIDASI DATA
# ------------------------------------------------------------
try:
    with st.spinner("Memuat dan memproses data dashboard..."):
        main_data, reviews_data = load_data()
        rfm_customers, rfm_summary = prepare_rfm(main_data)
        delivery_data = prepare_delivery(reviews_data)
        monthly_data = prepare_monthly_sales(main_data)

except (FileNotFoundError, ValueError, KeyError) as error:
    st.error(str(error))
    st.info(
        "Pastikan struktur file di GitHub seperti berikut:\n\n"
        "submission/\n"
        "├── main_data.csv\n"
        "├── reviews_data.csv\n"
        "└── dashboard/\n"
        "    └── dashboard.py\n\n"
        "Jika CSV berada di folder data/, kode juga akan mencarinya di sana."
    )
    st.stop()

except Exception as error:
    st.error(f"Terjadi kesalahan saat memproses data: {error}")
    st.exception(error)
    st.stop()

if rfm_customers.empty or rfm_summary.empty:
    st.error(
        "Data RFM kosong. Periksa nilai order_id, customer_unique_id, "
        "order_purchase_timestamp, dan payment_value."
    )
    st.stop()

# ------------------------------------------------------------
# 9. FILTER TANGGAL UNTUK TREN PENJUALAN
# ------------------------------------------------------------
st.sidebar.header("Filter Dashboard")

if not monthly_data.empty:
    min_date = monthly_data["month"].min().date()
    max_date = monthly_data["month"].max().date()

    selected_period = st.sidebar.date_input(
        "Pilih Rentang Tanggal Penjualan",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="DD/MM/YYYY",
    )

    if isinstance(selected_period, (tuple, list)) and len(selected_period) == 2:
        start_date, end_date = selected_period
    else:
        start_date = end_date = selected_period
else:
    start_date = end_date = None

# ============================================================
# BAGIAN 1 - ANALISIS RFM
# ============================================================
st.header("1. Analisis Karakteristik dan Segmentasi Pelanggan (RFM)")
st.caption(
    "Segmentasi pelanggan berdasarkan Recency, Frequency, dan Monetary "
    "menggunakan seluruh periode transaksi yang tersedia "
    "(September 2016–Oktober 2018)."
)

total_customers = rfm_customers["customer_unique_id"].nunique()
total_revenue = rfm_customers["Monetary"].sum()

rfm_kpi1, rfm_kpi2, rfm_kpi3 = st.columns(3)
rfm_kpi1.metric("Total Pelanggan", f"{total_customers:,.0f}")
rfm_kpi2.metric("Total Revenue", f"R$ {total_revenue:,.2f}")
rfm_kpi3.metric(
    "Rata-rata Frequency",
    f"{rfm_customers['Frequency'].mean():.2f} transaksi",
)

st.subheader("Total Revenue per Segmen Pelanggan (RFM Scoring 1–5)")

fig_rfm = px.bar(
    rfm_summary,
    x="Segment",
    y="Total_Revenue",
    color="Segment",
    color_discrete_map=SEGMENT_COLORS,
    category_orders={"Segment": SEGMENT_ORDER},
    custom_data=["Segment"],
    labels={
        "Segment": "Segmen Pelanggan",
        "Total_Revenue": "Total Revenue (R$)",
    },
)

fig_rfm.update_traces(
    text=rfm_summary["Total_Revenue"].apply(
        lambda value: f"R$ {value / 1_000_000:.2f} Juta"
        if value >= 1_000_000
        else f"R$ {value:,.0f}"
    ),
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Total Revenue: R$ %{y:,.2f}<extra></extra>"
    ),
)

fig_rfm.update_layout(
    height=520,
    showlegend=False,
    xaxis_title="Segmen Pelanggan",
    yaxis_title="Total Revenue (R$)",
    margin=dict(t=45, b=100, l=60, r=35),
)

rfm_explanations = {}
for _, row in rfm_summary.iterrows():
    segment = str(row["Segment"])
    rfm_explanations[segment] = (
        f"Segmen **{segment}** menghasilkan revenue sebesar "
        f"**R$ {row['Total_Revenue']:,.2f}**, berasal dari "
        f"**{row['Jumlah_Pelanggan']:,.0f} pelanggan** "
        f"atau **{row['Revenue (%)']:.2f}%** dari total revenue. "
        f"Rata-rata Recency segmen ini adalah **{row['Avg_Recency']:.1f} hari**, "
        f"Frequency **{row['Avg_Frequency']:.2f} transaksi**, dan "
        f"Monetary **R$ {row['Avg_Monetary']:,.2f}**."
    )

show_chart_with_explanation(
    fig_rfm,
    "rfm_revenue_chart",
    rfm_explanations,
)

st.subheader("Tabel Ringkasan Segmentasi RFM")

display_rfm = rfm_summary.copy()
display_rfm["Segment"] = display_rfm["Segment"].astype(str)
st.dataframe(
    display_rfm.style.format(
        {
            "Total_Revenue": "R$ {:,.2f}",
            "Jumlah_Pelanggan": "{:,.0f}",
            "Avg_Recency": "{:.2f}",
            "Avg_Frequency": "{:.2f}",
            "Avg_Monetary": "R$ {:,.2f}",
            "Revenue (%)": "{:.2f}%",
        }
    ),
    use_container_width=True,
    hide_index=True,
)

if not rfm_summary.empty:
    best_segment = rfm_summary.sort_values(
        "Total_Revenue", ascending=False
    ).iloc[0]

    st.info(
        f"**Insight Pertanyaan 1:** Segmen **{best_segment['Segment']}** "
        f"memberikan kontribusi revenue terbesar, yaitu "
        f"**{best_segment['Revenue (%)']:.2f}%** "
        f"(R$ {best_segment['Total_Revenue']:,.2f}). "
        "Berdasarkan hasil notebook, Others dan New / Recent Customer "
        "merupakan dua segmen dengan kontribusi revenue terbesar. "
        "Perusahaan dapat mendorong pembelian berulang pada pelanggan baru "
        "serta melakukan profiling lebih lanjut pada segmen Others."
    )

st.divider()

# ============================================================
# BAGIAN 2 - PENGIRIMAN DAN KEPUASAN PELANGGAN
# ============================================================
st.header("2. Analisis Ketepatan Pengiriman dan Kepuasan Pelanggan")
st.caption(
    "Perbandingan rata-rata skor ulasan pelanggan antara pesanan tepat waktu "
    "dan terlambat selama Januari 2017–Oktober 2018."
)

if delivery_data.empty:
    st.warning(
        "Tidak tersedia data pengiriman lengkap dengan skor ulasan "
        "pada periode analisis."
    )
else:
    delivery_summary = (
        delivery_data.groupby("delivery_status", as_index=False)
        .agg(
            avg_review_score=("review_score", "mean"),
            total_orders=("order_id", "nunique"),
        )
    )

    def delivery_value(status, column):
        result = delivery_summary[
            delivery_summary["delivery_status"] == status
        ]
        return float(result[column].iloc[0]) if not result.empty else 0.0

    on_time_score = delivery_value("Tepat Waktu", "avg_review_score")
    late_score = delivery_value("Terlambat", "avg_review_score")
    on_time_count = delivery_value("Tepat Waktu", "total_orders")
    late_count = delivery_value("Terlambat", "total_orders")
    score_difference = abs(on_time_score - late_score)

    d1, d2, d3 = st.columns(3)
    d1.metric("Skor Tepat Waktu", f"{on_time_score:.2f} / 5")
    d2.metric("Skor Terlambat", f"{late_score:.2f} / 5")
    d3.metric("Selisih Skor", f"{score_difference:.2f} poin")

    # Grafik 1: rata-rata skor ulasan.
    review_chart_data = pd.DataFrame(
        {
            "Status Pengiriman": ["Tepat Waktu", "Terlambat"],
            "Rata-rata Skor Ulasan": [on_time_score, late_score],
        }
    )

    # Grafik 2: jumlah pesanan.
    order_chart_data = pd.DataFrame(
        {
            "Status Pengiriman": ["Tepat Waktu", "Terlambat"],
            "Jumlah Pesanan": [on_time_count, late_count],
        }
    )

    delivery_left, delivery_right = st.columns(2)

    with delivery_left:
        st.subheader("Perbandingan Rata-rata Skor Ulasan")

        fig_review = px.bar(
            review_chart_data,
            x="Status Pengiriman",
            y="Rata-rata Skor Ulasan",
            color="Status Pengiriman",
            color_discrete_map=DELIVERY_COLORS,
            custom_data=["Status Pengiriman"],
            text="Rata-rata Skor Ulasan",
            labels={
                "Status Pengiriman": "Status Pengiriman",
                "Rata-rata Skor Ulasan": "Rata-rata Skor (1–5)",
            },
        )
        fig_review.update_traces(
            texttemplate="%{y:.2f}",
            textposition="outside",
            cliponaxis=False,
        )
        fig_review.update_yaxes(range=[0, 5])
        fig_review.update_layout(
            height=410,
            showlegend=False,
            margin=dict(t=35, b=55),
        )

        review_explanations = {
            "Tepat Waktu": (
                f"Pesanan yang diterima **tepat waktu** memiliki rata-rata "
                f"skor ulasan **{on_time_score:.2f} dari 5**, "
                f"dengan jumlah **{on_time_count:,.0f} pesanan**."
            ),
            "Terlambat": (
                f"Pesanan yang diterima **terlambat** memiliki rata-rata "
                f"skor ulasan **{late_score:.2f} dari 5**, "
                f"dengan jumlah **{late_count:,.0f} pesanan**."
            ),
        }

        show_chart_with_explanation(
            fig_review,
            "review_score_chart",
            review_explanations,
        )

    with delivery_right:
        st.subheader("Jumlah Pesanan berdasarkan Status")

        fig_delivery_count = px.bar(
            order_chart_data,
            x="Jumlah Pesanan",
            y="Status Pengiriman",
            orientation="h",
            color="Status Pengiriman",
            color_discrete_map=DELIVERY_COLORS,
            custom_data=["Status Pengiriman"],
            text="Jumlah Pesanan",
            labels={
                "Jumlah Pesanan": "Jumlah Pesanan",
                "Status Pengiriman": "Status Pengiriman",
            },
        )
        fig_delivery_count.update_traces(
            texttemplate="%{x:,.0f}",
            textposition="outside",
            cliponaxis=False,
        )
        fig_delivery_count.update_layout(
            height=410,
            showlegend=False,
            margin=dict(t=35, b=55),
        )

        count_explanations = {
            "Tepat Waktu": (
                f"Terdapat **{on_time_count:,.0f} pesanan tepat waktu** "
                "yang diterima tidak melewati tanggal estimasi pengiriman."
            ),
            "Terlambat": (
                f"Terdapat **{late_count:,.0f} pesanan terlambat** "
                "yang diterima setelah tanggal estimasi pengiriman."
            ),
        }

        show_chart_with_explanation(
            fig_delivery_count,
            "delivery_count_chart",
            count_explanations,
        )

    total_delivery_orders = on_time_count + late_count
    punctuality_rate = (
        on_time_count / total_delivery_orders * 100
        if total_delivery_orders
        else 0
    )

    if on_time_score > late_score:
        interpretation = (
            "Pesanan yang diterima tepat waktu memiliki rata-rata skor "
            "ulasan lebih tinggi dibandingkan pesanan terlambat."
        )
    elif late_score > on_time_score:
        interpretation = (
            "Pesanan terlambat memiliki rata-rata skor ulasan lebih tinggi "
            "pada data yang dianalisis."
        )
    else:
        interpretation = (
            "Kedua kategori memiliki rata-rata skor ulasan yang sama."
        )

    st.info(
        f"**Insight Pertanyaan 2:** {interpretation} "
        f"Selisih rata-rata skor adalah **{score_difference:.2f} poin**. "
        f"Proporsi pesanan tepat waktu sebesar **{punctuality_rate:.2f}%**. "
        "Hasil ini bersifat deskriptif dan tidak membuktikan hubungan sebab-akibat."
    )

    st.subheader("Tabel Ringkasan Pengiriman")
    display_delivery = delivery_summary.rename(
        columns={
            "delivery_status": "Status Pengiriman",
            "avg_review_score": "Rata-rata Skor Ulasan",
            "total_orders": "Jumlah Pesanan",
        }
    )
    st.dataframe(
        display_delivery.style.format(
            {
                "Rata-rata Skor Ulasan": "{:.2f}",
                "Jumlah Pesanan": "{:,.0f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# ============================================================
# BAGIAN 3 - TREN PENJUALAN BULANAN
# ============================================================
st.header("3. Analisis Tren Penjualan Bulanan")
st.caption(
    "Perkembangan jumlah pesanan dan total nilai pembayaran "
    "berdasarkan tanggal pembelian."
)

if monthly_data.empty:
    st.warning("Data penjualan bulanan tidak tersedia.")
else:
    filtered_sales = monthly_data[
        (monthly_data["month"].dt.date >= start_date)
        & (monthly_data["month"].dt.date <= end_date)
    ].copy()

    if filtered_sales.empty:
        st.warning("Tidak ada data pada periode yang dipilih.")
    else:
        total_orders_period = filtered_sales["total_orders"].sum()
        total_revenue_period = filtered_sales["total_revenue"].sum()

        s1, s2 = st.columns(2)
        s1.metric("Total Pesanan", f"{total_orders_period:,.0f}")
        s2.metric("Total Nilai Transaksi", f"R$ {total_revenue_period:,.2f}")

        sales_left, sales_right = st.columns(2)

        # Grafik jumlah pesanan bulanan.
        with sales_left:
            st.subheader("Perkembangan Jumlah Pesanan Bulanan")

            fig_orders = px.line(
                filtered_sales,
                x="month",
                y="total_orders",
                markers=True,
                custom_data=[
                    filtered_sales["month"].dt.strftime("%Y-%m")
                ],
                labels={
                    "month": "Bulan",
                    "total_orders": "Jumlah Pesanan",
                },
            )
            fig_orders.update_traces(
                line=dict(width=3),
                marker=dict(size=8),
                hovertemplate=(
                    "Bulan: %{x|%B %Y}<br>"
                    "Jumlah Pesanan: %{y:,.0f}<extra></extra>"
                ),
            )
            fig_orders.update_layout(
                height=410,
                xaxis_title="Bulan",
                yaxis_title="Jumlah Pesanan",
                hovermode="x unified",
                margin=dict(t=35, b=55),
            )

            order_explanations = {}
            for _, row in filtered_sales.iterrows():
                month_label = row["month"].strftime("%Y-%m")
                order_explanations[month_label] = (
                    f"Pada **{month_label}**, terdapat "
                    f"**{row['total_orders']:,.0f} pesanan**."
                )

            show_chart_with_explanation(
                fig_orders,
                "monthly_orders_chart",
                order_explanations,
            )

        # Grafik revenue bulanan.
        with sales_right:
            st.subheader("Perkembangan Revenue Bulanan")

            fig_revenue = px.line(
                filtered_sales,
                x="month",
                y="total_revenue",
                markers=True,
                custom_data=[
                    filtered_sales["month"].dt.strftime("%Y-%m")
                ],
                labels={
                    "month": "Bulan",
                    "total_revenue": "Total Revenue (R$)",
                },
            )
            fig_revenue.update_traces(
                line=dict(width=3),
                marker=dict(size=8),
                hovertemplate=(
                    "Bulan: %{x|%B %Y}<br>"
                    "Total Revenue: R$ %{y:,.2f}<extra></extra>"
                ),
            )
            fig_revenue.update_layout(
                height=410,
                xaxis_title="Bulan",
                yaxis_title="Total Revenue (R$)",
                hovermode="x unified",
                margin=dict(t=35, b=55),
            )

            revenue_explanations = {}
            for _, row in filtered_sales.iterrows():
                month_label = row["month"].strftime("%Y-%m")
                revenue_explanations[month_label] = (
                    f"Pada **{month_label}**, total nilai transaksi mencapai "
                    f"**R$ {row['total_revenue']:,.2f}**."
                )

            show_chart_with_explanation(
                fig_revenue,
                "monthly_revenue_chart",
                revenue_explanations,
            )

        st.subheader("Tabel Data Penjualan Bulanan")
        display_monthly = filtered_sales.copy()
        display_monthly["month"] = display_monthly["month"].dt.strftime("%Y-%m")
        display_monthly = display_monthly.rename(
            columns={
                "month": "Bulan",
                "total_orders": "Jumlah Pesanan",
                "total_revenue": "Total Nilai Transaksi (R$)",
            }
        )
        st.dataframe(
            display_monthly.style.format(
                {
                    "Jumlah Pesanan": "{:,.0f}",
                    "Total Nilai Transaksi (R$)": "R$ {:,.2f}",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        peak_order_month = filtered_sales.loc[
            filtered_sales["total_orders"].idxmax()
        ]
        st.info(
            f"**Insight Penjualan:** Bulan dengan jumlah pesanan tertinggi "
            f"pada periode terpilih adalah **{peak_order_month['month']:%B %Y}**, "
            f"sebanyak **{peak_order_month['total_orders']:,.0f} pesanan**."
        )

        if filtered_sales["month"].max() >= pd.Timestamp("2018-09-01"):
            st.caption(
                "Catatan: data pada bulan terakhir dataset dapat belum lengkap. "
                "Interpretasikan penurunan pada bulan terakhir dengan hati-hati."
            )

# ------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------
st.divider()
st.caption(
    "Sumber data: Brazilian E-Commerce Public Dataset by Olist. "
    "Dashboard dibuat untuk keperluan analisis proyek data."
)

# ============================================================
# DASHBOARD ANALISIS E-COMMERCE OLIST
# Sumber data: main_data.csv
# Butuh Streamlit >= 1.35 untuk fitur klik grafik.
# Jalankan: streamlit run app.py
# ============================================================

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# 1. KONFIGURASI HALAMAN
# ============================================================

st.set_page_config(
    page_title="Dashboard Analisis E-Commerce Olist",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = Path(__file__).parent
MAIN_DATA_FILE = DATA_DIR / "main_data.csv"

COLORS = {
    "Champions": "#6478C9",
    "Loyal Customers": "#91A4E8",
    "Potential Customers": "#B8C5F2",
    "Need Attention": "#D2D5DC",
    "Tepat Waktu": "#6478C9",
    "Terlambat": "#E58B82",
}

SEGMENT_ORDER = [
    "Champions",
    "Loyal Customers",
    "Potential Customers",
    "Need Attention"
]


# ============================================================
# 2. TAMPILAN DASHBOARD
# ============================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E8EAF0;
        padding: 16px 18px;
        border-radius: 12px;
    }
    [data-testid="stMetricLabel"] {
        color: #667085;
        font-size: 0.88rem;
    }
    [data-testid="stMetricValue"] {
        color: #202B45;
        font-weight: 650;
    }
    .section-note {
        color: #737B8C;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)



def plotly_chart_with_explanation(fig, chart_key, source_df, explain_row):
    """Render a selectable Plotly chart and show its explanation underneath."""
    event = st.plotly_chart(
        fig,
        use_container_width=True,
        key=chart_key,
        on_select="rerun",
        selection_mode="points"
    )

    selection = getattr(event, "selection", None)
    points = getattr(selection, "points", []) if selection is not None else []

    # Compatibility with Streamlit versions that expose event state as a dict.
    if isinstance(event, dict):
        points = event.get("selection", {}).get("points", [])

    if points:
        point = points[0]
        point_index = point.get("point_index", point.get("point_number"))
        if point_index is not None and 0 <= int(point_index) < len(source_df):
            selected_row = source_df.iloc[int(point_index)]
            st.info("**Penjelasan grafik yang dipilih**\n\n" + explain_row(selected_row))
        else:
            x_value = point.get("x", point.get("label", "-"))
            y_value = point.get("y", point.get("value", "-"))
            st.info(
                "**Penjelasan grafik yang dipilih**\n\n"
                f"Kategori: **{x_value}**. Nilai pada grafik: **{y_value}**."
            )
    else:
        st.caption("Klik salah satu titik, batang, atau irisan grafik untuk melihat penjelasannya di bawah grafik.")

# ============================================================
# 3. LOAD DAN PENGOLAHAN DATA
# ============================================================

@st.cache_data
def load_data():
    if not MAIN_DATA_FILE.exists():
        raise FileNotFoundError(
            "File main_data.csv tidak ditemukan. "
            "Simpan main_data.csv di folder yang sama dengan app.py."
        )

    data = pd.read_csv(MAIN_DATA_FILE, low_memory=False)

    required_columns = [
        "order_id",
        "customer_id",
        "customer_unique_id",
        "order_status",
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
        "total_payment",
        "review_score"
    ]

    missing = [col for col in required_columns if col not in data.columns]
    if missing:
        raise ValueError(
            "Kolom berikut belum tersedia di main_data.csv: "
            + ", ".join(missing)
        )

    date_columns = [
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date"
    ]
    for col in date_columns:
        data[col] = pd.to_datetime(data[col], errors="coerce")

    data["total_payment"] = pd.to_numeric(
        data["total_payment"], errors="coerce"
    )
    data["review_score"] = pd.to_numeric(
        data["review_score"], errors="coerce"
    )

    # Mengikuti notebook: analisis menggunakan pesanan delivered.
    master = data[data["order_status"].eq("delivered")].copy()

    if master.empty:
        raise ValueError("Tidak ditemukan pesanan dengan status delivered.")

    if master["order_id"].duplicated().any():
        raise ValueError(
            "Terdapat order_id duplikat. Pastikan pembayaran dan ulasan "
            "telah diagregasi per order_id sebelum membuat main_data.csv."
        )

    # --------------------------------------------------------
    # PERTANYAAN 1: tren bulanan, September 2017–Agustus 2018
    # --------------------------------------------------------
    sales = master[
        master["order_purchase_timestamp"].between(
            pd.Timestamp("2017-09-01"),
            pd.Timestamp("2018-08-31 23:59:59")
        )
    ].copy()

    monthly = (
        sales.groupby(
            sales["order_purchase_timestamp"].dt.to_period("M")
        )
        .agg(
            total_orders=("order_id", "nunique"),
            total_payment=("total_payment", "sum")
        )
        .reset_index()
    )

    monthly["period"] = monthly["order_purchase_timestamp"].astype(str)
    monthly = (
        monthly.drop(columns="order_purchase_timestamp")
        .sort_values("period")
        .reset_index(drop=True)
    )

    if monthly.empty:
        raise ValueError(
            "Tidak ada transaksi delivered pada periode "
            "September 2017–Agustus 2018."
        )

    # --------------------------------------------------------
    # PERTANYAAN 2: pengiriman dan ulasan, Jan 2017–Agu 2018
    # --------------------------------------------------------
    delivery = master[
        [
            "order_id",
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
            "review_score"
        ]
    ].copy()

    delivery = delivery[
        delivery["order_purchase_timestamp"].between(
            pd.Timestamp("2017-01-01"),
            pd.Timestamp("2018-08-31 23:59:59")
        )
    ].dropna(
        subset=[
            "order_delivered_customer_date",
            "order_estimated_delivery_date"
        ]
    ).copy()

    delivery["difference_days"] = (
        delivery["order_delivered_customer_date"]
        - delivery["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400

    delivery["delivery_status"] = delivery["difference_days"].apply(
        lambda days: "Terlambat" if days > 0 else "Tepat Waktu"
    )

    delivery_summary = (
        delivery.groupby("delivery_status", as_index=False)
        .agg(
            total_orders=("order_id", "nunique"),
            reviewed_orders=("review_score", "count"),
            average_review_score=("review_score", "mean")
        )
    )

    delivery_summary["percentage_orders"] = (
        delivery_summary["total_orders"]
        / delivery_summary["total_orders"].sum()
        * 100
    )

    # --------------------------------------------------------
    # PERTANYAAN 3: RFM, September 2016–Agustus 2018
    # --------------------------------------------------------
    rfm_master = master[
        master["order_purchase_timestamp"].between(
            pd.Timestamp("2016-09-01"),
            pd.Timestamp("2018-08-31 23:59:59")
        )
    ].dropna(
        subset=[
            "customer_unique_id",
            "order_purchase_timestamp",
            "total_payment"
        ]
    ).copy()

    if rfm_master.empty:
        raise ValueError("Tidak ditemukan data untuk analisis RFM.")

    reference_date = (
        rfm_master["order_purchase_timestamp"].max()
        + pd.Timedelta(days=1)
    )

    rfm = (
        rfm_master.groupby("customer_unique_id")
        .agg(
            recency=(
                "order_purchase_timestamp",
                lambda values: (reference_date - values.max()).days
            ),
            frequency=("order_id", "nunique"),
            monetary=("total_payment", "sum")
        )
        .reset_index()
    )

    # Metode scoring disamakan dengan notebook.
    rfm["r_score"] = pd.qcut(
        rfm["recency"].rank(method="first"),
        5,
        labels=[5, 4, 3, 2, 1]
    ).astype(int)

    rfm["f_score"] = pd.cut(
        rfm["frequency"],
        bins=[0, 1, 2, 3, 4, float("inf")],
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    rfm["m_score"] = pd.qcut(
        rfm["monetary"].rank(method="first"),
        5,
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    rfm["rfm_score"] = rfm[
        ["r_score", "f_score", "m_score"]
    ].sum(axis=1)

    def assign_segment(score):
        if score >= 13:
            return "Champions"
        if score >= 10:
            return "Loyal Customers"
        if score >= 7:
            return "Potential Customers"
        return "Need Attention"

    rfm["customer_segment"] = rfm["rfm_score"].apply(assign_segment)

    segments = (
        rfm.groupby("customer_segment")
        .agg(
            total_customers=("customer_unique_id", "nunique"),
            average_recency=("recency", "mean"),
            average_frequency=("frequency", "mean"),
            average_monetary=("monetary", "mean"),
            total_monetary=("monetary", "sum")
        )
        .reindex(SEGMENT_ORDER)
        .dropna()
        .reset_index()
    )

    segments["percentage"] = (
        segments["total_customers"]
        / segments["total_customers"].sum()
        * 100
    )
    segments["monetary_contribution"] = (
        segments["total_monetary"]
        / segments["total_monetary"].sum()
        * 100
    )

    return monthly, delivery_summary, rfm, segments


# ============================================================
# 4. MEMANGGIL DATA
# ============================================================

st.title("🛒 Dashboard Analisis E-Commerce Olist")
st.caption(
    "Analisis penjualan, ketepatan pengiriman, dan perilaku pelanggan "
    "berdasarkan E-Commerce Public Dataset Olist."
)

try:
    monthly, delivery_summary, rfm, segments = load_data()
except Exception as error:
    st.error(str(error))
    st.stop()


# ============================================================
# 5. FILTER DASHBOARD
# ============================================================

with st.sidebar:
    st.header("⚙️ Filter Dashboard")
    st.caption("Filter periode hanya diterapkan pada visualisasi tren transaksi.")

    month_options = monthly["period"].tolist()

    start_month = st.selectbox(
        "Mulai periode tren",
        month_options,
        index=0
    )
    end_month = st.selectbox(
        "Akhir periode tren",
        month_options,
        index=len(month_options) - 1
    )

    selected_segment = st.selectbox(
        "Segmen pelanggan",
        ["Semua Segmen"] + SEGMENT_ORDER
    )

    st.divider()
    st.caption(
        "Periode analisis tetap mengikuti notebook:\n"
        "- Tren: Sep 2017–Agu 2018\n"
        "- Pengiriman: Jan 2017–Agu 2018\n"
        "- RFM: Sep 2016–Agu 2018"
    )

start_index = month_options.index(start_month)
end_index = month_options.index(end_month)

if start_index <= end_index:
    monthly_view = monthly.iloc[start_index:end_index + 1].copy()
else:
    st.warning(
        "Bulan mulai berada setelah bulan akhir. "
        "Rentang ditampilkan secara berurutan dari bulan yang lebih awal."
    )
    monthly_view = monthly.iloc[end_index:start_index + 1].copy()


# ============================================================
# 6. RINGKASAN KPI
# ============================================================

st.subheader("Ringkasan Analisis")

total_orders_view = int(monthly_view["total_orders"].sum())
total_payment_view = monthly_view["total_payment"].sum()
total_customers = int(rfm["customer_unique_id"].nunique())
average_order_value = (
    total_payment_view / total_orders_view if total_orders_view else 0
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Pesanan Delivered", f"{total_orders_view:,.0f}")
k2.metric("Total Pembayaran", f"R$ {total_payment_view:,.2f}")
k3.metric("Total Pelanggan RFM", f"{total_customers:,.0f}")
k4.metric("Rata-rata Pembayaran / Pesanan", f"R$ {average_order_value:,.2f}")

st.caption(
    f"Ringkasan penjualan mengikuti filter bulan: "
    f"{monthly_view['period'].iloc[0]} sampai {monthly_view['period'].iloc[-1]}. "
    "Jumlah pelanggan RFM dihitung untuk periode September 2016–Agustus 2018."
)

st.divider()


# ============================================================
# 7. BAGIAN ANALISIS (DITAMPILKAN VERTIKAL)
# ============================================================

st.caption("Gulir halaman ke bawah untuk melihat seluruh bagian analisis.")


# ============================================================
# BAGIAN 1: TREN TRANSAKSI
# ============================================================

st.subheader("Pertanyaan 1 — Tren Pesanan dan Pembayaran Bulanan")
st.markdown(
    '<p class="section-note">Pesanan berstatus delivered, '
    'September 2017–Agustus 2018.</p>',
    unsafe_allow_html=True
)

peak_orders = monthly_view.loc[monthly_view["total_orders"].idxmax()]
peak_payment = monthly_view.loc[monthly_view["total_payment"].idxmax()]

left, right = st.columns(2)

with left:
    fig_orders = px.line(
        monthly_view,
        x="period",
        y="total_orders",
        markers=True,
        title="Tren Jumlah Pesanan Delivered",
        labels={
            "period": "Bulan",
            "total_orders": "Jumlah Pesanan"
        }
    )
    fig_orders.update_traces(
        line=dict(color="#6478C9", width=3),
        marker=dict(size=8)
    )
    fig_orders.update_layout(
        hovermode="x unified",
        margin=dict(l=10, r=10, t=55, b=10)
    )
    plotly_chart_with_explanation(
        fig_orders,
        "chart_monthly_orders",
        monthly_view,
        lambda row: (
            f"Pada **{row['period']}**, terdapat **{row['total_orders']:,.0f} pesanan delivered**. "
            "Angka ini menunjukkan jumlah pesanan yang berhasil diterima pelanggan pada bulan tersebut."
        )
    )

with right:
    fig_payment = px.line(
        monthly_view,
        x="period",
        y="total_payment",
        markers=True,
        title="Tren Total Pembayaran",
        labels={
            "period": "Bulan",
            "total_payment": "Total Pembayaran (BRL)"
        }
    )
    fig_payment.update_traces(
        line=dict(color="#7A83E8", width=3),
        marker=dict(size=8)
    )
    fig_payment.update_yaxes(tickprefix="R$ ")
    fig_payment.update_layout(
        hovermode="x unified",
        margin=dict(l=10, r=10, t=55, b=10)
    )
    plotly_chart_with_explanation(
        fig_payment,
        "chart_monthly_payment",
        monthly_view,
        lambda row: (
            f"Pada **{row['period']}**, total pembayaran tercatat sebesar "
            f"**R$ {row['total_payment']:,.2f}**. Nilai ini merupakan akumulasi pembayaran "
            "pesanan delivered pada bulan yang dipilih."
        )
    )

a, b = st.columns(2)
with a:
    st.info(
        f"**Puncak jumlah pesanan pada filter:** {peak_orders['period']} "
        f"dengan **{peak_orders['total_orders']:,.0f} pesanan**."
    )
with b:
    st.info(
        f"**Puncak pembayaran pada filter:** {peak_payment['period']} "
        f"dengan **R$ {peak_payment['total_payment']:,.2f}**."
    )

st.markdown("#### Detail Transaksi Bulanan")
display_monthly = monthly_view.copy()
display_monthly["total_payment"] = display_monthly["total_payment"].round(2)
st.dataframe(
    display_monthly.rename(
        columns={
            "period": "Bulan",
            "total_orders": "Jumlah Pesanan",
            "total_payment": "Total Pembayaran (BRL)"
        }
    ),
    use_container_width=True,
    hide_index=True
)

st.markdown("#### Insight Analisis")
st.write(
    "Berdasarkan hasil notebook, November 2017 merupakan periode dengan "
    "aktivitas transaksi tertinggi, yaitu **7.289 pesanan** dan total "
    "pembayaran **R$ 1.153.528,05**. Pada Agustus 2018, jumlah pesanan "
    "meningkat menjadi 6.351, sedangkan total pembayaran turun menjadi "
    "R$ 985.414,28. Hal ini menunjukkan bahwa kenaikan jumlah pesanan "
    "tidak selalu diikuti kenaikan total pembayaran."
)
st.markdown("**Rekomendasi:** optimalkan promosi dan persediaan pada periode "
            "transaksi tinggi, antisipasi penurunan penjualan melalui promosi "
            "khusus, serta pantau jumlah pesanan dan pembayaran setiap bulan.")


# ============================================================
# BAGIAN 2: PENGIRIMAN DAN ULASAN
# ============================================================

st.divider()

st.subheader("Pertanyaan 2 — Ketepatan Pengiriman dan Skor Ulasan")
st.markdown(
    '<p class="section-note">Periode Januari 2017–Agustus 2018. '
    'Terlambat berarti tanggal diterima melewati estimasi.</p>',
    unsafe_allow_html=True
)

delivery_order = ["Tepat Waktu", "Terlambat"]
delivery_plot = (
    delivery_summary.set_index("delivery_status")
    .reindex(delivery_order)
    .dropna(subset=["total_orders"])
    .reset_index()
)

on_time = delivery_summary.loc[
    delivery_summary["delivery_status"].eq("Tepat Waktu"),
    "average_review_score"
]
late = delivery_summary.loc[
    delivery_summary["delivery_status"].eq("Terlambat"),
    "average_review_score"
]

score_on_time = on_time.iloc[0] if not on_time.empty else float("nan")
score_late = late.iloc[0] if not late.empty else float("nan")
score_gap = score_on_time - score_late

m1, m2, m3 = st.columns(3)
m1.metric(
    "Rata-rata Skor Tepat Waktu",
    f"{score_on_time:.2f}" if pd.notna(score_on_time) else "N/A"
)
m2.metric(
    "Rata-rata Skor Terlambat",
    f"{score_late:.2f}" if pd.notna(score_late) else "N/A"
)
m3.metric(
    "Selisih Skor Ulasan",
    f"{score_gap:.2f} poin" if pd.notna(score_gap) else "N/A"
)

left, right = st.columns(2)

with left:
    fig_score = px.bar(
        delivery_plot,
        x="delivery_status",
        y="average_review_score",
        color="delivery_status",
        color_discrete_map=COLORS,
        text="average_review_score",
        title="Rata-rata Skor Ulasan (Skala 1–5)",
        labels={
            "delivery_status": "Status Pengiriman",
            "average_review_score": "Rata-rata Skor"
        }
    )
    fig_score.update_traces(
        texttemplate="%{y:.2f}",
        textposition="outside"
    )
    fig_score.update_yaxes(range=[0, 5])
    fig_score.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=55, b=10)
    )
    plotly_chart_with_explanation(
        fig_score,
        "chart_delivery_score",
        delivery_plot,
        lambda row: (
            f"Pesanan dengan status **{row['delivery_status']}** memiliki rata-rata skor ulasan "
            f"**{row['average_review_score']:.2f} dari 5**, berdasarkan "
            f"{row['reviewed_orders']:,.0f} pesanan yang memiliki ulasan."
        )
    )

with right:
    fig_delivery = px.pie(
        delivery_plot,
        names="delivery_status",
        values="total_orders",
        color="delivery_status",
        color_discrete_map=COLORS,
        hole=0.48,
        title="Proporsi Pesanan Berdasarkan Status Pengiriman"
    )
    fig_delivery.update_traces(
        textinfo="label+percent",
        hole=0.48
    )
    fig_delivery.update_layout(
        margin=dict(l=10, r=10, t=55, b=10)
    )
    plotly_chart_with_explanation(
        fig_delivery,
        "chart_delivery_share",
        delivery_plot,
        lambda row: (
            f"Kategori **{row['delivery_status']}** mencakup **{row['total_orders']:,.0f} pesanan** "
            f"atau **{row['percentage_orders']:.2f}%** dari seluruh pesanan yang dianalisis."
        )
    )

st.success(
    f"Pesanan tepat waktu memperoleh rata-rata skor **{score_on_time:.2f}**, "
    f"sedangkan pesanan terlambat memperoleh **{score_late:.2f}**. "
    f"Selisihnya adalah **{score_gap:.2f} poin**."
)

st.markdown("#### Detail Pengiriman dan Ulasan")
st.dataframe(
    delivery_summary.round(2).rename(
        columns={
            "delivery_status": "Status Pengiriman",
            "total_orders": "Jumlah Pesanan",
            "reviewed_orders": "Pesanan dengan Ulasan",
            "average_review_score": "Rata-rata Skor Ulasan",
            "percentage_orders": "Persentase Pesanan (%)"
        }
    ),
    use_container_width=True,
    hide_index=True
)

st.markdown("**Insight:** pelanggan yang menerima pesanan tepat waktu "
            "memberikan skor ulasan lebih tinggi dibandingkan pelanggan "
            "yang mengalami keterlambatan. Ketepatan pengiriman perlu menjadi "
            "prioritas dalam menjaga pengalaman pelanggan.")
st.markdown("**Rekomendasi:** evaluasi mitra logistik, pantau estimasi dan "
            "proses distribusi, berikan informasi status pengiriman secara "
            "berkala, serta gunakan skor ulasan untuk mengevaluasi layanan.")


# ============================================================
# BAGIAN 3: SEGMENTASI PELANGGAN RFM
# ============================================================

st.divider()

st.subheader("Pertanyaan 3 — Karakteristik dan Segmentasi Pelanggan RFM")
st.markdown(
    '<p class="section-note">Transaksi delivered, '
    'September 2016–Agustus 2018.</p>',
    unsafe_allow_html=True
)

if selected_segment == "Semua Segmen":
    filtered_rfm = rfm.copy()
    filtered_segments = segments.copy()
else:
    filtered_rfm = rfm[
        rfm["customer_segment"].eq(selected_segment)
    ].copy()
    filtered_segments = segments[
        segments["customer_segment"].eq(selected_segment)
    ].copy()

st.caption(f"Segmen yang ditampilkan: **{selected_segment}**")

rfm_k1, rfm_k2, rfm_k3 = st.columns(3)
rfm_k1.metric(
    "Jumlah Pelanggan",
    f"{filtered_rfm['customer_unique_id'].nunique():,}"
)
rfm_k2.metric(
    "Rata-rata Frequency",
    f"{filtered_rfm['frequency'].mean():.2f}"
    if not filtered_rfm.empty else "N/A"
)
rfm_k3.metric(
    "Rata-rata Monetary",
    f"R$ {filtered_rfm['monetary'].mean():,.2f}"
    if not filtered_rfm.empty else "N/A"
)

# Karakteristik RFM: tiga grafik sesuai hasil notebook.
recency_data = filtered_segments.sort_values("average_recency")
frequency_data = filtered_segments.sort_values("average_frequency")
monetary_data = filtered_segments.sort_values("average_monetary")

row1a, row1b = st.columns(2)

with row1a:
    fig_recency = px.bar(
        recency_data,
        x="average_recency",
        y="customer_segment",
        orientation="h",
        color="customer_segment",
        color_discrete_map=COLORS,
        text="average_recency",
        title="Rata-rata Recency per Segmen",
        labels={
            "average_recency": "Rata-rata Recency (Hari)",
            "customer_segment": "Segmen Pelanggan"
        }
    )
    fig_recency.update_traces(
        texttemplate="%{x:.2f}",
        textposition="outside"
    )
    fig_recency.update_layout(
        showlegend=False,
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=10, r=25, t=55, b=10)
    )
    plotly_chart_with_explanation(
        fig_recency,
        "chart_rfm_recency",
        recency_data,
        lambda row: (
            f"Segmen **{row['customer_segment']}** memiliki rata-rata Recency "
            f"**{row['average_recency']:.2f} hari**. Recency menunjukkan jarak hari sejak "
            "transaksi terakhir; nilai yang lebih kecil berarti pelanggan lebih baru bertransaksi."
        )
    )

with row1b:
    fig_frequency = px.bar(
        frequency_data,
        x="average_frequency",
        y="customer_segment",
        orientation="h",
        color="customer_segment",
        color_discrete_map=COLORS,
        text="average_frequency",
        title="Rata-rata Frequency per Segmen",
        labels={
            "average_frequency": "Rata-rata Frequency (Pesanan)",
            "customer_segment": "Segmen Pelanggan"
        }
    )
    fig_frequency.update_traces(
        texttemplate="%{x:.2f}",
        textposition="outside"
    )
    fig_frequency.update_layout(
        showlegend=False,
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=10, r=25, t=55, b=10)
    )
    plotly_chart_with_explanation(
        fig_frequency,
        "chart_rfm_frequency",
        frequency_data,
        lambda row: (
            f"Segmen **{row['customer_segment']}** memiliki rata-rata Frequency "
            f"**{row['average_frequency']:.2f} pesanan** per pelanggan. Frequency menunjukkan "
            "seberapa sering pelanggan melakukan transaksi."
        )
    )

row2a, row2b = st.columns(2)

with row2a:
    fig_monetary = px.bar(
        monetary_data,
        x="average_monetary",
        y="customer_segment",
        orientation="h",
        color="customer_segment",
        color_discrete_map=COLORS,
        text="average_monetary",
        title="Rata-rata Monetary per Segmen",
        labels={
            "average_monetary": "Rata-rata Monetary (BRL)",
            "customer_segment": "Segmen Pelanggan"
        }
    )
    fig_monetary.update_traces(
        texttemplate="R$ %{x:,.2f}",
        textposition="outside"
    )
    fig_monetary.update_layout(
        showlegend=False,
        yaxis={"categoryorder": "total ascending"},
        margin=dict(l=10, r=35, t=55, b=10)
    )
    plotly_chart_with_explanation(
        fig_monetary,
        "chart_rfm_monetary",
        monetary_data,
        lambda row: (
            f"Segmen **{row['customer_segment']}** memiliki rata-rata Monetary "
            f"**R$ {row['average_monetary']:,.2f}** per pelanggan. Monetary menggambarkan "
            "total nilai pembayaran yang dihasilkan pelanggan."
        )
    )

with row2b:
    fig_customers = px.pie(
        filtered_segments,
        names="customer_segment",
        values="total_customers",
        color="customer_segment",
        color_discrete_map=COLORS,
        hole=0.45,
        title="Proporsi Jumlah Pelanggan per Segmen"
    )
    fig_customers.update_traces(textinfo="label+percent")
    fig_customers.update_layout(
        margin=dict(l=10, r=10, t=55, b=10)
    )
    plotly_chart_with_explanation(
        fig_customers,
        "chart_rfm_customer_share",
        filtered_segments,
        lambda row: (
            f"Segmen **{row['customer_segment']}** terdiri dari **{row['total_customers']:,.0f} pelanggan** "
            f"atau **{row['percentage']:.2f}%** dari pelanggan yang sedang ditampilkan."
        )
    )

fig_contribution = px.bar(
    filtered_segments.sort_values("monetary_contribution"),
    x="monetary_contribution",
    y="customer_segment",
    orientation="h",
    color="customer_segment",
    color_discrete_map=COLORS,
    text="monetary_contribution",
    title="Kontribusi Pembayaran per Segmen",
    labels={
        "monetary_contribution": "Kontribusi Pembayaran (%)",
        "customer_segment": "Segmen Pelanggan"
    }
)
fig_contribution.update_traces(
    texttemplate="%{x:.2f}%",
    textposition="outside"
)
fig_contribution.update_layout(
    showlegend=False,
    xaxis_ticksuffix="%",
    yaxis={"categoryorder": "total ascending"},
    margin=dict(l=10, r=25, t=55, b=10)
)
plotly_chart_with_explanation(
    fig_contribution,
    "chart_rfm_payment_contribution",
    filtered_segments.sort_values("monetary_contribution").reset_index(drop=True),
    lambda row: (
        f"Segmen **{row['customer_segment']}** menyumbang **{row['monetary_contribution']:.2f}%** "
        f"dari total pembayaran segmen yang ditampilkan, dengan total nilai "
        f"**R$ {row['total_monetary']:,.2f}**."
    )
)

st.markdown("#### Ringkasan Segmentasi Pelanggan")
segment_table = filtered_segments[
    [
        "customer_segment",
        "total_customers",
        "average_recency",
        "average_frequency",
        "average_monetary",
        "percentage",
        "monetary_contribution"
    ]
].copy()

st.dataframe(
    segment_table.round(2).rename(
        columns={
            "customer_segment": "Segmen Pelanggan",
            "total_customers": "Jumlah Pelanggan",
            "average_recency": "Rata-rata Recency (Hari)",
            "average_frequency": "Rata-rata Frequency",
            "average_monetary": "Rata-rata Monetary (BRL)",
            "percentage": "Persentase Pelanggan (%)",
            "monetary_contribution": "Kontribusi Pembayaran (%)"
        }
    ),
    use_container_width=True,
    hide_index=True
)

st.markdown("#### Detail Data Pelanggan")
st.caption(
    "Gunakan filter segmen di sidebar untuk melihat pelanggan pada "
    "kelompok tertentu."
)

detail_columns = [
    "customer_unique_id",
    "recency",
    "frequency",
    "monetary",
    "r_score",
    "f_score",
    "m_score",
    "rfm_score",
    "customer_segment"
]

detail_data = filtered_rfm[detail_columns].sort_values(
    ["rfm_score", "monetary"],
    ascending=[False, False]
)

st.metric("Jumlah Baris Pelanggan Ditampilkan", f"{len(detail_data):,}")
st.dataframe(
    detail_data.rename(
        columns={
            "customer_unique_id": "Customer Unique ID",
            "recency": "Recency (Hari)",
            "frequency": "Frequency",
            "monetary": "Monetary (BRL)",
            "r_score": "R Score",
            "f_score": "F Score",
            "m_score": "M Score",
            "rfm_score": "RFM Score",
            "customer_segment": "Segmen Pelanggan"
        }
    ),
    use_container_width=True,
    hide_index=True,
    height=420
)

csv_data = detail_data.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Unduh Detail Pelanggan (CSV)",
    data=csv_data,
    file_name="detail_segmentasi_rfm_olist.csv",
    mime="text/csv"
)

st.markdown("#### Insight dan Rekomendasi Retensi")
st.write(
    "**Potential Customers** merupakan segmen terbesar, sebanyak "
    "**44.145 pelanggan (47,29%)**, serta menyumbang **54,48%** "
    "pembayaran. Fokuskan promosi personal, voucher, dan rekomendasi "
    "produk untuk mendorong pembelian ulang."
)
st.write(
    "**Need Attention** mencakup **37.124 pelanggan (39,77%)** dengan "
    "rata-rata Recency **341,57 hari**. Lakukan kampanye reaktivasi "
    "melalui penawaran khusus atau pengingat promosi."
)
st.write(
    "**Loyal Customers** berjumlah **12.020 pelanggan (12,88%)** dan "
    "memberikan kontribusi pembayaran **27,40%**. Pertahankan melalui "
    "program reward, poin belanja, dan penawaran eksklusif."
)
st.write(
    "**Champions** berjumlah **68 pelanggan (0,07%)**, dengan rata-rata "
    "Frequency **4,15** dan Monetary **R$ 708,16**. Berikan apresiasi "
    "khusus, akses awal produk baru, dan keuntungan loyalitas eksklusif."
)


# ============================================================
# 8. FOOTER
# ============================================================

st.divider()
st.caption(
    "Sumber: E-Commerce Public Dataset Olist. "
    "Perhitungan dashboard mengikuti periode, definisi, dan metode "
    "analisis pada Notebook.ipynb. Nilai pada grafik dan tabel dihitung "
    "kembali dari main_data.csv."
)

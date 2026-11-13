# ============================================================
# OLIST E-COMMERCE DASHBOARD
# Kriteria 4 - Streamlit
# Analisis: RFM, Ketepatan Pengiriman & Kepuasan, Tren Penjualan
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
    BASE_DIR / "data",
    BASE_DIR.parent / "data",
    BASE_DIR,
]


def find_csv(filename):
    """Mencari file CSV di folder dashboard/data, data/, atau dashboard/."""
    for folder in DATA_DIR_CANDIDATES:
        path = folder / filename
        if path.exists():
            return path

    searched = "\n".join(str(folder / filename) for folder in DATA_DIR_CANDIDATES)
    raise FileNotFoundError(
        f"File {filename} tidak ditemukan. Lokasi yang diperiksa:\n{searched}"
    )


@st.cache_data
def load_data():
    """Memuat dataset yang dibutuhkan dashboard."""
    files = {
        "orders": "orders_dataset.csv",
        "customers": "customers_dataset.csv",
        "payments": "order_payments_dataset.csv",
        "reviews": "order_reviews_dataset.csv",
    }

    data = {
        key: pd.read_csv(find_csv(filename))
        for key, filename in files.items()
    }

    date_columns = [
        "order_purchase_timestamp",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]

    for column in date_columns:
        if column in data["orders"].columns:
            data["orders"][column] = pd.to_datetime(
                data["orders"][column], errors="coerce"
            )

    return data


def check_columns(dataframe, required_columns, dataset_name):
    """Memastikan kolom yang diperlukan tersedia."""
    missing = [column for column in required_columns if column not in dataframe.columns]
    if missing:
        raise ValueError(
            f"Kolom berikut tidak ditemukan pada {dataset_name}: {', '.join(missing)}"
        )


# ------------------------------------------------------------
# 2. PENGOLAHAN DATA RFM
# ------------------------------------------------------------
@st.cache_data
def prepare_rfm(orders, customers, payments):
    """
    Membentuk RFM berdasarkan customer_unique_id.

    Pada dataset Olist, customer_unique_id berada di customers_dataset,
    bukan di orders_dataset. Karena itu, data pelanggan digabungkan
    melalui customer_id sebelum perhitungan RFM.
    """
    check_columns(
        orders,
        ["order_id", "customer_id", "order_purchase_timestamp"],
        "orders_dataset",
    )
    check_columns(
        customers,
        ["customer_id", "customer_unique_id"],
        "customers_dataset",
    )
    check_columns(payments, ["order_id", "payment_value"], "order_payments_dataset")

    customer_mapping = customers[["customer_id", "customer_unique_id"]].drop_duplicates(
        subset=["customer_id"]
    )
    valid_orders = orders.dropna(
        subset=["order_id", "customer_id", "order_purchase_timestamp"]
    ).merge(customer_mapping, on="customer_id", how="left")
    valid_orders = valid_orders.dropna(subset=["customer_unique_id"])

    payment_per_order = (
        payments.groupby("order_id", as_index=False)["payment_value"]
        .sum()
    )

    transactions = valid_orders.merge(
        payment_per_order,
        on="order_id",
        how="inner",
    )

    # Satu baris akhir untuk setiap pelanggan unik.
    customer_rfm = (
        transactions.groupby("customer_unique_id")
        .agg(
            last_purchase=("order_purchase_timestamp", "max"),
            frequency=("order_id", "nunique"),
            monetary=("payment_value", "sum"),
        )
        .reset_index()
    )

    if customer_rfm.empty:
        return customer_rfm

    # Tanggal acuan satu hari setelah pembelian terakhir pada dataset.
    snapshot_date = valid_orders["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

    customer_rfm["recency"] = (
        snapshot_date - customer_rfm["last_purchase"]
    ).dt.days

    # Ranking terlebih dahulu mengurangi risiko qcut gagal akibat nilai kembar.
    customer_rfm["R_score"] = pd.qcut(
        customer_rfm["recency"].rank(method="first"),
        q=5,
        labels=[5, 4, 3, 2, 1],
    ).astype(int)

    customer_rfm["F_score"] = pd.qcut(
        customer_rfm["frequency"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    customer_rfm["M_score"] = pd.qcut(
        customer_rfm["monetary"].rank(method="first"),
        q=5,
        labels=[1, 2, 3, 4, 5],
    ).astype(int)

    def assign_segment(row):
        r, f, m = row["R_score"], row["F_score"], row["M_score"]

        if r >= 4 and f >= 4 and m >= 4:
            return "Champions"
        if r >= 3 and f >= 4:
            return "Loyal Customers"
        if r >= 4 and f <= 2:
            return "New Customers"
        if r <= 2 and f >= 3:
            return "At Risk"
        if r <= 2 and f <= 2:
            return "Hibernating"
        return "Potential Customers"

    customer_rfm["segment"] = customer_rfm.apply(assign_segment, axis=1)
    return customer_rfm


# ------------------------------------------------------------
# 3. PENGOLAHAN DATA PENGIRIMAN DAN ULASAN
# ------------------------------------------------------------
@st.cache_data
def prepare_delivery(orders, reviews):
    """Menggabungkan ketepatan pengiriman dengan skor ulasan."""
    check_columns(
        orders,
        [
            "order_id",
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
        "orders_dataset",
    )
    check_columns(reviews, ["order_id", "review_score"], "order_reviews_dataset")

    start_date = pd.Timestamp("2017-01-01")
    end_date = pd.Timestamp("2018-11-01")  # Batas eksklusif: mencakup Oktober 2018.

    delivery = orders[
        [
            "order_id",
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    ].copy()

    delivery = delivery[
        (delivery["order_purchase_timestamp"] >= start_date)
        & (delivery["order_purchase_timestamp"] < end_date)
    ]

    # Pesanan harus sudah diterima dan memiliki tanggal estimasi.
    delivery = delivery.dropna(
        subset=[
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ]
    )

    delivery["delivery_status"] = (
        delivery["order_delivered_customer_date"]
        <= delivery["order_estimated_delivery_date"]
    ).map({True: "Tepat Waktu", False: "Terlambat"})

    # Rata-rata ulasan per order mencegah satu order dihitung berulang.
    review_per_order = (
        reviews.dropna(subset=["review_score"])
        .groupby("order_id", as_index=False)["review_score"]
        .mean()
    )

    return delivery.merge(review_per_order, on="order_id", how="inner")


# ------------------------------------------------------------
# 4. PENGOLAHAN TREN PENJUALAN BULANAN
# ------------------------------------------------------------
@st.cache_data
def prepare_monthly_sales(orders, payments):
    """Menghitung jumlah pesanan dan total pembayaran per bulan."""
    check_columns(
        orders,
        ["order_id", "order_purchase_timestamp"],
        "orders_dataset",
    )
    check_columns(payments, ["order_id", "payment_value"], "order_payments_dataset")

    valid_orders = orders.dropna(
        subset=["order_id", "order_purchase_timestamp"]
    ).copy()

    valid_orders["month"] = (
        valid_orders["order_purchase_timestamp"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    monthly_orders = (
        valid_orders.groupby("month")["order_id"]
        .nunique()
        .rename("total_orders")
    )

    payment_per_order = (
        payments.groupby("order_id", as_index=False)["payment_value"]
        .sum()
    )

    order_sales = (
        valid_orders[["order_id", "month"]]
        .drop_duplicates(subset=["order_id"])
        .merge(payment_per_order, on="order_id", how="inner")
    )

    monthly_revenue = (
        order_sales.groupby("month")["payment_value"]
        .sum()
        .rename("total_revenue")
    )

    monthly = (
        pd.concat([monthly_orders, monthly_revenue], axis=1)
        .fillna(0)
        .reset_index()
        .sort_values("month")
    )

    return monthly


# ------------------------------------------------------------
# 5. MEMUAT DAN MENYIAPKAN DATA
# ------------------------------------------------------------
st.title("🛍️ Olist E-Commerce Dashboard")
st.markdown(
    "Dashboard analisis data e-commerce Olist untuk memahami segmentasi "
    "pelanggan, performa pengiriman, kepuasan pelanggan, dan tren penjualan."
)

try:
    with st.spinner("Memuat dan memproses dataset Olist..."):
        raw_data = load_data()

        rfm_data = prepare_rfm(
            raw_data["orders"],
            raw_data["customers"],
            raw_data["payments"],
        )

        delivery_data = prepare_delivery(
            raw_data["orders"],
            raw_data["reviews"],
        )

        monthly_data = prepare_monthly_sales(
            raw_data["orders"],
            raw_data["payments"],
        )

except (FileNotFoundError, ValueError, KeyError) as error:
    st.error(str(error))
    st.info(
        "Pastikan struktur folder dan nama file seperti berikut:\n\n"
        "submission/\n"
        "├── data/\n"
        "│   ├── orders_dataset.csv\n"
        "│   ├── order_payments_dataset.csv\n"
        "│   └── order_reviews_dataset.csv\n"
        "└── dashboard/\n"
        "    └── dashboard.py"
    )
    st.stop()

except Exception as error:
    st.error(f"Terjadi kesalahan saat memproses data: {error}")
    st.info("Periksa kembali format dan isi dataset CSV.")
    st.stop()


if rfm_data.empty:
    st.error("Data RFM kosong. Periksa data pesanan dan pembayaran.")
    st.stop()


# ------------------------------------------------------------
# 6. NAVIGASI DASHBOARD
# ------------------------------------------------------------
tab_rfm, tab_delivery, tab_sales = st.tabs(
    [
        "👥 Segmentasi Pelanggan (RFM)",
        "🚚 Pengiriman & Kepuasan",
        "📈 Tren Penjualan",
    ]
)


# ============================================================
# TAB 1 - SEGMENTASI PELANGGAN (RFM)
# ============================================================
with tab_rfm:
    st.header("Analisis Segmentasi Pelanggan (RFM)")
    st.caption(
        "Segmentasi berdasarkan Recency, Frequency, dan Monetary "
        "menggunakan seluruh periode transaksi yang tersedia."
    )

    total_customers = rfm_data["customer_unique_id"].nunique()
    total_revenue = rfm_data["monetary"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pelanggan Unik", f"{total_customers:,.0f}")
    col2.metric("Total Revenue", f"R$ {total_revenue:,.2f}")
    col3.metric(
        "Rata-rata Frequency",
        f"{rfm_data['frequency'].mean():.2f} transaksi",
    )

    st.divider()
    st.subheader("Ringkasan RFM")

    r1, r2, r3 = st.columns(3)
    r1.metric("Rata-rata Recency", f"{rfm_data['recency'].mean():.1f} hari")
    r2.metric("Rata-rata Frequency", f"{rfm_data['frequency'].mean():.2f} transaksi")
    r3.metric("Rata-rata Monetary", f"R$ {rfm_data['monetary'].mean():,.2f}")

    segment_summary = (
        rfm_data.groupby("segment", as_index=False)
        .agg(
            total_customers=("customer_unique_id", "nunique"),
            total_revenue=("monetary", "sum"),
            avg_recency=("recency", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
        )
    )

    segment_summary["revenue_contribution"] = (
        segment_summary["total_revenue"] / total_revenue * 100
        if total_revenue
        else 0
    )

    segment_summary = segment_summary.sort_values(
        "total_revenue", ascending=False
    )

    best_segment = segment_summary.iloc[0]
    st.info(
        f"Segmen dengan revenue terbesar adalah **{best_segment['segment']}**, "
        f"dengan total revenue **R$ {best_segment['total_revenue']:,.2f}** "
        f"atau **{best_segment['revenue_contribution']:.2f}%** "
        "dari total revenue."
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Jumlah Pelanggan per Segmen")
        customer_chart_data = segment_summary.sort_values(
            "total_customers", ascending=False
        )
        fig_customers = px.bar(
            customer_chart_data,
            x="segment",
            y="total_customers",
            color="segment",
            text_auto=".2s",
            labels={
                "segment": "Segmen Pelanggan",
                "total_customers": "Jumlah Pelanggan",
            },
        )
        fig_customers.update_layout(
            showlegend=False,
            xaxis_title="Segmen Pelanggan",
            yaxis_title="Jumlah Pelanggan",
        )
        st.plotly_chart(fig_customers, use_container_width=True)

    with right:
        st.subheader("Revenue per Segmen")
        fig_revenue = px.bar(
            segment_summary,
            x="segment",
            y="total_revenue",
            color="segment",
            text_auto=".2s",
            labels={
                "segment": "Segmen Pelanggan",
                "total_revenue": "Total Revenue (R$)",
            },
        )
        fig_revenue.update_layout(
            showlegend=False,
            xaxis_title="Segmen Pelanggan",
            yaxis_title="Total Revenue (R$)",
        )
        st.plotly_chart(fig_revenue, use_container_width=True)

    st.subheader("Persentase Kontribusi Revenue")
    fig_contribution = px.pie(
        segment_summary,
        names="segment",
        values="total_revenue",
        hole=0.45,
    )
    fig_contribution.update_traces(
        textposition="inside",
        texttemplate="%{label}<br>%{percent}",
    )
    st.plotly_chart(fig_contribution, use_container_width=True)

    st.subheader("Tabel Ringkasan Segmentasi RFM")
    display_rfm = segment_summary.rename(
        columns={
            "segment": "Segmen",
            "total_customers": "Jumlah Pelanggan",
            "total_revenue": "Total Revenue (R$)",
            "revenue_contribution": "Kontribusi Revenue (%)",
            "avg_recency": "Rata-rata Recency (hari)",
            "avg_frequency": "Rata-rata Frequency",
            "avg_monetary": "Rata-rata Monetary (R$)",
        }
    )

    st.dataframe(
        display_rfm.style.format(
            {
                "Total Revenue (R$)": "R$ {:,.2f}",
                "Kontribusi Revenue (%)": "{:.2f}%",
                "Rata-rata Recency (hari)": "{:.1f}",
                "Rata-rata Frequency": "{:.2f}",
                "Rata-rata Monetary (R$)": "R$ {:,.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# TAB 2 - PENGIRIMAN DAN KEPUASAN PELANGGAN
# ============================================================
with tab_delivery:
    st.header("Analisis Ketepatan Pengiriman dan Kepuasan Pelanggan")
    st.caption(
        "Perbandingan rata-rata skor ulasan pesanan tepat waktu dan terlambat, "
        "periode Januari 2017–Oktober 2018."
    )

    if delivery_data.empty:
        st.warning(
            "Tidak tersedia pesanan yang memenuhi kriteria tanggal pengiriman "
            "dan skor ulasan pada periode analisis."
        )
    else:
        delivery_summary = (
            delivery_data.groupby("delivery_status", as_index=False)
            .agg(
                avg_review_score=("review_score", "mean"),
                total_orders=("order_id", "nunique"),
            )
        )

        on_time = delivery_summary[
            delivery_summary["delivery_status"] == "Tepat Waktu"
        ]
        late = delivery_summary[
            delivery_summary["delivery_status"] == "Terlambat"
        ]

        on_time_score = (
            float(on_time["avg_review_score"].iloc[0]) if not on_time.empty else 0
        )
        late_score = (
            float(late["avg_review_score"].iloc[0]) if not late.empty else 0
        )
        score_difference = abs(on_time_score - late_score)

        on_time_count = (
            int(on_time["total_orders"].iloc[0]) if not on_time.empty else 0
        )
        late_count = int(late["total_orders"].iloc[0]) if not late.empty else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Rata-rata Skor Tepat Waktu", f"{on_time_score:.2f} / 5")
        c2.metric("Rata-rata Skor Terlambat", f"{late_score:.2f} / 5")
        c3.metric("Selisih Skor Kepuasan", f"{score_difference:.2f} poin")

        st.divider()
        left, right = st.columns(2)

        with left:
            st.subheader("Rata-rata Skor Ulasan")
            fig_score = px.bar(
                delivery_summary,
                x="delivery_status",
                y="avg_review_score",
                color="delivery_status",
                text_auto=".2f",
                range_y=[0, 5],
                labels={
                    "delivery_status": "Status Pengiriman",
                    "avg_review_score": "Rata-rata Skor Ulasan",
                },
            )
            fig_score.update_layout(
                showlegend=False,
                xaxis_title="Status Pengiriman",
                yaxis_title="Rata-rata Skor (1–5)",
            )
            st.plotly_chart(fig_score, use_container_width=True)

        with right:
            st.subheader("Jumlah Pesanan per Kategori")
            count_data = pd.DataFrame(
                {
                    "Status Pengiriman": ["Tepat Waktu", "Terlambat"],
                    "Jumlah Pesanan": [on_time_count, late_count],
                }
            )
            fig_count = px.bar(
                count_data,
                x="Status Pengiriman",
                y="Jumlah Pesanan",
                color="Status Pengiriman",
                text_auto=True,
            )
            fig_count.update_layout(showlegend=False)
            st.plotly_chart(fig_count, use_container_width=True)

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
            f"**Insight:** {interpretation} Selisih rata-rata skor keduanya "
            f"adalah **{score_difference:.2f} poin**. Hasil ini menunjukkan "
            "hubungan deskriptif pada data, bukan bukti bahwa keterlambatan "
            "secara langsung menyebabkan perubahan kepuasan."
        )

        st.subheader("Ringkasan Data Pengiriman")
        display_delivery = delivery_summary.rename(
            columns={
                "delivery_status": "Status Pengiriman",
                "avg_review_score": "Rata-rata Skor Ulasan",
                "total_orders": "Jumlah Pesanan",
            }
        )
        st.dataframe(
            display_delivery.style.format(
                {"Rata-rata Skor Ulasan": "{:.2f}"}
            ),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# TAB 3 - TREN PENJUALAN
# ============================================================
with tab_sales:
    st.header("Analisis Tren Penjualan Bulanan")
    st.caption(
        "Perkembangan jumlah pesanan dan total nilai pembayaran "
        "berdasarkan tanggal pembelian."
    )

    if monthly_data.empty:
        st.warning("Data penjualan bulanan tidak tersedia.")
    else:
        min_month = monthly_data["month"].min().date()
        max_month = monthly_data["month"].max().date()

        selected_period = st.date_input(
            "Filter Periode Bulan",
            value=(min_month, max_month),
            min_value=min_month,
            max_value=max_month,
            format="DD/MM/YYYY",
        )

        if isinstance(selected_period, (tuple, list)) and len(selected_period) == 2:
            start_date, end_date = selected_period
        else:
            start_date = selected_period
            end_date = selected_period

        filtered_sales = monthly_data[
            (monthly_data["month"].dt.date >= start_date)
            & (monthly_data["month"].dt.date <= end_date)
        ].copy()

        if filtered_sales.empty:
            st.warning("Tidak ada data pada periode yang dipilih.")
        else:
            total_orders_period = filtered_sales["total_orders"].sum()
            total_revenue_period = filtered_sales["total_revenue"].sum()

            k1, k2 = st.columns(2)
            k1.metric(
                "Total Pesanan pada Periode Terpilih",
                f"{total_orders_period:,.0f}",
            )
            k2.metric(
                "Total Nilai Transaksi pada Periode Terpilih",
                f"R$ {total_revenue_period:,.2f}",
            )

            st.divider()
            st.subheader("Perkembangan Jumlah Pesanan Bulanan")

            fig_orders = px.line(
                filtered_sales,
                x="month",
                y="total_orders",
                markers=True,
                labels={
                    "month": "Bulan",
                    "total_orders": "Jumlah Pesanan",
                },
            )
            fig_orders.update_traces(line=dict(width=3))
            fig_orders.update_layout(
                xaxis_title="Bulan",
                yaxis_title="Jumlah Pesanan",
                hovermode="x unified",
            )
            st.plotly_chart(fig_orders, use_container_width=True)

            st.subheader("Perkembangan Total Nilai Transaksi Bulanan")
            fig_monthly_revenue = px.line(
                filtered_sales,
                x="month",
                y="total_revenue",
                markers=True,
                labels={
                    "month": "Bulan",
                    "total_revenue": "Total Nilai Transaksi (R$)",
                },
            )
            fig_monthly_revenue.update_traces(line=dict(width=3))
            fig_monthly_revenue.update_layout(
                xaxis_title="Bulan",
                yaxis_title="Total Nilai Transaksi (R$)",
                hovermode="x unified",
            )
            st.plotly_chart(fig_monthly_revenue, use_container_width=True)

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

            # Bulan terakhir dapat merupakan periode parsial pada dataset.
            if max_month.year == 2018 and max_month.month == 10:
                st.caption(
                    "Catatan: Oktober 2018 merupakan bulan terakhir pada dataset "
                    "dan dapat berisi data yang belum lengkap. Interpretasikan "
                    "penurunan pada bulan terakhir dengan hati-hati."
                )


# ------------------------------------------------------------
# 7. FOOTER
# ------------------------------------------------------------
st.divider()
st.caption(
    "Sumber data: Brazilian E-Commerce Public Dataset by Olist. "
    "Dashboard dibuat untuk keperluan analisis proyek data."
)

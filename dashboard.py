import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Dashboard Taksi NYC", layout="wide")

@st.cache_data
def load():
    return pd.read_csv("data.csv", parse_dates=["pickup"])

df = load()

st.title("Dashboard Perjalanan Taksi NYC (Maret 2019)")
st.markdown("""**Pertanyaan analisis**
1. Bagaimana tren pendapatan taksi per hari?
2. Wilayah (borough) mana dengan rata-rata tarif tertinggi?
3. Apakah jarak berpengaruh pada tarif, dan bagaimana tip per metode bayar?""")

# --- Filter sidebar ---
st.sidebar.header("Filter")
borough = st.sidebar.multiselect("Borough penjemputan", sorted(df["pickup_borough"].unique()),
                                 default=sorted(df["pickup_borough"].unique()))
tmin, tmax = df["pickup"].min().date(), df["pickup"].max().date()
rentang = st.sidebar.date_input("Rentang tanggal", (tmin, tmax), min_value=tmin, max_value=tmax)
if len(rentang) != 2 or not borough:
    st.warning("Pilih minimal 1 borough dan rentang tanggal (awal & akhir).")
    st.stop()

d = df[df["pickup_borough"].isin(borough)
       & df["pickup"].between(pd.Timestamp(rentang[0]), pd.Timestamp(rentang[1]) + pd.Timedelta(days=1))]
if d.empty:
    st.warning("Tidak ada data untuk filter ini.")
    st.stop()

# --- Ringkasan angka ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Jumlah perjalanan", f"{len(d):,}")
c2.metric("Total pendapatan", f"${d['total'].sum():,.0f}")
c3.metric("Rata-rata tarif", f"${d['fare'].mean():.2f}")
c4.metric("Jarak maksimum", f"{d['distance'].max():.1f} mil")

# --- Statistik deskriptif ---
st.subheader("Statistik Deskriptif")
cols = ["distance", "fare", "tip", "total"]
q = d[cols].describe().T
q["median"] = d[cols].median()
q["IQR"] = d[cols].quantile(.75) - d[cols].quantile(.25)
st.dataframe(q[["mean", "median", "std", "IQR"]].round(2))

# --- Grafik 1: tren harian ---
st.subheader("1. Tren pendapatan harian")
harian = d.set_index("pickup")["total"].resample("D").sum()
fig, ax = plt.subplots(figsize=(10, 3.5))
ax.plot(harian.index, harian.values)
ax.set(xlabel="Tanggal", ylabel="Total pendapatan (USD)", title="Pendapatan taksi per hari")
fig.autofmt_xdate()
st.pyplot(fig)
st.caption(f"Pendapatan tertinggi pada {harian.idxmax():%d %B %Y} (${harian.max():,.0f}), terendah "
           f"{harian.idxmin():%d %B %Y} (${harian.min():,.0f}). Artinya permintaan taksi berfluktuasi antar hari.")

# --- Grafik 2: per borough ---
st.subheader("2. Rata-rata tarif per borough")
per = d.groupby("pickup_borough")["fare"].mean().sort_values()
fig, ax = plt.subplots(figsize=(10, 3.5))
ax.barh(per.index, per.values)
ax.set(xlabel="Rata-rata tarif (USD)", ylabel="Borough", title="Tarif rata-rata per borough penjemputan")
st.pyplot(fig)
st.caption(f"Tertinggi: {per.index[-1]} (${per.iloc[-1]:.2f}), terendah: {per.index[0]} (${per.iloc[0]:.2f}). "
           "Artinya perjalanan dari wilayah tertentu cenderung lebih jauh/mahal.")

# --- Grafik 3: jarak vs tarif ---
st.subheader("3. Hubungan jarak dan tarif")
s = d.sample(min(len(d), 3000), random_state=0)
fig, ax = plt.subplots(figsize=(10, 4))
sns.scatterplot(data=s, x="distance", y="fare", alpha=.3, ax=ax)
ax.set(xlabel="Jarak (mil)", ylabel="Tarif (USD)", title="Jarak vs tarif (sampel 3000 titik)")
st.pyplot(fig)
r = d["distance"].corr(d["fare"])
st.caption(f"Korelasi = {r:.2f}. Makin mendekati 1, makin kuat hubungan: semakin jauh, semakin mahal.")

# --- Grafik 4: tip per metode bayar ---
st.subheader("4. Distribusi tip per metode pembayaran")
fig, ax = plt.subplots(figsize=(10, 3.5))
sns.boxplot(data=d, x="payment", y="tip", ax=ax)
ax.set(xlabel="Metode pembayaran", ylabel="Tip (USD)", title="Tip per metode pembayaran")
st.pyplot(fig)
t = d.groupby("payment")["tip"].mean().round(2).to_dict()
st.caption(f"Rata-rata tip: {t}. Tip tunai tampak 0 karena umumnya tidak tercatat; "
           "bandingkan dengan kartu kredit.")

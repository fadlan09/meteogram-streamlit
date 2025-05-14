import streamlit as st
import xarray as xr
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Realtime GFS Meteogram", layout="wide")

st.title("📡 GFS Meteogram Viewer (Realtime via NOMADS)")

# Sidebar inputs
st.sidebar.header("⚙️ Pengaturan")

# Default: hari ini - 1 agar data sudah tersedia
default_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y%m%d')

date = st.sidebar.text_input("Tanggal Model (YYYYMMDD)", value=default_date)
hour = st.sidebar.selectbox("Jam Model (UTC)", options=["00", "06", "12", "18"], index=0)

lat = st.sidebar.number_input("Latitude", value=-6.2, format="%.2f")
lon = st.sidebar.number_input("Longitude", value=106.8, format="%.2f")

if st.sidebar.button("🔍 Generate Meteogram"):

    try:
        url = f"https://nomads.ncep.noaa.gov:443/dods/gfs_0p25_1hr/gfs{date}/gfs_0p25_1hr_{hour}z"
        st.write(f"📥 Mengambil data dari: `{url}`")
        ds = xr.open_dataset(url)

        # Lokasi terdekat
        ds_loc = ds.sel(lat=lat, lon=lon, method='nearest')

        # Ambil data
        time = pd.to_datetime(ds_loc.time.values)
        temp = ds_loc.tmp2m - 273.15  # °C
        rh = ds_loc.rh2m
        cloud = ds_loc.tcdcclm
        wind_u = ds_loc.ugrd10m
        wind_v = ds_loc.vgrd10m
        wind_speed = np.sqrt(wind_u**2 + wind_v**2)
        # Ambil data curah hujan kumulatif
        rain_acc = ds_loc.apcpsfc

        # Hitung curah hujan per jam (selisih antar timestep)
        rain_hourly = rain_acc.diff(dim='time', label='upper')
        rain_hourly = rain_hourly.reindex(time=rain_acc.time[1:])  # samakan time dimension


        # Plotly chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time, y=temp, name="Temp (°C)", line=dict(color='red')))
        fig.add_trace(go.Scatter(x=time, y=rh, name="RH (%)", line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=time, y=wind_speed, name="Wind (m/s)", line=dict(color='green')))
        fig.add_trace(go.Scatter(x=time, y=cloud, name="Cloud Cover (%)", line=dict(color='gray', dash='dot')))
        fig.add_trace(go.Bar(x=time[1:], y=rain_hourly, name="Rain (mm/hr)", marker_color='cyan'))


        fig.update_layout(
            title=f"Meteogram @ Lat {lat:.2f}, Lon {lon:.2f} | GFS {date} {hour}Z",
            xaxis_title="Time (UTC)",
            yaxis_title="Value",
            height=700,
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat mengambil atau memproses data: {str(e)}")

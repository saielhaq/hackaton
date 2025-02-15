import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="RedGuard Dashboard", page_icon="✨", layout="wide")

st.title("RedGuard Dashboard")

@st.cache_data
def load_data():
    try:
        data = pd.read_csv('../data/data.csv')
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

data = load_data()

if data.empty:
    st.error("The dataset is empty. Please check the data file.")
else:
    if 'status' not in data.columns:
        st.error("The column 'status' is missing in the dataset. Please check the data file.")
    else:
        data_normal = data[data['status'] == 'normal']
        data_anomalous = data[data['status'] == 'anomalous']

        if data_normal.empty:
            st.warning("No 'normal' status entries found in the dataset.")
        if data_anomalous.empty:
            st.warning("No 'anomalous' status entries found in the dataset.")
        else:
            st.sidebar.markdown("# Blocked IPs")
            blocked_ips = data_anomalous['source_ip'].unique()
            for ip in blocked_ips:
                st.sidebar.text(ip)


        if not data_normal.empty:
            data_resampled_normal = data_normal.set_index('timestamp').resample('1h').count()
        if not data_anomalous.empty:
            data_resampled_anomalous = data_anomalous.set_index('timestamp').resample('1h').count()

        fig = go.Figure()
        if not data_normal.empty:
            fig.add_trace(go.Scatter(
                x=data_resampled_normal.index,
                y=data_resampled_normal['source_ip'],
                mode='lines',
                name='Normal Connections',
                line=dict(color='#0fd904')
            ))
        if not data_anomalous.empty:
            fig.add_trace(go.Scatter(
                x=data_resampled_anomalous.index,
                y=data_resampled_anomalous['source_ip'],
                mode='lines',
                name='Malicious Connections',
                line=dict(color='#ff034e')
            ))

        fig.update_layout(
            dragmode=False,
            xaxis_fixedrange=True,
            yaxis_fixedrange=True
        )

        total_normal = len(data_normal)
        total_anomalous = len(data_anomalous)

        bar_chart_data = pd.DataFrame({
            'Status': ['normal', 'anomalous'],
            'Count': [total_normal, total_anomalous]
        })

        bar_fig = go.Figure()
        bar_fig.add_trace(go.Bar(
            x=bar_chart_data['Status'],
            y=bar_chart_data['Count'],
            marker_color=['#0fd904', '#ff034e'],
            name='Status Counts'
        ))

        bar_fig.update_layout(
            title="Total Counts of normal and anomalous Statuses",
            xaxis_title="Status",
            yaxis_title="Count",
            dragmode=False,
            xaxis_fixedrange=True,
            yaxis_fixedrange=True
        )


        st.markdown("## Connection Status Over Time")
        st.plotly_chart(fig)

        st.markdown("---")  # Added separation line

        st.markdown("## Total Counts of Normal and Anomalous Statuses")
        st.plotly_chart(bar_fig)

        st.markdown("---")  # Added separation line

        st.markdown("## Why Use Our RedGuard AI Prototype?")
        st.markdown("### Protecting your data today secures your future.")
        st.markdown("Our RedGuard AI Prototype offers a robust solution to safeguard your valuable assets, ensuring peace of mind and enabling growth without the fear of cyber threats. By automating threat detection, RedGuard saves you time and money, allowing your team to focus on strategic goals. Invest in RedGuard to fortify your digital defenses and step confidently into a secure future.")
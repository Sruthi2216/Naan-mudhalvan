import streamlit as st
import pandas as pd
import numpy as np
import io
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt

st.set_page_config(page_title="EBPL Energy Optimization", layout="wide")
st.title("🔋 EBPL Energy Efficiency Optimization Dashboard")

# Upload CSV
uploaded_file = st.file_uploader("Upload energy usage CSV", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Check required columns
    required_cols = {'Date', 'Energy_Usage_kWh'}
    if not required_cols.issubset(df.columns):
        st.error(f"CSV must contain columns: {required_cols}")
        st.stop()

    # Preprocess
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['Hour'] = df['Date'].dt.hour
    df['DayOfWeek'] = df['Date'].dt.dayofweek
    df['IsWeekend'] = df['DayOfWeek'] >= 5
    df['RollingMean'] = df['Energy_Usage_kWh'].rolling(window=3).mean().fillna(method='bfill')

    st.write(f"Dataset contains **{df.shape[0]} rows**")

    # Anomaly sensitivity control
    contamination = st.slider("🔍 Anomaly Sensitivity (Contamination Rate)", 0.01, 0.2, 0.05, step=0.01)

    # Anomaly Detection
    X_if = df[['Energy_Usage_kWh', 'Hour']]
    iso_forest = IsolationForest(contamination=contamination, random_state=42)
    df['Anomaly'] = iso_forest.fit_predict(X_if)
    df['Anomaly'] = df['Anomaly'].apply(lambda x: "Anomaly" if x == -1 else "Normal")

    # Demand Prediction
    X = df[['DayOfWeek', 'Hour', 'IsWeekend']]
    y = df['Energy_Usage_kWh']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model_rf = RandomForestRegressor(n_estimators=100, random_state=42)
    model_rf.fit(X_train, y_train)
    y_pred = model_rf.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Recommendations
    def recommend_action(usage, threshold=100):
        return "⚠️ Turn off idle machines" if usage > threshold else "✅ All good"
    df['Recommendation'] = df['Energy_Usage_kWh'].apply(recommend_action)

    # Summary
    st.subheader("📊 Summary Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Mean Absolute Error", f"{mae:.2f} kWh")
    col2.metric("R² Score", f"{r2:.2f}")
    col3.metric("Total Anomalies Detected", df['Anomaly'].value_counts().get('Anomaly', 0))

    # Plot: Energy Usage with Anomalies
    st.subheader("📈 Energy Usage Over Time with Anomalies")
    fig, ax = plt.subplots(figsize=(14, 6), dpi=100)  # Increased DPI for clarity

    # Plot energy usage line
    ax.plot(df['Date'], df['Energy_Usage_kWh'], label='Energy Usage (kWh)', color='blue', linewidth=2)

    # Highlight anomalies
    anomalies = df[df['Anomaly'] == "Anomaly"]
    ax.scatter(anomalies['Date'], anomalies['Energy_Usage_kWh'], color='red', label='Anomalies', s=50, marker='x')

    # Labels and legend
    ax.set_title("Daily Energy Usage with Detected Anomalies", fontsize=16)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Energy Usage (kWh)", fontsize=12)
    ax.legend(fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.5)

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    # Show plot in Streamlit
    st.pyplot(fig)

    # Annotated Data Table
    st.subheader("🧾 Annotated Energy Data")
    st.dataframe(df[['Date', 'Energy_Usage_kWh', 'RollingMean', 'Recommendation', 'Anomaly']].reset_index(drop=True))

    # Download Enhanced CSV
    st.subheader("⬇️ Download Results")
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    st.download_button("Download Annotated CSV", buffer.getvalue(), file_name="energy_insights.csv", mime="text/csv")

else:
    st.info("Please upload a CSV file to begin analysis.")

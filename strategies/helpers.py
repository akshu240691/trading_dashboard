import pandas as pd
import altair as alt
from scipy.optimize import newton
import streamlit as st

# -----------------------------
# XIRR Calculation
# -----------------------------
def calculate_xirr_from_data(transactions_df):
    if transactions_df.empty or "CashFlow" not in transactions_df.columns:
        return 0.0

    transactions_df["Date"] = pd.to_datetime(transactions_df["Date"])
    transactions_df = transactions_df.sort_values("Date")

    def xnpv(rate):
        t0 = transactions_df["Date"].min()
        return sum(
            cf / ((1 + rate) ** ((d - t0).days / 365.0))
            for d, cf in zip(transactions_df["Date"], transactions_df["CashFlow"])
        )

    try:
        result = newton(lambda r: xnpv(r), 0.1)
        return result * 100
    except Exception as e:
        print("⚠️ XIRR calculation error:", e)
        return 0.0


# -----------------------------
# Portfolio Value Chart
# -----------------------------
def plot_portfolio_value_chart(data: pd.DataFrame, buy_days: pd.DataFrame):
    """
    Plot monthly portfolio value and return % as an interactive Altair chart.

    Parameters
    ----------
    data : pd.DataFrame
        Full price data (must include 'Close' column and DateTimeIndex).
    buy_days : pd.DataFrame
        Subset of data containing 'Units Bought' column and matching DateTimeIndex.
    """

    if data.empty or buy_days.empty:
        st.warning("⚠️ Not enough data to plot portfolio value chart.")
        return

    # --- Copy data to avoid modifying originals ---
    data = data.copy()

    # --- Ensure DateTime index ---
    if not isinstance(data.index, pd.DatetimeIndex):
        data.index = pd.to_datetime(data.index)
    if not isinstance(buy_days.index, pd.DatetimeIndex):
        buy_days.index = pd.to_datetime(buy_days.index)

    # --- Extract Series safely ---
    buy_units = buy_days["Units Bought"].reindex(data.index, fill_value=0).squeeze()
    close_prices = data["Close"].squeeze()

    # --- Cumulative units held over time ---
    data["Total Units"] = buy_units.cumsum()

    # --- Portfolio Value ---
    # Explicitly convert both sides to Series to avoid multi-column assignment
    data["Portfolio Value"] = (data["Total Units"].astype(float) * close_prices.astype(float)).astype(float)

    # --- Monthly portfolio values ---
    monthly_values = data.resample("M")["Portfolio Value"].last()
    monthly_returns = monthly_values.pct_change() * 100

    # --- Prepare dataframe for chart ---
    df_returns = pd.DataFrame({
        "Month": monthly_returns.index.strftime("%Y-%m"),
        "Return %": monthly_returns.values,
        "Portfolio Value": monthly_values.values
    }).dropna()

    # --- Altair Chart ---
    chart = (
        alt.Chart(df_returns)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Month:N", title="Month", sort=None),
            y=alt.Y("Return %:Q", title="Monthly Return (%)"),
            color=alt.condition(
                alt.datum["Return %"] > 0,
                alt.value("#00C49F"),  # green
                alt.value("#FF6B6B")   # red
            ),
            tooltip=[
                alt.Tooltip("Month", title="Month"),
                alt.Tooltip("Return %", title="Return (%)", format=".2f"),
                alt.Tooltip("Portfolio Value", title="Value (₹)", format=",.0f")
            ]
        )
        .properties(
            title="📊 Monthly Portfolio Returns",
            height=350
        )
    )

    st.altair_chart(chart, use_container_width=True)
    st.caption("🟢 Positive returns | 🔴 Negative returns — Hover to see value and return %")
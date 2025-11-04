import pandas as pd
import altair as alt
from scipy.optimize import newton
import streamlit as st
import numpy_financial as npf

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


def calculate_xirr_from_data_v2(transactions_df, current_value):
    """
    Version-independent XIRR calculator.
    Works even if numpy_financial.xirr is missing.
    """

    if transactions_df.empty or "Investment" not in transactions_df.columns:
        print("⚠️ Invalid transactions data for XIRR")
        return 0.0

    transactions_df["Date"] = pd.to_datetime(transactions_df["Date"])
    transactions_df["Investment"] = transactions_df["Investment"].astype(float)

    cashflows = [-x for x in transactions_df["Investment"].tolist()]
    dates = transactions_df["Date"].tolist()

    if pd.notna(current_value) and current_value > 0:
        cashflows.append(current_value)
        dates.append(pd.Timestamp.today())
    else:
        print("⚠️ Invalid or zero current value for XIRR")
        return 0.0

    # Inner function to compute NPV for a given rate
    def xnpv(rate):
        t0 = dates[0]
        return sum(
            cf / ((1 + rate) ** ((d - t0).days / 365.0))
            for cf, d in zip(cashflows, dates)
        )

    try:
        # Use Newton-Raphson to find rate that makes NPV = 0
        result = newton(lambda r: xnpv(r), 0.1)
        return round(result * 100, 2)
    except (RuntimeError, OverflowError, ValueError) as e:
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


def plot_adaptive_portfolio_chart(portfolio_df, buy_days):
    """
    Plot portfolio growth and investment points for adaptive dip-buy strategy.
    Expects:
      - portfolio_df: DataFrame with ['Date', 'Portfolio Value', 'Invested']
      - buy_days: DataFrame with ['Date', 'Close', 'Investment']
    """

    if portfolio_df.empty:
        st.warning("No portfolio data available to plot.")
        return

    # Ensure datetime format
    portfolio_df["Date"] = pd.to_datetime(portfolio_df["Date"])
    buy_days["Date"] = pd.to_datetime(buy_days["Date"])

    # Portfolio Growth Line
    portfolio_chart = alt.Chart(portfolio_df).mark_line(
        color="#4CAF50",
        strokeWidth=2
    ).encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y("Portfolio Value:Q", title="Portfolio Value (₹)"),
        tooltip=["Date:T", "Portfolio Value:Q", "Invested:Q"]
    )

    # Total Invested Line
    invested_chart = alt.Chart(portfolio_df).mark_line(
        color="#2196F3",
        strokeDash=[5, 5]
    ).encode(
        x="Date:T",
        y=alt.Y("Invested:Q", title="Invested (₹)"),
        tooltip=["Date:T", "Invested:Q"]
    )

    # Buy Points (markers)
    buy_points = alt.Chart(buy_days).mark_point(
        color="#FF5722",
        size=60,
        shape="triangle-up"
    ).encode(
        x="Date:T",
        y="Close:Q",
        tooltip=["Date:T", "Investment:Q"]
    )

    final_chart = (portfolio_chart + invested_chart + buy_points).properties(
        title="📈 Adaptive Portfolio Growth Over Time",
        height=400
    )

    st.altair_chart(final_chart, use_container_width=True)
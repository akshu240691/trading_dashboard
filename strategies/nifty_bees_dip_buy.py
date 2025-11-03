import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
from strategies.helpers import plot_portfolio_value_chart
from strategies.helpers import calculate_xirr_from_data

def run():
    st.header("📈 NiftyBees Dip-Buy Strategy")
    st.write("""
    This app simulates investing ₹5,000 on days when NiftyBees closes **0.5% or more below** 
    the previous day's close. Data is fetched directly from Yahoo Finance.
    """)
    st.sidebar.subheader("Strategy Configuration")

    ticker = st.sidebar.text_input("Enter ETF symbol:", "NIFTYBEES.NS")
    start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
    end_date = st.sidebar.date_input("End Date", pd.Timestamp.today())
    investment_per_trade = st.sidebar.number_input("Investment per trade (₹)", 5000, step=500)

    data = yf.download(ticker, start=start_date, end=end_date)
    data["Change %"] = (data["Close"] - data["Close"].shift(1)) / data["Close"].shift(1) * 100
    buy_days = data[data["Change %"] <= -0.5].copy()
    buy_days["Units Bought"] = investment_per_trade / buy_days["Close"]
    buy_days["Investment"] = investment_per_trade

    total_investment = buy_days["Investment"].sum()
    total_units = buy_days["Units Bought"].sum()
    current_price = float(data["Close"].iloc[-1])
    current_value = total_units * current_price
    profit = current_value - total_investment
    return_pct = (profit / total_investment) * 100

    # --- Prepare transactions for XIRR ---
    transactions = []

    # Outflows (money invested)
    for idx, row in buy_days.iterrows():
        transactions.append({
            "Date": pd.to_datetime(idx),
            "CashFlow": -float(row["Investment"])
        })

    # Add final portfolio value as inflow (today's date)
    transactions.append({
        "Date": pd.to_datetime(data.index[-1]),
        "CashFlow": float(current_value)
    })

    transactions_df = pd.DataFrame(transactions)

    # st.write("🧾 Debug: Transaction Cashflows for XIRR", transactions_df)

    # --- Calculate XIRR ---
    xirr_value = calculate_xirr_from_data(transactions_df)

    # --- Summary Metrics in a single row ---
    col1, col2, col3, col4,col5 = st.columns(5)
    with col1:
        st.metric("💰 Total Investment", f"₹{total_investment:,.0f}")

    with col2:
        st.metric("📈 Current Value", f"₹{current_value:,.0f}")

    with col3:
        st.metric("📊 Profit / Loss", f"₹{profit:,.0f}")

    with col4:
        st.metric("📈 Return %", f"{return_pct:.2f}%")
    with col5:
        st.metric("📈 XIRR %", f"{xirr_value:.2f}%")
    # st.metric("Total Investment", f"₹{total_investment:,.0f}")
    # st.metric("Current Value", f"₹{current_value:,.0f}")
    # st.metric("Profit / Loss", f"₹{profit:,.0f}")
    # st.metric("Return %", f"{return_pct:.2f}%")



    plot_portfolio_value_chart(data, buy_days)
    # --- Chart ---
    st.subheader("📊 Price Chart with Buy Points")

    # Reset index for Altair
    data = data.reset_index()
    buy_days = buy_days.reset_index()

    line = alt.Chart(data).mark_line(color='steelblue').encode(
        x='Date:T',
        y='Close:Q'
    )

    points = alt.Chart(buy_days).mark_point(color='red', size=80).encode(
        x='Date:T',
        y='Close:Q'
    )

    st.altair_chart(line + points, use_container_width=True)
    st.caption("🔵 NiftyBees closing price | 🔴 Red dots = Buy days")
    st.subheader("Transaction Log")
    st.dataframe(buy_days[["Close", "Change %", "Units Bought", "Investment"]])

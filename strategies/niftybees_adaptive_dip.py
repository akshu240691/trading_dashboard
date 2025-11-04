import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
from strategies.helpers import plot_portfolio_value_chart, calculate_xirr_from_data
from strategies.helpers import plot_adaptive_portfolio_chart
from strategies.helpers import calculate_xirr_from_data_v2

def run():
    st.header("📊 NiftyBees Adaptive Dip-Buy Strategy")

    st.write("""
    This strategy invests dynamically based on the **magnitude of the daily dip** in NiftyBees.
    Larger dips trigger higher investments automatically.
    """)

    # ----------------------------
    # Inputs
    # ----------------------------
    ticker = "NIFTYBEES.NS"
    start_date = st.date_input("Start Date", pd.to_datetime("2023-01-01"))
    end_date = st.date_input("End Date", pd.to_datetime("today"))

    st.markdown("### 🧩 Investment Rules")
    st.write("Define how much to invest based on % fall in NiftyBees:")

    rules = {
        ">= 0.20%": 2000,
        ">= 0.30%": 3000,
        ">= 0.40%": 4000,
        ">= 0.50%": 5000,
        ">= 0.60%": 6000,
        ">= 0.70%": 7000,
        ">= 0.80%": 8000,
        ">= 0.90%": 9000,
        ">= 1.00%": 10000,
    }

    rules_table = pd.DataFrame(list(rules.items()), columns=["Dip %", "Investment (₹)"])
    st.dataframe(rules_table, use_container_width=True)

    # ----------------------------
    # Fetch Data
    # ----------------------------
    df = yf.download(ticker, start=start_date, end=end_date)
    if df.empty:
        st.warning("⚠️ No data found for this ticker and date range.")
        return

    df = df.reset_index()

    # ✅ Approximate 3 PM price as the midpoint between Open and Close
    df["Close"] = (df["Open"] + df["Close"]) / 2

    # Calculate % change using this adjusted price
    df["Change %"] = df["Close"].pct_change() * 100

    buy_days = df[df["Change %"] < -0.50].copy()  # dips greater than 0.5%
    if buy_days.empty:
        st.warning("No buy signals found in the given period.")
        return

    # ----------------------------
    # Adaptive Investment Logic
    # ----------------------------
    sorted_rules = sorted(
        [(float(k.strip(">=% ").replace("%", "")), v) for k, v in rules.items()],
        key=lambda x: x[0]
    )

    # ----------------------------
    # Adaptive Investment Logic (Fixed ₹50,000 monthly cap)
    # ----------------------------
    sorted_rules = sorted(
        [(float(k.strip(">=% ").replace("%", "")), v) for k, v in rules.items()],
        key=lambda x: x[0]
    )

    buy_days["Investment"] = 0.0
    buy_days["Month"] = buy_days["Date"].dt.to_period("M")

    # ----------------------------
    # ✅ Adaptive Investment Logic with Strict ₹50,000 Monthly Cap (Final Safe Version)
    # ----------------------------
    sorted_rules = sorted(
        [(float(k.strip(">=% ").replace("%", "")), v) for k, v in rules.items()],
        key=lambda x: x[0]
    )

    buy_days["Investment"] = 0.0
    buy_days["Month"] = buy_days["Date"].dt.to_period("M")

    monthly_cap = 50000
    monthly_invested = {}
    investments = []

    # Sort buy_days by Date to maintain order
    buy_days = buy_days.sort_values("Date").reset_index(drop=True)

    for idx, row in buy_days.iterrows():
        fall = abs(float(row["Change %"]))
        month = str(row["Month"])  # store as string for dictionary key
        already_invested = monthly_invested.get(month, 0)

        # Determine base investment from dip %
        investment = 0
        for pct, amt in sorted_rules:
            if fall >= pct:
                investment = amt

        # Strict cap enforcement
        if already_invested + investment > monthly_cap:
            investment = max(0, monthly_cap - already_invested)

        # If cap already reached, skip
        if already_invested >= monthly_cap:
            investment = 0

        monthly_invested[month] = already_invested + investment
        investments.append(investment)

    buy_days["Investment"] = investments

    # 🧩 Final strict correction for any overshoot (due to rounding or float error)
    monthly_check = buy_days.groupby("Month")["Investment"].sum().reset_index()

    for _, row in monthly_check.iterrows():
        m = str(row["Month"])  # convert to string for consistent comparison
        total = row["Investment"]
        if total > monthly_cap:
            excess = total - monthly_cap
            month_mask = buy_days["Month"].astype(str) == m
            if month_mask.any():
                # Extract the last index as a plain integer (not array)
                last_idx = int(buy_days[month_mask].index[-1])
                current_value = float(buy_days.loc[last_idx, "Investment"])
                buy_days.loc[last_idx, "Investment"] = max(0, current_value - excess)

    # ✅ Ensure final cap compliance
    buy_days["Investment"] = buy_days["Investment"].clip(lower=0).round(2)
    monthly_check = buy_days.groupby("Month")["Investment"].sum().reset_index()

    # Log summary and small drift message if needed
    for _, row in monthly_check.iterrows():
        print(f"Month: {row['Month']}, Total Invested: ₹{row['Investment']:.2f}")

    if (monthly_check["Investment"] > monthly_cap + 1).any():
        print("⚠️ Minor rounding drift detected but capped safely.")

    # Ensure correct types
    # Ensure both are 1D Series, not DataFrames
    # --- Fix: ensure 1D Series before division ---
    investment_series = buy_days["Investment"]
    close_series = buy_days["Close"]

    # If either accidentally became a DataFrame, flatten it
    if isinstance(investment_series, pd.DataFrame):
        investment_series = investment_series.iloc[:, 0]
    if isinstance(close_series, pd.DataFrame):
        close_series = close_series.iloc[:, 0]

    buy_days["Units Bought"] = (investment_series.astype(float) / close_series.astype(float)).values

    # ----------------------------
    # Portfolio Calculation
    # ----------------------------
    total_invested = float(buy_days["Investment"].sum())
    total_units = float(buy_days["Units Bought"].sum())
    current_price = float(df["Close"].iloc[-1])
    current_value = float(total_units * current_price)
    profit = current_value - total_invested
    profit_percent = (profit / total_invested) * 100 if total_invested > 0 else 0

    # ----------------------------
    # Monthly Summary
    # ----------------------------
    buy_days["Month"] = buy_days["Date"].dt.to_period("M").astype(str)
    monthly_investment = buy_days.groupby("Month")["Investment"].sum().reset_index()

    # ----------------------------
    # Display Section
    # ----------------------------


    transactions_df = buy_days[["Date", "Investment"]].copy()
    # st.write("Transaction DF sample:", transactions_df.head())
    # st.write("🧾 Debug: Transactions DF")
    # st.dataframe(transactions_df)
    #
    # st.write("💰 Current Value:", current_value)
    xirr = calculate_xirr_from_data_v2(transactions_df, current_value)

    # xirr = calculate_xirr_from_data_v2(transactions_df)
    st.subheader("💰 Portfolio Summary")
    col1, col2, col3, col4,col5 = st.columns(5)
    col1.metric("Total Invested", f"₹{total_invested:,.0f}")
    col2.metric("Current Value", f"₹{current_value:,.0f}")
    col3.metric("Profit / Loss", f"₹{profit:,.0f}")
    col4.metric("Return %", f"{profit_percent:.2f}%")
    if xirr is not None:
        col5.metric("XIRR (%)", f"{xirr:.2f}%")
    else:
        col5.metric("XIRR (%)", "N/A")

    st.markdown("### 📈 Monthly Investment Pattern")
    chart = (
        alt.Chart(monthly_investment)
        .mark_bar(color="#2196f3")
        .encode(x="Month", y="Investment")
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)

    # ----------------------------
    # Portfolio Growth Over Time
    # ----------------------------
    portfolio_value = []
    total_units_so_far = 0
    total_invested_so_far = 0

    df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
    buy_days["Date"] = pd.to_datetime(buy_days["Date"]).dt.normalize()
    buy_dates = set(buy_days["Date"])

    for i in range(len(df)):
        date_raw = df.loc[i, "Date"]

        # Handle if it's a Series (e.g., multiple values with same index)
        if isinstance(date_raw, pd.Series):
            date_raw = date_raw.iloc[0]

        date_value = pd.to_datetime(date_raw)
        if isinstance(date_value, pd.Timestamp):
            date_value = date_value.normalize()
        if date_value in buy_dates:
            day_data = buy_days.loc[buy_days["Date"] == date_value]
            total_units_so_far += float(day_data["Units Bought"].sum())
            total_invested_so_far += float(day_data["Investment"].sum())

        value = total_units_so_far * float(df.loc[i, "Close"])
        portfolio_value.append({
            "Date": date_value,
            "Portfolio Value": value,
            "Invested": total_invested_so_far
        })

    portfolio_df = pd.DataFrame(portfolio_value)

    plot_adaptive_portfolio_chart(portfolio_df, buy_days)

    # ----------------------------
    # XIRR Calculation
    # ----------------------------
    # transactions = [
    #     {"Date": pd.to_datetime(idx), "CashFlow": -float(row["Investment"])}
    #     for idx, row in buy_days.iterrows()
    # ]
    # transactions.append({"Date": pd.to_datetime(df["Date"].iloc[-1]), "CashFlow": float(current_value)})
    # transactions_df = pd.DataFrame(transactions)
    #
    # xirr = calculate_xirr_from_data(transactions_df)
    # st.metric("📆 XIRR (Annualized Return)", f"{xirr:.2f}%")

    st.subheader("📅 Transaction Log")
    st.dataframe(
        buy_days[["Date", "Close", "Change %", "Investment", "Units Bought"]],
        use_container_width=True
    )


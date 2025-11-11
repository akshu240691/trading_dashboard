import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt
from upcoming_strategies.helpers import plot_portfolio_value_chart, calculate_xirr_from_data
from upcoming_strategies.helpers import plot_adaptive_portfolio_chart
from upcoming_strategies.helpers import calculate_xirr_from_data_v2

def run():
    st.header("📊 NiftyBees Adaptive Dip-Buy Strategy")

    st.write("""
    This strategy allocates capital dynamically based on the magnitude of daily dips in NiftyBees,
     with larger declines triggering proportionally higher investments. A strict monthly cap of ₹50,000 
     ensures disciplined deployment and prevents over-allocation. This adaptive dip-buying approach can
      potentially offer better returns than a fixed single-day SIP by taking advantage of market volatility.
    """)

    # ----------------------------
    # Inputs
    # ----------------------------
    # Nifty 50 ticker options (Yahoo Finance symbols)
    nifty50_tickers = {
        "NIFTYBEES (Default)": "NIFTYBEES.NS",
        "Reliance Industries": "RELIANCE.NS",
        "HDFC Bank": "HDFCBANK.NS",
        "ICICI Bank": "ICICIBANK.NS",
        "Infosys": "INFY.NS",
        "TCS": "TCS.NS",
        "Hindustan Unilever": "HINDUNILVR.NS",
        "ITC": "ITC.NS",
        "Kotak Mahindra Bank": "KOTAKBANK.NS",
        "Axis Bank": "AXISBANK.NS",
        "Larsen & Toubro": "LT.NS",
        "SBI": "SBIN.NS",
        "Bharti Airtel": "BHARTIARTL.NS",
        "Bajaj Finance": "BAJFINANCE.NS",
        "Asian Paints": "ASIANPAINT.NS",
        "Maruti Suzuki": "MARUTI.NS",
        "HCL Technologies": "HCLTECH.NS",
        "Nestle India": "NESTLEIND.NS",
        "UltraTech Cement": "ULTRACEMCO.NS",
        "Sun Pharma": "SUNPHARMA.NS",
        "Titan": "TITAN.NS",
        "Power Grid": "POWERGRID.NS",
        "NTPC": "NTPC.NS",
        "JSW Steel": "JSWSTEEL.NS",
        "Coal India": "COALINDIA.NS",
        "Tata Motors": "TATAMOTORS.NS",
        "Tata Steel": "TATASTEEL.NS",
        "Adani Ports": "ADANIPORTS.NS",
        "BPCL": "BPCL.NS",
        "Tech Mahindra": "TECHM.NS",
        "Eicher Motors": "EICHERMOT.NS",
        "Wipro": "WIPRO.NS",
        "Grasim": "GRASIM.NS",
        "Britannia": "BRITANNIA.NS",
        "HDFC Life": "HDFCLIFE.NS",
        "Cipla": "CIPLA.NS",
        "Apollo Hospitals": "APOLLOHOSP.NS",
        "ONGC": "ONGC.NS",
        "IndusInd Bank": "INDUSINDBK.NS",
        "SBI Life": "SBILIFE.NS",
        "UPL": "UPL.NS",
        "Divi's Labs": "DIVISLAB.NS",
        "Tata Consumer": "TATACONSUM.NS",
        "Bajaj Auto": "BAJAJ-AUTO.NS",
        "Hindalco": "HINDALCO.NS",
        "Mahindra & Mahindra": "M&M.NS",
        "Dr. Reddy's": "DRREDDY.NS",
        "Adani Enterprises": "ADANIENT.NS",
        "Hero MotoCorp": "HEROMOTOCO.NS",
    }
    selected_stock = st.selectbox("Select Stock (Nifty 50):", list(nifty50_tickers.keys()), index=0)
    ticker = nifty50_tickers[selected_stock]
    st.write(f"📈 Selected Stock: **{selected_stock}** ({ticker})")
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
    # ✅ STRICT ₹50,000 MONTHLY CAP LOGIC
    # ----------------------------
    sorted_rules = sorted(
        [(float(k.replace(">=", "").replace("%", "").strip()), v) for k, v in rules.items()],
        key=lambda x: x[0]
    )

    monthly_cap = 50000
    monthly_invested = {}
    investments = []

    buy_days = buy_days.sort_values("Date").reset_index(drop=True)
    buy_days["Month"] = buy_days["Date"].dt.to_period("M").astype(str)

    for idx, row in buy_days.iterrows():
        fall = float(abs(row["Change %"]))
        date_value = row["Date"]
        if isinstance(date_value, pd.Series):
            date_value = date_value.iloc[0]
        month = pd.to_datetime(date_value).strftime("%Y-%m")
        already = monthly_invested.get(month, 0)

        base_invest = 0
        for pct, amt in sorted_rules:
            if fall >= pct:
                base_invest = amt

        remaining = monthly_cap - already
        final_invest = min(base_invest, remaining)

        if remaining <= 0:
            final_invest = 0

        investments.append(final_invest)
        monthly_invested[month] = already + final_invest

    buy_days["Investment"] = investments

    inv = buy_days["Investment"]
    if isinstance(inv, pd.DataFrame):
        inv = inv.iloc[:, 0]

    close = buy_days["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    buy_days["Units Bought"] = inv.astype(float) / close.astype(float)

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
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
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


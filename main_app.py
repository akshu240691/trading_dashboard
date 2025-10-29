import streamlit as st
from strategies import nifty_bees_dip_buy, moving_average, rsi_strategy

st.set_page_config(page_title="Trading Strategy Dashboard", layout="wide")

st.title("📊 Backtesting Dashboard")
st.sidebar.header("Choose Strategy")

# Strategy selection
strategy = st.sidebar.selectbox(
    "Select a strategy to view:",
    (
        "NiftyBees Dip Buy",
        "Moving Average Crossover",
        "RSI Strategy"
    )
)

# Load the selected strategy
if strategy == "NiftyBees Dip Buy":
    nifty_bees_dip_buy.run()
elif strategy == "Moving Average Crossover":
    moving_average.run()
elif strategy == "RSI Strategy":
    rsi_strategy.run()
else:
    st.write("Please select a strategy from the sidebar.")

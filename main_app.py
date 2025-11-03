import streamlit as st
import importlib
import pkgutil
from strategies import *

# --- Page Configuration ---
st.set_page_config(page_title="Trading Strategy Dashboard", layout="wide")

# --- Header ---
st.title("📊 Trading Strategy Backtesting Dashboard")
st.caption("Explore and simulate trading strategies using real market data.")

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["🏠 Home", "📈 Strategies"])

# --- HOME PAGE ---
if page == "🏠 Home":
    st.header("Welcome to the Backtesting Dashboard 👋")
    st.write("""
    This platform allows you to **simulate and analyze trading strategies** 
    with real historical data.

    ### 💡 What you can do:
    - Explore multiple backtesting strategies  
    - Adjust configuration parameters (dates, investment size, etc.)  
    - View trade logs, charts, and performance metrics  

    ---
    **Future enhancements:**
    - Compare multiple strategies side-by-side  
    - Add custom or user-defined strategy scripts  
    - Portfolio & risk analytics  
    """)

    st.image(
        "https://cdn.dribbble.com/users/2382015/screenshots/5804013/stock-market-dashboard-dribbble.gif",
        use_container_width=True,
    )
    st.info("➡️ Use the **📈 Strategies** section from the sidebar to explore strategies.")

# --- STRATEGIES PAGE ---
elif page == "📈 Strategies":
    st.header("📈 Available Backtesting Strategies")

    # Dynamically list all strategy modules
    strategy_modules = {
        name: importlib.import_module(f"strategies.{name}")
        for _, name, _ in pkgutil.iter_modules(["strategies"])
    }

    # Default selection (None)
    strategy_list = ["-- Select a Strategy --"] + list(strategy_modules.keys())
    selected_strategy = st.selectbox("Choose a strategy to run:", strategy_list)

    if selected_strategy == "-- Select a Strategy --":
        st.info("""
        👈 Please select a strategy from the dropdown above to begin backtesting.

        Each strategy will:
        - Load historical market data (via Yahoo Finance)
        - Simulate trades based on defined rules
        - Display key metrics, charts, and logs
        """)
        st.image(
            "https://cdn.dribbble.com/users/1012566/screenshots/4242264/finance-dashboard.gif",
            use_container_width=True,
        )

    else:
        st.success(f"Running Strategy: **{selected_strategy.replace('_', ' ').title()}**")
        strategy_module = strategy_modules[selected_strategy]
        strategy_module.run()

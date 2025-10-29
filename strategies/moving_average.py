import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

def run():
    st.header("📈 Moving average Strategy")
    st.sidebar.subheader("Strategy Configuration")
import streamlit as st
from m import FiniteDifferences,FDExplicitEu,FDImplicitEu,FDCnEu,FDCnDo,FDCnAm
import m as tc

st.title("Option Pricing with Finite Differences")
S0 = st.sidebar.number_input("Initial Stock Price (S0)", value=50.0)
K = st.sidebar.number_input("Strike Price (K)", value=50.0)
r = st.sidebar.number_input("Interest Rate (r)", value=0.1)
T = st.sidebar.number_input("Time to Maturity (T)", value=5./12.)
sigma = st.sidebar.number_input("Volatility (sigma)", value=0.4)
Smax = st.sidebar.number_input("Maximum Stock Price (Smax)", value=100.0)
M = st.sidebar.number_input("Number of Stock Steps (M)", value=100, step=1)
N = st.sidebar.number_input("Number of Time Steps (N)", value=1000, step=1)
is_put = st.sidebar.checkbox("Is it a Put Option?", value=True)
Sbarrier = st.sidebar.number_input("Barrier Price (Sbarrier)", value=40.0)

method = st.radio("Select Pricing Method", ["Méthode explicite européen", "Méthodeimplicite européen",'Methode Crank-Nicolson européen','Methode Crank-Nicolson option exotique','Methode Crank-Nicolson américain'])
def calculate_option_price():
    option_price = None
    
    if method == "Méthode explicite européen":
        option = tc.FDExplicitEu(S0, K, r, T, sigma, Smax, M, N, is_put)
    elif method == "Méthode implicite européen":
        option = tc.FDImplicitEu(S0, K, r, T, sigma, Smax, M, N, is_put)
    elif method == "Methode Crank-Nicolson européen":
        option = tc.FDCnEu(S0, K, r, T, sigma, Smax, M, N, is_put)
    elif method == "Methode Crank-Nicolson option exotique":
        option = tc.FDCnDo(S0, K, r, T, sigma,Sbarrier, Smax, M, N, is_put)
    elif method == "Methode Crank-Nicolson américain":
        option = tc.FDCnAm( S0, K, r, T, sigma, 
            Smax, M, N, omega=1, tol=0, is_put=False)

    option_price = option.price()
    st.write(f'Option Price: {option_price:.4f}')

# Assuming you have variables like S0, K, r, T, sigma, Smax, M, N, is_put, and method defined

# Button to trigger the calculation
if st.button("Calculate Option Price"):
    calculate_option_price()


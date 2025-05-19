import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.title("💳 Debt Snowball Calculator")

st.sidebar.header("Monthly Budget")
base_budget = st.sidebar.number_input("Base Monthly Budget ($)", min_value=0.0, value=2000.0)
extra_budget = st.sidebar.number_input("Extra Snowball This Month ($)", min_value=0.0, value=0.0)
total_budget = base_budget + extra_budget

st.sidebar.markdown(f"**Total Snowball Budget:** ${total_budget:,.2f}")

st.header("Enter Your Debts")
initial_df = pd.DataFrame({
    "Debt Name": ["Credit Card A", "Credit Card B"],
    "Starting Balance": [1500, 3000],
    "Interest Rate (%)": [22.99, 19.99],
    "Minimum Payment": [50, 75]
})

debt_df = st.data_editor(initial_df, num_rows="dynamic", use_container_width=True)

if st.button("Calculate Snowball Plan"):
    month = 0
    active_debts = debt_df.copy()
    active_debts["Balance"] = active_debts["Starting Balance"]
    snowball_rows = []

    while (active_debts["Balance"] > 0).any() and month < 240:
        month += 1
        month_name = (datetime.today().replace(day=1) + pd.DateOffset(months=month-1)).strftime("%b %Y")

        # Step 1: Calculate minimum payments
        min_payments = []
        for i in active_debts.index:
            balance = active_debts.at[i, "Balance"]
            if balance > 0:
                min_payments.append(min(active_debts.at[i, "Minimum Payment"], balance))
            else:
                min_payments.append(0)

        remaining_budget = total_budget - sum(min_payments)

        # Step 2: Allocate payments
        for i in active_debts.index:
            balance = active_debts.at[i, "Balance"]
            if balance <= 0:
                continue

            rate = active_debts.at[i, "Interest Rate (%)"] / 100 / 12
            interest = balance * rate
            min_payment = min_payments[i]

            if i == active_debts[active_debts["Balance"] > 0].index[0]:
                payment = min(min_payment + remaining_budget, balance + interest)
            else:
                payment = min_payment

            principal = max(payment - interest, 0)
            new_balance = max(balance - principal, 0)

            snowball_rows.append({
                "Month": month_name,
                "Debt Name": active_debts.at[i, "Debt Name"],
                "Starting Balance": round(balance, 2),
                "Interest": round(interest, 2),
                "Principal": round(principal, 2),
                "Payment": round(payment, 2),
                "Ending Balance": round(new_balance, 2)
            })

            active_debts.at[i, "Balance"] = new_balance

    result_df = pd.DataFrame(snowball_rows)
    st.subheader("📆 Monthly Snowball Plan")
    st.dataframe(result_df, use_container_width=True)

    total_interest = result_df["Interest"].sum()
    months_needed = result_df["Month"].nunique()
    st.success(f"🎉 Debt free in {months_needed} months with ${total_interest:,.2f} in total interest paid.")

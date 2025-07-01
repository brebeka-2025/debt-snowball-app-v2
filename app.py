import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.title("Debt Snowball Calculator")

try:
    st.sidebar.header("Monthly Budget")
    base_budget = st.sidebar.number_input("Base Monthly Budget ($)", min_value=0.0, value=2000.0)
    extra_budget = st.sidebar.number_input("Extra Snowball This Month ($)", min_value=0.0, value=0.0)
    total_budget = base_budget + extra_budget
    st.sidebar.markdown(f"**Total Snowball Budget:** ${total_budget:,.2f}")
    
    st.sidebar.markdown("---")
    st.sidebar.header("Payoff Strategy")
    
    # Radio buttons for strategy selection (only one can be selected)
    strategy = st.sidebar.radio(
        "Choose your debt payoff strategy:",
        ["Snowball (Lowest Balance First)", "Avalanche (Highest Interest First)"],
        index=0,  # Default to Snowball
        help="Snowball: Pay minimum on all debts, then focus extra payments on the smallest balance. Avalanche: Pay minimum on all debts, then focus extra payments on the highest interest rate."
    )
    
    st.header("Enter Your Debts")
    
    initial_df = pd.DataFrame({
        "Debt Name": ["Credit Card A", "Credit Card B"],
        "Starting Balance": [1500, 3000],
        "Interest Rate (%)": [22.99, 19.99],
        "Minimum Payment": [50, 75]
    })
    
    debt_df = st.data_editor(initial_df, num_rows="dynamic", use_container_width=True)
    debt_df = debt_df.dropna()
    debt_df = debt_df[debt_df["Starting Balance"] > 0]
    
    # Calculate and display total minimum payments in sidebar
    if not debt_df.empty:
        total_min_payments = debt_df["Minimum Payment"].sum()
        st.sidebar.markdown("---")  # Add a separator line
        st.sidebar.markdown(f"**Total Minimum Payments:** ${total_min_payments:,.2f}")
        
        # Show remaining budget after minimum payments
        remaining_for_snowball = total_budget - total_min_payments
        if remaining_for_snowball >= 0:
            st.sidebar.markdown(f"**Available for Extra Payments:** ${remaining_for_snowball:,.2f}")
        else:
            st.sidebar.markdown(f"**Budget Shortfall:** ${abs(remaining_for_snowball):,.2f}")
            st.sidebar.warning("⚠️ Your minimum payments exceed your budget!")
        
        # Sort debts based on selected strategy for display
        if strategy == "Avalanche (Highest Interest First)":
            display_df = debt_df.sort_values("Interest Rate (%)", ascending=False).reset_index(drop=True)
            st.info("💡 **Avalanche Strategy**: Debts are prioritized by highest interest rate first to minimize total interest paid.")
        else:  # Snowball
            display_df = debt_df.sort_values("Starting Balance", ascending=True).reset_index(drop=True)
            st.info("💡 **Snowball Strategy**: Debts are prioritized by lowest balance first for quick psychological wins.")
        
        st.subheader("📋 Your Debts (Sorted by Strategy)")
        st.dataframe(display_df, use_container_width=True)
    
    if st.button("Calculate Snowball Plan"):
        with st.spinner("Calculating your payoff plan..."):
            month = 0
            active_debts = debt_df.copy()
            active_debts["Balance"] = active_debts["Starting Balance"]
            snowball_rows = []
            
            while (active_debts["Balance"] > 0).any() and month < 240:
                month += 1
                month_name = (datetime.today().replace(day=1) + pd.DateOffset(months=month-1)).strftime("%b %Y")
                
                min_payments = []
                for i in active_debts.index:
                    bal = active_debts.at[i, "Balance"]
                    min_payments.append(min(active_debts.at[i, "Minimum Payment"], bal) if bal > 0 else 0)
                
                monthly_budget = total_budget
                remaining_budget = monthly_budget
                payments = {}
                
                # Pay minimum payments first
                for i in active_debts.index:
                    bal = active_debts.at[i, "Balance"]
                    if bal <= 0:
                        payments[i] = 0
                        continue
                    pay = min(min_payments[i], remaining_budget)
                    payments[i] = pay
                    remaining_budget -= pay
                
                # Apply extra payments based on selected strategy
                sorted_debts = active_debts[active_debts["Balance"] > 0].copy()
                if strategy == "Avalanche (Highest Interest First)":
                    # Sort by highest interest rate first
                    sorted_debts = sorted_debts.sort_values("Interest Rate (%)", ascending=False)
                else:  # Snowball - lowest balance first
                    # Sort by lowest balance first
                    sorted_debts = sorted_debts.sort_values("Balance", ascending=True)
                
                for i in sorted_debts.index:
                    bal = active_debts.at[i, "Balance"]
                    if remaining_budget <= 0:
                        break
                    extra = min(bal, remaining_budget)
                    payments[i] += extra
                    remaining_budget -= extra
                
                # Process payments and calculate new balances
                for i in active_debts.index:
                    bal = active_debts.at[i, "Balance"]
                    if bal <= 0:
                        continue
                    
                    rate = active_debts.at[i, "Interest Rate (%)"] / 100 / 12
                    interest = bal * rate
                    payment = min(payments.get(i, 0), bal + interest)
                    principal = max(payment - interest, 0)
                    new_balance = max(bal - principal, 0)
                    
                    snowball_rows.append({
                        "Month": month_name,
                        "Debt Name": active_debts.at[i, "Debt Name"],
                        "Starting Balance": round(bal, 2),
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
            strategy_name = "Avalanche" if strategy == "Avalanche (Highest Interest First)" else "Snowball"
            st.success(f"🎉 Debt free in {months_needed} months using the **{strategy_name}** strategy with ${total_interest:,.2f} in total interest paid.")

except Exception as e:
    st.error(f"🚨 An error occurred: {e}")

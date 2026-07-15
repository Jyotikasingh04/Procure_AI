"""
Create Auction Page.

Lets a logged-in Buyer create a new auction via a simple form, then
returns to the Buyer Dashboard on success.
"""

import streamlit as st
import requests
from datetime import datetime

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Create Auction", layout="centered")

# --- Login guard ---
if "token" not in st.session_state or not st.session_state["token"]:
    st.warning("Please log in first.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state['token']}"}

st.title("Create Auction")

with st.form("create_auction_form"):
    title = st.text_input("Title")
    description = st.text_area("Description")
    material_name = st.text_input("Material Name")
    quantity = st.number_input("Quantity", min_value=1, step=1)
    unit = st.text_input("Unit (e.g. kg, tons)")
    base_price = st.number_input("Base Price", min_value=0.0, step=0.01)

    st.markdown("**Start Time**")
    start_date = st.date_input("Start Date")
    start_time_of_day = st.time_input("Start Time")

    st.markdown("**End Time**")
    end_date = st.date_input("End Date")
    end_time_of_day = st.time_input("End Time")

    submitted = st.form_submit_button("Create Auction")

if submitted:
    start_time = datetime.combine(start_date, start_time_of_day).isoformat()
    end_time = datetime.combine(end_date, end_time_of_day).isoformat()

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/auction/",
            headers=headers,
            json={
                "title": title,
                "description": description,
                "material_name": material_name,
                "quantity": quantity,
                "unit": unit,
                "base_price": base_price,
                "start_time": start_time,
                "end_time": end_time,
            },
            timeout=10,
        )
    except requests.exceptions.RequestException:
        st.error("Could not reach the backend. Is it running?")
    else:
        if response.status_code == 200:
            st.success("Auction created successfully. Returning to dashboard...")
            st.switch_page("pages/Buyer_Dashboard.py")
        else:
            st.error(f"Failed to create auction: {response.text}")
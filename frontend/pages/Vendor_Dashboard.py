"""
Vendor Dashboard.

Lets a logged-in Vendor browse LIVE auctions, submit a bid, and see
only their own rank and latest bid — never other vendors' bids,
names, the lowest bid amount, the winner, or buyer information.
Auto-refreshes every 3 seconds.
"""

import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

API_BASE_URL = "https://procure-ai-3lfy.onrender.com"

st.set_page_config(page_title="Vendor Dashboard", layout="wide")

# --- Global styling (visual only — no logic affected) ---
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1100px;
        }

        h1 {
            font-weight: 700;
            letter-spacing: -0.5px;
            margin-bottom: 0.25rem;
        }

        h3, h4 {
            font-weight: 600;
            letter-spacing: -0.2px;
        }

        [data-testid="stMetricLabel"] {
            font-size: 13px;
            color: #666;
            font-weight: 500;
        }

        [data-testid="stMetricValue"] {
            font-size: 20px;
            font-weight: 600;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 10px;
        }

        div[data-testid="column"] {
            padding-right: 8px;
        }

        .section-caption {
            color: #777;
            font-size: 13px;
            margin-top: -6px;
            margin-bottom: 4px;
        }

        .rank-card {
            padding: 16px;
            border-radius: 8px;
        }

        .rank-card-label {
            font-size: 13px;
            color: #666;
            font-weight: 500;
            margin-bottom: 4px;
        }

        .rank-card-value {
            font-size: 26px;
            font-weight: 700;
        }

        div.stButton > button {
            font-weight: 600;
            padding: 0.55rem 0;
        }

        hr {
            margin: 1.4rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Login guard ---
if "token" not in st.session_state or not st.session_state["token"]:
    st.warning("Please log in first.")
    st.stop()

headers = {"Authorization": f"Bearer {st.session_state['token']}"}

with st.sidebar:
    st.markdown(f"**Logged in as:** {st.session_state['role'].title()}")
    st.divider()

    if st.button("Profile", use_container_width=True):
        st.switch_page("pages/Profile.py")

    if st.button("Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("Home.py")

st.title("Vendor Procurement Dashboard")
st.markdown(
    "<div class='section-caption'>Track your live auction standing and manage your bids.</div>",
    unsafe_allow_html=True,
)

# --- List LIVE auctions ---
try:
    with st.spinner("Loading live auctions..."):
        auctions_response = requests.get(
            f"{API_BASE_URL}/api/auction/live",
            headers=headers,
            timeout=10,
        )
except requests.exceptions.RequestException:
    st.error("Could not reach the backend. Is it running?")
    st.stop()

if auctions_response.status_code != 200:
    st.error(f"Could not load live auctions: {auctions_response.text}")
    st.stop()

live_auctions = auctions_response.json()

if not live_auctions:
    st.info("No LIVE auctions right now.")
    st.stop()

with st.container(border=True):
    st.markdown("#### Auction Selection")
    st.markdown(
        "<div class='section-caption'>Choose a live auction to participate in.</div>",
        unsafe_allow_html=True,
    )

    auction_labels = [a["title"] for a in live_auctions]
    selected_index = st.selectbox(
        "Select Auction",
        options=range(len(live_auctions)),
        format_func=lambda i: auction_labels[i],
    )
    selected_auction = live_auctions[selected_index]
    selected_auction_id = selected_auction["id"]

st.divider()

# --- Auto-refresh every 3 seconds ---
st_autorefresh(interval=3000, key="vendor_dashboard_refresh")

# --- Your live status ---
try:
    with st.spinner("Loading your status..."):
        dashboard_response = requests.get(
            f"{API_BASE_URL}/api/dashboard/vendor/{selected_auction_id}",
            headers=headers,
            timeout=10,
        )
except requests.exceptions.RequestException:
    st.error("Could not reach the backend. Is it running?")
    st.stop()

if dashboard_response.status_code != 200:
    st.error(f"Could not load your dashboard: {dashboard_response.text}")
    st.stop()

data = dashboard_response.json()

if data["remaining_time_seconds"] <= 0:
    remaining_display = "Auction Closed"
else:
    hours, remainder = divmod(data["remaining_time_seconds"], 3600)
    minutes, seconds = divmod(remainder, 60)
    remaining_display = f"{hours}h {minutes}m {seconds}s"

rank = data["your_rank"]
latest_bid = data["your_latest_bid"]

# --- Rank -> color band ---
if rank is None:
    rank_color = "#6c757d"   # grey - not ranked yet
    rank_label = "Not ranked yet"
elif rank == 1:
    rank_color = "#1e7e34"   # green
    rank_label = f"Rank {rank}"
elif rank in (2, 3):
    rank_color = "#b8860b"   # amber
    rank_label = f"Rank {rank}"
else:
    rank_color = "#c0392b"   # red
    rank_label = f"Rank {rank}"

# --- Auction summary card ---
with st.container(border=True):
    st.markdown(f"### {selected_auction['title']}")
    st.markdown(
        "<div class='section-caption'>Auction Overview</div>",
        unsafe_allow_html=True,
    )

    base_price = selected_auction.get("base_price")
    base_price_display = f"₹ {float(base_price):,.2f}" if base_price is not None else "—"

    detail_col1, detail_col2, detail_col3, detail_col4, detail_col5 = st.columns(5)
    detail_col1.metric("Material", selected_auction.get("material_name", "—"))
    detail_col2.metric(
        "Quantity",
        f"{selected_auction.get('quantity', '—')} {selected_auction.get('unit', '')}".strip(),
    )
    detail_col3.metric("Base Price", base_price_display)
    detail_col4.metric("Remaining Time", remaining_display)
    detail_col5.metric("Status", selected_auction["status"].capitalize())

    st.caption(
        "Only your own ranking is shown. Competing vendors' bids remain confidential."
    )

st.divider()

# --- Your standing card ---
with st.container(border=True):
    st.markdown("#### Your Standing")
    st.markdown(
        "<div class='section-caption'>Your current position in this auction</div>",
        unsafe_allow_html=True,
    )

    standing_col1, standing_col2, standing_col3 = st.columns(3)

    with standing_col1:
        st.markdown(
            f"""
            <div class="rank-card" style="background-color: {rank_color}20;
                        border: 1px solid {rank_color};">
                <div class="rank-card-label">Current Rank</div>
                <div class="rank-card-value" style="color: {rank_color};">
                    {rank_label}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    latest_bid_display = (
        f"₹ {float(latest_bid):,.2f}" if latest_bid is not None else "No bids yet"
    )
    standing_col2.metric("Latest Bid", latest_bid_display)
    standing_col3.metric("Total Bidders", data["total_bidders"])

st.divider()

# --- Bid submission card ---
with st.container(border=True):
    st.markdown("#### Place a Bid")
    st.markdown(
        "<div class='section-caption'>Submit or update your bid for this auction</div>",
        unsafe_allow_html=True,
    )

    if data["remaining_time_seconds"] <= 0:
        st.warning("This auction has ended.")
    else:
        bid_amount = st.number_input(
            "Your Bid Amount (₹)",
            min_value=0.01,
            step=0.01,
            help="Enter the amount you wish to quote.",
        )

        submit_bid = st.button(
            "Submit Bid",
            type="primary",
            use_container_width=True,
        )

        if submit_bid:
            try:
                with st.spinner("Submitting bid..."):
                    bid_response = requests.post(
                        f"{API_BASE_URL}/api/bid/",
                        headers=headers,
                        json={
                            "auction_id": selected_auction_id,
                            "bid_amount": bid_amount,
                        },
                        timeout=10,
                    )
            except requests.exceptions.RequestException:
                st.error("Could not reach the backend. Is it running?")
            else:
                if bid_response.status_code == 200:
                    st.success("Bid submitted successfully.")
                    st.rerun()
                else:
                    try:
                        detail = bid_response.json()["detail"]
                    except Exception:
                        detail = bid_response.text
                    st.error(detail)
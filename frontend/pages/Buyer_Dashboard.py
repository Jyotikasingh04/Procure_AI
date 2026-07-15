"""
Buyer Dashboard.

Shows the live status of a selected auction (title, status, remaining
time, lowest bid, total bids, total vendors) and refreshes
automatically every 5 seconds. Below that, shows the action available
for the auction's current lifecycle stage:

  DRAFT   -> Start Auction button
  LIVE    -> End Auction button
  ENDED   -> Bid comparison table, radio winner selection, confirmation
             checkbox, Award Winner button
  AWARDED -> read-only winner info, no action buttons

When the auction is ENDED or AWARDED, an AI Procurement Summary
section is also shown. The summary is only generated when the buyer
presses the button, and is cached in session_state per auction id so
it survives the 5-second auto-refresh instead of being regenerated
every cycle.

Auction creation happens on a separate page.
"""

from datetime import datetime

import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Buyer Dashboard", layout="wide")

# --- Minimal custom CSS for polish (no logic affected) ---
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2.5rem;
            padding-bottom: 3rem;
        }
        .page-title {
            font-size: 2.25rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 0.25rem;
        }
        .page-subtitle {
            font-size: 1rem;
            color: #6b7280;
            margin-bottom: 1.5rem;
        }
        .section-heading {
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
        }
        .section-caption {
            font-size: 0.9rem;
            color: #6b7280;
            margin-bottom: 0.75rem;
        }
        .auction-name {
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 0.15rem;
        }
        .status-badge {
            display: inline-block;
            padding: 0.2rem 0.75rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .status-draft {
            background-color: rgba(107, 114, 128, 0.12);
            color: #4b5563;
        }
        .status-live {
            background-color: rgba(16, 185, 129, 0.12);
            color: #047857;
        }
        .status-ended {
            background-color: rgba(249, 115, 22, 0.12);
            color: #c2410c;
        }
        .status-awarded {
            background-color: rgba(139, 92, 246, 0.12);
            color: #6d28d9;
        }
        .subsection-label {
            font-size: 1rem;
            font-weight: 700;
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .summary-card {
            padding: 1rem 1.25rem;
            line-height: 1.6;
        }
        .vendor-name {
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
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
    st.write(f"Logged in as: {st.session_state['role'].title()}")

    if st.button("Profile", use_container_width=True):
        st.switch_page("pages/Profile.py")

    if st.button("Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("Home.py")

title_col, action_col = st.columns([3, 1])
with title_col:
    st.markdown("<div class='page-title'>Buyer Dashboard</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='page-subtitle'>Monitor and manage your reverse auctions in real time.</div>",
        unsafe_allow_html=True,
    )
with action_col:
    st.write("")
    if st.button("+ Create Auction", use_container_width=True):
        st.switch_page("pages/Create_Auction.py")

st.divider()

# --- List auctions to pick from ---
try:
    with st.spinner("Loading auctions..."):
        auctions_response = requests.get(
            f"{API_BASE_URL}/api/auction/",
            headers=headers,
            timeout=10,
        )
except requests.exceptions.RequestException:
    st.error("Could not reach the backend. Is it running?")
    st.stop()

if auctions_response.status_code != 200:
    st.error(f"Could not load auctions: {auctions_response.text}")
    st.stop()

auctions = auctions_response.json()

if not auctions:
    st.info("No auctions yet. Click 'Create Auction' above.")
    st.stop()

auction_labels = [f"{a['title']} ({a['status'].upper()})" for a in auctions]

with st.container(border=True):
    st.markdown("<div class='section-heading'>Auction Selection</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-caption'>Choose an auction to monitor</div>", unsafe_allow_html=True)
    selected_index = st.selectbox(
        "Select an auction",
        options=range(len(auctions)),
        format_func=lambda i: auction_labels[i],
        label_visibility="collapsed",
    )
selected_auction_id = auctions[selected_index]["id"]

st.divider()

# --- Auto-refresh every 5 seconds ---
st_autorefresh(interval=5000, key="buyer_dashboard_refresh")

# --- Live dashboard for selected auction ---
try:
    with st.spinner("Loading auction status..."):
        dashboard_response = requests.get(
            f"{API_BASE_URL}/api/dashboard/buyer/{selected_auction_id}",
            headers=headers,
            timeout=10,
        )
except requests.exceptions.RequestException:
    st.error("Could not reach the backend. Is it running?")
    st.stop()

if dashboard_response.status_code != 200:
    st.error(f"Could not load live dashboard: {dashboard_response.text}")
    st.stop()

data = dashboard_response.json()

status_value = data["auction_status"].lower()
status_badges = {
    "draft": "Draft",
    "live": "Live",
    "ended": "Ended",
    "awarded": "Awarded",
}
status_badge = status_badges.get(status_value, status_value.capitalize())
status_css_class = f"status-{status_value}" if status_value in status_badges else "status-draft"

hours, remainder = divmod(data["remaining_time_seconds"], 3600)
minutes, seconds = divmod(remainder, 60)

if data["remaining_time_seconds"] <= 0:
    remaining_time_display = "Auction Closed"
else:
    remaining_time_display = f"{hours}h {minutes}m {seconds}s"

if data["lowest_bid"] is None:
    lowest_bid_display = "No bids yet"
else:
    lowest_bid_display = f"₹ {float(data['lowest_bid']):,.2f}"

with st.container(border=True):
    st.markdown(f"<div class='auction-name'>{data['auction_title']}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='status-badge {status_css_class}'>{status_badge}</div>",
        unsafe_allow_html=True,
    )

    st.write("")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        with st.container(border=True):
            st.metric("Remaining Time", remaining_time_display)
    with col2:
        with st.container(border=True):
            st.metric("Lowest Bid", lowest_bid_display)
    with col3:
        with st.container(border=True):
            st.metric("Total Bids", data["total_bids"])
    with col4:
        with st.container(border=True):
            st.metric("Total Vendors", data["total_unique_vendors"])

st.divider()

# --- Lifecycle action panel, driven entirely by status_value ---
with st.container(border=True):
    st.markdown("<div class='section-heading'>Auction Actions</div>", unsafe_allow_html=True)

    if status_value == "draft":
        if st.button("Start Auction", type="primary"):
            try:
                with st.spinner("Starting auction..."):
                    start_response = requests.patch(
                        f"{API_BASE_URL}/api/auction/{selected_auction_id}/start",
                        headers=headers,
                        timeout=10,
                    )
            except requests.exceptions.RequestException:
                st.error("Could not reach the backend. Is it running?")
                st.stop()

            if start_response.status_code == 200:
                st.success("Auction has been started successfully.")
                st.rerun()
            else:
                st.error(f"Could not start auction: {start_response.text}")

    elif status_value == "live":
        if st.button("End Auction", type="primary"):
            try:
                with st.spinner("Ending auction..."):
                    end_response = requests.patch(
                        f"{API_BASE_URL}/api/auction/{selected_auction_id}/end",
                        headers=headers,
                        timeout=10,
                    )
            except requests.exceptions.RequestException:
                st.error("Could not reach the backend. Is it running?")
                st.stop()

            if end_response.status_code == 200:
                st.success("Auction ended successfully.")
                st.rerun()
            else:
                st.error(f"Could not end auction: {end_response.text}")

    elif status_value == "ended":
        st.markdown("<div class='subsection-label'>Bid Table</div>", unsafe_allow_html=True)

        try:
            with st.spinner("Loading bids..."):
                bids_response = requests.get(
                    f"{API_BASE_URL}/api/auction/{selected_auction_id}/bids",
                    headers=headers,
                    timeout=10,
                )
        except requests.exceptions.RequestException:
            st.error("Could not reach the backend. Is it running?")
            st.stop()

        if bids_response.status_code != 200:
            st.error(f"Could not load bids: {bids_response.text}")
            st.stop()

        bids = bids_response.json()

        if not bids:
            st.info("No bids were placed on this auction. Nothing to award.")
        else:
            # Sort lowest bid first for display and default selection.
            sorted_bids = sorted(bids, key=lambda b: b["bid_amount"])
            lowest_amount = sorted_bids[0]["bid_amount"]

            def _format_bid_time(raw_time: str) -> str:
                try:
                    return datetime.fromisoformat(raw_time).strftime("%d-%m-%Y %H:%M")
                except (ValueError, TypeError):
                    return raw_time

            st.dataframe(
                [
                    {
                        "Vendor Company": b["vendor_company_name"],
                        "Bid Amount": f"₹ {float(b['bid_amount']):,.2f}",
                        "Bid Time": _format_bid_time(b["bid_time"]),
                    }
                    for b in sorted_bids
                ],
                use_container_width=True,
                hide_index=True,
            )
            st.markdown(
                f"**Lowest Bid: ₹ {float(lowest_amount):,.2f} "
                f"({sorted_bids[0]['vendor_company_name']})**"
            )

            st.divider()
            st.markdown("<div class='subsection-label'>Winner Selection</div>", unsafe_allow_html=True)

            selected_bid_index = st.radio(
                "Select Winner",
                options=range(len(sorted_bids)),
                format_func=lambda i: (
                    f"{sorted_bids[i]['vendor_company_name']} "
                    f"(₹ {float(sorted_bids[i]['bid_amount']):,.2f})"
                ),
            )
            selected_winner_id = sorted_bids[selected_bid_index]["vendor_company_id"]
            selected_winner_name = sorted_bids[selected_bid_index]["vendor_company_name"]

            st.divider()
            st.markdown("<div class='subsection-label'>Confirmation</div>", unsafe_allow_html=True)

            st.markdown("<div class='section-caption'>Selected Vendor</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='vendor-name'>{selected_winner_name}</div>", unsafe_allow_html=True)

            confirmed = st.checkbox(
                f"I confirm {selected_winner_name} as the winning vendor for this auction."
            )

            st.divider()

            if st.button("Award Winner", type="primary", disabled=not confirmed):
                try:
                    with st.spinner("Awarding auction..."):
                        award_response = requests.patch(
                            f"{API_BASE_URL}/api/auction/{selected_auction_id}/award",
                            headers=headers,
                            json={"winner_company_id": selected_winner_id},
                            timeout=10,
                        )
                except requests.exceptions.RequestException:
                    st.error("Could not reach the backend. Is it running?")
                    st.stop()

                if award_response.status_code == 200:
                    st.success("Winner has been selected successfully.")
                    st.rerun()
                else:
                    st.error(f"Could not award auction: {award_response.text}")

    elif status_value == "awarded":
        winner_name = data.get("winner_company_name", "Unknown vendor")
        st.markdown("<div class='subsection-label'>Auction Result</div>", unsafe_allow_html=True)
        st.write(f"Winner Company: **{winner_name}**")
        st.write(f"Status: **{status_badge}**")

    else:
        st.info(f"No actions available for status: {status_badge}")

# --- AI Procurement Summary (ENDED or AWARDED auctions only) ---
if status_value in ("ended", "awarded"):
    st.divider()

    with st.container(border=True):
        st.markdown("<div class='section-heading'>AI Procurement Summary</div>", unsafe_allow_html=True)

        summary_key = f"ai_summary_{selected_auction_id}"

        if st.button("Generate AI Summary", use_container_width=True):
            try:
                with st.spinner("Generating summary..."):
                    summary_response = requests.get(
                        f"{API_BASE_URL}/api/auction/{selected_auction_id}/summary",
                        headers=headers,
                        timeout=10,
                    )
            except requests.exceptions.RequestException:
                st.error("Could not reach the backend. Is it running?")
            else:
                if summary_response.status_code == 200:
                    st.session_state[summary_key] = summary_response.json()["summary"]
                else:
                    st.error(f"Could not generate summary: {summary_response.text}")

        if summary_key in st.session_state:
            st.divider()
            st.markdown("<div class='subsection-label'>Procurement Analysis</div>", unsafe_allow_html=True)
            st.divider()
            with st.container(border=True):
                st.markdown(
                    f"<div class='summary-card'>{st.session_state[summary_key]}</div>",
                    unsafe_allow_html=True,
                )
            st.caption(
                "AI provides analytical insights only. Final supplier selection "
                "remains the buyer's responsibility."
            )
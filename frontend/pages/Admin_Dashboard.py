"""
Admin Dashboard.

Shows platform-wide summary metrics and lets the admin review and
approve/reject company registrations by verification status.
Only ADMIN-role users may access this page — the backend enforces
this too, but the page checks role locally to avoid showing the UI
to a non-admin who lands here directly.
"""

import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Admin Dashboard", layout="wide")

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

        .company-name {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 2px;
        }

        .company-meta {
            font-size: 13px;
            color: #555;
            margin-bottom: 2px;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
        }

        div.stButton > button {
            font-weight: 600;
        }

        hr {
            margin: 1.4rem 0;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Login guard ---
if "token" not in st.session_state or not st.session_state["token"]:
    st.warning("Please log in first.")
    st.stop()

if st.session_state.get("role") != "admin":
    st.error("You do not have access to this page.")
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

st.title("Admin Dashboard")
st.markdown(
    "<div class='section-caption'>Platform overview and company verification management.</div>",
    unsafe_allow_html=True,
)

# --- Summary metrics ---
try:
    with st.spinner("Loading dashboard..."):
        dashboard_response = requests.get(
            f"{API_BASE_URL}/api/admin/dashboard",
            headers=headers,
            timeout=10,
        )
except requests.exceptions.RequestException:
    st.error("Could not reach the backend. Is it running?")
    st.stop()

if dashboard_response.status_code != 200:
    st.error(f"Could not load dashboard: {dashboard_response.text}")
    st.stop()

metrics = dashboard_response.json()

st.markdown("#### Platform Summary")
st.markdown(
    "<div class='section-caption'>Key metrics across the platform</div>",
    unsafe_allow_html=True,
)

with st.container(border=True):
    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
    metric_col1.metric("Pending Companies", metrics["pending_companies"])
    metric_col2.metric("Approved Companies", metrics["approved_companies"])
    metric_col3.metric("Total Buyers", metrics["total_buyers"])
    metric_col4.metric("Total Vendors", metrics["total_vendors"])
    metric_col5.metric("Total Auctions", metrics["total_auctions"])

st.divider()

# --- Company review ---
st.markdown("#### Company Registrations")
st.markdown(
    "<div class='section-caption'>Review and manage company verification status</div>",
    unsafe_allow_html=True,
)

with st.container(border=True):
    status_tab_pending, status_tab_approved, status_tab_rejected = st.tabs(
        ["Pending", "Approved", "Rejected"]
    )

    def _render_company_list(status_value: str, allow_actions: bool) -> None:
        """
        Fetch and display companies for a given verification status.
        When allow_actions is True (PENDING tab), each row gets Approve
        and Reject buttons that call the corresponding PATCH endpoint.
        """
        try:
            with st.spinner("Loading companies..."):
                companies_response = requests.get(
                    f"{API_BASE_URL}/api/admin/companies",
                    headers=headers,
                    params={"status": status_value},
                    timeout=10,
                )
        except requests.exceptions.RequestException:
            st.error("Could not reach the backend. Is it running?")
            return

        if companies_response.status_code != 200:
            st.error(f"Could not load companies: {companies_response.text}")
            return

        companies = companies_response.json()

        if not companies:
            st.info(f"No {status_value} companies.")
            return

        st.write("")

        for company in companies:
            with st.container(border=True):
                info_col, action_col = st.columns([4, 1])

                with info_col:
                    st.markdown(
                        f"<div class='company-name'>{company['company_name']} "
                        f"({company['company_type'].capitalize()})</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div class='company-meta'>GST: {company['gst_number']} | "
                        f"PAN: {company['pan_number']}</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div class='company-meta'>Email: {company['official_email']} | "
                        f"Phone: {company['phone_number']}</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<div class='company-meta'>{company['address']}, {company['city']}, "
                        f"{company['state']}, {company['country']} - {company['pincode']}</div>",
                        unsafe_allow_html=True,
                    )

                if allow_actions:
                    with action_col:
                        st.write("")
                        if st.button("Approve", key=f"approve_{company['id']}", use_container_width=True, type="primary"):
                            try:
                                with st.spinner("Approving..."):
                                    approve_response = requests.patch(
                                        f"{API_BASE_URL}/api/admin/companies/{company['id']}/approve",
                                        headers=headers,
                                        timeout=10,
                                    )
                            except requests.exceptions.RequestException:
                                st.error("Could not reach the backend. Is it running?")
                            else:
                                if approve_response.status_code == 200:
                                    st.success(f"{company['company_name']} approved.")
                                    st.rerun()
                                else:
                                    st.error(approve_response.text)

                        if st.button("Reject", key=f"reject_{company['id']}", use_container_width=True):
                            try:
                                with st.spinner("Rejecting..."):
                                    reject_response = requests.patch(
                                        f"{API_BASE_URL}/api/admin/companies/{company['id']}/reject",
                                        headers=headers,
                                        timeout=10,
                                    )
                            except requests.exceptions.RequestException:
                                st.error("Could not reach the backend. Is it running?")
                            else:
                                if reject_response.status_code == 200:
                                    st.success(f"{company['company_name']} rejected.")
                                    st.rerun()
                                else:
                                    st.error(reject_response.text)
                else:
                    with action_col:
                        status_value_display = company["verification_status"].capitalize()
                        if company["verification_status"] == "approved":
                            badge_bg, badge_fg = "#1e7e3420", "#1e7e34"
                        elif company["verification_status"] == "rejected":
                            badge_bg, badge_fg = "#c0392b20", "#c0392b"
                        else:
                            badge_bg, badge_fg = "#6c757d20", "#6c757d"

                        st.markdown(
                            f"<span class='status-badge' style='background-color: {badge_bg}; "
                            f"color: {badge_fg};'>{status_value_display}</span>",
                            unsafe_allow_html=True,
                        )


    with status_tab_pending:
        _render_company_list("pending", allow_actions=True)

    with status_tab_approved:
        _render_company_list("approved", allow_actions=False)

    with status_tab_rejected:
        _render_company_list("rejected", allow_actions=False)
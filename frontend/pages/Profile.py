"""
Profile Page.

Shows the logged-in user's own company, address, and user details.
Read-only — no editing. Data comes entirely from GET /api/profile,
scoped server-side to the authenticated JWT.
"""

import streamlit as st
import requests

API_BASE_URL = "https://procure-ai-3lfy.onrender.com"

st.set_page_config(page_title="Profile", layout="wide")

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

        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 10px;
        }

        .section-caption {
            color: #777;
            font-size: 13px;
            margin-top: -6px;
            margin-bottom: 12px;
        }

        .field-label {
            font-size: 13px;
            color: #666;
            font-weight: 500;
            margin-bottom: 2px;
        }

        .field-value {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 14px;
        }

        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
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

    if st.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("Home.py")

st.title("My Profile")
st.markdown(
    "<div class='section-caption'>View your company, address and account details.</div>",
    unsafe_allow_html=True,
)

try:
    with st.spinner("Loading profile..."):
        profile_response = requests.get(
            f"{API_BASE_URL}/api/profile/",
            headers=headers,
            timeout=10,
        )
except requests.exceptions.RequestException:
    st.error("Could not reach the backend. Is it running?")
    st.stop()

if profile_response.status_code != 200:
    st.error(f"Could not load profile: {profile_response.text}")
    st.stop()

data = profile_response.json()
company = data["company"]
address = data["address"]
user = data["user"]


def _field(label: str, value) -> None:
    """Render a label/value pair with consistent typography."""
    st.markdown(
        f"<div class='field-label'>{label}</div>"
        f"<div class='field-value'>{value}</div>",
        unsafe_allow_html=True,
    )


# --- Verification status badge colors ---
verification_status = company["verification_status"]
if verification_status == "approved":
    badge_bg, badge_fg = "#1e7e3420", "#1e7e34"
elif verification_status == "rejected":
    badge_bg, badge_fg = "#c0392b20", "#c0392b"
else:
    badge_bg, badge_fg = "#6c757d20", "#6c757d"

# --- User Information ---
with st.container(border=True):
    st.markdown("#### User Information")
    st.markdown(
        "<div class='section-caption'>Your account details</div>",
        unsafe_allow_html=True,
    )

    user_col1, user_col2, user_col3 = st.columns(3)
    with user_col1:
        _field("Full Name", user["full_name"])
    with user_col2:
        _field("Email", user["email"])
    with user_col3:
        _field("Role", user["role"].capitalize())

st.divider()

# --- Company Information ---
with st.container(border=True):
    st.markdown("#### Company Information")
    st.markdown(
        "<div class='section-caption'>Registered company details</div>",
        unsafe_allow_html=True,
    )

    company_col1, company_col2, company_col3 = st.columns(3)
    with company_col1:
        _field("Company Name", company["company_name"])
    with company_col2:
        _field("Company Type", company["company_type"].capitalize())
    with company_col3:
        st.markdown(
            "<div class='field-label'>Verification Status</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<span class='status-badge' style='background-color: {badge_bg}; "
            f"color: {badge_fg};'>{verification_status.capitalize()}</span>",
            unsafe_allow_html=True,
        )

    company_col4, company_col5, company_col6 = st.columns(3)
    with company_col4:
        _field("GST Number", company["gst_number"])
    with company_col5:
        _field("PAN Number", company["pan_number"])
    with company_col6:
        _field("CIN Number", company["cin_number"] or "—")

    company_col7, company_col8 = st.columns(2)
    with company_col7:
        _field("Official Email", company["official_email"])
    with company_col8:
        _field("Phone Number", company["phone_number"])

st.divider()

# --- Address ---
with st.container(border=True):
    st.markdown("#### Address")
    st.markdown(
        "<div class='section-caption'>Registered address details</div>",
        unsafe_allow_html=True,
    )

    _field("Address", address["address"])

    address_col1, address_col2, address_col3, address_col4 = st.columns(4)
    with address_col1:
        _field("City", address["city"])
    with address_col2:
        _field("State", address["state"])
    with address_col3:
        _field("Country", address["country"])
    with address_col4:
        _field("Pincode", address["pincode"])
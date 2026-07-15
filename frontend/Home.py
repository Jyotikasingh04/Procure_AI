"""
Home Page.

Landing page for ProcureAI. Introduces the platform and routes the
visitor to either the Login or Register page.
"""

import streamlit as st

st.set_page_config(page_title="ProcureAI", layout="wide")

# --- Minimal custom CSS for polish (no logic affected) ---
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 3rem;
            padding-bottom: 3rem;
            max-width: 1100px;
        }
        .hero-title {
            text-align: center;
            font-size: 3.5rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 0.25rem;
        }
        .hero-subtitle {
            text-align: center;
            font-size: 1.15rem;
            font-weight: 500;
            color: #6b7280;
            margin-bottom: 1.5rem;
        }
        .hero-description {
            text-align: center;
            font-size: 1rem;
            color: #4b5563;
            max-width: 760px;
            margin: 0 auto 2.5rem auto;
            line-height: 1.6;
        }
        .section-heading {
            text-align: center;
            font-size: 1.5rem;
            font-weight: 700;
            margin-top: 1rem;
            margin-bottom: 1.5rem;
        }
        .feature-card {
            padding: 1.25rem;
            height: 100%;
            min-height: 180px;
            display: flex;
            flex-direction: column;
        }
        .feature-title {
            font-size: 1.15rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }
        .feature-text {
            font-size: 0.92rem;
            color: #4b5563;
            line-height: 1.5;
        }
        .cta-heading {
            text-align: center;
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
        }
        .cta-subtext {
            text-align: center;
            font-size: 0.95rem;
            color: #4b5563;
            margin-bottom: 1.5rem;
        }
        .footer-text {
            text-align: center;
            color: #9ca3af;
            font-size: 0.85rem;
            margin-top: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Hero section ---
st.markdown("<div class='hero-title'>ProcureAI</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='hero-subtitle'>AI Powered Reverse Procurement Platform</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='hero-description'>"
    "ProcureAI is an AI-assisted reverse procurement platform that enables "
    "buyers to create reverse auctions, vendors to compete through live "
    "bidding, and buyers to make informed supplier decisions using "
    "AI-generated procurement insights."
    "</div>",
    unsafe_allow_html=True,
)

st.divider()

# --- Feature cards ---
st.markdown("<div class='section-heading'>Platform Features</div>", unsafe_allow_html=True)

card_col1, card_col2, card_col3, card_col4 = st.columns(4)

with card_col1:
    with st.container(border=True):
        st.markdown(
            "<div class='feature-card'>"
            "<div class='feature-title'>Reverse Auctions</div>"
            "<div class='feature-text'>Buyers create RFQs and run private reverse "
            "auctions with invited vendors.</div>"
            "</div>",
            unsafe_allow_html=True,
        )

with card_col2:
    with st.container(border=True):
        st.markdown(
            "<div class='feature-card'>"
            "<div class='feature-title'>Live Vendor Bidding</div>"
            "<div class='feature-text'>Vendors compete in real time, seeing only "
            "their own rank and latest bid.</div>"
            "</div>",
            unsafe_allow_html=True,
        )

with card_col3:
    with st.container(border=True):
        st.markdown(
            "<div class='feature-card'>"
            "<div class='feature-title'>AI Procurement Summary</div>"
            "<div class='feature-text'>AI analyzes participation and bid trends "
            "to support buyer decisions.</div>"
            "</div>",
            unsafe_allow_html=True,
        )

with card_col4:
    with st.container(border=True):
        st.markdown(
            "<div class='feature-card'>"
            "<div class='feature-title'>Secure Role-Based Access</div>"
            "<div class='feature-text'>JWT authentication with distinct Buyer, "
            "Vendor, and Admin roles.</div>"
            "</div>",
            unsafe_allow_html=True,
        )

st.divider()

# --- Call to action section (heading, subtext, and buttons together) ---
with st.container(border=True):
    st.write("")
    st.markdown(
        "<div class='cta-heading'>Ready to get started?</div>"
        "<div class='cta-subtext'>Log in to your account or register as a new "
        "Buyer or Vendor to begin using ProcureAI.</div>",
        unsafe_allow_html=True,
    )

    button_col1, button_col2, button_col3 = st.columns([1, 1, 1])
    with button_col2:
        inner_col1, inner_col2 = st.columns(2)
        with inner_col1:
            if st.button("Login", type="primary", use_container_width=True):
                st.switch_page("pages/login.py")
        with inner_col2:
            if st.button("Register", use_container_width=True):
                st.switch_page("pages/Register.py")

    st.write("")

st.divider()

# --- Footer ---
st.markdown(
    "<div class='footer-text'>ProcureAI | AI Powered Reverse Procurement Platform</div>",
    unsafe_allow_html=True,
)
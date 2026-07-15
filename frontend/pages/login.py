"""
Login Page.

Authenticates against the FastAPI backend, stores the JWT and derived
user info in session state, and redirects to the correct dashboard
based on role.
"""

import streamlit as st
import requests
from jose import jwt

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Login", layout="centered")

# --- Minimal custom CSS for polish (no logic affected) ---
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 3rem;
            padding-bottom: 3rem;
        }
        .auth-title {
            text-align: center;
            font-size: 2.75rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 0.25rem;
        }
        .auth-subtitle {
            text-align: center;
            font-size: 1.05rem;
            font-weight: 500;
            color: #6b7280;
            margin-bottom: 1.5rem;
        }
        .auth-heading {
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
        }
        .auth-footer-text {
            text-align: center;
            color: #9ca3af;
            font-size: 0.9rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Centered form via three-column layout ---
left, center, right = st.columns([1, 2, 1])

with center:
    st.markdown("<div class='auth-title'>ProcureAI</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='auth-subtitle'>AI Powered Reverse Procurement Platform</div>",
        unsafe_allow_html=True,
    )
    st.caption("Sign in to access your procurement dashboard.")

    st.write("")

    with st.container(border=True):
        st.write("")
        st.markdown(
            "<div class='auth-heading' style='text-align:center;'>Sign In</div>",
            unsafe_allow_html=True,
        )

        email = st.text_input(
            "Email",
            placeholder="name@company.com",
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
        )

        st.write("")

        login_clicked = st.button(
            "Login",
            type="primary",
            use_container_width=True,
        )

        st.write("")

        if login_clicked:
            try:
                with st.spinner("Authenticating..."):
                    response = requests.post(
                        f"{API_BASE_URL}/api/auth/login",
                        json={"email": email, "password": password},
                        timeout=10,
                    )
            except requests.exceptions.RequestException:
                st.error("Could not connect to the server.")
            else:
                if response.status_code != 200:
                    st.error("Invalid email or password.")
                else:
                    token = response.json()["access_token"]

                    # The token was just issued to us by our own backend, so we
                    # decode it here purely to read its claims (role, company_id)
                    # without re-verifying the signature.
                    payload = jwt.decode(token, key="", options={"verify_signature": False})

                    # Clear any state left over from a previous session/user
                    # before writing the new one. Deleting keys individually
                    # (rather than st.session_state.clear()) avoids rerun
                    # edge cases where a widget tries to reattach to a key
                    # that was wiped mid-cycle.
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]

                    st.session_state["token"] = token
                    st.session_state["role"] = payload.get("role")
                    st.session_state["company_id"] = payload.get("company_id")
                    st.session_state["user_id"] = payload.get("sub")

                    st.success("Login successful.")

                    if st.session_state["role"] == "buyer":
                        st.switch_page("pages/Buyer_Dashboard.py")
                    elif st.session_state["role"] == "vendor":
                        st.switch_page("pages/Vendor_Dashboard.py")
                    elif st.session_state["role"] == "admin":
                        st.switch_page("pages/Admin_Dashboard.py")
                    else:
                        st.error("Unknown role. Cannot redirect.")

    st.write("")
    st.markdown(
        "<div class='auth-footer-text'>Don't have an account? Register below.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    st.divider()

    if st.button("Register", use_container_width=True):
     st.switch_page("pages/Register.py")
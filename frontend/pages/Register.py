"""
Register Page.

Registers a new Buyer or Vendor company against the FastAPI backend.
Field set and endpoint paths match CompanyRegisterRequest and the
routes declared in app/routers/auth.py exactly - no invented fields.
"""

import streamlit as st
import requests

API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Register", layout="centered")

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
        .section-heading {
            font-size: 1.15rem;
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

left, center, right = st.columns([1, 2, 1])

with center:
    st.markdown("<div class='auth-title'>ProcureAI</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='auth-subtitle'>AI Powered Reverse Procurement Platform</div>",
        unsafe_allow_html=True,
    )
    st.caption("Create your account to start using ProcureAI.")

    st.write("")

    company_type = st.radio(
        "Company Type",
        options=["Buyer", "Vendor"],
        horizontal=True,
    )
    st.caption("Choose the type of organization you are registering.")

    st.write("")

    # --- Company Information ---
    with st.container(border=True):
        st.write("")
        st.markdown("<div class='section-heading'>Company Information</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name", placeholder="Acme Pvt Ltd")
        with col2:
            gst_number = st.text_input("GST Number", placeholder="22AAAAA0000A1Z5")

        col3, col4 = st.columns(2)
        with col3:
            pan_number = st.text_input("PAN Number", placeholder="AAAAA0000A")
        with col4:
            cin_number = st.text_input("CIN Number (optional)", placeholder="U12345MH2020PTC000000")

        col5, col6 = st.columns(2)
        with col5:
            official_email = st.text_input("Official Email", placeholder="contact@company.com")
        with col6:
            phone_number = st.text_input("Phone Number", placeholder="+91 98765 43210")

        st.write("")

    st.write("")

    # --- Address Information ---
    with st.container(border=True):
        st.write("")
        st.markdown("<div class='section-heading'>Address Information</div>", unsafe_allow_html=True)

        address = st.text_area("Address", placeholder="Street, building, area")

        col7, col8 = st.columns(2)
        with col7:
            city = st.text_input("City", placeholder="Mumbai")
        with col8:
            state = st.text_input("State", placeholder="Maharashtra")

        col9, col10 = st.columns(2)
        with col9:
            country = st.text_input("Country", value="India")
        with col10:
            pincode = st.text_input("Pincode", placeholder="400001")

        st.caption("Provide the registered business address.")

        st.write("")

    st.write("")

    # --- User Account Information ---
    with st.container(border=True):
        st.write("")
        st.markdown("<div class='section-heading'>User Account Information</div>", unsafe_allow_html=True)

        full_name = st.text_input("Full Name", placeholder="Your full name")
        email = st.text_input("Email (used for login)", placeholder="name@company.com")

        col11, col12 = st.columns(2)
        with col11:
            password = st.text_input("Password", type="password", placeholder="Enter your password")
        with col12:
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")

        st.caption("These credentials will be used to sign in.")

        st.write("")

        register_clicked = st.button(
            "Register",
            type="primary",
            use_container_width=True,
        )

        st.write("")

        if register_clicked:
            # Required fields — cin_number is intentionally excluded,
            # since the backend schema marks it optional.
            required_fields = {
                "Company Name": company_name,
                "GST Number": gst_number,
                "PAN Number": pan_number,
                "Official Email": official_email,
                "Phone Number": phone_number,
                "Address": address,
                "City": city,
                "State": state,
                "Country": country,
                "Pincode": pincode,
                "Full Name": full_name,
                "Email": email,
                "Password": password,
                "Confirm Password": confirm_password,
            }
            missing_fields = [label for label, value in required_fields.items() if not value.strip()]

            if missing_fields:
                st.error(f"Please fill in: {', '.join(missing_fields)}.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                payload = {
                    "company_name": company_name,
                    "gst_number": gst_number,
                    "pan_number": pan_number,
                    "cin_number": cin_number or None,
                    "official_email": official_email,
                    "phone_number": phone_number,
                    "address": address,
                    "city": city,
                    "state": state,
                    "country": country,
                    "pincode": pincode,
                    "full_name": full_name,
                    "email": email,
                    "password": password,
                }

                endpoint = (
                    "/api/auth/register/buyer"
                    if company_type == "Buyer"
                    else "/api/auth/register/vendor"
                )

                try:
                    with st.spinner("Creating account..."):
                        response = requests.post(
                            f"{API_BASE_URL}{endpoint}",
                            json=payload,
                            timeout=10,
                        )
                except requests.exceptions.RequestException:
                    st.error("Could not connect to the server.")
                else:
                    if response.status_code == 200:
                        st.success("Registration successful. Redirecting to login...")
                        st.switch_page("pages/Login.py")
                    else:
                        st.error(response.text)

    st.write("")
    st.markdown(
        "<div class='auth-footer-text'>Already have an account? Log in below.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    st.divider()

    if st.button("Login", use_container_width=True):
        st.switch_page("pages/Login.py")
# ProcureAI – AI Powered Reverse Procurement Platform

## Overview

ProcureAI is an AI-powered reverse procurement platform that enables organizations to conduct secure reverse auctions for raw material procurement. Buyers can create auctions, invite vendors to participate, monitor live bidding, and award contracts efficiently. Vendors compete by submitting confidential bids while only viewing their own ranking, ensuring a fair and transparent procurement process.

The platform also integrates AI-generated procurement summaries to assist buyers in making informed purchasing decisions.

---

# Features

## Buyer

* Register and log in securely
* Create reverse auctions
* Start and end auctions
* View live auction statistics
* Monitor vendor participation
* Award winning vendor
* Generate AI procurement summary
* View complete bid history

---

## Vendor

* Register company
* Participate in live auctions
* Receive email notifications when auctions go live
* Submit multiple bids
* View only:

  * Current Rank
  * Latest Bid
  * Remaining Time
* Cannot view:

  * Competitor bids
  * Vendor identities
  * Lowest bid amount
  * Buyer information

---

## Admin

* Review company registrations
* Approve companies
* Reject companies
* Manage verified buyers and vendors

---

## AI Features

* Gemini AI Procurement Summary
* Bid participation analysis
* Pricing trend analysis
* Procurement recommendations

---

## Email Notifications

Automatic email notifications are sent when:

* Auction becomes LIVE
* Winning vendor is awarded

---

# Technology Stack

## Frontend

* Streamlit

## Backend

* FastAPI

## Database

* PostgreSQL (Neon)

## ORM

* SQLAlchemy

## Authentication

* JWT Authentication

## AI

* Google Gemini API

## Email Service

* Gmail SMTP

## Deployment

* Streamlit Community Cloud
* Render
* Neon PostgreSQL

---

# System Workflow

1. Buyer registers
2. Vendor registers
3. Admin approves companies
4. Buyer creates auction
5. Buyer starts auction
6. Vendors receive email notification
7. Vendors place confidential bids
8. Buyer monitors auction
9. Buyer awards winner
10. Winning vendor receives email
11. Buyer generates AI summary

---

# Project Structure

```
ProcureAI
│
├── frontend
│   ├── Home.py
│   ├── pages
│   │   ├── Login.py
│   │   ├── Register.py
│   │   ├── Buyer_Dashboard.py
│   │   ├── Vendor_Dashboard.py
│   │   ├── Admin_Dashboard.py
│   │   └── Profile.py
│
├── backend
│   ├── app
│   │   ├── routers
│   │   ├── services
│   │   ├── models
│   │   ├── schemas
│   │   ├── database
│   │   ├── config
│   │   └── core
│
├── requirements.txt
└── README.md
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/<your-username>/ProcureAI.git
```

```bash
cd ProcureAI
```

---

# Backend Setup

Create virtual environment

```bash
python -m venv venv
```

Activate environment

Windows

```bash
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create `.env`

```env
DATABASE_URL=your_database_url

SECRET_KEY=your_secret_key

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=60

GEMINI_API_KEY=your_gemini_key

SMTP_SERVER=smtp.gmail.com

SMTP_PORT=587

SMTP_EMAIL=your_email@gmail.com

SMTP_PASSWORD=your_app_password
```

Run backend

```bash
uvicorn app.main:app --reload
```

---

# Frontend Setup

```bash
cd frontend
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run Streamlit

```bash
streamlit run Home.py
```

---

# Deployment

## Backend

* Render

## Database

* Neon PostgreSQL

## Frontend

* Streamlit Community Cloud

---

# Security

* JWT Authentication
* Password hashing using bcrypt
* Role-based authorization
* Buyer/Vendor/Admin access separation
* Confidential bidding
* Secure SMTP credentials using environment variables

---

# Future Enhancements

* Real-time WebSocket bidding
* PDF purchase order generation
* Multi-buyer organizations
* Vendor performance analytics
* Dashboard analytics
* SMS and WhatsApp notifications
* File upload for RFQs
* Audit logs
* Procurement reports

---

# Contributors

**Jyotika Singh**

AI Powered Reverse Procurement Platform

---

# License

This project is developed for educational and demonstration purposes.

import os
import io
import time
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import database
import pdf_extractor
import ml_engine
import report_generator
import sample_generator

# Page Configuration
st.set_page_config(
    page_title="ExpenseAI - Intelligent Expense Tracker",
    page_icon="₹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema
database.init_db()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_PDF_PATH = os.path.join(BASE_DIR, "sample_bank_statement.pdf")
if not os.path.exists(SAMPLE_PDF_PATH):
    try:
        sample_generator.generate_sample_pdf(SAMPLE_PDF_PATH)
    except Exception as e:
        print("Sample PDF error:", e)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
REPORTS_FOLDER = os.path.join(BASE_DIR, "reports")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

# Custom Fintech CSS Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
}

.num-mono {
    font-family: 'JetBrains Mono', monospace;
    font-feature-settings: "tnum";
}

/* Metric Card Container */
.metric-box {
    background: #ffffff;
    border: 1px solid rgba(226, 232, 240, 0.9);
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
    transition: all 0.2s ease;
}
.metric-box:hover {
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
    transform: translateY(-1px);
}
.metric-label {
    font-size: 0.76rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.metric-value {
    font-size: 1.55rem;
    font-weight: 800;
    margin: 4px 0;
    font-family: 'JetBrains Mono', monospace;
}
.metric-sub {
    font-size: 0.78rem;
    color: #64748b;
}

/* Financial Health Banner */
.health-banner {
    background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #3b82f6 100%);
    color: white;
    border-radius: 14px;
    padding: 22px 26px;
    margin-bottom: 24px;
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.22);
}

/* Category Badges */
.cat-badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 9999px;
    font-size: 0.74rem;
    font-weight: 600;
    background: #f1f5f9;
    color: #334155;
    border: 1px solid #e2e8f0;
}
.badge-income {
    background: #ecfdf5;
    color: #065f46;
    border: 1px solid #a7f3d0;
}
.badge-expense {
    background: #fef2f2;
    color: #991b1b;
    border: 1px solid #fecaca;
}

/* Pulse Beacon */
.pulse-beacon {
    display: inline-block;
    width: 8px;
    height: 8px;
    background-color: #10b981;
    border-radius: 50%;
    margin-right: 6px;
}
</style>
""", unsafe_allow_html=True)

# Session State for Authentication
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

def do_logout():
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_email = None
    st.rerun()

# -------------------------------------------------------------
# Authentication Screen (if not logged in)
# -------------------------------------------------------------
if not st.session_state.user_id:
    st.markdown("""
    <div style="text-align: center; margin-top: 30px; margin-bottom: 20px;">
        <div style="display:inline-flex; width: 52px; height: 52px; background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); color: white; border-radius: 14px; align-items: center; justify-content: center; font-weight: 800; font-size: 1.6rem; box-shadow: 0 4px 14px rgba(37,99,235,0.3);">₹</div>
        <h1 style="font-size: 1.85rem; font-weight: 800; margin-top: 10px; color: #0f172a; letter-spacing: -0.4px;">ExpenseAI</h1>
        <p style="color: #64748b; font-size: 0.95rem;">Intelligent Expense Tracker with Personalized Spending Insights</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register, tab_demo = st.tabs(["🔐 Sign In", "✨ Create Account", "🚀 Instant Demo Access"])

        with tab_login:
            st.markdown("#### Sign in to your financial vault")
            with st.form("login_form"):
                email = st.text_input("Email Address", placeholder="you@example.com").strip()
                password = st.text_input("Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

                if submitted:
                    if not email or not password:
                        st.error("Please provide both email and password.")
                    else:
                        user = database.verify_user(email, password)
                        if user:
                            st.session_state.user_id = user["id"]
                            st.session_state.user_name = user["name"]
                            st.session_state.user_email = user["email"]
                            st.success(f"Welcome back, {user['name']}!")
                            time.sleep(0.4)
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")

        with tab_register:
            st.markdown("#### Create your private account")
            with st.form("register_form"):
                reg_name = st.text_input("Full Name", placeholder="Rahul Sharma").strip()
                reg_email = st.text_input("Email Address", placeholder="you@example.com").strip()
                reg_password = st.text_input("Password (min 4 characters)", type="password", placeholder="••••••••")
                reg_submitted = st.form_submit_button("Register & Initialize Vault", use_container_width=True, type="primary")

                if reg_submitted:
                    if not reg_name or not reg_email or not reg_password:
                        st.error("All fields are required.")
                    elif len(reg_password) < 4:
                        st.error("Password must be at least 4 characters.")
                    else:
                        user = database.create_user(reg_name, reg_email, reg_password)
                        if user:
                            st.session_state.user_id = user["id"]
                            st.session_state.user_name = user["name"]
                            st.session_state.user_email = user["email"]
                            st.success("Account created successfully!")
                            time.sleep(0.4)
                            st.rerun()
                        else:
                            st.error("An account with this email already exists.")

        with tab_demo:
            st.markdown("#### Instant Review Access")
            st.info("Click below to instantly log in as a Demo User with pre-populated sample transactions and ML models.")
            if st.button("🚀 Explore Demo Account Now", use_container_width=True, type="primary"):
                demo_email = "demo@expenseai.local"
                demo_user = database.get_user_by_email(demo_email)
                if not demo_user:
                    demo_user = database.create_user("Demo User", demo_email, "demo123")
                    # Populate demo user with sample statement transactions
                    if os.path.exists(SAMPLE_PDF_PATH):
                        res = pdf_extractor.extract_from_pdf(SAMPLE_PDF_PATH)
                        if res["success"]:
                            database.add_transactions_bulk(demo_user["id"], res["transactions"])
                            # Set default budgets
                            curr_mth = datetime.now().strftime("%Y-%m")
                            database.set_budget(demo_user["id"], "Food & Dining", curr_mth, 3000.0)
                            database.set_budget(demo_user["id"], "Shopping & Retail", curr_mth, 2000.0)
                            database.set_budget(demo_user["id"], "Travel & Transport", curr_mth, 1500.0)
                            database.set_budget(demo_user["id"], "Bills & Utilities", curr_mth, 2500.0)

                st.session_state.user_id = demo_user["id"]
                st.session_state.user_name = demo_user["name"]
                st.session_state.user_email = demo_user["email"]
                st.rerun()

        st.markdown("""
        <div style="margin-top: 24px; padding: 12px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 0.8rem; color: #475569; text-align: center;">
            🔒 <strong>On-Device Encryption:</strong> Passwords securely hashed with PBKDF2. Data is safely stored in local SQLite.
        </div>
        """, unsafe_allow_html=True)

    st.stop()

# -------------------------------------------------------------
# Authenticated App Shell & Navigation
# -------------------------------------------------------------
user_id = st.session_state.user_id
user_name = st.session_state.user_name
user_email = st.session_state.user_email
curr_date = datetime.now().strftime("%Y-%m-%d")
curr_month = datetime.now().strftime("%Y-%m")

# Sidebar
with st.sidebar:
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap: 10px; padding: 6px 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 16px;">
        <div style="width: 38px; height: 38px; background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); color: white; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.15rem;">₹</div>
        <div>
            <div style="font-weight: 800; font-size: 1.1rem; color: #0f172a; line-height: 1.1;">ExpenseAI</div>
            <div style="font-size: 0.72rem; color: #64748b; font-weight: 600; text-transform: uppercase;">Smart Wealth OS</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    menu_selection = st.radio(
        "Navigation",
        [
            "📊 Financial Overview",
            "📥 Upload Statement",
            "📑 Transaction Ledger",
            "🎯 Budget Management",
            "🧠 AI Financial Insights",
            "📄 Reports & Downloads"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    avatar_char = (user_name or "U")[0].upper()
    display_name = user_name or "User"
    display_email = user_email or ""

    st.markdown(f"""
    <div style="padding: 8px 10px; background: #f1f5f9; border-radius: 8px; font-size: 0.75rem; color: #334155; margin-bottom: 14px;">
        <span class="pulse-beacon"></span>
        <strong>Engine Online</strong> &bull; SQLite Storage
    </div>
    <div style="display: flex; align-items: center; gap: 8px;">
        <div style="width: 32px; height: 32px; border-radius: 8px; background: #3b82f6; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700;">
            {avatar_char}
        </div>
        <div style="flex: 1; overflow: hidden;">
            <div style="font-weight: 700; font-size: 0.85rem; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">{display_name}</div>
            <div style="font-size: 0.72rem; color: #64748b; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">{display_email}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sign Out", use_container_width=True, type="secondary"):
        do_logout()

# -------------------------------------------------------------
# Page 1: Financial Overview (Dashboard)
# -------------------------------------------------------------
if menu_selection == "📊 Financial Overview":
    st.markdown(f"### Financial Overview")
    st.caption("Real-time summary of your income, expenses, and AI spending patterns")

    summary = database.get_dashboard_summary(user_id)
    budget_data = database.get_budget_utilization(user_id, curr_month)
    tx_all = database.get_transactions(user_id)
    df_all = pd.DataFrame(tx_all) if tx_all else pd.DataFrame()
    overspend_analysis = ml_engine.generate_overspending_solutions(df_all, budget_data)
    patterns = ml_engine.analyze_spending_patterns(df_all)

    # Health Rating Hero Banner
    burn_info = f"₹{patterns['daily_avg']:,.2f}/day" if patterns.get("has_data") else "N/A"
    peak_day = patterns.get("top_spending_day", "N/A") if patterns.get("has_data") else "N/A"
    status_icon = "⚠️" if overspend_analysis["has_overspending"] else "✓"
    status_note = "Action required: Category overspending detected. View AI recovery action plan." if overspend_analysis["has_overspending"] else "Optimal financial trajectory: Spending remains within established benchmarks."

    st.markdown(f"""
    <div class="health-banner">
        <div style="display:flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
            <div>
                <span style="font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.8px; opacity: 0.85; font-weight: 700;">Financial Health Intelligence &bull; AI AUDIT</span>
                <div style="font-size: 1.45rem; font-weight: 800; margin-top: 4px;">{overspend_analysis['health_grade']}</div>
                <div style="font-size: 0.85rem; opacity: 0.95; margin-top: 4px;">{status_icon} {status_note}</div>
            </div>
            <div style="display: flex; gap: 20px; align-items: center;">
                <div>
                    <div style="font-size: 0.72rem; opacity: 0.8; text-transform: uppercase; font-weight: 700;">Daily Burn Rate</div>
                    <div style="font-size: 1.25rem; font-weight: 800;" class="num-mono">{burn_info}</div>
                </div>
                <div style="height: 35px; width: 1px; background: rgba(255,255,255,0.25);"></div>
                <div>
                    <div style="font-size: 0.72rem; opacity: 0.8; text-transform: uppercase; font-weight: 700;">Peak Outflow Day</div>
                    <div style="font-size: 1.25rem; font-weight: 800;">{peak_day}</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 5 Summary Metric Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Total Income</div>
            <div class="metric-value" style="color: #10b981;">+₹{summary['total_income']:,.2f}</div>
            <div class="metric-sub">Verified credits</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Total Expenses</div>
            <div class="metric-value" style="color: #ef4444;">-₹{summary['total_expense']:,.2f}</div>
            <div class="metric-sub">{len(summary['category_breakdown'])} Active Categories</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        bal_color = "#2563eb" if summary["balance"] >= 0 else "#ef4444"
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Net Balance</div>
            <div class="metric-value" style="color: {bal_color};">₹{summary['balance']:,.2f}</div>
            <div class="metric-sub">Liquid capital</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        rate = f"{(summary['balance'] / summary['total_income'] * 100):.1f}%" if summary["total_income"] > 0 else "0.0%"
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Savings Velocity</div>
            <div class="metric-value" style="color: #8b5cf6;">₹{summary['monthly_savings']:,.2f}</div>
            <div class="metric-sub">{rate} Savings Rate</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Transactions</div>
            <div class="metric-value" style="color: #0f172a;">{summary['total_transactions']}</div>
            <div class="metric-sub">Total ledger count</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    ch1, ch2 = st.columns([1.6, 1.2])
    with ch1:
        st.markdown("##### 📈 Income & Expense Trend")
        if summary["monthly_trend"]:
            m_df = pd.DataFrame(summary["monthly_trend"])
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=m_df["month"], y=m_df["income"], name="Income (₹)",
                marker_color="#10b981", marker_line_width=0
            ))
            fig.add_trace(go.Bar(
                x=m_df["month"], y=m_df["expense"], name="Expense (₹)",
                marker_color="#3b82f6", marker_line_width=0
            ))
            fig.update_layout(
                barmode="group", height=280, margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No transaction timeline available yet.")

    with ch2:
        st.markdown("##### 🍩 Category Breakdown")
        if summary["category_breakdown"]:
            c_df = pd.DataFrame(summary["category_breakdown"])
            fig_pie = px.pie(
                c_df, values="total", names="category", hole=0.68,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_pie.update_layout(
                height=280, margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2),
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expense categorization data yet.")

    # Two column bottom section: Budget Health + Top Payees
    b_col, p_col = st.columns(2)
    with b_col:
        st.markdown(f"##### 🎯 Monthly Budget Health ({curr_month})")
        if budget_data["items"]:
            for b in budget_data["items"][:5]:
                spent = b["spent"]
                alloc = b["allocated"]
                pct = min(100.0, b["percentage"])
                col_prog = "#ef4444" if b["percentage"] >= 100 else ("#f59e0b" if b["percentage"] >= 80 else "#10b981")
                st.write(f"**{b['category']}**: ₹{spent:,.0f} / ₹{alloc:,.0f} ({b['percentage']}%)")
                st.progress(pct / 100.0)
        else:
            st.caption("No monthly budgets set yet. Set them in Budget Management.")

    with p_col:
        st.markdown("##### 🏢 Top Payees & Merchants")
        top_payees = database.get_top_payees(user_id, limit=5)
        if top_payees:
            for payee in top_payees:
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 7px 12px; background: #f8fafc; border-radius: 8px; margin-bottom: 6px;">
                    <div>
                        <strong>{payee.get('description', 'Unknown')}</strong>
                        <div style="font-size: 0.75rem; color: #64748b;">{payee.get('tx_count', 1)} transactions</div>
                    </div>
                    <div style="font-weight: 700; color: #ef4444;" class="num-mono">₹{payee.get('total_amount', 0):,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("No payee volume recorded yet.")

# -------------------------------------------------------------
# Page 2: Statement Upload
# -------------------------------------------------------------
elif menu_selection == "📥 Upload Statement":
    st.markdown("### Bank Statement Upload (Multi-Strategy AI Parser)")
    st.caption("Upload digital monthly PDF statements from PhonePe, Google Pay, Paytm, SBI, HDFC, ICICI, etc.")

    up_col1, up_col2 = st.columns([1.3, 0.9])

    with up_col1:
        st.markdown("##### Select Bank Statement (PDF)")
        uploaded_pdf = st.file_uploader(
            "Choose a PDF file", type=["pdf"],
            help="Supports tabular and narrative digital statements with selectable text"
        )

        if uploaded_pdf is not None:
            save_path = os.path.join(UPLOAD_FOLDER, f"{user_id}_{int(time.time())}_{uploaded_pdf.name}")
            with open(save_path, "wb") as f:
                f.write(uploaded_pdf.getbuffer())

            with st.spinner("Extracting transactions, debits, credits, and contacts..."):
                ext_result = pdf_extractor.extract_from_pdf(save_path)

            if ext_result["success"]:
                tx_list = ext_result["transactions"]
                meta = ext_result.get("metadata", {})
                st.success(f"✓ Extracted {len(tx_list)} transactions successfully!")

                st.markdown(f"""
                <div style="padding: 12px 16px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; margin: 12px 0;">
                    <strong>Detected Source:</strong> {meta.get('provider', 'Digital Bank Statement')} &bull;
                    <strong>Account / ID:</strong> {meta.get('account', 'N/A')} &bull;
                    <strong>Cycle:</strong> {meta.get('period', 'Current Period')}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("##### ✏️ Review & Adjust Extracted Transactions Before Saving")
                df_extracted = pd.DataFrame(tx_list)

                # Editable Table
                edited_df = st.data_editor(
                    df_extracted,
                    column_config={
                        "date": st.column_config.DateColumn("Date", required=True),
                        "description": st.column_config.TextColumn("Description / Payee", required=True),
                        "category": st.column_config.SelectboxColumn("Category", options=database.ALL_CATEGORIES, required=True),
                        "type": st.column_config.SelectboxColumn("Type", options=["expense", "income"], required=True),
                        "amount": st.column_config.NumberColumn("Amount (₹)", min_value=0.01, format="₹%.2f", required=True)
                    },
                    use_container_width=True,
                    num_rows="dynamic"
                )

                if st.button("💾 Confirm & Save to Financial Vault", type="primary", use_container_width=True):
                    final_txs = edited_df.to_dict(orient="records")
                    # Clean date formats
                    for t in final_txs:
                        if isinstance(t["date"], (pd.Timestamp, datetime)):
                            t["date"] = t["date"].strftime("%Y-%m-%d")
                    added, duplicates = database.add_transactions_bulk(user_id, final_txs)
                    st.success(f"Saved {added} new transactions! ({duplicates} duplicates skipped)")
                    time.sleep(1.0)
                    st.rerun()

            else:
                if ext_result.get("is_scanned"):
                    st.warning("⚠️ Scanned Image PDF Detected: This document contains images rather than digital text. OCR support is not included in this edition.")
                else:
                    st.error(f"Extraction failed: {ext_result.get('message')}")

    with up_col2:
        st.markdown("##### ℹ️ Instructions & Verified Formats")
        st.markdown("""
        * **Digital Statements:** Supports PhonePe UPI statements, Google Pay exports, SBI, HDFC, ICICI, Axis, and standard banks.
        * **Duplicate Protection:** Uploading overlapping statements will automatically prevent duplicate entries via SHA-256 fingerprinting.
        * **Smart Categorization:** Automatically routes contact transfers (e.g. `Paid to Varun`) to `Personal & P2P Transfers` and gifts (`Received from Daddy`) to `Allowances & Gifts`.
        """)

        st.markdown("##### 🧪 Test with Sample Statement")
        if os.path.exists(SAMPLE_PDF_PATH):
            with open(SAMPLE_PDF_PATH, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                "📥 Download Pre-Generated Sample Statement (PDF)",
                data=pdf_bytes,
                file_name="sample_bank_statement.pdf",
                mime="application/pdf",
                use_container_width=True
            )

# -------------------------------------------------------------
# Page 3: Transaction Ledger
# -------------------------------------------------------------
elif menu_selection == "📑 Transaction Ledger":
    st.markdown("### Transaction Ledger")
    st.caption("Search, filter, edit, or manually record transactions")

    # Action Toolbar: Add Manual + Smart Rules
    with st.expander("➕ Record New Transaction Manually", expanded=False):
        with st.form("manual_tx_form"):
            tc1, tc2, tc3 = st.columns(3)
            with tc1:
                m_date = st.date_input("Date", value=datetime.now())
                m_type = st.selectbox("Type", ["expense", "income"])
            with tc2:
                m_desc = st.text_input("Description / Payee", placeholder="e.g. Swiggy, Amazon, Metro")
                m_cat = st.selectbox("Category", database.ALL_CATEGORIES)
            with tc3:
                m_amt = st.number_input("Amount (₹)", min_value=0.01, step=10.0, format="%.2f")
                st.write("")
                st.write("")
                save_manual = st.form_submit_button("Record Transaction", type="primary", use_container_width=True)

            if save_manual:
                if not m_desc or m_amt <= 0:
                    st.error("Please provide valid description and amount.")
                else:
                    success, msg = database.add_transaction(
                        user_id, m_date.strftime("%Y-%m-%d"), m_desc, m_cat, m_type, m_amt
                    )
                    if success:
                        st.success("Transaction recorded successfully!")
                        st.rerun()
                    else:
                        st.warning(msg)

    with st.expander("⚙️ Smart Category Automation Rules (Contact Mapping)", expanded=False):
        st.caption("Automatically map recurring contacts or merchants (e.g. Map 'Daddy' to 'Allowances & Gifts', or 'Varun' to 'Personal & P2P Transfers').")
        with st.form("rule_form"):
            rc1, rc2, rc3 = st.columns([1.5, 1.5, 1])
            with rc1:
                r_keyword = st.text_input("Contact or Merchant Keyword", placeholder="e.g. Varun, Chai Point")
            with rc2:
                r_cat = st.selectbox("Assign to Category", database.ALL_CATEGORIES)
            with rc3:
                r_reclass = st.checkbox("Reclassify existing", value=True)
                r_submit = st.form_submit_button("Create Rule", type="primary", use_container_width=True)

            if r_submit and r_keyword:
                s, m = database.save_category_rule(user_id, r_keyword, r_cat, reclassify_existing=r_reclass)
                st.success(m)
                st.rerun()

    # Filters
    fc1, fc2, fc3 = st.columns([2, 1, 1])
    with fc1:
        search_kw = st.text_input("🔍 Search transactions", placeholder="Filter by merchant, contact, notes...").strip()
    with fc2:
        cat_filter = st.selectbox("Filter Category", ["All Categories"] + database.ALL_CATEGORIES)
    with fc3:
        type_filter = st.selectbox("Filter Type", ["All Types", "Expense Only", "Income Only"])

    tx_type_param = "expense" if type_filter == "Expense Only" else ("income" if type_filter == "Income Only" else "all")
    cat_param = "all" if cat_filter == "All Categories" else cat_filter

    txs = database.get_transactions(
        user_id,
        category=cat_param,
        tx_type=tx_type_param,
        search=search_kw
    )

    st.write(f"**Showing {len(txs)} Records**")

    if txs:
        df_tx = pd.DataFrame(txs)
        display_df = df_tx[["id", "date", "description", "category", "type", "amount"]].copy()
        display_df["amount"] = display_df["amount"].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(
            display_df,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "date": st.column_config.TextColumn("Date", width="medium"),
                "description": st.column_config.TextColumn("Description / Payee"),
                "category": st.column_config.TextColumn("Category"),
                "type": st.column_config.TextColumn("Type"),
                "amount": st.column_config.TextColumn("Amount")
            },
            use_container_width=True,
            hide_index=True
        )

        # Delete transaction tool
        with st.expander("🗑️ Delete a Transaction"):
            del_id = st.number_input("Enter Transaction ID to delete", min_value=1, step=1)
            if st.button("Permanently Delete Transaction", type="secondary"):
                if database.delete_transaction(del_id, user_id):
                    st.success(f"Transaction #{del_id} deleted.")
                    st.rerun()
                else:
                    st.error("Transaction not found or unauthorized.")
    else:
        st.info("No transactions match the selected filter criteria.")

# -------------------------------------------------------------
# Page 4: Budget Management
# -------------------------------------------------------------
elif menu_selection == "🎯 Budget Management":
    st.markdown("### Budget Management & Guardrails")
    st.caption("Set category spending limits, track utilization pace, and prevent overspending")

    sel_month = st.selectbox("Audit Month", [curr_month, "2026-10", "2026-09", "2026-08", "2026-07"])
    util = database.get_budget_utilization(user_id, sel_month)

    # Top summary metrics
    bc1, bc2, bc3, bc4 = st.columns(4)
    with bc1:
        st.metric("Total Allocated", f"₹{util['total_budget']:,.2f}")
    with bc2:
        st.metric("Total Spent", f"₹{util['total_spent']:,.2f}")
    with bc3:
        st.metric("Remaining Limit", f"₹{util['remaining_budget']:,.2f}")
    with bc4:
        st.metric("Overall Pace", f"{util['overall_percentage']}%")

    st.progress(min(100.0, util["overall_percentage"]) / 100.0)
    st.markdown("<br>", unsafe_allow_html=True)

    # Set Budget Form
    with st.expander("⚙️ Set / Adjust Category Budget Limit", expanded=False):
        with st.form("set_budget_form"):
            sb1, sb2 = st.columns(2)
            with sb1:
                b_cat = st.selectbox("Category", database.DEFAULT_BUDGET_CATEGORIES)
            with sb2:
                b_limit = st.number_input("Monthly Limit (₹)", min_value=0.0, step=500.0, value=2500.0)
            b_submit = st.form_submit_button("Save Budget Limit", type="primary", use_container_width=True)

            if b_submit:
                database.set_budget(user_id, b_cat, sel_month, b_limit)
                st.success(f"Budget for {b_cat} set to ₹{b_limit:,.2f}")
                st.rerun()

    # Category Grid Cards
    st.markdown("##### Category Budget Utilization")
    b_cols = st.columns(3)
    for idx, item in enumerate(util["items"]):
        with b_cols[idx % 3]:
            cat_name = item["category"]
            allocated = item["allocated"]
            spent = item["spent"]
            remaining = item["remaining"]
            pct = item["percentage"]

            status_style = "border: 1px solid #e2e8f0;"
            if item["status"] == "exceeded":
                status_style = "border: 1px solid #fecaca; background: #fffdfd;"
            elif item["status"] == "warning":
                status_style = "border: 1px solid #fde68a; background: #fffdfa;"

            st.markdown(f"""
            <div style="padding: 16px; border-radius: 12px; {status_style} margin-bottom: 14px;">
                <div style="font-weight: 800; font-size: 1rem; color: #0f172a;">{cat_name}</div>
                <div style="font-size: 0.78rem; color: #64748b;">Allocated: ₹{allocated:,.2f}</div>
                <div style="display:flex; justify-content:space-between; margin-top: 8px; font-size: 0.85rem;">
                    <span style="color: #ef4444; font-weight: 700;">Spent: ₹{spent:,.2f}</span>
                    <span style="color: {'#10b981' if remaining >= 0 else '#ef4444'}; font-weight: 700;">
                        {'Left: ₹' if remaining >= 0 else 'Over: ₹'}{abs(remaining):,.2f}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(min(100.0, pct) / 100.0)
            if item["status"] == "exceeded":
                st.error(f"⚠️ Overspending Alert: Exceeded by {pct}%")
            elif item["status"] == "warning":
                st.warning(f"🔔 Caution: {pct}% utilized")

# -------------------------------------------------------------
# Page 5: AI Financial Insights (ML Engine)
# -------------------------------------------------------------
elif menu_selection == "🧠 AI Financial Insights":
    st.markdown("### AI Financial Insights & Machine Learning Analytics")
    st.caption("Unsupervised anomaly detection, Pandas spending decomposition, and personalized recommendations")

    all_txs = database.get_transactions(user_id)
    if not all_txs:
        st.info("Insufficient historical data available. Upload bank statements to generate ML insights.")
    else:
        df = pd.DataFrame(all_txs)
        budget_data = database.get_budget_utilization(user_id, curr_month)
        patterns = ml_engine.analyze_spending_patterns(df)
        unusual = ml_engine.detect_unusual_transactions(df)
        comparison = ml_engine.compare_monthly_spending(df)
        recs = ml_engine.generate_personalized_recommendations(df, budget_data)

        # 1. Personalized Recommendations
        st.markdown("##### 💡 Personalized AI Financial Recommendations")
        for r in recs:
            bg_col = "#ecfdf5" if r["severity"] == "success" else ("#fffbeb" if r["severity"] == "warning" else "#eff6ff")
            b_border = "#a7f3d0" if r["severity"] == "success" else ("#fde68a" if r["severity"] == "warning" else "#bfdbfe")
            st.markdown(f"""
            <div style="padding: 14px 18px; background: {bg_col}; border: 1px solid {b_border}; border-radius: 10px; margin-bottom: 10px;">
                <strong style="font-size: 0.95rem;">{r['title']}</strong>
                <p style="margin: 4px 0 0 0; font-size: 0.88rem; color: #334155;">{r['message']}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. Behavioral Patterns (Pandas)
        st.markdown("##### 📈 Spending Pattern Decomposition (Pandas Engine)")
        pc1, pc2, pc3, pc4 = st.columns(4)
        with pc1:
            st.metric("Avg Per Transaction", f"₹{patterns.get('avg_per_tx', 0):,.2f}")
        with pc2:
            st.metric("Daily Average Outflow", f"₹{patterns.get('daily_avg', 0):,.2f}")
        with pc3:
            st.metric("Top Outflow Day", str(patterns.get("top_spending_day", "N/A")))
        with pc4:
            st.metric("Micro-Payments (≤ ₹50)", f"{patterns.get('micro_count', 0)} Taps", f"₹{patterns.get('micro_total', 0):,.2f}")

        st.markdown("<br>", unsafe_allow_html=True)

        # 3. Isolation Forest Outliers
        st.markdown("##### 🔍 Unusual Transaction Detection (Isolation Forest ML)")
        st.caption("Statistical anomalies identified through scikit-learn Isolation Forest algorithm based on transaction size and timing.")

        if unusual:
            df_unusual = pd.DataFrame(unusual)
            st.dataframe(
                df_unusual[["date", "description", "category", "amount", "reason"]],
                column_config={
                    "date": "Date",
                    "description": "Description",
                    "category": "Category",
                    "amount": st.column_config.NumberColumn("Amount", format="₹%.2f"),
                    "reason": "Anomaly Reason"
                },
                use_container_width=True,
                hide_index=True
            )
            st.caption("⚠️ **Notice:** These transactions deviate statistically from your median spending patterns. This is an informational anomaly, not a confirmed fraudulent transaction.")
        else:
            st.success("✓ No abnormal statistical outliers detected in your expense history.")

        st.markdown("<br>", unsafe_allow_html=True)

        # 4. Month-over-Month Comparison
        st.markdown("##### 📅 Month-over-Month Spending Comparison")
        if comparison.get("has_comparison"):
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                st.metric(f"Previous ({comparison['prev_month']})", f"₹{comparison['prev_total']:,.2f}")
            with mc2:
                st.metric(f"Latest ({comparison['latest_month']})", f"₹{comparison.get('latest_total', comparison.get('curr_total', 0)):,.2f}")
            with mc3:
                shift_val = comparison.get("diff_amount", 0)
                shift_pct = comparison.get("percent_change", 0)
                st.metric("Net Shift", f"₹{shift_val:,.2f}", f"{shift_pct:+.1f}%", delta_color="inverse")

            changes = comparison.get("category_comparison") or comparison.get("category_changes")
            if changes:
                st.markdown("###### Category Variance Table")
                df_changes = pd.DataFrame(changes)
                st.dataframe(
                    df_changes[["category", "previous", "current", "difference", "percent_change"]],
                    column_config={
                        "category": "Category",
                        "previous": st.column_config.NumberColumn("Previous (₹)", format="₹%.2f"),
                        "current": st.column_config.NumberColumn("Latest (₹)", format="₹%.2f"),
                        "difference": st.column_config.NumberColumn("Variance (₹)", format="₹%.2f"),
                        "percent_change": st.column_config.NumberColumn("Shift %", format="%.1f%%")
                    },
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info(comparison.get("message", "Need transactions from at least 2 distinct months to generate comparative analysis."))

# -------------------------------------------------------------
# Page 6: Reports & Downloads
# -------------------------------------------------------------
elif menu_selection == "📄 Reports & Downloads":
    st.markdown("### Financial Audit Reports & Exports")
    st.caption("Generate official PDF statements and spreadsheet CSV exports")

    rc1, rc2 = st.columns(2)
    with rc1:
        rep_month = st.selectbox("Filter Month", ["All Time", curr_month, "2026-10", "2026-09"])
    with rc2:
        rep_cat = st.selectbox("Filter Category", ["All Categories"] + database.ALL_CATEGORIES)

    mth_val = "" if rep_month == "All Time" else rep_month
    cat_val = "all" if rep_cat == "All Categories" else rep_cat

    # Action buttons for download
    st.markdown("##### 📥 Instant File Downloads")
    d_col1, d_col2 = st.columns(2)

    with d_col1:
        csv_data = report_generator.generate_csv_report(user_id, month=mth_val, category=cat_val)
        st.download_button(
            label="📊 Download Spreadsheet Ledger (CSV)",
            data=csv_data,
            file_name=f"Expense_Ledger_{user_id}_{mth_val or 'all'}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with d_col2:
        pdf_path = report_generator.generate_pdf_report(
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            month=mth_val,
            category=cat_val
        )
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📑 Download Audit Statement Report (PDF)",
                data=pdf_bytes,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                use_container_width=True
            )

    # Executive Scorecard Preview
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### 🛡️ Overspending Diagnosis & Action Plan")
    tx_rep = database.get_transactions(user_id, category=cat_val)
    if mth_val:
        tx_rep = [t for t in tx_rep if t["date"].startswith(mth_val)]

    df_rep = pd.DataFrame(tx_rep) if tx_rep else pd.DataFrame()
    bud_util = database.get_budget_utilization(user_id, mth_val or curr_month)
    sol_analysis = ml_engine.generate_overspending_solutions(df_rep, bud_util)

    if sol_analysis["solutions"]:
        for sol in sol_analysis["solutions"]:
            st.markdown(f"""
            <div style="padding: 12px 16px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; margin-bottom: 8px;">
                <strong>{sol['title']}</strong> &bull; <span style="color: #d97706; font-weight: 700;">{sol['impact']}</span>
                <p style="margin: 4px 0 0 0; font-size: 0.85rem; color: #475569;">{sol['description']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✓ No critical budget overspending detected for this audit period.")

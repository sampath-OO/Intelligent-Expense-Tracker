import os
import sys
import time
import io
from datetime import datetime, date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configure Streamlit Page
st.set_page_config(
    page_title="Intelligent Expense Tracker",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Core imports
import database
import pdf_extractor
import ml_engine
import report_generator
import sample_generator

# Initialize database schema
database.init_db()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
REPORTS_FOLDER = os.path.join(BASE_DIR, "reports")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

# Generate sample bank statement PDF if missing
SAMPLE_PDF_PATH = os.path.join(BASE_DIR, "sample_bank_statement.pdf")
if not os.path.exists(SAMPLE_PDF_PATH):
    try:
        sample_generator.generate_sample_pdf(SAMPLE_PDF_PATH)
    except Exception as e:
        print("Sample PDF generation error:", e)

# -------------------------------------------------------------
# Premium Styling: Fintech Navy & Emerald Theme
# -------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
        max-width: 1250px;
    }

    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    /* Metric Boxes */
    .metric-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .metric-label {
        font-size: 0.76rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 800;
        margin-top: 4px;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-sub {
        font-size: 0.74rem;
        color: #94a3b8;
        margin-top: 4px;
    }

    /* Health Score Banner */
    .health-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
        color: white;
        padding: 22px 26px;
        border-radius: 14px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.12);
        margin-bottom: 20px;
    }

    /* Pulse Beacon */
    .pulse-beacon {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 0 rgba(16, 185, 129, 0.4);
        animation: pulse 2s infinite;
        margin-right: 6px;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); }
        70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    .num-mono {
        font-family: 'JetBrains Mono', monospace;
    }

    /* Form Buttons */
    .stButton > button[kind="primary"] {
        background-color: #2563eb;
        border-color: #2563eb;
        font-weight: 600;
        border-radius: 8px;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8;
        border-color: #1d4ed8;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Session State & Auth Handling
# -------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

def do_login(user):
    st.session_state.authenticated = True
    st.session_state.user_id = user["id"]
    st.session_state.user_name = user["name"]
    st.session_state.user_email = user["email"]

def do_logout():
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_email = None
    st.rerun()

# -------------------------------------------------------------
# Authentication Screen
# -------------------------------------------------------------
if not st.session_state.authenticated:
    auth_col1, auth_col2, auth_col3 = st.columns([1, 1.3, 1])
    with auth_col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); color: white; border-radius: 14px; font-size: 26px; font-weight: 800; margin-bottom: 12px; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);">
                ₹
            </div>
            <h2 style="margin: 0; font-weight: 800; color: #0f172a; letter-spacing: -0.5px;">ExpenseAI</h2>
            <p style="color: #64748b; font-size: 0.9rem; margin-top: 4px;">Autonomous Personal Wealth & Spending Intelligence</p>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register, tab_guest = st.tabs(["🔐 Sign In", "✨ Create Account", "⚡ Guest Demo"])

        with tab_login:
            with st.form("login_form"):
                l_email = st.text_input("Email Address", placeholder="e.g. user@example.com").strip().lower()
                l_pass = st.text_input("Password", type="password")
                l_submit = st.form_submit_button("Sign In to Financial Vault", type="primary", use_container_width=True)

                if l_submit:
                    if not l_email or not l_pass:
                        st.error("Please enter both email and password.")
                    else:
                        user = database.verify_user(l_email, l_pass)
                        if user:
                            do_login(user)
                            st.success(f"Welcome back, {user['name']}!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")

        with tab_register:
            with st.form("register_form"):
                r_name = st.text_input("Full Name", placeholder="e.g. John Doe")
                r_email = st.text_input("Email Address", placeholder="e.g. john@example.com").strip().lower()
                r_pass = st.text_input("Password (min 4 characters)", type="password")
                r_submit = st.form_submit_button("Create My Account", type="primary", use_container_width=True)

                if r_submit:
                    if not r_name or not r_email or not r_pass:
                        st.error("All fields are required.")
                    elif len(r_pass) < 4:
                        st.error("Password must be at least 4 characters.")
                    else:
                        new_user = database.create_user(r_name, r_email, r_pass)
                        if new_user:
                            do_login(new_user)
                            st.success(f"Account registered! Welcome, {new_user['name']}!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("An account with this email address already exists.")

        with tab_guest:
            st.markdown("""
            <div style="padding: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; margin-bottom: 14px;">
                <p style="margin: 0; font-size: 0.88rem; color: #475569;">
                    <strong>Instant Sandbox Access:</strong> Launch a pre-configured demo portfolio loaded with realistic multi-month bank statements, budget guardrails, and ML insights.
                </p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 Launch Instant Demo Session", type="primary", use_container_width=True):
                demo_email = "demo_executive@expenseai.local"
                demo_pass = "demo1234"
                demo_user = database.get_user_by_email(demo_email)
                if not demo_user:
                    demo_user = database.create_user("Executive Portfolio", demo_email, demo_pass)
                    if os.path.exists(SAMPLE_PDF_PATH) and demo_user:
                        ext = pdf_extractor.extract_from_pdf(SAMPLE_PDF_PATH)
                        if ext["success"]:
                            database.add_transactions_bulk(demo_user["id"], ext["transactions"])
                            curr_mth = datetime.now().strftime("%Y-%m")
                            database.set_budget(demo_user["id"], "Food & Dining", curr_mth, 6000.0)
                            database.set_budget(demo_user["id"], "Shopping & Retail", curr_mth, 5000.0)
                            database.set_budget(demo_user["id"], "Bills & Utilities", curr_mth, 8000.0)
                            database.set_budget(demo_user["id"], "Travel & Transport", curr_mth, 4000.0)
                if demo_user:
                    do_login(demo_user)
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
user_name = st.session_state.user_name or "User"
user_email = st.session_state.user_email or "user@local"
curr_date = datetime.now().strftime("%Y-%m-%d")
curr_month = datetime.now().strftime("%Y-%m")

# Sidebar
with st.sidebar:
    st.markdown("""
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
            "🏢 Merchants & Payees",
            "🎯 Budget Management",
            "🧠 AI Financial Insights",
            "📄 AI Audit & Reports"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    avatar_char = (user_name or "U")[0].upper()

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
            <div style="font-weight: 700; font-size: 0.85rem; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">{user_name}</div>
            <div style="font-size: 0.72rem; color: #64748b; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">{user_email}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Sign Out", use_container_width=True, type="secondary"):
        do_logout()

# =============================================================
# Page 1: Financial Overview (High-Level Cash Flow & KPIs ONLY)
# =============================================================
if menu_selection == "📊 Financial Overview":
    st.markdown("### Executive Financial Overview")
    st.caption("Real-time snapshot of your income, expenses, and cash flow trajectory")

    summary = database.get_dashboard_summary(user_id)
    budget_data = database.get_budget_utilization(user_id, curr_month)
    tx_all = database.get_transactions(user_id)
    df_all = pd.DataFrame(tx_all) if tx_all else pd.DataFrame()
    overspend_analysis = ml_engine.compute_financial_health_audit(df_all, budget_data)
    patterns = ml_engine.analyze_spending_patterns(df_all)

    # Health Rating Hero Banner
    burn_info = f"₹{patterns['daily_avg']:,.2f}/day" if patterns.get("has_data") else "N/A"
    peak_day = patterns.get("top_spending_day", "N/A") if patterns.get("has_data") else "N/A"
    status_icon = "⚠️" if overspend_analysis["has_overspending"] else "✓"
    status_note = "Action required: Budget overruns detected. View AI Audit & Reports for recovery roadmap." if overspend_analysis["has_overspending"] else "Optimal financial trajectory: Cash flow remains within healthy discipline benchmarks."

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
            <div class="metric-sub">Liquid capital retained</div>
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
            <div class="metric-label">Ledger Volume</div>
            <div class="metric-value" style="color: #0f172a;">{summary['total_transactions']}</div>
            <div class="metric-sub">Total recorded records</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # High-level Cash Flow Charts
    ch1, ch2 = st.columns([1.6, 1.2])
    with ch1:
        st.markdown("##### 📈 Cash Flow Trajectory (Income vs Outflow Trend)")
        if summary["monthly_trend"]:
            m_df = pd.DataFrame(summary["monthly_trend"])
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=m_df["month"], y=m_df["income"], name="Income Credits (₹)",
                marker_color="#10b981", marker_line_width=0
            ))
            fig.add_trace(go.Bar(
                x=m_df["month"], y=m_df["expense"], name="Expense Debits (₹)",
                marker_color="#3b82f6", marker_line_width=0
            ))
            fig.update_layout(
                barmode="group", height=290, margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No transaction timeline available yet. Upload statements to visualize trends.")

    with ch2:
        st.markdown("##### 🍩 Category Outflow Share")
        if summary["category_breakdown"]:
            c_df = pd.DataFrame(summary["category_breakdown"])
            fig_pie = px.pie(
                c_df, values="total", names="category", hole=0.68,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_pie.update_layout(
                height=290, margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2),
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expense categorization data yet.")

    # Executive Cash Flow Vitality Indicators
    st.markdown("##### 🛡️ Cash Flow Vitality & Liquidity Multipliers")
    v1, v2, v3 = st.columns(3)
    coverage = (summary["total_income"] / summary["total_expense"]) if summary["total_expense"] > 0 else 0.0
    with v1:
        st.markdown(f"""
        <div style="padding: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;">
            <div style="font-size: 0.76rem; font-weight: 700; color: #64748b;">INFLOW / OUTFLOW COVERAGE</div>
            <div style="font-size: 1.3rem; font-weight: 800; color: {'#16a34a' if coverage >= 1.2 else ('#eab308' if coverage >= 1.0 else '#dc2626')};">{coverage:.2f}x</div>
            <div style="font-size: 0.74rem; color: #64748b; margin-top: 2px;">{'Healthy surplus buffer' if coverage >= 1.2 else 'Deficit risk alert'}</div>
        </div>
        """, unsafe_allow_html=True)
    with v2:
        ret_rate = ((summary["balance"] / summary["total_income"]) * 100) if summary["total_income"] > 0 else 0.0
        st.markdown(f"""
        <div style="padding: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;">
            <div style="font-size: 0.76rem; font-weight: 700; color: #64748b;">LIQUID CAPITAL RETENTION</div>
            <div style="font-size: 1.3rem; font-weight: 800; color: {'#16a34a' if ret_rate >= 20 else '#eab308'};">{ret_rate:.1f}%</div>
            <div style="font-size: 0.74rem; color: #64748b; margin-top: 2px;">Target benchmark: &ge; 20%</div>
        </div>
        """, unsafe_allow_html=True)
    with v3:
        avg_tx = (summary["total_expense"] / summary["total_transactions"]) if summary["total_transactions"] > 0 else 0.0
        st.markdown(f"""
        <div style="padding: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;">
            <div style="font-size: 0.76rem; font-weight: 700; color: #64748b;">AVERAGE OUTFLOW PER TRANSACTION</div>
            <div style="font-size: 1.3rem; font-weight: 800; color: #0f172a;">₹{avg_tx:,.2f}</div>
            <div style="font-size: 0.74rem; color: #64748b; margin-top: 2px;">Aggregated across all categories</div>
        </div>
        """, unsafe_allow_html=True)

# =============================================================
# Page 2: Statement Upload (Ingestion & Pre-Commit Review ONLY)
# =============================================================
elif menu_selection == "📥 Upload Statement":
    st.markdown("### Bank Statement Ingestion (Multi-Format AI Parser)")
    st.caption("Upload digital monthly PDF statements from PhonePe, Google Pay, Paytm, SBI, HDFC, ICICI, Axis, etc.")

    up_col1, up_col2 = st.columns([1.3, 0.9])

    with up_col1:
        st.markdown("##### Select Digital Statement (PDF)")
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
                    <strong>Detected Provider:</strong> {meta.get('provider', 'Digital Bank Statement')} &bull;
                    <strong>Account / Identifier:</strong> {meta.get('account', 'N/A')} &bull;
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
                    for t in final_txs:
                        if isinstance(t["date"], (pd.Timestamp, datetime, date)):
                            t["date"] = t["date"].strftime("%Y-%m-%d")
                    added, duplicates = database.add_transactions_bulk(user_id, final_txs)
                    st.success(f"Saved {added} new transactions! ({duplicates} duplicates skipped)")
                    time.sleep(1.0)
                    st.rerun()

            else:
                if ext_result.get("is_scanned"):
                    st.warning("⚠️ Scanned Image PDF Detected: This document contains images rather than digital text. Please upload digital PDF statements.")
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

# =============================================================
# Page 3: Transaction Ledger (Master Records & Search ONLY)
# =============================================================
elif menu_selection == "📑 Transaction Ledger":
    st.markdown("### Transaction Ledger & Vault")
    st.caption("Search, filter, edit, or manually record individual transactions")

    # Action Toolbar: Add Manual
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

    # Multi-Filter Bar
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

# =============================================================
# Page 4: Merchants & Payees Directory (DEDICATED NEW SECTION)
# =============================================================
elif menu_selection == "🏢 Merchants & Payees":
    st.markdown("### Merchants & Payees Directory")
    st.caption("Deep-dive merchant spending analytics, volume concentration, and automated categorization rules")

    top_payees = database.get_top_payees(user_id, limit=50)

    if not top_payees:
        st.info("No merchant transactions recorded yet. Ingest bank statements to analyze merchants.")
    else:
        df_merchants = pd.DataFrame(top_payees)
        total_merchant_spend = df_merchants["total_amount"].sum()
        total_merchant_txs = df_merchants["tx_count"].sum()

        # Merchant Summary KPIs
        m_kpi1, m_kpi2, m_kpi3 = st.columns(3)
        with m_kpi1:
            st.metric("Total Unique Merchants", len(df_merchants))
        with m_kpi2:
            top_m = df_merchants.iloc[0]
            st.metric("Top Outflow Merchant", top_m["description"], f"₹{top_m['total_amount']:,.2f}")
        with m_kpi3:
            avg_ticket = (total_merchant_spend / total_merchant_txs) if total_merchant_txs > 0 else 0
            st.metric("Average Merchant Spend", f"₹{avg_ticket:,.2f}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Chart & Leaderboard
        mc_col1, mc_col2 = st.columns([1.4, 1.6])
        with mc_col1:
            st.markdown("##### 📊 Top Merchants by Outflow Volume")
            top10 = df_merchants.head(10).sort_values("total_amount", ascending=True)
            fig_bar = px.bar(
                top10,
                x="total_amount",
                y="description",
                orientation="h",
                text="total_amount",
                color="total_amount",
                color_continuous_scale="Blues"
            )
            fig_bar.update_traces(texttemplate="₹%{text:,.0f}", textposition="inside")
            fig_bar.update_layout(
                height=340,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis_title="Total Outflow (₹)",
                yaxis_title="",
                coloraxis_showscale=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with mc_col2:
            st.markdown("##### 🏢 Merchant Concentration Leaderboard")
            disp_m = df_merchants[["description", "category", "tx_count", "total_amount"]].copy()
            disp_m["avg_spend"] = (disp_m["total_amount"] / disp_m["tx_count"]).apply(lambda x: f"₹{x:,.2f}")
            disp_m["total_amount"] = disp_m["total_amount"].apply(lambda x: f"₹{x:,.2f}")
            disp_m.columns = ["Merchant / Payee", "Primary Category", "Transactions", "Total Spend", "Avg Spend"]
            st.dataframe(disp_m, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Merchant Transaction Drilldown
        st.markdown("##### 🔍 Merchant Transaction Drilldown")
        all_payee_names = [p["description"] for p in top_payees]
        selected_merchant = st.selectbox("Inspect Transactions for Merchant:", all_payee_names)

        if selected_merchant:
            m_txs = database.get_transactions(user_id, search=selected_merchant)
            if m_txs:
                st.write(f"**Found {len(m_txs)} transactions with {selected_merchant}**")
                df_mtx = pd.DataFrame(m_txs)[["date", "description", "category", "type", "amount"]]
                df_mtx["amount"] = df_mtx["amount"].apply(lambda x: f"₹{x:,.2f}")
                st.dataframe(df_mtx, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Smart Category Automation Rules (Contact Mapping)
        st.markdown("##### ⚙️ Smart Category Automation Rules (Merchant & Contact Mapping)")
        st.caption("Automatically map recurring contacts or merchants (e.g. Map 'Daddy' to 'Allowances & Gifts', or 'Varun' to 'Personal & P2P Transfers').")

        with st.form("rule_form"):
            rc1, rc2, rc3 = st.columns([1.5, 1.5, 1])
            with rc1:
                r_keyword = st.text_input("Contact or Merchant Keyword", placeholder="e.g. Varun, Swiggy, Chai Point")
            with rc2:
                r_cat = st.selectbox("Assign to Category", database.ALL_CATEGORIES)
            with rc3:
                r_reclass = st.checkbox("Reclassify existing", value=True)
                r_submit = st.form_submit_button("Create Automation Rule", type="primary", use_container_width=True)

            if r_submit and r_keyword:
                s, m = database.save_category_rule(user_id, r_keyword, r_cat, reclassify_existing=r_reclass)
                st.success(m)
                time.sleep(0.5)
                st.rerun()

        # Display Existing Active Rules
        existing_rules = database.get_category_rules(user_id)
        if existing_rules:
            st.markdown("###### Active Automation Rules")
            for r in existing_rules:
                r_c1, r_c2, r_c3 = st.columns([2, 2, 1])
                with r_c1:
                    st.write(f"Keyword: **{r['keyword']}**")
                with r_c2:
                    st.write(f"Routes to: **{r['category']}**")
                with r_c3:
                    if st.button("Delete", key=f"del_rule_{r['id']}", type="secondary"):
                        database.delete_category_rule(r["id"], user_id)
                        st.success("Rule removed.")
                        st.rerun()

# =============================================================
# Page 5: Budget Management (Spending Limits & Guardrails ONLY)
# =============================================================
elif menu_selection == "🎯 Budget Management":
    st.markdown("### Budget Guardrails & Ceilings")
    st.caption("Configure monthly category spending allowances, track utilization velocity, and prevent budget leaks")

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

    # Safe Daily Spending Allowance
    today = datetime.now()
    if sel_month == curr_month:
        import calendar
        _, last_day = calendar.monthrange(today.year, today.month)
        days_left = max(1, last_day - today.day + 1)
        safe_daily = max(0.0, util["remaining_budget"] / days_left)
        st.markdown(f"""
        <div style="padding: 12px 16px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px; margin: 12px 0;">
            🌱 <strong>Safe Daily Spending Allowance:</strong> You can safely spend <strong>₹{safe_daily:,.2f}/day</strong> across all categories for the remaining {days_left} days of this month without exceeding your budget.
        </div>
        """, unsafe_allow_html=True)

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
                time.sleep(0.5)
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

# =============================================================
# Page 6: AI Financial Insights (ML Models & Pattern Decomposition ONLY)
# =============================================================
elif menu_selection == "🧠 AI Financial Insights":
    st.markdown("### AI Financial Insights & Machine Learning Analytics")
    st.caption("Unsupervised anomaly detection, Pandas spending decomposition, and behavioral pattern modeling")

    all_txs = database.get_transactions(user_id)
    if not all_txs:
        st.info("Insufficient historical data available. Upload bank statements to generate ML insights.")
    else:
        df = pd.DataFrame(all_txs)
        patterns = ml_engine.analyze_spending_patterns(df)
        unusual = ml_engine.detect_unusual_transactions(df)
        comparison = ml_engine.compare_monthly_spending(df)

        # 1. Behavioral Patterns (Pandas Engine)
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

        # Weekday vs Weekend Spending
        exp_df = df[df["type"] == "expense"].copy()
        if not exp_df.empty:
            exp_df["dt"] = pd.to_datetime(exp_df["date"], errors="coerce")
            exp_df["is_weekend"] = exp_df["dt"].dt.dayofweek >= 5
            w_end = exp_df[exp_df["is_weekend"]]["amount"].mean() if not exp_df[exp_df["is_weekend"]].empty else 0
            w_day = exp_df[~exp_df["is_weekend"]]["amount"].mean() if not exp_df[~exp_df["is_weekend"]].empty else 0
            surge = ((w_end - w_day) / w_day * 100) if w_day > 0 else 0

            st.markdown(f"""
            <div style="padding: 12px 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; margin-top: 10px;">
                🗓️ <strong>Weekend vs Weekday Dynamic:</strong> Average weekend transaction is <strong>₹{w_end:,.2f}</strong> vs weekday average of <strong>₹{w_day:,.2f}</strong> ({'+' if surge > 0 else ''}{surge:.1f}% weekend differential).
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. Isolation Forest Outliers
        st.markdown("##### 🔍 Unusual Transaction Detection (Isolation Forest ML)")
        st.caption("Statistical anomalies identified through scikit-learn Isolation Forest algorithm based on transaction size and timing relative to category baseline.")

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

        # 3. Month-over-Month Comparison
        st.markdown("##### 📅 Month-over-Month Spending Trajectory")
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

# =============================================================
# Page 7: AI Audit Reports & Downloads (Comprehensive Reports ONLY)
# =============================================================
elif menu_selection == "📄 AI Audit & Reports":
    st.markdown("### AI Financial Health Audit & Advisory Reports")
    st.caption("Deep-dive financial health diagnosis, 50/30/20 rule breakdown, micro-leakage analysis, and downloadable audit statements")

    rc1, rc2 = st.columns(2)
    with rc1:
        rep_month = st.selectbox("Audit Month", ["All Time", curr_month, "2026-10", "2026-09"])
    with rc2:
        rep_cat = st.selectbox("Category Filter", ["All Categories"] + database.ALL_CATEGORIES)

    mth_val = "" if rep_month == "All Time" else rep_month
    cat_val = "all" if rep_cat == "All Categories" else rep_cat

    # Action buttons for download
    st.markdown("##### 📥 Instant Official Downloads")
    d_col1, d_col2 = st.columns(2)

    with d_col1:
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
                label="📑 Download Certified AI Audit Report (PDF)",
                data=pdf_bytes,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

    with d_col2:
        csv_data = report_generator.generate_csv_report(user_id, month=mth_val, category=cat_val)
        st.download_button(
            label="📊 Download Spreadsheet Ledger (CSV)",
            data=csv_data,
            file_name=f"Expense_Ledger_{user_id}_{mth_val or 'all'}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Fetch audit data
    tx_rep = database.get_transactions(user_id, category=cat_val)
    if mth_val:
        tx_rep = [t for t in tx_rep if t["date"].startswith(mth_val)]

    df_rep = pd.DataFrame(tx_rep) if tx_rep else pd.DataFrame()
    bud_util = database.get_budget_utilization(user_id, mth_val or curr_month)
    audit = ml_engine.compute_financial_health_audit(df_rep, bud_util)

    # 1. Executive Health Scorecard Preview
    st.markdown("##### 🛡️ Executive Financial Health Scorecard")
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.metric("Total Verified Inflow", f"+₹{audit['total_income']:,.2f}")
    with sc2:
        st.metric("Total Outflow", f"-₹{audit['total_expense']:,.2f}")
    with sc3:
        st.metric("Net Capital Balance", f"₹{audit['balance']:,.2f}")
    with sc4:
        st.metric("Health Grade", audit["health_grade"].split("—")[0].strip())

    st.markdown(f"""
    <div style="padding: 14px 18px; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 10px; margin-top: 10px; font-size: 0.9rem; color: #1e293b;">
        <strong>AI Executive Diagnosis:</strong> {audit['executive_summary']}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. 50/30/20 Rule Breakdown
    st.markdown("##### 1. In-Depth 50/30/20 Spending Health Diagnosis")
    r50 = audit.get("rule_50_30_20", {})
    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        st.markdown(f"""
        <div style="padding: 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;">
            <div style="font-weight: 700; font-size: 0.85rem; color: #64748b;">ESSENTIAL NEEDS (Target: 50%)</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #0f172a; margin-top: 4px;">₹{r50.get('needs_amount', 0):,.2f}</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">{r50.get('needs_pct', 0):.1f}% of Inflow &bull; <strong>{r50.get('needs_status', 'Optimal')}</strong></div>
        </div>
        """, unsafe_allow_html=True)
    with r_col2:
        st.markdown(f"""
        <div style="padding: 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;">
            <div style="font-weight: 700; font-size: 0.85rem; color: #64748b;">DISCRETIONARY WANTS (Target: 30%)</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #0f172a; margin-top: 4px;">₹{r50.get('wants_amount', 0):,.2f}</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">{r50.get('wants_pct', 0):.1f}% of Inflow &bull; <strong>{r50.get('wants_status', 'Optimal')}</strong></div>
        </div>
        """, unsafe_allow_html=True)
    with r_col3:
        st.markdown(f"""
        <div style="padding: 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;">
            <div style="font-weight: 700; font-size: 0.85rem; color: #64748b;">NET SAVINGS & CAPITAL (Target: 20%)</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #16a34a; margin-top: 4px;">₹{r50.get('savings_amount', 0):,.2f}</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">{r50.get('savings_pct', 0):.1f}% of Inflow &bull; <strong>{r50.get('savings_status', 'Optimal')}</strong></div>
        </div>
        """, unsafe_allow_html=True)

    if r50.get("ai_commentary"):
        st.caption(f"💡 **AI Commentary:** {r50['ai_commentary']}")

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Category Overspending & Root-Cause Diagnosis
    st.markdown("##### 2. Overspending Diagnosis & Root-Cause Analysis")
    if audit["solutions"]:
        for sol in audit["solutions"]:
            b_color = "#fecaca" if sol["severity"] == "danger" else "#fde68a"
            bg_color = "#fffdfd" if sol["severity"] == "danger" else "#fffdfa"
            st.markdown(f"""
            <div style="padding: 14px 18px; background: {bg_color}; border: 1px solid {b_color}; border-radius: 10px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="font-size: 0.95rem; color: #0f172a;">{sol['title']}</strong>
                    <span style="font-weight: 800; color: #dc2626; font-size: 0.85rem;">{sol['impact']}</span>
                </div>
                <p style="margin: 6px 0 0 0; font-size: 0.88rem; color: #334155;">{sol['description']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✓ No critical budget overspending detected for this audit window.")

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Micro-Expense Leakage
    st.markdown("##### 3. Micro-Expense Leakage Audit (≤ ₹50 Outflows)")
    m_leak = audit.get("micro_leakage", {})
    st.markdown(f"""
    <div style="padding: 14px 18px; background: #fefce8; border: 1px solid #fef08a; border-radius: 10px;">
        <strong>Identified {m_leak.get('count', 0)} Micro-Payments:</strong> Total outflow of <strong>₹{m_leak.get('total_amount', 0):,.2f}</strong> ({m_leak.get('pct_of_total', 0):.1f}% of all expenses).
        <p style="margin: 6px 0 4px 0; font-size: 0.88rem; color: #334155;">{m_leak.get('explanation', '')}</p>
        <p style="margin: 0; font-size: 0.85rem; color: #713f12;"><strong>Prescription:</strong> {m_leak.get('prescription', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 5. Prescriptive 30-Day Recovery Roadmap
    st.markdown("##### 4. Prescriptive 30-Day Financial Recovery Roadmap")
    roadmap = audit.get("recovery_roadmap", [])
    if roadmap:
        r_cards = st.columns(4)
        for idx, rm in enumerate(roadmap):
            with r_cards[idx % 4]:
                st.markdown(f"""
                <div style="padding: 16px; background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 12px; height: 100%;">
                    <div style="font-size: 0.76rem; font-weight: 700; color: #0284c7;">{rm['week'].upper()}</div>
                    <div style="font-weight: 800; font-size: 0.95rem; color: #0c4a6e; margin-top: 4px;">{rm['phase']}</div>
                    <p style="font-size: 0.8rem; color: #334155; margin-top: 6px;">{rm['action']}</p>
                    <div style="font-size: 0.82rem; font-weight: 700; color: #16a34a; margin-top: 8px;">Target: {rm['target_savings']}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 6. Budget Matrix & Itemized Ledger
    with st.expander("📊 View Itemized Ledger Records for this Period", expanded=False):
        if tx_rep:
            df_preview = pd.DataFrame(tx_rep)[["date", "description", "category", "type", "amount"]]
            df_preview["amount"] = df_preview["amount"].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(df_preview, use_container_width=True, hide_index=True)
        else:
            st.info("No records in this filtered view.")

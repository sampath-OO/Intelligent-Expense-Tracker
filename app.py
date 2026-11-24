import os
import functools
from datetime import datetime
import pandas as pd
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_file, Response
)
from werkzeug.utils import secure_filename

import database
import pdf_extractor
import ml_engine
import report_generator
import sample_generator

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "expense_tracker_secret_key_local_2026")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
REPORTS_FOLDER = os.path.join(BASE_DIR, "reports")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

# Initialize database schema on startup
database.init_db()

# Generate sample bank statement PDF if it doesn't already exist
sample_pdf_path = os.path.join(BASE_DIR, "sample_bank_statement.pdf")
if not os.path.exists(sample_pdf_path):
    try:
        sample_generator.generate_sample_pdf(sample_pdf_path)
    except Exception as e:
        print("Sample PDF generation error:", e)

# Authentication Decorator
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("Please sign in to access your financial dashboard.", "warning")
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view

@app.context_processor
def inject_globals():
    return {
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "current_month": datetime.now().strftime("%Y-%m")
    }

# ----------------- Auth Routes -----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = database.verify_user(email, password)
        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "error")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if len(password) < 4:
            flash("Password must be at least 4 characters long.", "error")
            return render_template("register.html")

        user = database.create_user(name, email, password)
        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            flash("Account registered successfully! Welcome to Intelligent Expense Tracker.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("An account with this email address already exists.", "error")

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for("login"))

# ----------------- Main Pages -----------------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    current_mth = datetime.now().strftime("%Y-%m")

    # Get overall summary and budget status
    summary = database.get_dashboard_summary(user_id)
    budget_data = database.get_budget_utilization(user_id, current_mth)
    recent_txs = database.get_transactions(user_id, limit=6)
    top_payees = database.get_top_payees(user_id, limit=5)

    tx_all = database.get_transactions(user_id)
    df = pd.DataFrame(tx_all) if tx_all else pd.DataFrame()
    overspend_analysis = ml_engine.generate_overspending_solutions(df, budget_data)
    patterns = ml_engine.analyze_spending_patterns(df)

    # Get latest insights
    insights = database.get_insights(user_id, limit=3)
    if not insights and tx_all:
        recs = ml_engine.generate_personalized_recommendations(df, budget_data)
        database.save_insights(user_id, recs)
        insights = database.get_insights(user_id, limit=3)

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        summary=summary,
        budget_data=budget_data,
        recent_transactions=recent_txs,
        top_payees=top_payees,
        overspend_analysis=overspend_analysis,
        patterns=patterns,
        insights=insights
    )

@app.route("/upload")
@login_required
def upload_page():
    return render_template("upload.html", active_page="upload")

@app.route("/api/extract-statement", methods=["POST"])
@login_required
def api_extract_statement():
    if "statement" not in request.files:
        return jsonify({"success": False, "message": "No file uploaded.", "transactions": [], "is_scanned": False}), 400

    file = request.files["statement"]
    if file.filename == "":
        return jsonify({"success": False, "message": "No selected file.", "transactions": [], "is_scanned": False}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"success": False, "message": "Only PDF statement files are supported.", "transactions": [], "is_scanned": False}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}")
    file.save(save_path)

    # Extract transactions using our hybrid PDF parser
    extraction_result = pdf_extractor.extract_from_pdf(save_path)
    return jsonify(extraction_result)

@app.route("/api/save-extracted", methods=["POST"])
@login_required
def api_save_extracted():
    user_id = session["user_id"]
    data = request.get_json() or {}
    tx_list = data.get("transactions", [])

    if not tx_list:
        return jsonify({"success": False, "message": "No transactions provided."}), 400

    added, duplicates = database.add_transactions_bulk(user_id, tx_list)

    # Recompute and update AI insights for the user
    try:
        all_tx = database.get_transactions(user_id)
        if all_tx:
            df = pd.DataFrame(all_tx)
            current_mth = datetime.now().strftime("%Y-%m")
            b_data = database.get_budget_utilization(user_id, current_mth)
            new_recs = ml_engine.generate_personalized_recommendations(df, b_data)
            database.save_insights(user_id, new_recs)
    except Exception as e:
        print("Insight update error after upload:", e)

    msg = f"Successfully saved {added} transactions."
    if duplicates > 0:
        msg += f" ({duplicates} duplicate transactions automatically skipped)."

    return jsonify({"success": True, "message": msg, "added": added, "duplicates": duplicates})

@app.route("/download/sample-statement")
def download_sample_pdf_route():
    if not os.path.exists(sample_pdf_path):
        sample_generator.generate_sample_pdf(sample_pdf_path)
    return send_file(sample_pdf_path, as_attachment=True, download_name="sample_bank_statement.pdf")

@app.route("/transactions")
@login_required
def transactions_page():
    user_id = session["user_id"]
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "all")
    tx_type = request.args.get("type", "all")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    txs = database.get_transactions(
        user_id=user_id,
        category=category,
        tx_type=tx_type,
        start_date=start_date,
        end_date=end_date,
        search=search
    )

    return render_template(
        "transactions.html",
        active_page="transactions",
        transactions=txs,
        categories=database.ALL_CATEGORIES,
        selected_category=category,
        selected_type=tx_type,
        start_date=start_date,
        end_date=end_date,
        search=search
    )

@app.route("/api/category-rule/add", methods=["POST"])
@login_required
def add_category_rule_route():
    user_id = session["user_id"]
    keyword = request.form.get("keyword", "").strip()
    category = request.form.get("category", "").strip()
    reclassify = request.form.get("reclassify", "yes") == "yes"

    if not keyword or not category:
        flash("Contact/Merchant Name and Category are required.", "error")
        return redirect(request.referrer or url_for("transactions_page"))

    success, msg = database.save_category_rule(user_id, keyword, category, reclassify_existing=reclassify)
    if success:
        flash(msg, "success")
    else:
        flash(f"Error saving rule: {msg}", "error")

    return redirect(request.referrer or url_for("transactions_page"))

@app.route("/api/transaction/add", methods=["POST"])
@login_required
def add_transaction_route():
    user_id = session["user_id"]
    date = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()
    tx_type = request.form.get("type", "expense").strip()
    category = request.form.get("category", "Others").strip()
    amount = float(request.form.get("amount", 0.0))

    if not date or not description or amount <= 0:
        flash("Invalid transaction details. Please check the values.", "error")
        return redirect(request.referrer or url_for("transactions_page"))

    success, msg = database.add_transaction(user_id, date, description, category, tx_type, amount)
    if success:
        flash("Transaction recorded successfully.", "success")
    else:
        flash(f"Could not record transaction: {msg}", "warning")

    return redirect(request.referrer or url_for("transactions_page"))

@app.route("/api/transaction/update", methods=["POST"])
@login_required
def update_transaction_route():
    user_id = session["user_id"]
    tx_id = request.form.get("id")
    date = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()
    tx_type = request.form.get("type", "expense").strip()
    category = request.form.get("category", "Others").strip()
    amount = float(request.form.get("amount", 0.0))

    if not tx_id or not date or not description or amount <= 0:
        flash("Invalid transaction update data.", "error")
        return redirect(url_for("transactions_page"))

    updated = database.update_transaction(tx_id, user_id, date, description, category, tx_type, amount)
    if updated:
        flash("Transaction updated successfully.", "success")
    else:
        flash("Failed to update transaction.", "error")

    return redirect(url_for("transactions_page"))

@app.route("/api/transaction/delete", methods=["POST"])
@login_required
def delete_transaction_route():
    user_id = session["user_id"]
    data = request.get_json() or {}
    tx_id = data.get("id")

    if not tx_id:
        return jsonify({"success": False, "message": "Transaction ID is required."}), 400

    deleted = database.delete_transaction(tx_id, user_id)
    return jsonify({"success": deleted, "message": "Transaction deleted" if deleted else "Not found"})

@app.route("/budget")
@login_required
def budget_page():
    user_id = session["user_id"]
    selected_month = request.args.get("month", datetime.now().strftime("%Y-%m"))
    utilization = database.get_budget_utilization(user_id, selected_month)

    return render_template(
        "budget.html",
        active_page="budget",
        selected_month=selected_month,
        utilization=utilization
    )

@app.route("/api/budget/set", methods=["POST"])
@login_required
def set_budget_route():
    user_id = session["user_id"]
    category = request.form.get("category", "").strip()
    month = request.form.get("month", "").strip()
    amount = float(request.form.get("allocated_amount", 0.0))

    if not category or not month:
        flash("Category and month are required to set a budget.", "error")
        return redirect(url_for("budget_page"))

    database.set_budget(user_id, category, month, amount)
    flash(f"Monthly budget for {category} set to ₹{amount:,.2f}.", "success")
    return redirect(url_for("budget_page", month=month))

@app.route("/insights")
@login_required
def insights_page():
    user_id = session["user_id"]
    all_txs = database.get_transactions(user_id)
    current_mth = datetime.now().strftime("%Y-%m")
    budget_data = database.get_budget_utilization(user_id, current_mth)

    if not all_txs:
        return render_template(
            "insights.html",
            active_page="insights",
            patterns={"has_data": False},
            unusual_transactions=[],
            comparison={"has_comparison": False, "message": "No transactions recorded yet."},
            recommendations=[]
        )

    df = pd.DataFrame(all_txs)

    # 1. Spending pattern analysis using Pandas
    patterns = ml_engine.analyze_spending_patterns(df)

    # 2. Isolation Forest Anomaly Detection
    unusual = ml_engine.detect_unusual_transactions(df)

    # 3. Monthly expense comparison
    comparison = ml_engine.compare_monthly_spending(df)

    # 4. Personalized Data-Driven Recommendations
    recs = ml_engine.generate_personalized_recommendations(df, budget_data)

    # Store insights
    database.save_insights(user_id, recs)

    return render_template(
        "insights.html",
        active_page="insights",
        patterns=patterns,
        unusual_transactions=unusual,
        comparison=comparison,
        recommendations=recs
    )

@app.route("/reports")
@login_required
def reports_page():
    user_id = session["user_id"]
    selected_month = request.args.get("month", "")
    selected_category = request.args.get("category", "all")

    txs = database.get_transactions(user_id, category=selected_category)
    if selected_month:
        txs = [t for t in txs if t["date"].startswith(selected_month)]

    total_income = sum(t["amount"] for t in txs if t["type"] == "income")
    total_expense = sum(t["amount"] for t in txs if t["type"] == "expense")
    balance = total_income - total_expense

    # Overspending diagnosis and solutions
    mth_eval = selected_month or datetime.now().strftime("%Y-%m")
    budget_util = database.get_budget_utilization(user_id, mth_eval)
    df = pd.DataFrame(txs) if txs else pd.DataFrame()
    overspend_analysis = ml_engine.generate_overspending_solutions(df, budget_util)

    return render_template(
        "reports.html",
        active_page="reports",
        transactions=txs,
        categories=database.ALL_CATEGORIES,
        selected_month=selected_month,
        selected_category=selected_category,
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        budget_util=budget_util,
        overspend_analysis=overspend_analysis
    )

@app.route("/reports/download/csv")
@login_required
def download_csv_route():
    user_id = session["user_id"]
    month = request.args.get("month", "")
    category = request.args.get("category", "all")

    csv_data = report_generator.generate_csv_report(user_id, month=month, category=category)
    filename = f"Expense_Report_{month or 'all'}_{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.route("/reports/download/pdf")
@login_required
def download_pdf_route():
    user_id = session["user_id"]
    month = request.args.get("month", "")
    category = request.args.get("category", "all")

    user_name = session.get("user_name", "User")
    user_email = session.get("user_email", "user@local")

    pdf_file_path = report_generator.generate_pdf_report(
        user_id=user_id,
        user_name=user_name,
        user_email=user_email,
        month=month,
        category=category
    )

    filename = os.path.basename(pdf_file_path)
    return send_file(pdf_file_path, as_attachment=True, download_name=filename)

if __name__ == "__main__":
    print("=" * 65)
    print("  Intelligent Expense Tracker with Personalized Spending Insights")
    print("  Running locally at: http://127.0.0.1:5000")
    print("=" * 65)
    app.run(host="127.0.0.1", port=5000, debug=True)

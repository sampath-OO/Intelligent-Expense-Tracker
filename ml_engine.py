import re
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

CATEGORY_KEYWORDS = {
    "Food & Dining": [
        "swiggy", "zomato", "restaurant", "cafe", "mcdonald", "kfc", "starbucks",
        "domino", "pizza", "burger", "dine", "food", "bakery", "bar", "kitchen",
        "grocery", "supermarket", "super market", "instamart", "blinkit", "zepto", "bigbasket",
        "meat", "dairy", "subway", "dunkin", "coffee", "bistro", "eats", "hotel",
        "tiffin", "mess", "canteen", "tea", "bakes", "juices", "sweets", "palkavva",
        "provisions", "mart", "rice", "veg", "fruits", "dhaba", "bhavan", "fast food"
    ],
    "Shopping & Retail": [
        "amazon", "flipkart", "myntra", "zara", "h&m", "cloth", "apparel", "retail",
        "mall", "store", "electronics", "croma", "reliance digital", "shopping",
        "shoes", "footwear", "fashion", "ikea", "decathlon", "ajio", "nykaa",
        "lifestyle", "shoppers stop", "tatacliq", "aliexpress", "boutique", "textiles",
        "silks", "readymade", "jewellers", "fancy", "traders", "agencies", "enterprises"
    ],
    "Travel & Transport": [
        "uber", "ola", "rapido", "metro", "irctc", "rail", "flight", "indigo",
        "air india", "fuel", "petrol", "diesel", "hpcl", "bpcl", "ioccl", "shell",
        "toll", "fastag", "bus", "redbus", "transport", "cab", "auto", "parking",
        "airlines", "makemytrip", "goibibo", "yatra", "cleartrip", "apsrtc", "ksrtc",
        "msrtc", "corporation", "travels", "railway", "ticket", "chennai transport",
        "state transport", "villupuram transport"
    ],
    "Entertainment & Recreation": [
        "netflix", "spotify", "hotstar", "prime video", "cinema", "pvr", "inox",
        "movie", "theatre", "gaming", "steam", "playstation", "concert", "event",
        "bookmyshow", "youtube", "disney", "apple music", "audible", "game", "multiplex", "resort"
    ],
    "Healthcare & Medical": [
        "hospital", "clinic", "pharmacy", "apollo", "medplus", "1mg", "pharmeasy",
        "doctor", "dental", "diagnostic", "pathology", "lab", "medicine", "health",
        "opticals", "wellness", "therapist", "dr.", "chemist", "medical", "nursing",
        "healthcare", "drugs", "saveetha institute of medical"
    ],
    "Bills & Utilities": [
        "electricity", "water bill", "bescom", "cesc", "gas", "indane", "hp gas",
        "broadband", "wifi", "airtel", "jio", "vi", "vodafone", "bill payment",
        "recharge", "dth", "tata sky", "maintenance", "rent", "tax", "insurance",
        "lic", "utility", "postpaid", "cylinder", "bescom", "tneb"
    ],
    "Education & Learning": [
        "school", "college", "university", "tuition", "course", "udemy", "coursera",
        "books", "stationery", "academy", "institute", "exam fee", "coaching",
        "skillshare", "edx", "tutor", "training", "polytechnic", "sciences", "vidyalaya", "library"
    ],
    "Allowances & Gifts": [
        "daddy", "father", "mom", "mother", "family", "parents", "brother", "sister", "allowance", "pocket money"
    ],
    "Salary & Income": [
        "salary", "payroll", "dividend", "interest", "stipend", "bonus",
        "freelance", "cashback", "credit interest", "consulting", "reimbursement",
        "incentive", "neft credit", "imps credit", "ach credit", "neft", "imps"
    ]
}

def categorize_transaction(description, tx_type="expense"):
    """
    Intelligent transaction classifier.
    Eliminates generic 'Others' by recognizing UPI P2P transfers, commercial entities, and family support.
    """
    if not description:
        return "General Expenses" if tx_type == "expense" else "Salary & Income"

    desc_lower = description.lower()

    # 1. Income categorization
    if tx_type == "income":
        for kw in CATEGORY_KEYWORDS["Allowances & Gifts"]:
            if kw in desc_lower:
                return "Allowances & Gifts"
        for kw in CATEGORY_KEYWORDS["Salary & Income"]:
            if kw in desc_lower:
                return "Salary & Income"
        if "received from" in desc_lower or "upi received" in desc_lower:
            return "Salary & Income"
        return "Salary & Income"

    # 2. Expense: Check specific commercial and vendor keywords first
    for category, keywords in CATEGORY_KEYWORDS.items():
        if category in ("Salary & Income", "Allowances & Gifts"):
            continue
        for kw in keywords:
            if " " in kw:
                if kw in desc_lower:
                    return category
            else:
                if re.search(r"\b" + re.escape(kw) + r"\b", desc_lower):
                    return category

    # 3. Smart UPI Person vs Merchant detection
    # If the transaction is "Paid to <Contact/Person Name>", classify as Personal & P2P Transfers
    if desc_lower.startswith("paid to"):
        recipient = desc_lower.replace("paid to", "").strip()
        # Check if recipient has commercial keywords
        commercial_terms = [
            "store", "shop", "centre", "center", "mart", "super", "market", "hotel", "bhavan",
            "mess", "tiffin", "canteen", "transport", "travels", "medical", "pharmacy", "agency",
            "enterprises", "traders", "bakery", "sweets", "dairy", "fuel", "petrol", "auto"
        ]
        if any(term in recipient for term in commercial_terms):
            for category, keywords in CATEGORY_KEYWORDS.items():
                if category in ("Salary & Income", "Allowances & Gifts"):
                    continue
                if any(kw in recipient for kw in keywords):
                    return category
            return "Shopping & Retail"
        else:
            # Person-to-person transfer (e.g. Paid to Khadeer, Paid to Varun, Paid to Naga Sai)
            return "Personal & P2P Transfers"

    return "General Expenses"

def analyze_spending_patterns(transactions_df):
    if transactions_df.empty or len(transactions_df[transactions_df["type"] == "expense"]) == 0:
        return {
            "has_data": False,
            "message": "Insufficient expense data available for spending pattern analysis. Please upload or add more transactions."
        }

    expenses_df = transactions_df[transactions_df["type"] == "expense"].copy()
    expenses_df["amount"] = pd.to_numeric(expenses_df["amount"], errors="coerce").fillna(0)
    expenses_df["date"] = pd.to_datetime(expenses_df["date"], errors="coerce")
    expenses_df = expenses_df.dropna(subset=["date"])

    if expenses_df.empty:
        return {"has_data": False, "message": "Invalid date or amount formats in transactions."}

    total_spent = float(expenses_df["amount"].sum())
    tx_count = len(expenses_df)
    avg_per_tx = float(expenses_df["amount"].mean())
    max_tx = expenses_df.loc[expenses_df["amount"].idxmax()]

    # Micro-transactions audit (< ₹50)
    micro_txs = expenses_df[expenses_df["amount"] <= 50.0]
    micro_count = len(micro_txs)
    micro_total = float(micro_txs["amount"].sum())

    min_date = expenses_df["date"].min()
    max_date = expenses_df["date"].max()
    days_active = max(1, (max_date - min_date).days + 1)
    daily_avg = total_spent / days_active

    cat_group = expenses_df.groupby("category")["amount"].agg(["sum", "count"]).reset_index()
    cat_group["percentage"] = (cat_group["sum"] / total_spent * 100).round(1)
    cat_group = cat_group.sort_values(by="sum", ascending=False)
    top_category = cat_group.iloc[0]["category"] if not cat_group.empty else "N/A"
    top_cat_amount = float(cat_group.iloc[0]["sum"]) if not cat_group.empty else 0.0

    expenses_df["day_name"] = expenses_df["date"].dt.day_name()
    day_group = expenses_df.groupby("day_name")["amount"].sum()
    top_spending_day = day_group.idxmax() if not day_group.empty else "N/A"

    expenses_df["is_weekend"] = expenses_df["date"].dt.dayofweek.isin([5, 6])
    weekend_spent = float(expenses_df[expenses_df["is_weekend"]]["amount"].sum())
    weekday_spent = float(expenses_df[~expenses_df["is_weekend"]]["amount"].sum())

    return {
        "has_data": True,
        "total_spent": round(total_spent, 2),
        "tx_count": tx_count,
        "avg_per_tx": round(avg_per_tx, 2),
        "daily_avg": round(daily_avg, 2),
        "days_active": days_active,
        "micro_count": micro_count,
        "micro_total": round(micro_total, 2),
        "top_category": top_category,
        "top_cat_amount": round(top_cat_amount, 2),
        "top_spending_day": top_spending_day,
        "weekend_spent": round(weekend_spent, 2),
        "weekday_spent": round(weekday_spent, 2),
        "max_tx": {
            "description": str(max_tx["description"]),
            "amount": float(max_tx["amount"]),
            "date": max_tx["date"].strftime("%Y-%m-%d"),
            "category": str(max_tx["category"])
        },
        "category_summary": cat_group.to_dict(orient="records")
    }

def detect_unusual_transactions(transactions_df, contamination=0.05):
    if transactions_df.empty:
        return []

    expenses = transactions_df[transactions_df["type"] == "expense"].copy()
    if len(expenses) < 5:
        return []

    expenses["amount"] = pd.to_numeric(expenses["amount"], errors="coerce").fillna(0)
    expenses["date"] = pd.to_datetime(expenses["date"], errors="coerce")
    expenses = expenses.dropna(subset=["date"])

    if len(expenses) < 5:
        return []

    features = pd.DataFrame({
        "amount": expenses["amount"],
        "day": expenses["date"].dt.day
    })

    effective_contamination = min(0.15, max(0.02, 1.0 / len(expenses)))

    try:
        model = IsolationForest(
            contamination=effective_contamination,
            random_state=42,
            n_estimators=100
        )
        model.fit(features)
        predictions = model.predict(features)
        decision_scores = model.decision_function(features)

        expenses["is_unusual"] = predictions == -1
        expenses["anomaly_score"] = decision_scores

        flagged = expenses[expenses["is_unusual"]].sort_values(by="amount", ascending=False)
        mean_amount = float(expenses["amount"].mean())
        std_amount = float(expenses["amount"].std()) if len(expenses) > 1 else 1.0

        unusual_list = []
        for _, row in flagged.iterrows():
            amt = float(row["amount"])
            deviation = (amt - mean_amount) / std_amount if std_amount > 0 else 0
            reason = f"₹{amt:,.2f} deviates significantly from your average expense of ₹{mean_amount:,.2f}" if amt > mean_amount else f"Unusual spending timing pattern on {row['date'].strftime('%b %d')}"

            unusual_list.append({
                "id": int(row.get("id", 0)),
                "date": row["date"].strftime("%Y-%m-%d"),
                "description": str(row["description"]),
                "category": str(row["category"]),
                "amount": amt,
                "deviation_ratio": round(deviation, 2),
                "reason": reason,
                "disclaimer": "Statistically unusual transaction flag based on your spending history. This is an informational anomaly, not a confirmed fraudulent transaction."
            })

        return unusual_list
    except Exception as e:
        print("Anomaly detection error:", e)
        return []

def compare_monthly_spending(transactions_df):
    if transactions_df.empty:
        return {"has_comparison": False, "message": "No transaction data available."}

    df = transactions_df[transactions_df["type"] == "expense"].copy()
    if df.empty:
        return {"has_comparison": False, "message": "No expense transactions recorded."}

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df = df.dropna(subset=["date"])
    df["month_year"] = df["date"].dt.strftime("%Y-%m")

    unique_months = sorted(df["month_year"].unique())
    if len(unique_months) < 2:
        current_mth = unique_months[0] if unique_months else "N/A"
        current_spent = float(df[df["month_year"] == current_mth]["amount"].sum())
        return {
            "has_comparison": False,
            "message": f"Only one month of data ({current_mth}) is available. Upload additional statements to enable Month-over-Month comparative analysis.",
            "current_month": current_mth,
            "current_total": round(current_spent, 2)
        }

    latest_month = unique_months[-1]
    prev_month = unique_months[-2]

    curr_df = df[df["month_year"] == latest_month]
    prev_df = df[df["month_year"] == prev_month]

    curr_total = float(curr_df["amount"].sum())
    prev_total = float(prev_df["amount"].sum())

    diff_amount = curr_total - prev_total
    percent_change = ((diff_amount / prev_total) * 100) if prev_total > 0 else 0.0

    curr_cat = curr_df.groupby("category")["amount"].sum().to_dict()
    prev_cat = prev_df.groupby("category")["amount"].sum().to_dict()

    category_changes = []
    all_cats = set(curr_cat.keys()).union(set(prev_cat.keys()))

    for cat in all_cats:
        c_val = float(curr_cat.get(cat, 0.0))
        p_val = float(prev_cat.get(cat, 0.0))
        c_diff = c_val - p_val
        c_pct = ((c_diff / p_val) * 100) if p_val > 0 else (100.0 if c_val > 0 else 0.0)

        category_changes.append({
            "category": cat,
            "current": round(c_val, 2),
            "latest": round(c_val, 2),
            "previous": round(p_val, 2),
            "prev": round(p_val, 2),
            "difference": round(c_diff, 2),
            "diff": round(c_diff, 2),
            "percent_change": round(c_pct, 1),
            "increased": c_diff > 0
        })

    category_changes.sort(key=lambda x: abs(x["difference"]), reverse=True)

    return {
        "has_comparison": True,
        "latest_month": latest_month,
        "prev_month": prev_month,
        "curr_total": round(curr_total, 2),
        "latest_total": round(curr_total, 2),
        "prev_total": round(prev_total, 2),
        "diff_amount": round(diff_amount, 2),
        "percent_change": round(percent_change, 1),
        "increased": diff_amount > 0,
        "category_changes": category_changes,
        "category_comparison": category_changes
    }

def generate_overspending_solutions(transactions_df, budget_utilization=None):
    """
    Diagnoses budget overspending and calculates concrete, actionable solutions.
    """
    if transactions_df.empty:
        return {
            "has_overspending": False,
            "overspent_categories": [],
            "solutions": [],
            "health_grade": "A",
            "health_status": "No expenses recorded."
        }

    expenses_df = transactions_df[transactions_df["type"] == "expense"].copy()
    income_df = transactions_df[transactions_df["type"] == "income"].copy()

    total_income = float(income_df["amount"].sum()) if not income_df.empty else 0.0
    total_expense = float(expenses_df["amount"].sum()) if not expenses_df.empty else 0.0

    overspent_items = []
    total_overspend = 0.0

    if budget_utilization and budget_utilization.get("items"):
        for b in budget_utilization["items"]:
            if b["status"] == "exceeded" and b["allocated"] > 0:
                surplus = b["spent"] - b["allocated"]
                total_overspend += surplus
                overspent_items.append({
                    "category": b["category"],
                    "allocated": b["allocated"],
                    "spent": b["spent"],
                    "overspent_by": surplus,
                    "percentage": b["percentage"]
                })

    # Actionable Solutions formulation
    solutions = []

    # Solution 1: Overspent Category Emergency Caps
    if overspent_items:
        for item in overspent_items:
            cat = item["category"]
            over = item["overspent_by"]
            pct = item["percentage"]
            solutions.append({
                "title": f"Freeze & Cap {cat} Immediately",
                "severity": "danger",
                "impact": f"Save ₹{over:,.2f}",
                "description": f"You have exceeded your {cat} budget by ₹{over:,.2f} ({pct:.0f}% utilized). Pause non-essential purchases in {cat} for the rest of this month to avoid worsening deficit."
            })

    # Solution 2: Personal P2P Transfer Consolidation
    p2p_df = expenses_df[expenses_df["category"] == "Personal & P2P Transfers"]
    if not p2p_df.empty:
        p2p_total = float(p2p_df["amount"].sum())
        p2p_count = len(p2p_df)
        if p2p_count >= 8:
            solutions.append({
                "title": "Consolidate High-Frequency P2P Transfers",
                "severity": "warning",
                "impact": f"Target Savings: ₹{p2p_total * 0.20:,.2f}/mo",
                "description": f"You made {p2p_count} individual peer transfers totaling ₹{p2p_total:,.2f}. Frequent small UPI transfers often lead to untracked budget leakage. Setting a weekly allowance of ₹{p2p_total/4:,.0f} could save ~20%."
            })

    # Solution 3: Micro-Transaction Accumulation Control (< ₹50)
    micro_df = expenses_df[expenses_df["amount"] <= 50.0]
    if len(micro_df) >= 10:
        micro_sum = float(micro_df["amount"].sum())
        solutions.append({
            "title": "Plug Micro-Expense Leakage (< ₹50 payments)",
            "severity": "info",
            "impact": f"Leakage: ₹{micro_sum:,.2f}",
            "description": f"You have {len(micro_df)} micro-payments of ₹50 or less totaling ₹{micro_sum:,.2f}. These small frequent snacks, teas, and quick UPI taps quietly consume a large portion of your monthly cash flow."
        })

    # Solution 4: 50/30/20 Budget Realignment
    if total_income > 0:
        needs_cats = ["Bills & Utilities", "Healthcare & Medical", "Travel & Transport", "Education & Learning"]
        wants_cats = ["Food & Dining", "Shopping & Retail", "Entertainment & Recreation", "Personal & P2P Transfers"]

        needs_spent = float(expenses_df[expenses_df["category"].isin(needs_cats)]["amount"].sum())
        wants_spent = float(expenses_df[expenses_df["category"].isin(wants_cats)]["amount"].sum())
        savings = max(0.0, total_income - total_expense)

        needs_pct = (needs_spent / total_income) * 100
        wants_pct = (wants_spent / total_income) * 100
        savings_pct = (savings / total_income) * 100

        if wants_pct > 35:
            surplus_wants = wants_spent - (total_income * 0.30)
            solutions.append({
                "title": "50/30/20 Rule Discretionary Realignment",
                "severity": "warning",
                "impact": f"Reallocate: ₹{surplus_wants:,.2f}",
                "description": f"Discretionary spending ('Wants') is currently taking {wants_pct:.1f}% of your total income (optimal: 30%). Trimming discretionary purchases by ₹{surplus_wants:,.2f} will restore your savings rate to 20%."
            })

    # Health Grade
    if total_income > 0:
        net_ratio = (total_income - total_expense) / total_income
        if total_overspend > 0 or net_ratio < 0:
            health_grade = "D (Overspending Deficit)"
        elif net_ratio < 0.10:
            health_grade = "C (Borderline Savings)"
        elif net_ratio < 0.25:
            health_grade = "B (Healthy & Balanced)"
        else:
            health_grade = "A (Exceptional Financial Discipline)"
    else:
        health_grade = "B (Unclassified Income Baseline)"

    return {
        "has_overspending": len(overspent_items) > 0 or total_expense > total_income,
        "total_overspend_amount": round(total_overspend, 2),
        "overspent_categories": overspent_items,
        "solutions": solutions,
        "health_grade": health_grade
    }

def generate_personalized_recommendations(transactions_df, budget_utilization=None):
    recommendations = []

    if transactions_df.empty:
        return [
            {
                "type": "starter",
                "severity": "info",
                "title": "Welcome to Intelligent Insights",
                "message": "Upload your monthly bank statement or add transactions to receive personalized AI spending insights."
            }
        ]

    expenses_df = transactions_df[transactions_df["type"] == "expense"].copy()
    income_df = transactions_df[transactions_df["type"] == "income"].copy()

    total_income = float(income_df["amount"].sum()) if not income_df.empty else 0.0
    total_expense = float(expenses_df["amount"].sum()) if not expenses_df.empty else 0.0

    # Overspending solutions
    overspend_analysis = generate_overspending_solutions(transactions_df, budget_utilization)
    for sol in overspend_analysis["solutions"]:
        recommendations.append({
            "type": "solution",
            "severity": sol["severity"],
            "title": sol["title"],
            "message": f"{sol['description']} ({sol['impact']})"
        })

    # Monthly Comparative Recommendation
    comparison = compare_monthly_spending(transactions_df)
    if comparison.get("has_comparison"):
        curr_mth = comparison["latest_month"]
        prev_mth = comparison["prev_month"]
        pct = comparison["percent_change"]
        diff = comparison["diff_amount"]

        if pct > 10:
            recommendations.append({
                "type": "trend",
                "severity": "warning",
                "title": f"Spending Spike in {curr_mth}",
                "message": f"Your overall expenses increased by {pct:.1f}% (+₹{diff:,.2f}) compared to {prev_mth}."
            })
        elif pct < -5:
            recommendations.append({
                "type": "trend",
                "severity": "success",
                "title": f"Disciplined Spending in {curr_mth}",
                "message": f"Well done! You spent {abs(pct):.1f}% less (-₹{abs(diff):,.2f}) in {curr_mth} compared to {prev_mth}."
            })

    if not recommendations:
        recommendations.append({
            "type": "healthy",
            "severity": "success",
            "title": "Financial Habits On Track",
            "message": "Your current spending shows balanced patterns across categories without abnormal surges."
        })

    return recommendations

import sqlite3
import hashlib
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = "expense_tracker.db"

DEFAULT_BUDGET_CATEGORIES = [
    "Food & Dining",
    "Shopping & Retail",
    "Travel & Transport",
    "Personal & P2P Transfers",
    "Bills & Utilities",
    "Healthcare & Medical",
    "Education & Learning",
    "Entertainment & Recreation",
    "General Expenses"
]

ALL_CATEGORIES = DEFAULT_BUDGET_CATEGORIES + [
    "Salary & Income",
    "Allowances & Gifts"
]

def get_db_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DB_NAME)

def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Enable WAL mode for high-performance concurrent reads/writes
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
    except Exception:
        pass

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Transactions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            amount REAL NOT NULL,
            tx_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Budgets Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            month TEXT NOT NULL,
            allocated_amount REAL NOT NULL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, category, month),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Category Custom Rules Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            keyword TEXT NOT NULL,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, keyword),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Insights Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT DEFAULT 'info',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_user_date ON transactions(user_id, date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_hash ON transactions(tx_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_budget_user_month ON budgets(user_id, month)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cat_rules_user ON category_rules(user_id)")

    conn.commit()
    conn.close()

def generate_tx_hash(user_id, date, amount, description):
    clean_desc = (description or "").strip().lower()
    raw = f"{user_id}_{date}_{float(amount):.2f}_{clean_desc}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

# ----------------- User Management -----------------

def create_user(name, email, password):
    email = email.strip().lower()
    name = name.strip()
    pw_hash = generate_password_hash(password)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, pw_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {"id": user_id, "name": name, "email": email}
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def verify_user(email, password):
    user = get_user_by_email(email)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None

# ----------------- Transactions -----------------

def add_transaction(user_id, date, description, category, tx_type, amount):
    tx_hash = generate_tx_hash(user_id, date, amount, description)
    conn = get_db_connection()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT id FROM transactions WHERE user_id = ? AND tx_hash = ?", (user_id, tx_hash)).fetchone()
    if existing:
        conn.close()
        return False, "Duplicate transaction"

    cursor.execute(
        """INSERT INTO transactions (user_id, date, description, category, type, amount, tx_hash)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, date, description.strip(), category, tx_type, float(amount), tx_hash)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return True, new_id

def add_transactions_bulk(user_id, tx_list):
    conn = get_db_connection()
    cursor = conn.cursor()
    added = 0
    duplicates = 0

    # Fetch custom rules for user
    rule_rows = cursor.execute("SELECT keyword, category FROM category_rules WHERE user_id = ?", (user_id,)).fetchall()
    rules = {r["keyword"].lower(): r["category"] for r in rule_rows}

    for item in tx_list:
        date = item.get("date", "").strip()
        description = item.get("description", "").strip()
        category = item.get("category", "General Expenses").strip()
        tx_type = item.get("type", "expense").strip().lower()
        amount = float(item.get("amount", 0.0))

        if not date or amount <= 0:
            continue

        # Apply custom rule if matched
        desc_lower = description.lower()
        for kw, cat in rules.items():
            if kw in desc_lower:
                category = cat
                break

        tx_hash = generate_tx_hash(user_id, date, amount, description)
        existing = cursor.execute(
            "SELECT id FROM transactions WHERE user_id = ? AND tx_hash = ?",
            (user_id, tx_hash)
        ).fetchone()

        if existing:
            duplicates += 1
        else:
            cursor.execute(
                """INSERT INTO transactions (user_id, date, description, category, type, amount, tx_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, date, description, category, tx_type, amount, tx_hash)
            )
            added += 1

    conn.commit()
    conn.close()
    return added, duplicates

def get_transactions(user_id, category=None, tx_type=None, start_date=None, end_date=None, search=None, limit=None, offset=None):
    conn = get_db_connection()
    query = "SELECT * FROM transactions WHERE user_id = ?"
    params = [user_id]

    if category and category != "all":
        query += " AND category = ?"
        params.append(category)

    if tx_type and tx_type != "all":
        query += " AND type = ?"
        params.append(tx_type)

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    if search:
        query += " AND (description LIKE ? OR category LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term])

    query += " ORDER BY date DESC, id DESC"

    if limit is not None:
        query += " LIMIT ?"
        params.append(int(limit))
        if offset is not None:
            query += " OFFSET ?"
            params.append(int(offset))

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_transaction_by_id(tx_id, user_id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_transaction(tx_id, user_id, date, description, category, tx_type, amount):
    tx_hash = generate_tx_hash(user_id, date, amount, description)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE transactions
           SET date = ?, description = ?, category = ?, type = ?, amount = ?, tx_hash = ?
           WHERE id = ? AND user_id = ?""",
        (date, description.strip(), category, tx_type, float(amount), tx_hash, tx_id, user_id)
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

def delete_transaction(tx_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

# ----------------- Custom Category Rules -----------------

def save_category_rule(user_id, keyword, category, reclassify_existing=True):
    kw_clean = keyword.strip()
    if not kw_clean or not category:
        return False, "Invalid keyword or category."

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO category_rules (user_id, keyword, category)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id, keyword)
               DO UPDATE SET category = excluded.category""",
            (user_id, kw_clean, category)
        )
        updated_count = 0
        if reclassify_existing:
            cursor.execute(
                """UPDATE transactions
                   SET category = ?
                   WHERE user_id = ? AND description LIKE ?""",
                (category, user_id, f"%{kw_clean}%")
            )
            updated_count = cursor.rowcount

        conn.commit()
        return True, f"Rule saved! {updated_count} existing transactions updated to '{category}'."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_category_rules(user_id):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM category_rules WHERE user_id = ? ORDER BY keyword ASC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_category_rule(rule_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM category_rules WHERE id = ? AND user_id = ?", (rule_id, user_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

# ----------------- Dashboard & Analytics Summary -----------------

def get_dashboard_summary(user_id, month=None):
    conn = get_db_connection()
    
    where_clause = "WHERE user_id = ?"
    params = [user_id]
    if month:
        where_clause += " AND strftime('%Y-%m', date) = ?"
        params.append(month)

    income_row = conn.execute(
        f"SELECT COALESCE(SUM(amount), 0) as total FROM transactions {where_clause} AND type = 'income'",
        params
    ).fetchone()
    total_income = float(income_row["total"]) if income_row else 0.0

    expense_row = conn.execute(
        f"SELECT COALESCE(SUM(amount), 0) as total FROM transactions {where_clause} AND type = 'expense'",
        params
    ).fetchone()
    total_expense = float(expense_row["total"]) if expense_row else 0.0

    tx_count_row = conn.execute(
        f"SELECT COUNT(*) as cnt FROM transactions {where_clause}",
        params
    ).fetchone()
    total_transactions = tx_count_row["cnt"] if tx_count_row else 0

    balance = total_income - total_expense
    monthly_savings = max(0.0, balance)

    cat_rows = conn.execute(
        f"""SELECT category, COALESCE(SUM(amount), 0) as total
            FROM transactions
            {where_clause} AND type = 'expense'
            GROUP BY category
            ORDER BY total DESC""",
        params
    ).fetchall()
    categories = [{"category": r["category"], "total": float(r["total"])} for r in cat_rows]

    trend_rows = conn.execute(
        """SELECT strftime('%Y-%m', date) as mth,
                  COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as income,
                  COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as expense
           FROM transactions
           WHERE user_id = ?
           GROUP BY mth
           ORDER BY mth ASC
           LIMIT 12""",
        (user_id,)
    ).fetchall()
    trend = [{"month": r["mth"], "income": float(r["income"]), "expense": float(r["expense"])} for r in trend_rows]

    conn.close()

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "monthly_savings": monthly_savings,
        "total_transactions": total_transactions,
        "category_breakdown": categories,
        "monthly_trend": trend
    }

def get_top_payees(user_id, tx_type="expense", limit=8):
    conn = get_db_connection()
    rows = conn.execute(
        """SELECT description, category, type,
                  COUNT(*) as tx_count,
                  COALESCE(SUM(amount), 0) as total_amount,
                  MAX(date) as last_date
           FROM transactions
           WHERE user_id = ? AND type = ?
           GROUP BY description
           ORDER BY total_amount DESC
           LIMIT ?""",
        (user_id, tx_type, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ----------------- Budgets -----------------

def set_budget(user_id, category, month, allocated_amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO budgets (user_id, category, month, allocated_amount)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(user_id, category, month)
           DO UPDATE SET allocated_amount = excluded.allocated_amount""",
        (user_id, category, month, float(allocated_amount))
    )
    conn.commit()
    conn.close()
    return True

def get_budget_utilization(user_id, month):
    conn = get_db_connection()
    
    budget_rows = conn.execute(
        "SELECT category, allocated_amount FROM budgets WHERE user_id = ? AND month = ?",
        (user_id, month)
    ).fetchall()
    budget_map = {r["category"]: float(r["allocated_amount"]) for r in budget_rows}

    spend_rows = conn.execute(
        """SELECT category, COALESCE(SUM(amount), 0) as spent
           FROM transactions
           WHERE user_id = ? AND strftime('%Y-%m', date) = ? AND type = 'expense'
           GROUP BY category""",
        (user_id, month)
    ).fetchall()
    spend_map = {r["category"]: float(r["spent"]) for r in spend_rows}
    conn.close()

    categories_to_show = list(DEFAULT_BUDGET_CATEGORIES)
    for cat in list(budget_map.keys()) + list(spend_map.keys()):
        if cat not in categories_to_show and cat not in ["Salary & Income", "Allowances & Gifts"]:
            categories_to_show.append(cat)

    utilization_list = []
    total_budget = 0.0
    total_spent = 0.0
    overspent_categories = []

    for cat in categories_to_show:
        allocated = budget_map.get(cat, 0.0)
        spent = spend_map.get(cat, 0.0)
        remaining = allocated - spent
        percentage = (spent / allocated * 100.0) if allocated > 0 else (100.0 if spent > 0 else 0.0)

        status = "normal"
        if allocated > 0:
            if percentage >= 100.0:
                status = "exceeded"
                overspent_categories.append({
                    "category": cat,
                    "allocated": allocated,
                    "spent": spent,
                    "overspent_by": spent - allocated,
                    "percentage": round(percentage, 1)
                })
            elif percentage >= 80.0:
                status = "warning"
        elif spent > 0:
            status = "unbudgeted"

        total_budget += allocated
        total_spent += spent

        utilization_list.append({
            "category": cat,
            "allocated": allocated,
            "spent": spent,
            "remaining": remaining,
            "percentage": round(percentage, 1),
            "status": status
        })

    overall_percentage = (total_spent / total_budget * 100.0) if total_budget > 0 else 0.0

    return {
        "month": month,
        "items": utilization_list,
        "total_budget": total_budget,
        "total_spent": total_spent,
        "remaining_budget": total_budget - total_spent,
        "overall_percentage": round(overall_percentage, 1),
        "overspent_categories": overspent_categories
    }

# ----------------- Insights -----------------

def save_insights(user_id, insights_list):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM insights WHERE user_id = ?", (user_id,))
    for ins in insights_list:
        cursor.execute(
            """INSERT INTO insights (user_id, type, title, message, severity)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, ins.get("type", "general"), ins.get("title", ""), ins.get("message", ""), ins.get("severity", "info"))
        )
    conn.commit()
    conn.close()

def get_insights(user_id, limit=20):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM insights WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

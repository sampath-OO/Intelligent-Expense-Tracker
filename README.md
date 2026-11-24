# Intelligent Expense Tracker with Personalized Spending Insights

An intelligent, modern, and beginner-friendly local personal finance dashboard built with **Python Flask**, **SQLite**, **Pandas**, **Scikit-learn**, and **Chart.js**.

The application runs entirely on your local laptop, requiring no external cloud services, no paid APIs, and no internet access for core operations.

---

## 🌟 Key Features

### 1. 🔐 User Authentication & Multi-User Isolation
- Clean registration and login using email & password.
- Secure cryptographic password hashing via `werkzeug.security`.
- Strict user data isolation: each user's financial statements, budgets, transactions, and insights are isolated in SQLite.

### 2. 📊 Executive Dashboard
- **Key Financial Metrics:** Total Income, Total Expenses, Net Balance, Monthly Savings, and Savings Rate.
- **Visual Analytics:** Interactive monthly cash flow trend chart and category spending doughnut chart (powered by Chart.js).
- **Recent Transactions:** Real-time stream of the latest banking activity.
- **Budget Health Preview:** Quick visual progress bars of top budget allocations.
- **AI Alert Banner:** Highlighted recommendation or anomaly flag right at the top.

### 3. 📄 Universal Statement Extraction (PhonePe, GPay, Paytm & All Bank Formats)
- **Multi-Format Parsing Engine:** Supports:
  - **UPI Apps:** **PhonePe**, **Google Pay**, **Paytm** statements (multi-page, `Nov 21, 2026`, `CREDIT / DEBIT`, `₹Amount`, clean narration extraction, filtering out UTRs and disclaimers).
  - **Traditional Bank Statements:** **SBI**, **HDFC**, **ICICI**, **Axis**, **PNB**, **Chase**, etc.
  - **Tabular & Free-form:** Automatically detects columns and line structures.
- **Pre-Commit Review Table:** Extracted transactions are displayed in an editable table where you can adjust dates, descriptions, categories, amounts, or remove rows before confirming.
- **Duplicate Prevention:** Cryptographic SHA-256 transaction hashes prevent duplicate transactions if the same statement is uploaded more than once.
- **Scanned PDF Detection:** Gracefully identifies scanned (image-only) PDFs and displays an informative notice explaining that OCR is not included in this local version.
- **Built-in Sample Statement:** Download our pre-generated sample bank statement (`sample_bank_statement.pdf`) with one click to test extraction immediately!

---

## 🖥️ Launch as a Proper Desktop App (No Terminal / No Localhost Typing)

You do **not** need to open a terminal or type `python app.py` every time:

1. **Desktop App Icon:**
   - A desktop shortcut named **`Intelligent Expense Tracker`** has been created directly on your Windows Desktop!
   - Just double-click the shortcut to open the application in a standalone native desktop window (no browser address bar, no tabs).
2. **One-Click Batch Launcher:**
   - Double-click **`Launch_App.bat`** or **`Launch_Silent.vbs`** in the project folder to start the app silently.

### 4. 💳 Transaction Management
- Comprehensive transaction table with pagination/search.
- Search by merchant or narration keywords.
- Filter by category (Food, Shopping, Travel, Entertainment, Healthcare, Bills, Education, Salary/Income, Others).
- Filter by transaction type (Income vs Expense) and custom date ranges.
- Quick **Manual Transaction Entry**, **Edit Transaction**, and **Delete Transaction** with confirmation modals.

### 5. 🎯 Category Budget Management
- Allocate monthly spending limits for standard categories:
  - 🍔 Food
  - 🛍️ Shopping
  - 🚗 Travel
  - 🎬 Entertainment
  - 🏥 Healthcare
  - 💡 Bills & Utilities
  - 🎓 Education
  - 📦 Others
- Real-time spend vs budget tracking with smooth color-coded progress bars:
  - 🟢 **Normal:** `< 80%` of budget used.
  - 🟡 **Warning Alert:** `>= 80%` of budget used.
  - 🔴 **Overspending Warning:** `>= 100%` budget exceeded with exact surplus amount.

### 6. 🧠 AI Financial Insights & ML Analytics
- **Keyword & Rule Categorization:** High-precision categorizer maps bank statement transaction narrations to relevant expense categories.
- **Spending Pattern Analysis (Pandas Engine):**
  - Average expense per transaction.
  - Average daily burn rate across active days.
  - Day-of-week spending distribution (e.g. highest spending day, weekend vs weekday split).
  - Top expense category and highest single transaction callout.
- **Unusual Transaction Detection (Scikit-learn Isolation Forest):**
  - Unsupervised machine learning model identifies statistical outliers in transaction amounts and frequency relative to historical baseline.
  - Transparent reasons (e.g., *"₹18,900.00 is significantly higher than your average expense of ₹1,450.00"*).
  - Explicit disclaimer clarifying that flags represent statistical variance, not confirmed fraud.
- **Month-over-Month Comparison:** Compares current month spending against previous month with percentage deltas and category-by-category changes.
- **Personalized Recommendations:** Data-driven actionable advice (e.g. savings rate evaluation, discretionary spending reduction opportunities, and budget adherence tips).

### 7. 📑 Statement Reports & Downloads
- Filter statement data by specific month and category.
- **Instant CSV Export:** Standard spreadsheet format compatible with Excel and Google Sheets.
- **Audit-Ready PDF Export:** Professionally styled PDF statement generated locally with ReportLab, featuring summary KPI metrics, category breakdowns, and transaction tables.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3 (Modern Light Design System), Vanilla JavaScript |
| **Visualizations** | Chart.js (Bundled locally for 100% offline support) |
| **Backend** | Python Flask |
| **Database** | SQLite3 with foreign keys and index optimization |
| **Data Processing** | Pandas, NumPy |
| **Machine Learning** | Scikit-learn (`IsolationForest`) |
| **PDF Extraction** | `pypdf` / `pdfplumber` |
| **PDF Generation** | `reportlab` |

---

## 📂 Project Structure

```text
c:\Users\sampa\OneDrive\Documents\SE IMP\
├── app.py                      # Flask server, routes, and API endpoints
├── database.py                 # SQLite database schema, CRUD, and queries
├── pdf_extractor.py            # PDF parsing engine (tabular and text fallback)
├── ml_engine.py                # AI/ML analytics, Isolation Forest, recommendations
├── report_generator.py         # PDF (ReportLab) & CSV statement export generators
├── sample_generator.py         # Sample bank statement PDF generator
├── sample_bank_statement.pdf   # Pre-generated sample statement for quick testing
├── requirements.txt            # Python dependencies
├── test_app.py                 # Automated test suite (7 comprehensive test cases)
├── templates/
│   ├── base.html               # Shared layout, sidebar navigation, modals
│   ├── login.html              # Sign-in page
│   ├── register.html           # Account registration page
│   ├── dashboard.html          # Main financial dashboard & charts
│   ├── upload.html             # PDF upload dropzone & interactive review table
│   ├── transactions.html       # Transaction search, filter, edit & delete table
│   ├── budget.html             # Monthly budget cards & progress bars
│   ├── insights.html           # AI spending patterns, anomalies & saving tips
│   └── reports.html            # Statement generator & PDF/CSV download
├── static/
│   ├── css/
│   │   └── style.css           # Modern professional financial UI stylesheet
│   └── js/
│       ├── app.js              # Client application logic, upload & modals
│       ├── charts.js           # Chart.js initialization & themes
│       └── chart.min.js        # Offline Chart.js library (205 KB)
├── uploads/                    # Secure local temporary statement uploads
└── reports/                    # Generated export statements
```

---

## 🚀 How to Run the Application

### Step 1: Install Dependencies
Open PowerShell or your command prompt in this directory and run:

```powershell
pip install -r requirements.txt
```

### Step 2: Start the Web Application
Run:

```powershell
python app.py
```

### Step 3: Open in Browser
Open your browser and navigate to:

👉 **`http://127.0.0.1:5000`**

---

## 🧪 Testing the Application

### 1. Run Automated Tests
A complete automated test suite is provided in `test_app.py`:

```powershell
python test_app.py
```

All 7 test cases verify:
1. User registration, password hashing, and authentication.
2. PDF text extraction from digital bank statements.
3. Duplicate transaction prevention with cryptographic hashing.
4. Budget allocation and utilization calculation.
5. Pandas spending pattern decomposition and Isolation Forest anomaly detection.
6. PDF and CSV report generation.
7. Flask routes, views, and downloads.

### 2. Manual End-to-End Walkthrough
1. **Register an Account:** Go to `http://127.0.0.1:5000/register` and create an account.
2. **Upload Bank Statement:**
   - Go to **Upload Statement** from the sidebar.
   - Click **Download Sample PDF** to obtain `sample_bank_statement.pdf`.
   - Drag & drop `sample_bank_statement.pdf` into the upload box.
   - Watch the extraction animation process the 15 transactions.
   - Review or edit any rows in the interactive table, then click **Confirm & Save Transactions**.
3. **Explore Dashboard:** View the updated totals, income vs expense monthly trend chart, and category doughnut chart.
4. **Budget Management:** Navigate to **Budget Management** to view allocations for Food, Shopping, Bills, etc., and observe the progress bars.
5. **AI Financial Insights:** Navigate to **AI Financial Insights** to see the Pandas spending decomposition, Isolation Forest outlier flags, and data-driven recommendations.
6. **Download Reports:** Go to **Reports & Download**, select a month or category, and click **Download PDF Report** or **Download CSV**.

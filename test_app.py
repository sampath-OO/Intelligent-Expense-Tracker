import unittest
import os
import json
import pandas as pd
import database
import pdf_extractor
import ml_engine
import report_generator
import sample_generator
from app import app

class TestExpenseTracker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        database.init_db()
        # Generate sample statement
        cls.sample_pdf = os.path.join(os.path.dirname(__file__), "sample_bank_statement.pdf")
        if not os.path.exists(cls.sample_pdf):
            sample_generator.generate_sample_pdf(cls.sample_pdf)

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    def test_01_user_registration_and_auth(self):
        test_email = "tester_unit@example.com"
        test_pass = "securepass123"
        test_name = "Unit Tester"

        # Clean existing test user if any
        conn = database.get_db_connection()
        conn.execute("DELETE FROM users WHERE email = ?", (test_email,))
        conn.commit()
        conn.close()

        # Create user
        user = database.create_user(test_name, test_email, test_pass)
        self.assertIsNotNone(user, "User creation failed")
        self.assertEqual(user["email"], test_email)

        # Verify password
        verified = database.verify_user(test_email, test_pass)
        self.assertIsNotNone(verified, "Password verification failed")
        self.assertEqual(verified["name"], test_name)

        # Invalid password check
        bad_verified = database.verify_user(test_email, "wrongpassword")
        self.assertIsNone(bad_verified, "Bad password should return None")

    def test_02_pdf_extraction_real(self):
        # 1. Test Standard Tabular Bank Statement
        res = pdf_extractor.extract_from_pdf(self.sample_pdf)
        self.assertTrue(res["success"], f"Extraction failed: {res.get('message')}")
        self.assertGreaterEqual(len(res["transactions"]), 10, "Expected at least 10 extracted transactions")

        # 2. Test PhonePe UPI Statement Format
        phonepe_path = os.path.join(os.path.dirname(__file__), "uploads", "4_20261121123929_PhonePe_Statement_Oct2026_Nov2026.pdf")
        if os.path.exists(phonepe_path):
            p_res = pdf_extractor.extract_from_pdf(phonepe_path)
            self.assertTrue(p_res["success"], f"PhonePe extraction failed: {p_res.get('message')}")
            self.assertEqual(len(p_res["transactions"]), 40, f"Expected 40 PhonePe transactions, got {len(p_res['transactions'])}")

        # Verify fields in extracted transactions
        for tx in res["transactions"]:
            self.assertIn("date", tx)
            self.assertIn("description", tx)
            self.assertIn("amount", tx)
            self.assertIn("type", tx)
            self.assertIn("category", tx)
            self.assertGreater(tx["amount"], 0)
            self.assertIn(tx["type"], ["income", "expense"])

    def test_03_duplicate_prevention(self):
        user = database.get_user_by_email("tester_unit@example.com")
        user_id = user["id"]

        sample_txs = [
            {"date": "2026-11-01", "description": "Duplicate Test Merchant", "amount": 500.0, "type": "expense", "category": "Food"},
            {"date": "2026-11-02", "description": "Another Test Merchant", "amount": 1200.0, "type": "expense", "category": "Shopping"}
        ]

        # First insert
        added1, dup1 = database.add_transactions_bulk(user_id, sample_txs)
        self.assertEqual(added1, 2)
        self.assertEqual(dup1, 0)

        # Re-upload same transactions -> should prevent duplicates
        added2, dup2 = database.add_transactions_bulk(user_id, sample_txs)
        self.assertEqual(added2, 0)
        self.assertEqual(dup2, 2, "Duplicate transactions should have been skipped")

    def test_04_budget_management(self):
        user = database.get_user_by_email("tester_unit@example.com")
        user_id = user["id"]
        test_month = "2026-11"

        # Set budget for Food
        database.set_budget(user_id, "Food", test_month, 2000.0)

        # Check utilization
        util = database.get_budget_utilization(user_id, test_month)
        food_item = next((item for item in util["items"] if item["category"] == "Food"), None)
        self.assertIsNotNone(food_item)
        self.assertEqual(food_item["allocated"], 2000.0)
        self.assertGreaterEqual(food_item["spent"], 500.0)
        self.assertEqual(food_item["status"], "normal")

    def test_05_ml_engine_analysis(self):
        user = database.get_user_by_email("tester_unit@example.com")
        user_id = user["id"]

        # Insert batch from sample statement to test full ML features
        res = pdf_extractor.extract_from_pdf(self.sample_pdf)
        database.add_transactions_bulk(user_id, res["transactions"])

        all_tx = database.get_transactions(user_id)
        df = pd.DataFrame(all_tx)

        # 1. Spending patterns
        patterns = ml_engine.analyze_spending_patterns(df)
        self.assertTrue(patterns["has_data"])
        self.assertGreater(patterns["total_spent"], 0)
        self.assertIn("top_spending_day", patterns)

        # 2. Anomaly detection via Isolation Forest
        anomalies = ml_engine.detect_unusual_transactions(df)
        self.assertIsInstance(anomalies, list)
        if anomalies:
            self.assertIn("reason", anomalies[0])
            self.assertIn("disclaimer", anomalies[0])

        # 3. Personalized recommendations
        budget_util = database.get_budget_utilization(user_id, "2026-11")
        recs = ml_engine.generate_personalized_recommendations(df, budget_util)
        self.assertIsInstance(recs, list)
        self.assertGreater(len(recs), 0)

    def test_06_report_generation(self):
        user = database.get_user_by_email("tester_unit@example.com")
        user_id = user["id"]

        # CSV Report
        csv_out = report_generator.generate_csv_report(user_id)
        self.assertIn("ID,Date,Description,Category,Type,Amount (INR)", csv_out)

        # PDF Report
        pdf_out_path = report_generator.generate_pdf_report(
            user_id=user_id,
            user_name="Unit Tester",
            user_email="tester_unit@example.com"
        )
        self.assertTrue(os.path.exists(pdf_out_path))
        self.assertGreater(os.path.getsize(pdf_out_path), 1000)

    def test_07_flask_routes(self):
        # 1. Login flow
        resp = self.client.post("/login", data={
            "email": "tester_unit@example.com",
            "password": "securepass123"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Financial Overview", resp.data)

        # 2. Dashboard
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Total Income", resp.data)

        # 3. Upload page
        resp = self.client.get("/upload")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Digital Bank Statement", resp.data)

        # 4. Transactions page
        resp = self.client.get("/transactions")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"All Transactions", resp.data)

        # 5. Budget page
        resp = self.client.get("/budget")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Budget Management", resp.data)

        # 6. Insights page
        resp = self.client.get("/insights")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"AI Financial Insights", resp.data)

        # 7. Reports page
        resp = self.client.get("/reports")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Financial Audit & Advisory Reports", resp.data)

        # 8. CSV Download
        resp = self.client.get("/reports/download/csv")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "text/csv")

        # 9. PDF Download
        resp = self.client.get("/reports/download/pdf")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("pdf", resp.mimetype)
        resp.close()

    def test_08_insights_with_multi_month_comparison(self):
        user = database.get_user_by_email("tester_unit@example.com")
        user_id = user["id"]

        # Add transactions across two distinct months (e.g. Oct 2026 and Nov 2026)
        multi_txs = [
            {"date": "2026-10-15", "description": "October Expense", "amount": 1500.0, "type": "expense", "category": "Food & Dining"},
            {"date": "2026-10-20", "description": "October Retail", "amount": 2500.0, "type": "expense", "category": "Shopping & Retail"},
            {"date": "2026-11-10", "description": "November Dining", "amount": 1800.0, "type": "expense", "category": "Food & Dining"},
            {"date": "2026-11-12", "description": "November Travel", "amount": 800.0, "type": "expense", "category": "Travel & Transport"}
        ]
        database.add_transactions_bulk(user_id, multi_txs)

        # Login and request /insights page
        self.client.post("/login", data={
            "email": "tester_unit@example.com",
            "password": "securepass123"
        })
        resp = self.client.get("/insights")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Month-over-Month Spending Comparison", resp.data)
        self.assertIn(b"Net Shift", resp.data)

if __name__ == "__main__":
    unittest.main()

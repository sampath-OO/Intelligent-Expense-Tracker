import os
import io
import csv
import html
from datetime import datetime
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

import database
import ml_engine

def safe_text(val):
    """Safely escapes text for ReportLab XML parser."""
    if val is None:
        return ""
    text = str(val).strip()
    return html.escape(text)

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total pages and stamp
    running headers and footers on every page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor('#64748b'))

        # Running Top Header (Pages 2+)
        if self._pageNumber > 1:
            self.drawString(36, 762, "ExpenseAI &bull; Autonomous Wealth & Financial Audit System")
            self.drawRightString(576, 762, "CONFIDENTIAL AUDIT REPORT")
            self.setStrokeColor(colors.HexColor('#e2e8f0'))
            self.setLineWidth(0.6)
            self.line(36, 756, 576, 756)

        # Running Bottom Footer (All Pages)
        self.setStrokeColor(colors.HexColor('#e2e8f0'))
        self.setLineWidth(0.6)
        self.line(36, 42, 576, 42)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor('#64748b'))
        self.drawString(36, 30, "Generated On-Device &bull; Private Financial Record &bull; End-to-End Encrypted")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 30, page_str)
        self.restoreState()

def generate_csv_report(user_id, month=None, category=None):
    """
    Generates a clean CSV spreadsheet export of user transactions.
    """
    txs = database.get_transactions(user_id, category=category)
    if month:
        txs = [t for t in txs if t["date"].startswith(month)]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Date", "Description", "Category", "Type", "Amount (INR)"])

    for t in txs:
        writer.writerow([
            t["id"],
            t["date"],
            t["description"],
            t["category"],
            t["type"].capitalize(),
            f"{t['amount']:.2f}"
        ])

    return output.getvalue()

def generate_pdf_report(user_id, user_name, user_email, month=None, category=None, output_path=None):
    """
    Generates an executive-grade AI Financial Audit PDF Report with:
    - Executive Financial Health Scorecard & Letter Grade
    - In-Depth 50/30/20 Rule Spending Health Diagnosis
    - Category-by-Category Overspending Root-Causes & Prescriptive Solutions
    - Micro-Expense Leakage Analysis (< ₹50 Small Taps)
    - Machine Learning Anomaly Review (Isolation Forest)
    - Prescriptive 30-Day Financial Recovery Roadmap
    - Monthly Budget Performance Matrix
    - Itemized Transaction Ledger
    """
    if not output_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(base_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"Expense_AI_Audit_{user_id}_{month or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join(reports_dir, filename)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=46,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()

    # Custom Typography Hierarchy
    brand_style = ParagraphStyle(
        'RepBrand',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#2563eb'),
        fontName='Helvetica-Bold'
    )
    title_style = ParagraphStyle(
        'RepTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold'
    )
    meta_style = ParagraphStyle(
        'RepMeta',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor('#475569')
    )
    sec_header = ParagraphStyle(
        'SecHeader',
        parent=styles['Heading2'],
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor('#1e40af'),
        fontName='Helvetica-Bold'
    )
    body_style = ParagraphStyle(
        'RepBody',
        parent=styles['Normal'],
        fontSize=8.2,
        leading=11.5,
        textColor=colors.HexColor('#334155')
    )
    bold_cell = ParagraphStyle(
        'BoldCell',
        parent=styles['Normal'],
        fontSize=8.2,
        leading=11.5,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold'
    )
    alert_title = ParagraphStyle(
        'AlertTitle',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#991b1b'),
        fontName='Helvetica-Bold'
    )
    alert_body = ParagraphStyle(
        'AlertBody',
        parent=styles['Normal'],
        fontSize=8.0,
        leading=11.0,
        textColor=colors.HexColor('#7f1d1d')
    )
    info_box_style = ParagraphStyle(
        'InfoBox',
        parent=styles['Normal'],
        fontSize=8.2,
        leading=12.0,
        textColor=colors.HexColor('#1e293b')
    )

    elements = []

    # Fetch Data
    txs = database.get_transactions(user_id, category=category)
    if month:
        txs = [t for t in txs if t["date"].startswith(month)]

    current_mth = month or datetime.now().strftime("%Y-%m")
    budget_util = database.get_budget_utilization(user_id, current_mth)
    df = pd.DataFrame(txs) if txs else pd.DataFrame()

    # Run AI Financial Audit Computation
    if hasattr(ml_engine, "compute_financial_health_audit"):
        audit = ml_engine.compute_financial_health_audit(df, budget_util)
    else:
        audit = ml_engine.generate_overspending_solutions(df, budget_util)

    # ---------------------------------------------------------
    # Header Banner
    # ---------------------------------------------------------
    elements.append(Paragraph("EXPENSEAI &bull; AUTONOMOUS WEALTH & SPENDING INTELLIGENCE", brand_style))
    elements.append(Spacer(1, 3))
    elements.append(Paragraph("AI Financial Health Audit & Spending Optimization Report", title_style))
    elements.append(Spacer(1, 8))

    period_str = f"Audit Window: {safe_text(month)}" if month else "Audit Window: All Historical Records"
    cat_str = f" | Filtered Category: {safe_text(category)}" if category and category != 'all' else " | Category: All Categories"
    meta_html = (
        f"<b>Account Holder:</b> {safe_text(user_name)} ({safe_text(user_email)}) &nbsp;|&nbsp; "
        f"<b>Report Generated:</b> {datetime.now().strftime('%d %b %Y, %I:%M %p')}<br/>"
        f"<b>{period_str}{cat_str}</b> &nbsp;|&nbsp; "
        f"<b>Engine:</b> Scikit-Learn Isolation Forest &amp; Pandas Decomposer"
    )
    elements.append(Paragraph(meta_html, meta_style))
    elements.append(Spacer(1, 12))

    # ---------------------------------------------------------
    # 1. Executive Financial Health Scorecard
    # ---------------------------------------------------------
    scorecard_data = [
        ["Total Verified Credits", "Total Debits / Outflow", "Net Retained Capital", "Financial Health Grade"],
        [
            f"+₹{audit['total_income']:,.2f}",
            f"-₹{audit['total_expense']:,.2f}",
            f"₹{audit['balance']:,.2f}",
            audit['health_grade']
        ]
    ]
    scorecard_table = Table(scorecard_data, colWidths=[135, 135, 135, 135])
    scorecard_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f8fafc')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 10.5),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 7),
        ('TOPPADDING', (0, 1), (-1, 1), 7),
        ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor('#16a34a')),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#dc2626')),
        ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (3, 1), (3, 1), colors.HexColor('#7c3aed')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(scorecard_table)
    elements.append(Spacer(1, 8))

    # Executive AI Narrative Box
    exec_narrative_html = f"<b>AI Executive Diagnosis:</b> {safe_text(audit['executive_summary'])}"
    narrative_table = Table([[Paragraph(exec_narrative_html, info_box_style)]], colWidths=[540])
    narrative_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(narrative_table)
    elements.append(Spacer(1, 12))

    # ---------------------------------------------------------
    # 2. 50/30/20 Rule Spending Health Diagnosis
    # ---------------------------------------------------------
    elements.append(Paragraph("1. In-Depth 50/30/20 Rule Spending Health Diagnosis", sec_header))
    elements.append(Spacer(1, 5))

    r50 = audit.get("rule_50_30_20", {})
    r50_data = [
        ["Budget Component", "Benchmark %", "Actual Spent (₹)", "Actual % of Inflow", "Variance Status"],
        [
            Paragraph("<b>Essential Needs (50%)</b><br/><font color='#64748b' size=7>Bills, Groceries, Medical, Transport</font>", body_style),
            "50.0%",
            f"₹{r50.get('needs_amount', 0):,.2f}",
            f"{r50.get('needs_pct', 0):.1f}%",
            Paragraph(f"<b>{safe_text(r50.get('needs_status', 'Optimal'))}</b>", body_style)
        ],
        [
            Paragraph("<b>Discretionary Wants (30%)</b><br/><font color='#64748b' size=7>Dining, Shopping, Entertainment, P2P</font>", body_style),
            "30.0%",
            f"₹{r50.get('wants_amount', 0):,.2f}",
            f"{r50.get('wants_pct', 0):.1f}%",
            Paragraph(f"<b>{safe_text(r50.get('wants_status', 'Optimal'))}</b>", body_style)
        ],
        [
            Paragraph("<b>Net Savings & Capital (20%)</b><br/><font color='#64748b' size=7>Retained balance, debt payoff, liquid fund</font>", body_style),
            "20.0%",
            f"₹{r50.get('savings_amount', 0):,.2f}",
            f"{r50.get('savings_pct', 0):.1f}%",
            Paragraph(f"<b>{safe_text(r50.get('savings_status', 'Optimal'))}</b>", body_style)
        ]
    ]
    r50_table = Table(r50_data, colWidths=[170, 75, 105, 100, 90])
    r50_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.0),
        ('ALIGN', (1, 0), (3, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    elements.append(r50_table)
    elements.append(Spacer(1, 5))

    # Commentary note
    if r50.get("ai_commentary"):
        r50_note = Paragraph(f"💡 <b>AI Commentary:</b> {safe_text(r50['ai_commentary'])}", body_style)
        elements.append(r50_note)
    elements.append(Spacer(1, 12))

    # ---------------------------------------------------------
    # 3. Category Overspending & Root-Cause Diagnosis
    # ---------------------------------------------------------
    elements.append(Paragraph("2. Overspending Diagnosis & Root-Cause Analysis", sec_header))
    elements.append(Spacer(1, 5))

    if audit["solutions"]:
        sol_data = [["Target Category / Strategy", "Projected Impact", "Root Cause & Prescriptive Solution"]]
        for sol in audit["solutions"][:6]:
            sol_data.append([
                Paragraph(f"<b>{safe_text(sol['title'])}</b>", alert_title),
                Paragraph(f"<b>{safe_text(sol['impact'])}</b>", bold_cell),
                Paragraph(safe_text(sol['description']), body_style)
            ])

        sol_table = Table(sol_data, colWidths=[150, 100, 290])
        sol_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fee2e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#991b1b')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8.0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#fffafa'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fecaca')),
        ]))
        elements.append(sol_table)
    else:
        elements.append(Paragraph("✓ <b>Pristine Budget Adherence:</b> No categories exceeded budget limits during this evaluation window.", body_style))
    elements.append(Spacer(1, 12))

    # ---------------------------------------------------------
    # 4. Micro-Expense Leakage Analysis (< ₹50)
    # ---------------------------------------------------------
    elements.append(Paragraph("3. Micro-Expense Leakage Audit (&le; ₹50 Small Outflows)", sec_header))
    elements.append(Spacer(1, 5))

    m_leak = audit.get("micro_leakage", {})
    leak_html = (
        f"<b>Leakage Findings:</b> {safe_text(m_leak.get('explanation', ''))}<br/>"
        f"<b>Actionable Prescription:</b> {safe_text(m_leak.get('prescription', ''))}"
    )
    leak_table = Table([[
        Paragraph(f"<b>Count:</b> {m_leak.get('count', 0)} Transactions<br/><b>Total Outflow:</b> ₹{m_leak.get('total_amount', 0):,.2f}<br/><b>Annual Drain:</b> ₹{m_leak.get('annualized_projection', 0):,.2f}", bold_cell),
        Paragraph(leak_html, body_style)
    ]], colWidths=[140, 400])
    leak_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fefce8')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#fef08a')),
        ('PADDING', (0, 0), (-1, -1), 7),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(leak_table)
    elements.append(Spacer(1, 12))

    # ---------------------------------------------------------
    # 5. Isolation Forest Machine Learning Anomaly Review
    # ---------------------------------------------------------
    anomalies = audit.get("anomalies", [])
    if anomalies:
        elements.append(Paragraph("4. Machine Learning Anomaly Review (Isolation Forest)", sec_header))
        elements.append(Spacer(1, 5))

        anom_data = [["Date", "Merchant / Payee", "Category", "Amount (₹)", "ML Statistical Deviation"]]
        for anom in anomalies[:8]:
            anom_data.append([
                safe_text(anom.get("date", "")),
                safe_text(anom.get("description", "")[:28]),
                safe_text(anom.get("category", "")),
                f"₹{anom.get('amount', 0):,.2f}",
                Paragraph(safe_text(anom.get("reason", "Outlier detected")), body_style)
            ])

        anom_table = Table(anom_data, colWidths=[65, 145, 110, 75, 145])
        anom_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ede9fe')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#5b21b6')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8.0),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#faf5ff')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd6fe')),
        ]))
        elements.append(anom_table)
        elements.append(Spacer(1, 4))
        elements.append(Paragraph("<i>* Compliance Notice: Anomalies are statistical variance indicators computed via Scikit-Learn Isolation Forest based on transaction size relative to category baseline. This is an advisory review, not confirmed fraud.</i>", ParagraphStyle('SubDisclaimer', parent=body_style, fontSize=7, textColor=colors.HexColor('#6b7280'))))
        elements.append(Spacer(1, 10))

    # ---------------------------------------------------------
    # 6. Prescriptive 30-Day Recovery Roadmap
    # ---------------------------------------------------------
    roadmap = audit.get("recovery_roadmap", [])
    if roadmap:
        elements.append(Paragraph("5. Prescriptive 30-Day Financial Recovery Roadmap", sec_header))
        elements.append(Spacer(1, 5))

        road_data = [["Timeline", "Strategic Phase", "Action Plan", "Target Recovery (₹)"]]
        for rm in roadmap:
            road_data.append([
                Paragraph(f"<b>{safe_text(rm['week'])}</b>", bold_cell),
                Paragraph(f"<b>{safe_text(rm['phase'])}</b>", body_style),
                Paragraph(safe_text(rm['action']), body_style),
                Paragraph(f"<b>{safe_text(rm['target_savings'])}</b>", bold_cell)
            ])

        road_table = Table(road_data, colWidths=[95, 125, 230, 90])
        road_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0f2fe')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0369a1')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8.0),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9ff')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bae6fd')),
        ]))
        elements.append(road_table)
        elements.append(Spacer(1, 12))

    # ---------------------------------------------------------
    # 7. Monthly Budget Performance Matrix
    # ---------------------------------------------------------
    if budget_util.get("items"):
        elements.append(Paragraph("6. Monthly Budget Allocation & Performance Matrix", sec_header))
        elements.append(Spacer(1, 5))

        b_data = [["Category", "Allocated (₹)", "Actual Spent (₹)", "Balance (₹)", "Utilization %", "Status"]]
        for b in budget_util["items"]:
            if b["allocated"] > 0 or b["spent"] > 0:
                rem_str = f"₹{b['remaining']:,.2f}" if b['remaining'] >= 0 else f"-₹{-b['remaining']:,.2f}"
                st_color = "#dc2626" if b["status"] == "exceeded" else ("#d97706" if b["status"] == "warning" else "#16a34a")
                st_text = b["status"].upper()
                b_data.append([
                    safe_text(b["category"]),
                    f"₹{b['allocated']:,.2f}",
                    f"₹{b['spent']:,.2f}",
                    rem_str,
                    f"{b['percentage']:.1f}%",
                    Paragraph(f"<font color='{st_color}'><b>{st_text}</b></font>", body_style)
                ])

        if len(b_data) > 1:
            b_table = Table(b_data, colWidths=[140, 80, 80, 90, 80, 70])
            b_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8.0),
                ('ALIGN', (1, 0), (4, -1), 'RIGHT'),
                ('ALIGN', (5, 0), (5, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ]))
            elements.append(b_table)
            elements.append(Spacer(1, 12))

    # ---------------------------------------------------------
    # 8. Itemized Transaction Ledger
    # ---------------------------------------------------------
    elements.append(Paragraph(f"7. Itemized Transaction Ledger ({len(txs)} Records)", sec_header))
    elements.append(Spacer(1, 5))

    tx_table_data = [["Date", "Description / Payee", "Category", "Type", "Amount (₹)"]]
    for t in txs[:65]:
        tx_table_data.append([
            safe_text(t["date"]),
            safe_text(t["description"][:34]),
            safe_text(t["category"]),
            safe_text(t["type"].capitalize()),
            f"{t['amount']:,.2f}"
        ])

    tx_table = Table(tx_table_data, colWidths=[65, 215, 110, 60, 90])
    tx_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.0),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
    ]))
    elements.append(tx_table)

    if len(txs) > 65:
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"* Note: Showing first 65 of {len(txs)} transactions in this print edition. Complete unfiltered records are available in the CSV download.", meta_style))

    # Build document with custom canvas
    doc.build(elements, canvasmaker=NumberedCanvas)
    return output_path

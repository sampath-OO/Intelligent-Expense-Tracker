import os
import io
import csv
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import database
import ml_engine

def generate_csv_report(user_id, month=None, category=None):
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
    if not output_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(base_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"Expense_Report_{user_id}_{month or 'all'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join(reports_dir, filename)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'RepTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold'
    )
    meta_style = ParagraphStyle(
        'RepMeta',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569')
    )
    sec_header = ParagraphStyle(
        'SecHeader',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e40af'),
        fontName='Helvetica-Bold'
    )
    body_style = ParagraphStyle(
        'RepBody',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#334155')
    )
    alert_header = ParagraphStyle(
        'AlertHead',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#991b1b'),
        fontName='Helvetica-Bold'
    )

    elements = []

    # Title & Metadata
    elements.append(Paragraph("INTELLIGENT EXPENSE TRACKER", title_style))
    elements.append(Paragraph("Financial Health Audit, Overspending Diagnosis & Action Plan", ParagraphStyle('Sub', parent=title_style, fontSize=11, leading=14, textColor=colors.HexColor('#2563eb'))))
    elements.append(Spacer(1, 10))

    period_str = f"Filtered Period: {month}" if month else "Period: All Recorded Transactions"
    cat_str = f" | Category: {category}" if category and category != 'all' else ""
    meta_text = f"<b>Account Holder:</b> {user_name} ({user_email})<br/><b>Report Generated:</b> {datetime.now().strftime('%d %b %Y, %I:%M %p')}<br/><b>{period_str}{cat_str}</b>"
    elements.append(Paragraph(meta_text, meta_style))
    elements.append(Spacer(1, 14))

    # Fetch Data
    txs = database.get_transactions(user_id, category=category)
    if month:
        txs = [t for t in txs if t["date"].startswith(month)]

    total_income = sum(t["amount"] for t in txs if t["type"] == "income")
    total_expense = sum(t["amount"] for t in txs if t["type"] == "expense")
    balance = total_income - total_expense
    savings_rate = (balance / total_income * 100) if total_income > 0 else 0.0

    # Overspending diagnosis
    current_mth = month or datetime.now().strftime("%Y-%m")
    budget_util = database.get_budget_utilization(user_id, current_mth)
    df = pd.DataFrame(txs) if txs else pd.DataFrame()
    overspend_analysis = ml_engine.generate_overspending_solutions(df, budget_util)

    # 1. Executive Summary Box
    summary_data = [
        ["Total Income", "Total Expenses", "Net Savings / Balance", "Financial Health Grade"],
        [f"₹{total_income:,.2f}", f"₹{total_expense:,.2f}", f"₹{balance:,.2f}", overspend_analysis["health_grade"]]
    ]
    summary_table = Table(summary_data, colWidths=[135, 135, 135, 135])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#334155')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 11),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
        ('TOPPADDING', (0, 1), (-1, 1), 8),
        ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor('#16a34a')),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#dc2626')),
        ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (3, 1), (3, 1), colors.HexColor('#7c3aed')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    # 2. Overspending Diagnosis & Action Plan
    elements.append(Paragraph("Overspending Diagnosis & Prescriptive Action Plan", sec_header))
    elements.append(Spacer(1, 6))

    if overspend_analysis["solutions"]:
        sol_data = [["Actionable Strategy", "Target Impact", "Prescriptive Solution"]]
        for sol in overspend_analysis["solutions"][:5]:
            sol_data.append([
                Paragraph(f"<b>{sol['title']}</b>", alert_header),
                Paragraph(f"<b>{sol['impact']}</b>", body_style),
                Paragraph(sol['description'], body_style)
            ])

        sol_table = Table(sol_data, colWidths=[150, 110, 280])
        sol_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fee2e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#991b1b')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#fffafa'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fecaca')),
        ]))
        elements.append(sol_table)
    else:
        elements.append(Paragraph("✓ <b>No critical overspending detected.</b> Spending remains in positive alignment with budget guidelines.", body_style))
    elements.append(Spacer(1, 14))

    # 3. Budget Utilization Breakdown
    if budget_util.get("items"):
        elements.append(Paragraph("Monthly Budget Performance", sec_header))
        elements.append(Spacer(1, 6))

        b_data = [["Category", "Allocated (₹)", "Actual Spent (₹)", "Balance (₹)", "Utilization (%)"]]
        for b in budget_util["items"]:
            if b["allocated"] > 0 or b["spent"] > 0:
                rem_str = f"₹{b['remaining']:,.2f}" if b['remaining'] >= 0 else f"-₹{-b['remaining']:,.2f} (OVER)"
                b_data.append([
                    b["category"],
                    f"₹{b['allocated']:,.2f}",
                    f"₹{b['spent']:,.2f}",
                    rem_str,
                    f"{b['percentage']:.1f}%"
                ])

        if len(b_data) > 1:
            b_table = Table(b_data, colWidths=[160, 95, 95, 105, 85])
            b_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8.5),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ]))
            elements.append(b_table)
            elements.append(Spacer(1, 14))

    # 4. Detailed Transaction History
    elements.append(Paragraph(f"Itemized Transaction Ledger ({len(txs)} Records)", sec_header))
    elements.append(Spacer(1, 6))

    tx_table_data = [["Date", "Description", "Category", "Type", "Amount (₹)"]]
    for t in txs[:60]:
        tx_table_data.append([
            t["date"],
            t["description"][:36],
            t["category"],
            t["type"].capitalize(),
            f"{t['amount']:,.2f}"
        ])

    tx_table = Table(tx_table_data, colWidths=[65, 220, 105, 65, 85])
    tx_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(tx_table)

    if len(txs) > 60:
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"* Note: Showing first 60 of {len(txs)} transactions. Full unfiltered records are available in the CSV download.", meta_style))

    doc.build(elements)
    return output_path

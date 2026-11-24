import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_sample_pdf(file_path):
    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1e3a8a')
    )
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748b')
    )
    bold_style = ParagraphStyle(
        'BoldMeta',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )

    elements = []

    elements.append(Paragraph("GLOBAL APEX BANK - ACCOUNT STATEMENT", title_style))
    elements.append(Paragraph("Account Holder: Jane Doe | Account No: 987654321001 | Branch: MG Road, Bengaluru", subtitle_style))
    elements.append(Paragraph("Statement Period: 01 Nov 2026 to 20 Nov 2026 | Currency: INR (₹)", subtitle_style))
    elements.append(Spacer(1, 15))

    # Transaction Table Data
    table_data = [
        ["Date", "Description / Narration", "Ref / Chq", "Debit (₹)", "Credit (₹)", "Balance (₹)"],
        ["01/11/2026", "SALARY CREDIT - TECH CORP ACCT", "NEFT90281", "-", "75,000.00", "95,450.00"],
        ["02/11/2026", "SWIGGY BANGALORE ORDER #982", "UPI/65431", "450.00", "-", "95,000.00"],
        ["03/11/2026", "ELECTRICITY BILL BESCOM", "BBPS48291", "1,850.00", "-", "93,150.00"],
        ["05/11/2026", "AMAZON INDIA RETAIL PVT LTD", "POS88712", "3,299.00", "-", "89,851.00"],
        ["07/11/2026", "UBER TRIP BANGALORE", "UPI44192", "380.00", "-", "89,471.00"],
        ["09/11/2026", "NETFLIX DIGITAL SUBSCRIPTION", "ACH00921", "649.00", "-", "88,822.00"],
        ["10/11/2026", "APOLLO PHARMACY HEALTHCARE", "POS33120", "1,250.00", "-", "87,572.00"],
        ["12/11/2026", "STARBUCKS COFFEE KORAMANGALA", "UPI77182", "580.00", "-", "86,992.00"],
        ["14/11/2026", "ZOMATO RESTAURANT DINING", "UPI12984", "1,420.00", "-", "85,572.00"],
        ["15/11/2026", "FREELANCE UI DESIGN PAYMENT", "IMPS8912", "-", "12,500.00", "98,072.00"],
        ["16/11/2026", "PETROL HPCL FUEL STATION", "POS99214", "2,500.00", "-", "95,572.00"],
        ["17/11/2026", "FLIPKART INTERNET PVT LTD", "POS55122", "4,150.00", "-", "91,422.00"],
        ["18/11/2026", "AIRTEL BROADBAND FIBER BILL", "BBPS1192", "1,061.00", "-", "90,361.00"],
        ["19/11/2026", "UNUSUAL LUXURY ELECTRONICS STORE", "POS44129", "18,900.00", "-", "71,461.00"],
        ["20/11/2026", "UDEMY ONLINE COURSE CERT", "INTL7712", "799.00", "-", "70,662.00"],
    ]

    t = Table(table_data, colWidths=[65, 195, 75, 65, 65, 75])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TEXTCOLOR', (3, 1), (3, -1), colors.HexColor('#b91c1c')), # Debits red
        ('TEXTCOLOR', (4, 1), (4, -1), colors.HexColor('#15803d')), # Credits green
    ]))

    elements.append(t)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Summary: 15 Transactions processed. This is a computer-generated bank statement.", subtitle_style))

    doc.build(elements)
    return file_path

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    sample_path = os.path.join(out_dir, "sample_bank_statement.pdf")
    generate_sample_pdf(sample_path)
    print("Generated:", sample_path)

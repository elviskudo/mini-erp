"""
PO PDF Generation Service using WeasyPrint
WeasyPrint converts HTML/CSS to PDF with excellent CSS support
"""
from io import BytesIO
from datetime import datetime

# Install: pip install weasyprint
# Note: WeasyPrint requires cairo, pango, gdk-pixbuf system dependencies

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: A4;
            margin: 20mm;
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 30px;
            border-bottom: 2px solid #2563eb;
            padding-bottom: 20px;
        }
        .logo-section {
            flex: 1;
        }
        .logo {
            max-height: 60px;
            max-width: 200px;
        }
        .company-name {
            font-size: 18px;
            font-weight: bold;
            color: #1e40af;
            margin-top: 10px;
        }
        .po-info {
            text-align: right;
        }
        .po-title {
            font-size: 24px;
            font-weight: bold;
            color: #2563eb;
            margin-bottom: 10px;
        }
        .po-number {
            font-size: 16px;
            color: #666;
        }
        .po-date {
            color: #666;
        }
        .addresses {
            display: flex;
            gap: 40px;
            margin-bottom: 30px;
        }
        .address-box {
            flex: 1;
            padding: 15px;
            background: #f8fafc;
            border-radius: 8px;
        }
        .address-title {
            font-weight: bold;
            color: #1e40af;
            margin-bottom: 10px;
            font-size: 14px;
        }
        .vendor-name {
            font-weight: bold;
            font-size: 14px;
        }
        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }
        .items-table th {
            background: #2563eb;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        .items-table th:last-child,
        .items-table td:last-child {
            text-align: right;
        }
        .items-table td {
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }
        .items-table tr:nth-child(even) {
            background: #f8fafc;
        }
        .totals {
            width: 300px;
            margin-left: auto;
        }
        .totals-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e5e7eb;
        }
        .totals-row.grand-total {
            font-size: 16px;
            font-weight: bold;
            color: #2563eb;
            border-top: 2px solid #2563eb;
            border-bottom: none;
            padding-top: 12px;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
        }
        .terms-title {
            font-weight: bold;
            margin-bottom: 10px;
        }
        .terms {
            color: #666;
            font-size: 11px;
        }
        .signature-section {
            display: flex;
            justify-content: space-between;
            margin-top: 60px;
        }
        .signature-box {
            width: 200px;
            text-align: center;
        }
        .signature-line {
            border-top: 1px solid #333;
            margin-top: 50px;
            padding-top: 10px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-section">
            {% if tenant_logo %}
            <img src="{{ tenant_logo }}" class="logo" alt="Logo">
            {% endif %}
            <div class="company-name">{{ tenant_name }}</div>
            <div>{{ tenant_address }}</div>
        </div>
        <div class="po-info">
            <div class="po-title">PURCHASE ORDER</div>
            <div class="po-number">{{ po_number }}</div>
            <div class="po-date">Date: {{ po_date }}</div>
            <div class="po-date">Expected: {{ expected_date }}</div>
        </div>
    </div>

    <div class="addresses">
        <div class="address-box">
            <div class="address-title">VENDOR</div>
            <div class="vendor-name">{{ vendor_name }}</div>
            <div>{{ vendor_address }}</div>
            <div>{{ vendor_email }}</div>
            <div>{{ vendor_phone }}</div>
        </div>
        <div class="address-box">
            <div class="address-title">SHIP TO</div>
            <div class="vendor-name">{{ ship_to_name }}</div>
            <div>{{ ship_to_address }}</div>
        </div>
    </div>

    <table class="items-table">
        <thead>
            <tr>
                <th style="width: 50px">#</th>
                <th>Product</th>
                <th style="width: 80px">Qty</th>
                <th style="width: 100px">Unit Price</th>
                <th style="width: 120px">Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ item.product_name }}</td>
                <td>{{ item.quantity }}</td>
                <td>Rp {{ "{:,.0f}".format(item.unit_price) }}</td>
                <td>Rp {{ "{:,.0f}".format(item.total) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="totals">
        <div class="totals-row">
            <span>Subtotal:</span>
            <span>Rp {{ "{:,.0f}".format(subtotal) }}</span>
        </div>
        {% if shipping_cost > 0 %}
        <div class="totals-row">
            <span>Shipping:</span>
            <span>Rp {{ "{:,.0f}".format(shipping_cost) }}</span>
        </div>
        {% endif %}
        {% if insurance_cost > 0 %}
        <div class="totals-row">
            <span>Insurance:</span>
            <span>Rp {{ "{:,.0f}".format(insurance_cost) }}</span>
        </div>
        {% endif %}
        {% if customs_duty > 0 %}
        <div class="totals-row">
            <span>Customs Duty:</span>
            <span>Rp {{ "{:,.0f}".format(customs_duty) }}</span>
        </div>
        {% endif %}
        <div class="totals-row grand-total">
            <span>GRAND TOTAL:</span>
            <span>Rp {{ "{:,.0f}".format(grand_total) }}</span>
        </div>
    </div>

    <div class="footer">
        <div class="terms-title">Terms & Conditions</div>
        <div class="terms">
            {{ terms or "1. Payment due within 30 days of invoice date.<br>2. All goods remain property of vendor until payment is received.<br>3. Please reference PO number on all correspondence." }}
        </div>
    </div>

    <div class="signature-section">
        <div class="signature-box">
            <div class="signature-line">Prepared By</div>
        </div>
        <div class="signature-box">
            <div class="signature-line">Approved By</div>
        </div>
        <div class="signature-box">
            <div class="signature-line">Vendor Signature</div>
        </div>
    </div>
</body>
</html>
"""


def generate_po_pdf(po_data: dict) -> bytes:
    """
    Generate PDF for Purchase Order
    
    Args:
        po_data: Dictionary containing:
            - po_number: str
            - po_date: str
            - expected_date: str
            - tenant_name: str
            - tenant_logo: str (optional, base64 or URL)
            - tenant_address: str
            - vendor_name: str
            - vendor_address: str
            - vendor_email: str
            - vendor_phone: str
            - ship_to_name: str
            - ship_to_address: str
            - items: list of {product_name, quantity, unit_price, total}
            - subtotal: float
            - shipping_cost: float
            - insurance_cost: float
            - customs_duty: float
            - grand_total: float
            - terms: str (optional)
    
    Returns:
        PDF bytes
    """
    try:
        from weasyprint import HTML
        from jinja2 import Template
    except ImportError:
        # Fallback to simple PDF generation without WeasyPrint
        return generate_simple_pdf(po_data)
    
    template = Template(HTML_TEMPLATE)
    html_content = template.render(**po_data)
    
    pdf_bytes = BytesIO()
    HTML(string=html_content).write_pdf(pdf_bytes)
    pdf_bytes.seek(0)
    
    return pdf_bytes.read()


def generate_simple_pdf(po_data: dict) -> bytes:
    """
    Fallback PDF generation using FPDF2 (simpler, no system dependencies)
    """
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError("Please install fpdf2: pip install fpdf2")
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Header
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 10, 'PURCHASE ORDER', align='C', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 8, f"PO Number: {po_data.get('po_number', 'N/A')}", new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 8, f"Date: {po_data.get('po_date', 'N/A')}", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(10)
    
    # Vendor Info
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'VENDOR:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 6, po_data.get('vendor_name', 'N/A'), new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, po_data.get('vendor_address', ''), new_x='LMARGIN', new_y='NEXT')
    pdf.ln(10)
    
    # Items Table Header
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(37, 99, 235)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(10, 8, '#', border=1, fill=True)
    pdf.cell(70, 8, 'Product', border=1, fill=True)
    pdf.cell(25, 8, 'Qty', border=1, align='R', fill=True)
    pdf.cell(40, 8, 'Unit Price', border=1, align='R', fill=True)
    pdf.cell(45, 8, 'Total', border=1, align='R', new_x='LMARGIN', new_y='NEXT', fill=True)
    
    # Items
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(0, 0, 0)
    for idx, item in enumerate(po_data.get('items', []), 1):
        pdf.cell(10, 7, str(idx), border=1)
        pdf.cell(70, 7, str(item.get('product_name', ''))[:30], border=1)
        pdf.cell(25, 7, str(item.get('quantity', 0)), border=1, align='R')
        pdf.cell(40, 7, f"Rp {item.get('unit_price', 0):,.0f}", border=1, align='R')
        pdf.cell(45, 7, f"Rp {item.get('total', 0):,.0f}", border=1, align='R', new_x='LMARGIN', new_y='NEXT')
    
    pdf.ln(5)
    
    # Totals
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(145, 7, 'Subtotal:', align='R')
    pdf.cell(45, 7, f"Rp {po_data.get('subtotal', 0):,.0f}", align='R', new_x='LMARGIN', new_y='NEXT')
    
    if po_data.get('shipping_cost', 0) > 0:
        pdf.cell(145, 7, 'Shipping:', align='R')
        pdf.cell(45, 7, f"Rp {po_data.get('shipping_cost', 0):,.0f}", align='R', new_x='LMARGIN', new_y='NEXT')
    
    if po_data.get('insurance_cost', 0) > 0:
        pdf.cell(145, 7, 'Insurance:', align='R')
        pdf.cell(45, 7, f"Rp {po_data.get('insurance_cost', 0):,.0f}", align='R', new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(145, 10, 'GRAND TOTAL:', align='R')
    pdf.cell(45, 10, f"Rp {po_data.get('grand_total', 0):,.0f}", align='R', new_x='LMARGIN', new_y='NEXT')
    
    return pdf.output()

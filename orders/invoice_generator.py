import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_pdf_invoice(order):
    """
    Generates a professional, branded PDF invoice using ReportLab.
    Returns a bytes buffer suitable for Django FileResponse / HttpResponse.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    brand_style = ParagraphStyle(
        'BrandTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1e293b')
    )
    
    tagline_style = ParagraphStyle(
        'BrandTagline',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b')
    )

    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#0f172a')
    )

    body_style = ParagraphStyle(
        'InvoiceBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1e293b')
    )

    elements = []

    # Header Row: Brand on left, Invoice details on right
    header_data = [
        [
            Paragraph("<b>ShopSphere</b>", brand_style),
            Paragraph(f"<b>INVOICE</b><br/><font size=9 color='#64748b'>Order: #{order.order_number}</font>", ParagraphStyle('InvRight', parent=brand_style, alignment=2, fontSize=16, leading=20))
        ],
        [
            Paragraph("Premium E-Commerce Platform<br/>support@shopsphere.com | www.shopsphere.com", tagline_style),
            Paragraph(f"Date: {order.created_at.strftime('%B %d, %Y')}<br/>Status: <b>{order.order_status}</b> | Payment: <b>{order.payment_status}</b>", ParagraphStyle('DateRight', parent=body_style, alignment=2))
        ]
    ]

    header_table = Table(header_data, colWidths=[270, 270])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceAfter=15))

    # Addresses Row: Bill To & Ship To
    address_data = [
        [
            Paragraph("<b>Billed & Shipped To:</b>", h2_style),
            Paragraph("<b>Payment & Shipping Method:</b>", h2_style)
        ],
        [
            Paragraph(
                f"<b>{order.shipping_full_name}</b><br/>"
                f"{order.shipping_address_line1}<br/>"
                f"{order.shipping_address_line2 + '<br/>' if order.shipping_address_line2 else ''}"
                f"{order.shipping_city}, {order.shipping_state} {order.shipping_postal_code}<br/>"
                f"{order.shipping_country}<br/>"
                f"Phone: {order.shipping_phone}<br/>"
                f"Email: {order.user.email}",
                body_style
            ),
            Paragraph(
                f"<b>Payment Method:</b> {order.get_payment_method_display()}<br/>"
                f"<b>Payment Status:</b> {order.payment_status}<br/>"
                f"<b>Tracking Number:</b> {order.tracking_number or 'Assigned upon dispatch'}<br/>"
                f"<b>Estimated Delivery:</b> {order.estimated_delivery.strftime('%B %d, %Y') if order.estimated_delivery else '3-5 Business Days'}",
                body_style
            )
        ]
    ]

    addr_table = Table(address_data, colWidths=[270, 270])
    addr_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(addr_table)
    elements.append(Spacer(1, 15))

    # Items Table
    item_rows = [
        [
            Paragraph("<b>#</b>", table_header_style),
            Paragraph("<b>Item Description</b>", table_header_style),
            Paragraph("<b>Unit Price</b>", table_header_style),
            Paragraph("<b>Qty</b>", table_header_style),
            Paragraph("<b>Total</b>", table_header_style),
        ]
    ]

    for idx, item in enumerate(order.items.all(), 1):
        item_rows.append([
            Paragraph(str(idx), table_cell_style),
            Paragraph(item.product_name, table_cell_style),
            Paragraph(f"${item.unit_price:.2f}", table_cell_style),
            Paragraph(str(item.quantity), table_cell_style),
            Paragraph(f"${item.total_price:.2f}", table_cell_style),
        ])

    items_table = Table(item_rows, colWidths=[30, 270, 80, 50, 110])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 15))

    # Summary Table
    summary_data = [
        [Paragraph("", body_style), Paragraph("<b>Subtotal:</b>", body_style), Paragraph(f"${order.subtotal:.2f}", ParagraphStyle('R1', parent=body_style, alignment=2))],
        [Paragraph("", body_style), Paragraph("<b>Discount:</b>", body_style), Paragraph(f"-${order.discount_amount:.2f}", ParagraphStyle('R2', parent=body_style, alignment=2, textColor=colors.HexColor('#10b981')))],
        [Paragraph("", body_style), Paragraph("<b>Shipping:</b>", body_style), Paragraph(f"${order.shipping_charge:.2f}", ParagraphStyle('R3', parent=body_style, alignment=2))],
        [Paragraph("", body_style), Paragraph("<b>Total Amount:</b>", ParagraphStyle('RTotal', parent=h2_style, fontSize=11)), Paragraph(f"<b>${order.total_amount:.2f}</b>", ParagraphStyle('RTotalVal', parent=h2_style, alignment=2, fontSize=11, textColor=colors.HexColor('#2563eb')))],
    ]

    summary_table = Table(summary_data, colWidths=[270, 140, 130])
    summary_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEABOVE', (1, -1), (-1, -1), 1, colors.HexColor('#cbd5e1')),
    ]))
    elements.append(summary_table)

    # Footer Notes
    elements.append(Spacer(1, 25))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceAfter=10))
    elements.append(Paragraph("<b>Thank you for shopping with ShopSphere!</b> For warranty, returns, or support, please contact us at support@shopsphere.com quoting your Order Number.", ParagraphStyle('FooterNote', parent=tagline_style, alignment=1)))

    doc.build(elements)
    buffer.seek(0)
    return buffer

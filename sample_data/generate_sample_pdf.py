import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_sample_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        alignment=0
    )

    sub_title_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#2563eb')
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155')
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#991b1b')
    )

    story = []

    # Header section
    story.append(Paragraph("AIVOA PHARMACEUTICAL QUALITY ASSURANCE", sub_title_style))
    story.append(Paragraph("OFFICIAL CUSTOMER COMPLAINT INTAKE REPORT", title_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceAfter=15, spaceBefore=5))

    # Meta Table
    meta_data = [
        [Paragraph("<b>Complaint ID:</b> CMP-2026-0891", body_style), Paragraph("<b>Intake Date:</b> 2026-03-10", body_style)],
        [Paragraph("<b>Reported By:</b> Dr. Eleanor Vance (Chief Pharmacist)", body_style), Paragraph("<b>Incident / Event Date:</b> 2026-03-08", body_style)],
        [Paragraph("<b>Facility Name:</b> St. Jude Memorial Hospital", body_style), Paragraph("<b>Contact:</b> e.vance@stjudememorial.org / +1-555-019-2834", body_style)]
    ]
    meta_table = Table(meta_data, colWidths=[260, 260])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # Product Details Table
    story.append(Paragraph("<b>1. PRODUCT IDENTIFICATION & LOT TRACEABILITY</b>", styles['Heading2']))
    
    # Note: manufacturing_site is deliberately omitted to demonstrate AI completeness check!
    product_data = [
        [Paragraph("<b>Product Name</b>", body_style), Paragraph("Ceftriaxone Sodium for Injection USP", body_style)],
        [Paragraph("<b>Dosage & Strength</b>", body_style), Paragraph("1 g / vial (Dry powder for reconstitution)", body_style)],
        [Paragraph("<b>Dosage Form / Type</b>", body_style), Paragraph("Sterile Lyophilized Vial for IV/IM", body_style)],
        [Paragraph("<b>Batch / Lot Number</b>", body_style), Paragraph("CTX-2025-098B", body_style)],
        [Paragraph("<b>Manufacturing Date</b>", body_style), Paragraph("2025-08-14", body_style)],
        [Paragraph("<b>Expiration Date</b>", body_style), Paragraph("2027-08-31", body_style)],
        [Paragraph("<b>Quantity Affected</b>", body_style), Paragraph("24 vials (from Box 03 of Carton 12)", body_style)],
        [Paragraph("<b>Manufacturing Site</b>", body_style), Paragraph("<i>[NOT PROVIDED BY REPORTER - PENDING QA LOOKUP]</i>", body_style)]
    ]
    prod_table = Table(product_data, colWidths=[160, 360])
    prod_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(prod_table)
    story.append(Spacer(1, 15))

    # Incident Statement
    story.append(Paragraph("<b>2. DEFECT STATEMENT & CLINICAL OBSERVATIONS</b>", styles['Heading2']))
    statement_text = (
        "During pre-administration preparation in the Intensive Care Unit (ICU), the attending clinical nurse reconstituted "
        "vials of Ceftriaxone 1g (Batch CTX-2025-098B) using 10 mL Sterile Water for Injection USP under laminar flow. "
        "Upon visual inspection under direct light, visible dark particulate matter and suspended fibers were observed "
        "floating within the reconstituted solution in multiple vials. Furthermore, slight amber discoloration was noted "
        "in 4 adjacent unconstituted vials from the same pack. "
        "The administration was immediately halted prior to patient infusion. No adverse drug reaction or patient harm occurred. "
        "All 24 vials from this carton have been segregated into quarantine storage at 2-8°C awaiting QA disposal or return authorization."
    )
    story.append(Paragraph(statement_text, body_style))
    story.append(Spacer(1, 12))

    # Initial Reporter Severity Classification
    story.append(Paragraph("<b>3. REPORTER HAZARD CATEGORIZATION</b>", styles['Heading2']))
    hazard_box = [
        [Paragraph(
            "<b>Defect Classification:</b> Physical Contamination / Foreign Particulate Matter in Sterile Injectable.<br/>"
            "<b>Critical Patient Safety Alert:</b> Intravenous administration of particulate-contaminated parenteral solutions "
            "poses high risk of microvascular pulmonary embolism, localized inflammatory phlebitis, or systemic antigenic reaction.",
            callout_style
        )]
    ]
    h_table = Table(hazard_box, colWidths=[520])
    h_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fef2f2')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#f87171')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(h_table)
    story.append(Spacer(1, 20))

    # Signoff footer
    story.append(Paragraph("Reported by: Dr. Eleanor Vance, PharmD, BCPS &bull; Received by: QA Intake Desk &bull; AIVOA GMP Records System", ParagraphStyle('Foot', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#64748b'))))

    doc.build(story)
    print(f"Sample PDF successfully generated at: {output_path}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_pdf = os.path.join(current_dir, "complaint_pdf_1.pdf")
    generate_sample_pdf(output_pdf)

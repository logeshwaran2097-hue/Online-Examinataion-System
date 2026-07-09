import os
import base64
import uuid
from io import BytesIO
from datetime import datetime
import qrcode
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def generate_unique_certificate_number():
    """
    Generates a unique, professional certificate serial number.
    Format: CERT-YYYYMMDD-[8-CHAR-UUID]
    """
    date_str = datetime.utcnow().strftime('%Y%m%d')
    random_str = str(uuid.uuid4()).split('-')[0].upper()
    return f"CERT-{date_str}-{random_str}"

def generate_qr_code_bytes(url):
    """
    Generates a QR code image as bytes for the PDF.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=4,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def generate_certificate_pdf(student_name, exam_title, score, certificate_number, issue_date_str, verification_url):
    """
    Generate a high-end landscape certificate PDF in memory with a verification QR code.
    Returns: BytesIO buffer containing the PDF binary.
    """
    buffer = BytesIO()
    
    # Page setup
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom elegant styles
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=34,
        leading=40,
        textColor=colors.HexColor('#1e3a8a'), # Premium Navy
        alignment=1
    )
    
    subtitle_style = ParagraphStyle(
        'CertSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#475569'), # Muted Slate
        alignment=1
    )
    
    name_style = ParagraphStyle(
        'CertName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=colors.HexColor('#b45309'), # Golden Amber
        alignment=1
    )
    
    text_style = ParagraphStyle(
        'CertText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#334155'),
        alignment=1
    )
    
    meta_style = ParagraphStyle(
        'CertMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#475569'),
        alignment=0
    )
    
    signature_style = ParagraphStyle(
        'CertSig',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        alignment=1
    )

    story = []
    story.append(Spacer(1, 0.5 * inch))
    
    # Content flow
    story.append(Paragraph("CERTIFICATE OF COMPLETION", title_style))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("THIS IS PROUDLY PRESENTED TO", subtitle_style))
    story.append(Spacer(1, 0.25 * inch))
    
    # Recipient Name
    story.append(Paragraph(student_name.upper(), name_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Certification text
    desc_text = f"for successfully demonstrating proficiency and passing the assessment in<br/>" \
                f"<b>{exam_title}</b> with an academic grade of <b>{score}%</b>."
    story.append(Paragraph(desc_text, text_style))
    story.append(Spacer(1, 0.35 * inch))
    
    # QR Code & Signatures Table
    qr_img_bytes = generate_qr_code_bytes(verification_url)
    qr_flowable = Image(qr_img_bytes, width=1.1 * inch, height=1.1 * inch)
    
    # Footer Layout: Metas Left, QR Center, Signature Right
    footer_data = [
        [
            Paragraph(f"<b>Certificate No:</b><br/>{certificate_number}<br/><b>Issue Date:</b><br/>{issue_date_str}", meta_style),
            qr_flowable,
            Paragraph("<b>BOARD OF EXAMINERS</b><br/><font color='#64748b'>EduExam Certification Authority</font>", signature_style)
        ]
    ]
    
    footer_table = Table(footer_data, colWidths=[3.2 * inch, 1.6 * inch, 3.2 * inch])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(footer_table)
    
    # Draw double border on background via canvas callback
    def draw_certificate_border(canvas, doc):
        canvas.saveState()
        # Outer Navy Border
        canvas.setStrokeColor(colors.HexColor('#1e3a8a'))
        canvas.setLineWidth(6)
        canvas.rect(18, 18, 11 * inch - 36, 8.5 * inch - 36)
        
        # Inner Gold Border
        canvas.setStrokeColor(colors.HexColor('#b45309'))
        canvas.setLineWidth(1.5)
        canvas.rect(24, 24, 11 * inch - 48, 8.5 * inch - 48)
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_certificate_border)
    buffer.seek(0)
    return buffer

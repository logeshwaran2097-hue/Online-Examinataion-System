from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
import base64

def generate_certificate_pdf(student_name, exam_title, score, certificate_number, issue_date, qr_base64=None):
    """
    Generate a professional, beautiful landscape certificate PDF in memory using ReportLab.
    Returns: BytesIO buffer containing the PDF binary.
    """
    buffer = BytesIO()
    
    # Use landscape letter size
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom elegant styles for the certificate
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=36,
        leading=42,
        textColor=colors.HexColor('#1e3a8a'), # Premium Navy
        alignment=1 # Center
    )
    
    subtitle_style = ParagraphStyle(
        'CertSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#475569'), # Muted Slate
        alignment=1
    )
    
    name_style = ParagraphStyle(
        'CertName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=32,
        textColor=colors.HexColor('#b45309'), # Golden Amber
        alignment=1
    )
    
    text_style = ParagraphStyle(
        'CertText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#334155'),
        alignment=1
    )
    
    footer_style = ParagraphStyle(
        'CertFooter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        alignment=1
    )

    story = []
    
    story.append(Spacer(1, 0.4 * inch))
    
    # Certificate Header
    story.append(Paragraph("CERTIFICATE OF EXCELLENCE", title_style))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("PROUDLY PRESENTED TO", subtitle_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Student Name
    story.append(Paragraph(student_name.upper(), name_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Course/Exam Details
    achievement_text = f"for successfully passing the examination in <b>{exam_title}</b><br/>" \
                       f"with an outstanding score of <b>{score}%</b>."
    story.append(Paragraph(achievement_text, text_style))
    story.append(Spacer(1, 0.4 * inch))
    
    # QR Code placeholder or details table
    # Set up a grid for signatures, dates, and verification QR codes
    footer_data = [
        [
            Paragraph(f"<b>Verification No:</b> {certificate_number}<br/><b>Issue Date:</b> {issue_date}", footer_style),
            Paragraph("<b>BOARD OF DIRECTORS</b><br/>EduExam Academy", footer_style)
        ]
    ]
    
    footer_table = Table(footer_data, colWidths=[4 * inch, 4 * inch])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(footer_table)
    
    # Draw double border on background via canvas draw
    def draw_background(canvas, doc):
        canvas.saveState()
        # Primary outer border
        canvas.setStrokeColor(colors.HexColor('#1e3a8a'))
        canvas.setLineWidth(5)
        canvas.rect(20, 20, 11 * inch - 40, 8.5 * inch - 40)
        
        # Inner thin border
        canvas.setStrokeColor(colors.HexColor('#b45309'))
        canvas.setLineWidth(1.5)
        canvas.rect(26, 26, 11 * inch - 52, 8.5 * inch - 52)
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_background)
    buffer.seek(0)
    return buffer

def generate_results_pdf(student_name, results_list):
    """
    Generate a professional tabular transcript/report of results in memory.
    Returns: BytesIO buffer containing the PDF binary.
    """
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0f172a'),
        alignment=0 # Left
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569')
    )

    story = []
    
    # Header Section
    story.append(Paragraph("EXAMINATION ACADEMIC TRANSCRIPT", title_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(f"<b>Student Name:</b> {student_name}<br/><b>Date Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", meta_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Table headers
    table_data = [["Exam Subject", "Score", "Percentage", "Grade", "Status", "Date Taken"]]
    
    for r in results_list:
        table_data.append([
            r['exam_title'],
            f"{r['obtained_marks']}/{r['total_marks']}",
            f"{r['percentage']}%",
            r['grade'],
            r['status'].upper(),
            r['date']
        ])
        
    t = Table(table_data, colWidths=[2.2 * inch, 0.9 * inch, 0.9 * inch, 0.6 * inch, 0.8 * inch, 1.3 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'), # Left align subject names
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    
    story.append(t)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_individual_result_pdf(student_name, student_email, department, year, exam_title, subject_name, scorecard, qr_base64=None):
    """
    Generates a professional, detailed PDF scorecard report for an individual attempt.
    """
    buffer = io.BytesIO() if 'io' in globals() else BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1e3a8a')
    )
    
    header_style = ParagraphStyle(
        'SecHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0f172a')
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    
    story = []
    
    # 1. Document Title
    story.append(Paragraph("INDIVIDUAL EXAMINATION REPORT", title_style))
    story.append(Spacer(1, 0.15 * inch))
    
    # 2. Student & Exam Details Tables
    info_data = [
        ["Student Name:", student_name, "Exam Title:", exam_title],
        ["Email:", student_email, "Subject:", subject_name],
        ["Department:", department or "N/A", "Duration:", f"{scorecard.get('duration_minutes', '--')} mins"],
        ["Year of Study:", f"Year {year}" if year else "N/A", "Exam Date:", scorecard.get('date_taken', '--')]
    ]
    info_table = Table(info_data, colWidths=[1.3 * inch, 2.2 * inch, 1.0 * inch, 2.0 * inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#475569')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#475569')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 0.25 * inch))
    
    # 3. Scorecard table grid
    story.append(Paragraph("SCORE DETAILS", header_style))
    story.append(Spacer(1, 0.05 * inch))
    
    score_data = [
        ["Obtained Marks", "Total Marks", "Percentage", "Grade", "Rank Status", "Result Status"],
        [
            f"{scorecard.get('obtained_marks')}",
            f"{scorecard.get('total_marks')}",
            f"{scorecard.get('percentage')}%",
            f"{scorecard.get('grade')}",
            f"Rank #{scorecard.get('rank')}",
            f"{scorecard.get('pass_fail_status').upper()}"
        ]
    ]
    
    score_table = Table(score_data, colWidths=[1.15 * inch, 1.15 * inch, 1.15 * inch, 0.9 * inch, 1.15 * inch, 1.0 * inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.25 * inch))
    
    # 4. Answers Analytics & Verification Panel
    story.append(Paragraph("QUESTION-WISE BREAKDOWN", header_style))
    story.append(Spacer(1, 0.05 * inch))
    
    breakdown_data = [
        ["Total Questions:", f"{scorecard.get('total_questions')}"],
        ["Correct Answers:", f"{scorecard.get('correct_answers')}"],
        ["Wrong Answers:", f"{scorecard.get('wrong_answers')}"],
        ["Skipped Questions:", f"{scorecard.get('skipped_questions')}"]
    ]
    
    breakdown_table = Table(breakdown_data, colWidths=[1.8 * inch, 1.5 * inch])
    breakdown_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
    ]))
    
    # Check if QR code is attached to embed dynamically
    from reportlab.platypus import Image
    qr_flowable = Paragraph("<b>Secure Verification</b><br/>Scan to confirm authenticity.", body_style)
    
    if qr_base64:
        try:
            if "," in qr_base64:
                qr_base64 = qr_base64.split(",", 1)[1]
            qr_bytes = base64.b64decode(qr_base64)
            import io
            qr_buffer = io.BytesIO(qr_bytes)
            qr_flowable = Image(qr_buffer, width=1.1 * inch, height=1.1 * inch)
        except Exception as e:
            print(f"Error drawing QR code in ReportLab PDF: {e}")
            
    breakdown_row_data = [
        [breakdown_table, qr_flowable]
    ]
    
    analysis_container = Table(breakdown_row_data, colWidths=[3.8 * inch, 2.7 * inch])
    analysis_container.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(analysis_container)
    story.append(Spacer(1, 0.4 * inch))
    
    # 5. Footer Signature line
    sig_data = [
        ["", "___________________________"],
        ["", "BOARD OF EXAMINERS"],
        ["", "EduExam Online Assessment Portal"]
    ]
    sig_table = Table(sig_data, colWidths=[4.2 * inch, 2.3 * inch])
    sig_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#64748b')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(sig_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

from typing import List, Dict
from io import BytesIO
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer
from reportlab.platypus import Paragraph
from reportlab.platypus import Image
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from results.utils import get_letter_grade, session_letter_grades_count

DEBUG_MODE = False

w, h = A4
margin_X = 1*cm
margin_Y = 1*cm

pdfmetrics.registerFont(TTFont('roboto', settings.BASE_DIR/'results/static/results/fonts/Roboto-Regular.ttf'))
pdfmetrics.registerFont(TTFont('roboto-bold', settings.BASE_DIR/'results/static/results/fonts/Roboto-Bold.ttf'))
pdfmetrics.registerFont(TTFont('roboto-italic', settings.BASE_DIR/'results/static/results/fonts/Roboto-MediumItalic.ttf'))
pdfmetrics.registerFont(TTFont('roboto-m', settings.BASE_DIR/'results/static/results/fonts/Roboto-Medium.ttf'))



class HorizontalLine(Flowable):
    def __init__(self, width, thickness=1, color=colors.black):
        self.width = width
        self.thickness = thickness
        self.color = color

    def wrap(self, available_width, available_height):
        return self.width, self.thickness

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(-100, 0, self.width, 0)
        

def calculate_column_widths(num_columns, container_width, margin):
    available_width = container_width - 2*margin 
    column_width = available_width / num_columns
    return [column_width] * num_columns

def get_grading_scheme_table() -> Table:
    data = [
        ['Numerical Grade', 'Letter Grade', 'Grade Point'],
        ['80% or above', 'A+', '4.00'],
        ['75% to less than 80%', 'A', '3.75'],
        ['70% to less than 75%', 'A-', '3.50'],
        ['65% to less than 70%', 'B+', '3.25'],
        ['60% to less than 65%', 'B', '3.00'],
        ['55% to less than 60%', 'B-', '2.75'],
        ['50% to less than 55%', 'C+', '2.50'],
        ['45% to less than 50%', 'C', '2.25'],
        ['40% to less than 45%', 'C-', '2.00'],
        ['less than 40%', 'F', '0.00'],
    ]
    style_config = [
        ('FONTSIZE', (0, 0), (-1, -1), 7), 
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Bold'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (-2, 1), (-2, -1), 18),
    ]
    if DEBUG_MODE:
        style_config.extend([('GRID', (0,0), (-1,-1), 0.25, colors.ReportLabGreen)])
    

    # Create a Table
    first_col_str = data[0][0]
    second_col_str = data[0][1]
    third_col_str = data[0][2]
    for dataset in data[1:]:
        first_col_str += "\n" + dataset[0]
        second_col_str += "\n" + dataset[1]
        third_col_str += "\n" + dataset[2]
    rowHeights = [11]
    rowHeights.extend([10 for i in range(len(data)-1)])
    
     
    tbl = Table(data=data, rowHeights=rowHeights)
    tbl.setStyle(TableStyle(style_config));
    return tbl

def get_exam_controller_table() -> Table:
    data = [
        ["Controller of Examinations"],
        ['Shahjalal University of Science and'],
        ['Technology, Post Office: Sylhet-3114'],
        ['District: Sylhet, Bangladesh']
    ]
    style_config = [
        ('FONTSIZE', (0, 0), (0, 0), 15), 
        ('FONTSIZE', (0, 1), (0, -1), 11), 
        ('FONTNAME', (0, 0), (0, 0), 'roboto-bold'),
        ('FONTNAME', (0, 1), (0, -1), 'roboto'),
    ]
    if DEBUG_MODE:
        style_config.extend([('GRID', (0,0), (-1,-1), 0.25, colors.royalblue)])
    table = Table(data=data)
    table.setStyle(TableStyle(style_config))
    return table
    

def build_header(flowables) -> None: 
    logo = Image(settings.BASE_DIR/'results/static/results/images/sust.png', width=55, height=60.434)
    controller_table = get_exam_controller_table()
    phone_icon = settings.BASE_DIR/'results/static/results/images/phone.png'
    brown_paragraph_style = custom_style = ParagraphStyle(
        name='brown_paragraph_style',
        fontName = "roboto-m",
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#956b2d"),  # Set the font color
    )
    contact_info1 = "+880-821-7279-62, PABX +880-821- 713850/714479 /728741/ 717850 / 715393 / 716123, Ext-205"
    contact_info2 = "Fax: +880-821-715-257, E-mail: exm@sust.edu"
    paragraph1 =  Paragraph(f'<img src="{phone_icon}" width="10" height="10" /> : {contact_info1}<br/>{contact_info2}', brown_paragraph_style)
    # paragraph2 =  Paragraph(contact_info2, brown_paragraph_style)

    data = [
        [logo, controller_table],
        [paragraph1],
    ]
    
    style_config = [
        ('ALIGN', (1, 0), (1, 0), "RIGHT"),
        ('VALIGN', (0, 1), (0, 1), "MIDDLE"),
        ('SPAN', (0, 1), (-1, 1)),
    ]
    if DEBUG_MODE:
        style_config.extend([('GRID', (0,0), (-1,-1), 0.25, colors.gray)])
    rowsheights = [1.1*inch, 1.45*cm]
    table = Table(data=data, colWidths=calculate_column_widths(2, w, margin_X), rowHeights=rowsheights)
    table.setStyle(TableStyle(style_config))
    flowables.append(table)
    line = HorizontalLine(w)
    flowables.append(line)

def get_yearOfExamsTable(scheduled, held) -> Table:
    data = [
        ['(a) Scheduled', f':  {scheduled}'],
        ['(b) Held On', f':  {held}'],
    ]
    style_config = [
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Times-Roman'), 
        ('FONTNAME', (-1, 0), (-1, -1), 'Times-Bold'), 
        ('FONTSIZE', (0, 0), (-1, -1), 9), 
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('LEFTPADDING', (-1, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]
    if DEBUG_MODE:
        style_config.extend([('GRID', (0,0), (-1,-1), 0.25, colors.royalblue)])
    table = Table(data=data)
    table.setStyle(TableStyle(style_config))
    return table
        
def get_main_table(context: Dict) -> Table:
    table_fontSize = 9
    table_fontName_normal = 'Times-Roman'
    table_fontName_bold = 'Times-Bold'
    normalStyle = ParagraphStyle(
        name='normalStyle',
        fontName='Times',
        fontSize=table_fontSize,
        textColor=colors.black,
    )
    university_paragraph = Paragraph("Shahjalal University of Science & Technology<br/>P.O.: University, Sylhet, Bangladesh.", style=normalStyle)
    bottom_info = """The results of the student mentioned above are compiled considering aggregated of <u>four years for B. Sc. (Engg.)</u><br/>examinations.
    Additional sheets containing the subject studied, course number and grade obtained in each course<br/>are enclosed."""
    # Extracting requied data
    student = context['student']
    STUDENT_CGPA = student.total_points / student.credits_completed
    SESSION_TOTAL_CREDITS = student.session.count_total_credits()
    PERIOD_ATTENDED_FROM_YEAR = str(student.registration)[:4]
    LAST_SEMESTER_SHEDULE_TIME = context['last_semester'].start_month.split(' ')[-1]
    LAST_SEMESTER_HELD_TIME = LAST_SEMESTER_SHEDULE_TIME
    GRADES_COUNT = session_letter_grades_count(student.session)
    NUM_INCOMPLETE_STUDENTS = student.session.studentaccount_set.filter(credits_completed__lt=SESSION_TOTAL_CREDITS).count()
    if NUM_INCOMPLETE_STUDENTS == 0:
        NUM_INCOMPLETE_STUDENTS = 'Nil'
    if hasattr(context['last_semester'], 'semesterdocument'):
        semesterDoc = context['last_semester'].semesterdocument
        if semesterDoc.tabulatiobn_sheet_render_config is not None:
            try:
                held_time = semesterDoc.tabulatiobn_sheet_render_config['render_config']['tabulation_exam_time']
                LAST_SEMESTER_HELD_TIME = held_time.split(' ')[-1]
            except KeyError:
                pass
    LAST_SEMESTER_ENROLLS_COUNT = context['last_semester'].semesterenroll_set.count()    
    data = [
        ["1.", 'Name of the Student', ':', student.student_name.upper()],
        ["2.", 'Name of the College', ':', 'Sylhet Engineering College, Sylhet'],
        ["3.", 'Name of the University', ':', university_paragraph],
        ["4.", 'Registration & Exam Roll No.', ':', student.registration],
        ["5.", 'Period Attended', ':', f'{PERIOD_ATTENDED_FROM_YEAR}-{LAST_SEMESTER_HELD_TIME}'],
        ["6.", 'Years of Examination', ':', get_yearOfExamsTable(LAST_SEMESTER_SHEDULE_TIME, LAST_SEMESTER_HELD_TIME)],
        ["7.", 'Degree(s) Awarded', ':', f'B.Sc. (Engg.) in {student.session.dept.fullname}'],
        ["8.", 'Grading System', ':', get_grading_scheme_table()],
        [Spacer(1, 10)],
        ["9.", 'Credits Completed', ':', student.credits_completed],
        ["10.", 'Cumulative  Grade Point Obtained', ':', Paragraph(f"CGPA: <b>{round(STUDENT_CGPA, 2)} (With Distinction)</b>", style=normalStyle)],
        ["11.", 'Letter Grade Obtained', ':', Paragraph(f"<b>{get_letter_grade(STUDENT_CGPA)}</b>", style=normalStyle)],
        ["12.", 'Total Number of Students Appeared', ':', Paragraph(f"<b>{LAST_SEMESTER_ENROLLS_COUNT}</b>", style=normalStyle)],
        ["13."
         , Paragraph(
             'Total Number of  Degree Awarded<br/>this Year in Applicant\'s Academic Field', style=normalStyle
         )
         , ':'
         , Paragraph(
            f"<b>A+ = {GRADES_COUNT['A+']}, A = {GRADES_COUNT['A']}, A- = {GRADES_COUNT['A-']}, B+ = {GRADES_COUNT['B+']}, B = {GRADES_COUNT['B']}, B- = {GRADES_COUNT['B-']}, C+ = {GRADES_COUNT['C+']} <br/>C = {GRADES_COUNT['C']}, C- = {GRADES_COUNT['C-']}, Withheld = Nil, Incomplete = {NUM_INCOMPLETE_STUDENTS}</b>",
            style=normalStyle
         )
        ],
        ["14.", 'Medium of Instruction', ':', Paragraph("<b>English</b>", style=normalStyle)],
        [Paragraph(bottom_info, normalStyle), '', '', '']
    ]
    style_config = [
        ('ALIGN', (0,0), (0,-1), "RIGHT"),
        ('VALIGN', (0,0), (-1,-1), "TOP"),
        ('FONTSIZE', (0, 0), (-1, -1), table_fontSize), 
        ('FONTNAME', (0, 0), (-1, -1), table_fontName_normal), 
        ('FONTNAME', (-1, 0), (-1, 1), table_fontName_bold), # Student Name and College
        ('FONTNAME', (2, 0), (2, -1), table_fontName_bold), # Colon Column
        ('FONTNAME', (-1, 3), (-1, 4), table_fontName_bold), # Regisration No.and Peroid attended
        ('FONTNAME', (-1, 6), (-1, 6), table_fontName_bold), # Degree(s) Awarded
        ('FONTNAME', (-1, 9), (-1, 9), table_fontName_bold), # Credits
        ('SPAN', (0, -1), (-1, -1)), # Bottom info
        ('LEFTPADDING', (0, -1), (0, -1), 20),
        ('RIGHTPADDING', (0, -1), (0, -1), 0),
        ('TOPPADDING', (0, -1), (0, -1), 30),
        ('ALIGN', (0, -1), (0, -1), "CENTER"),
    ]
    if DEBUG_MODE:
        style_config.extend([('GRID', (0,0), (-1,-1), 0.25, colors.gray)])
    colwidths = [0.6*cm, 2.5*inch, 0.5*cm, 3.5*inch]
    table = Table(data=data, colWidths=colwidths)
    table.setStyle(TableStyle(style_config))
    return table

def build_body(flowables: List, context: Dict) -> None:
    title_style = ParagraphStyle(
        name='TitleStyle',
        fontName='Times-Bold',
        fontSize=11,
        textColor=colors.black,
        alignment=1,
    )
    flowables.append(Paragraph("<u>TRANSCRIPT OF ACADEMIC RECORDS</u>", style=title_style))
    flowables.append(Spacer(1, 15))
    flowables.append(get_main_table(context))

def get_footer(context):
    footer_data = [
        [f"Prepared by: {context['admin_name']}", 'Compared by:', 'Deputy Controller of Examinations']
    ]
    style_config = [
        ('FONTSIZE', (0, 0), (-1, -1), 10), 
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('ALIGN', (-1, 0), (-1, 0), 'CENTER'),
    ]
    if DEBUG_MODE:
        style_config.extend([('GRID', (0,0), (-1,-1), 0.25, colors.ReportLabLightBlue)])
        
    signature_table = Table(data=footer_data, colWidths=calculate_column_widths(len(footer_data[0]), w-2*cm, 1.2*cm))
    signature_table.setStyle(TableStyle(style_config))
    
    return signature_table
  
def add_footer(canvas, doc, context):
    footer = get_footer(context)
    footer.wrapOn(canvas, 0, 0)
    footer.drawOn(canvas=canvas, x=0.9*inch, y=0.7*inch)  

def get_transcript(context: Dict):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=margin_Y, title="Academic Transcript")
    story = []
    build_header(story)
    story.append(Spacer(1, 15))
    build_body(story, context)
   
    doc.build(story, onFirstPage=lambda canv, doc: add_footer(canvas=canv, doc=doc, context=context))
    return buffer.getvalue()
    

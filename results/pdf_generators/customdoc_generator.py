from .transcript_generator_manual import get_transcript
from .gradesheet_generator_manual import get_gradesheet
import io
import fitz  # PyMuPDF

def map_context_for_transcript(data):
    context = {
        'name': data['student_data']['name'],
        'reg_num': data['student_data']['registration'],
        'cgpa': data['student_data']['grade_point'],
        'degree': data['student_data']['degree_awarded'],
        'letter_grade': data['student_data']['letter_grade'],
        'credits_complete': data['student_data']['credits_completed'],
        'duration': data['student_data']['period_attended'],
        'exam_scheduled': data['student_data']['years_of_exam_scheduled'],
        'exam_held': data['student_data']['years_of_exam_held_in'],
        'session_degrees_count': data['student_data']['total_number_of_degree_awarded'],
        'students_appears': data['student_data']['students_appeared'],
    }
    return context

def map_formdata_for_gradesheet(data):
    formdata = {
        'dept': data['student_data']['dept_name'],
        'session': data['student_data']['session'],
        'reg_num': data['student_data']['registration'],
        'name': data['student_data']['name'],
        'final_res_credit': data['student_data']['credits_completed'],
        'final_res_cgpa': data['student_data']['grade_point'],
        'final_res_letter_grade': data['student_data']['letter_grade'],
    }
    return formdata

def map_semester_for_gradesheet(data, year_num, year_semester):
    year = data['years'][year_num]
    if len(year) == 0:
        return None
    semester = year[year_semester]
    semester_data = {
        'year': year_num,
        'year_semester': year_semester,
        'held_in': semester['held_in'],
        'semester_credits': semester['semester_credits'],
        'semester_gp': semester['semester_gp'],
        'cumulative_credits': semester['semester_credits'],
        'cumulative_gp': semester['cumulative_gp'],
        'cumulative_lg': semester['cumulative_lg'],
        'courses': semester['courses']
    }
    return semester_data
    

def merge_pdfs_from_buffers(pdf_buffers):
    # Create a new PDF document to store the merged pages
    merged_pdf = fitz.open()

    # Iterate through each PDF buffer and add pages to the merged document
    for buffer in pdf_buffers:
        pdf_document = fitz.open("pdf", buffer)
        merged_pdf.insert_pdf(pdf_document)

    # Save the merged PDF to a buffer
    merged_buffer = io.BytesIO()
    merged_pdf.save(merged_buffer)
    merged_buffer.seek(0)  # Set the buffer's cursor to the beginning
    merged_pdf.close()

    return merged_buffer

# Example list of PDF buffers (replace these with your actual PDF buffers)
# pdf_buffers_list = [b'...', b'...', b'...']  # Replace with your PDF buffers

# Merge the PDF buffers from the list
# merged_buffer = merge_pdfs_from_buffers(pdf_buffers_list)

# Now, merged_buffer contains the merged PDF in a buffer
# You can save it to a file or use it as needed
# For example, to save the merged PDF to a file:
# with open('merged.pdf', 'wb') as output_file:
#     output_file.write(merged_buffer.read())


def render_customdoc(data, admin_name):
    transcript_context = map_context_for_transcript(data)
    transcript_context['admin_name'] = admin_name
    documents = []
    transcript = get_transcript(transcript_context)
    documents.append(transcript)
    formdata = map_formdata_for_gradesheet(data)
    for i in range(4):
        excel_data = {}
        year_num = i+1
        for sem_num in data['years'][year_num]:
            semester_data = map_semester_for_gradesheet(data, year_num, sem_num)
            if semester_data is not None:
                excel_data[f'semester_{sem_num}'] = semester_data
        if num_semesters:= len(excel_data):
                gradesheet = get_gradesheet(formdata, excel_data, num_semesters)
                documents.append(gradesheet)
    merged_buffer = merge_pdfs_from_buffers(documents)
    return merged_buffer.getvalue()
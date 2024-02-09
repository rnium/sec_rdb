import fitz
import io

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

BANGLA_ORDINAL_MAPPING = {
    1 : '১ম',
    2 : '২য়',
    3 : '৩য়',
    4 : '৪র্থ',
    5 : '৫ম',
    6 : '৬ষ্ঠ',
    7 : '৭ম',
    8 : '৮ম'
}

BANGLA_NUMBER_MAPPING = {
    0 : '০',
    1 : '১',
    2 : '২',
    3 : '৩',
    4 : '৪',
    5 : '৫',
    6 : '৬',
    7 : '৭',
    8 : '৮',
    9 : '৯'
}

def get_bangla_ordinal_upto_eight(n):
    return BANGLA_ORDINAL_MAPPING.get(n, '*')

def get_year_number_in_bangla(year):
    bn_year = ''
    for c in str(year):
        if bn_char:=BANGLA_NUMBER_MAPPING.get(int(c.strip()), False):
            print(bn_char, flush=1)
            bn_year += bn_char
    return bn_year
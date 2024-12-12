# document.py
import os
import json 
from flask import flash, session, request, redirect, render_template, url_for


from reportlab.pdfgen import canvas
from flask import send_file
from io import BytesIO
from docx import Document

from auth import is_logged_in

import pandas as pd

from fpdf import FPDF

DOCUMENTS_FILE = './documents'


# Create a PDF class
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Approaches for Exploring Dataset to Build Business KPIs', align='C', ln=1)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')


def format_text2df(text):
    # Splitting text into lines and extracting rows
    lines = text.strip().split("\n")
    header = [col.strip() for col in lines[0].split("|")[1:-1]]  # Extracting header
    rows = [line.split("|")[1:-1] for line in lines[2:]]  # Extracting rows

    # Parsing each row and cleaning data
    parsed_data = [{header[i]: cell.strip() for i, cell in enumerate(row)} for row in rows]

    # Creating a DataFrame for better presentation and manipulation
    return pd.DataFrame(parsed_data)


def export_text2pdf(text, filename):
    print("START ", text)
    # Step 1: Find the first and last pipe positions
    start_table = text.find('|') 
    print("START ", start_table)
    end_table = text.rfind('|')
    print("END ", end_table)
  

    # Step 2: Extract the pretext, table, and posttext
    pretext = text[:start_table-1].strip()  # Text before the first pipe
    table_text = text[start_table:end_table].strip()  # Text between the pipes
    posttext = text[end_table+1:].strip()  # Text after the last pipe


    print(table_text)
    # format text into a dataframe
    df = format_text2df(table_text)

    # Initialize a new PDF instance
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Table configuration
    col_widths = [60, 80, 50]  # Column widths
   
    # Set column widths and header row
    pdf.set_font('Arial', '', 10)
    col_widths = [60, 80, 50]

    # Add pre text
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, pretext)
    pdf.ln(10)

    # Add table rows
    pdf.set_font('Arial', '', 10)
    for _, row in df.iterrows():
        row_height = max([pdf.get_string_width(str(field)) // col_widths[idx] * 10 for idx, field in enumerate(row)]) + 10
        x_start = pdf.get_x()
        y_start = pdf.get_y()
    
        for idx, field in enumerate(row):
            pdf.multi_cell(col_widths[idx], 10, str(field), border=1, align='L')
            x_start += col_widths[idx]
            pdf.set_xy(x_start, y_start)
        pdf.ln(row_height)  # Move to the next row

    pdf.ln(10)
    # Add post-table text
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, posttext)


    # Step 2: Write the PDF to an in-memory buffer
    pdf_buffer = BytesIO()
    pdf_buffer.seek(0)

    # Step 3: Return the PDF as an HTTP response
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        headers={
            "Content-Disposition": "inline; filename=report.pdf"
        }
    )

   


# Function to export text to a PDF file
def export_text_to_pdf(text, filename):
    # Create a BytesIO buffer to hold the PDF data
    pdf_buffer = BytesIO()
    
    # Create a canvas using reportlab
    pdf_canvas = canvas.Canvas(pdf_buffer)
    pdf_canvas.setTitle(filename)

    x_position = 120
    y_position = 800

    # Split the text into lines
    lines = text.split('\n')
    for line in lines:
        pdf_canvas.drawString(x_position, y_position, line)
        y_position -= 15

        # Create a new page if the text goes too low
        if y_position < 50:
            pdf_canvas.showPage()
            y_position = 800

    pdf_canvas.save()
    print(f"Text successfully exported to {filename}")

    # Move the buffer cursor to the beginning
    pdf_buffer.seek(0)

    # Return the PDF file as an HTTP response
    return send_file(
        pdf_buffer,
        as_attachment=True,  # Set to False if you want to view in the browser
        download_name="summary_result.pdf",
        mimetype="application/pdf"
    )







def export_text_to_docx(text, filename):
   # Create a new RTF Document
    doc = Document()

    # Add a title (optional)
    doc.add_heading("Result Summary", level=1)

    # Add text content
    doc.add_paragraph(text)

    # Save the document to memory (using BytesIO)
    byte_stream = BytesIO()
    doc.save(byte_stream)
    byte_stream.seek(0)  # Go to the beginning of the byte stream


    # Return the PDF file as an HTTP response
    return send_file(
        byte_stream,
        as_attachment=True,  # Set to False if you want to view in the browser
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )







# Function to create a new prompt
def create_document(filename, pretext, posttext, summary):
    if request.method == 'POST':
        # print(filename, pretext, posttext)
        if filename and pretext and posttext:
            documents = read_documents()
            document_id = len(documents) + 1
            user_id = session['user']
            new_document = {'id': document_id, 'user_id': user_id, 'filename': filename, 'pretext': pretext, 'posttext': posttext, 'summary': summary}
            write_documents(new_document)
            flash('Documents created successfully!')
            return document_id
        else:
            flash('Document text cannot be empty.')
    return 


def write_documents(document):
    path = os.path.join(DOCUMENTS_FILE, session['user'])
    if not os.path.exists(path):
        os.makedirs(path)   

    # print('path', path)
    # print('document', f"{os.path.join(path, document['filename'])}.json")
    with open(f"{os.path.join(path, document['filename'])}.json", 'w') as file:
        json.dump(document, file, indent=4)

# Helper function to read prompts from JSON file
def read_documents():
    path = os.path.join(DOCUMENTS_FILE, session['user'])
    results = []
    if not os.path.exists(path):
        return []
    for filename in os.listdir(path):
        if filename.endswith('.json'):
            file_path = os.path.join(path, filename)
            with open(file_path, 'r') as file:
                try:
                    # load json data
                    data = json.load(file)
                    # extract id and filename if they exist 
                    if 'id' in data and 'filename' in data:
                        results.append({
                            'id': data['id'],
                            'filename': data['filename']
                        })
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from file {filename}: {e}")
    return results


# Function for prompt page
def documents_page():
    # If user is not logged in, redirect to login page
    if not is_logged_in():
        return redirect(url_for('login'))
    session.pop('_flashes', None)
    # print(read_documents())
    return render_template('documents.html', documents=read_documents())




def replace_pipe_with_line_break(data):
    # This function will traverse the data and replace pipes with line breaks in strings
    if isinstance(data, dict):
        # Iterate over dictionary items
        return {key: replace_pipe_with_line_break(value) for key, value in data.items()}
    elif isinstance(data, list):
        # Iterate over list elements
        return [replace_pipe_with_line_break(element) for element in data]
    elif isinstance(data, str):
        # Replace pipes with line breaks in strings
        return data.replace(' | ', '\n')
    else:
        # If it's neither a list, dict, nor str, return as is
        return data

def document_preview(filename):
    # If user is not logged in, redirect to login page
    if not is_logged_in():
        return redirect(url_for('login'))
    
    
    if request.method == 'POST':
        filename = request.form['filename']
   
        if 'download' in request.form:
            summary = request.form['summary']
            # export to PDF
            return export_text_to_docx(summary, "result_summary.docx")
        elif 'cancel' in request.form:
            # Go back to the form
            return redirect(url_for('home'))
        

    file_path = f"{os.path.join(DOCUMENTS_FILE, session['user'], filename)}.json"
    with open(file_path, 'r') as file:
        # load json data
        json_data = json.load(file)
    
    # Apply pipe replacement
    document = replace_pipe_with_line_break(json_data)
               
    if not document:
        flash('Document not found.')
        return redirect(url_for('documents'))
    
    return render_template('result.html', page_title="My Documents (Archieved)", filename=filename, result=document['summary'])

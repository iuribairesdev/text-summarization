# document.py
import os
import json 
from flask import flash, session, request, redirect, render_template, url_for
from auth import is_logged_in
DOCUMENTS_FILE = './documents'



# Function to create a new prompt
def create_document(filename, pretext, posttext, summary):
    if request.method == 'POST':
        print(filename, pretext, posttext)
        if filename and pretext and posttext:
            documents = read_documents()
            document_id = len(documents) + 1
            user_id = session['user']
            new_document = {'id': document_id, 'user_id': user_id, 'filename': filename, 'pretext': pretext, 'posttext': posttext, 'summary': summary}
            documents.append(new_document)
            write_documents(documents)
            flash('Documents created successfully!')
            return document_id
        else:
            flash('Document text cannot be empty.')
    return 


def write_documents(documents):
    path = os.path.join(DOCUMENTS_FILE, session['user'])
    if not os.path.exists(path):
        os.makedirs(path)   

    print('path', path)
    print('document', f"{os.path.join(path, documents[0]['filename'])}.json")
    with open(f"{os.path.join(path, documents[0]['filename'])}.json", 'w') as file:
        json.dump(documents, file, indent=4)

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
                    for i in range(len(data)):
                        if 'id' in data[i] and 'filename' in data[i]:
                            results.append({
                                'id': data[i]['id'],
                                'filename': data[i]['filename']
                            })
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from file {filename}: {e}")
    return results


# Function for prompt page
def documents_page():
    # If user is not logged in, redirect to login page
    if not is_logged_in():
        return redirect(url_for('login'))
    print(read_documents())
    return render_template('documents.html', documents=read_documents())


def document_preview(filename):
    # If user is not logged in, redirect to login page
    if not is_logged_in():
        return redirect(url_for('login'))
        
    file_path = f"{os.path.join(DOCUMENTS_FILE, session['user'], filename)}.json"
    with open(file_path, 'r') as file:
        # load json data
        document = json.load(file)[0]
                   
    if not document:
        flash('Document not found.')
        return redirect(url_for('documents'))

    return render_template('document_preview.html', document=document)

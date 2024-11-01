import os
from flask import Flask, flash, jsonify, request, redirect, render_template, session, url_for
from werkzeug.utils import secure_filename
from contract import Contract
import json
from dotenv import load_dotenv
import dill

# Initialize Flask application
app = Flask(__name__)

load_dotenv()

# Secret key to encrypt session data
app.secret_key = os.environ.get('SECRET_KEY')

# Define the folder to save uploaded files
UPLOAD_FOLDER = './uploaded_files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed Extensions
ALLOWED_EXTENSIONS = {'pdf'}

PROMPT_FILE = 'prompts.json'

# Hardcoded user credentials for demonstration purposes
users = json.loads(os.getenv('USERS'))


# Create a helper function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to validate if the input is a valid list of strings
def validate_string(str1):
    if not isinstance(str1, str):
        return False, []
    # Convert comma-separated string to a list and strip any extra spaces
    str_list = [s.strip() for s in str1.split(',') if s.strip()]
    # If the list is empty, return False
    if len(str_list) == 0:
        return False, []
    return True, str_list



# Route to display the file preview
@app.route('/process', methods=['POST'])
def process():
    # If user is not logged in, redirect to login page
    if not is_logged_in():
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'confirm' in request.form:

            filename = request.form['filename']
            client_name = request.form['client_name']
            prompt_id = request.form.get('prompt_id')

            # Validate and convert search_string to a list
            is_valid, str_list = validate_string(client_name)
            if not is_valid:
                return jsonify({"error": "search_string must be a comma-separated list of strings"}), 400


            prompts = read_prompts()
            prompt = next((p for p in prompts if str(p['id']) == prompt_id), None)
            pretext = prompt['pretext']
            posttext = prompt['posttext']

            # print('pretext', pretext)

            # print('posttext', posttext)

            contract = Contract(os.path.join(app.config['UPLOAD_FOLDER']), str_list, pretext, posttext)
            contract.save_object()

            # print('contract ', contract.contracts_text_with_prepost)
            # print('contract', contract.contracts_text)
            result = contract.send_to_openai()

            # resp = contract.paste_text()
            # return jsonify({"message": f"Successfully Sent to OpenAI!",
            #               "parsed_text": f"{resp}"
            #                }), 200

            # Proceed to the next stage with confirmed data
            # flash('Contract processed successfully!')

            # return redirect(url_for('home'))
        elif 'cancel' in request.form:
            # Go back to the form
            return redirect(url_for('home'))

    return render_template('result.html', result=result)
 

# Route to display the file preview
@app.route('/preview', methods=['POST'])
def preview():
    # If user is not logged in, redirect to login page
    if not is_logged_in():
        return redirect(url_for('login'))

    if request.method == 'POST':

        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        client_name = request.form['client_name']
        prompt_id = request.form.get('prompt_id')

        # Validate and convert search_string to a list
        is_valid, str_list = validate_string(client_name)
        if not is_valid:
            return jsonify({"error": "search_string must be a comma-separated list of strings"}), 400


        # If no file is selected
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if not allowed_file(file.filename):
            return jsonify({"error": "Please, upload PDF files only!"}), 400


        # If file is valid and has allowed extension
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print('File successfully uploaded!')        
 
            prompts = read_prompts()
            prompt = next((p for p in prompts if str(p['id']) == prompt_id), None)
            pretext = prompt['pretext']
            posttext = prompt['posttext']

            contract = Contract(os.path.join(app.config['UPLOAD_FOLDER']), str_list, pretext, posttext)
            # contract.save_object()
    


    return render_template('preview.html', filename=filename, client_name=client_name, prompt_id=prompt_id, contract=contract)
 

   
# Route to handle the home page and file uploads
@app.route('/', methods=['GET', 'POST'])
def home():
     # If user is not logged in, redirect to login page
    if not is_logged_in():
        return redirect(url_for('login'))

    # GET request renders the upload form
    return render_template('home.html', prompts=read_prompts())




# Helper function to check if user is logged in
def is_logged_in():
    return 'user' in session

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the credentials are valid
        if username in users and users[username] == password:
            session['user'] = username
            return redirect(url_for('home'))
        else:
            error = "Invalid credentials. Please try again."
            return render_template('login.html', error=error)

    # Render the login form for GET requests
    return render_template('login.html')

# Route for logging out
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))





# Helper function to write prompts to JSON file
def write_prompts(prompts):
    with open(PROMPT_FILE, 'w') as file:
        json.dump(prompts, file, indent=4)


# Route to create a new prompt
@app.route('/create', methods=['GET', 'POST'])
def create_prompt():
    if request.method == 'POST':
        title = request.form.get('title')
        pretext = request.form.get('pretext')
        posttext = request.form.get('posttext')
        print(title, pretext, posttext)
        if title and pretext and posttext:
            prompts = read_prompts()
            prompt_id = len(prompts) + 1
            new_prompt = {'id': prompt_id, 'title': title, 'pretext': pretext, 'posttext': posttext}
            prompts.append(new_prompt)
            write_prompts(prompts)
            flash('Prompt created successfully!')
            return redirect(url_for('prompts'))
        else:
            flash('Prompt text cannot be empty.')
    
    return render_template('prompt_form.html', action='Create', prompt=None)

# Route to edit an existing prompt
@app.route('/edit/<int:prompt_id>', methods=['GET', 'POST'])
def edit_prompt(prompt_id):
    prompts = read_prompts()
    prompt = next((p for p in prompts if p['id'] == prompt_id), None)
    
    if not prompt:
        flash('Prompt not found.')
        return redirect(url_for('prompts'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        pretext = request.form.get('pretext')
        posttext = request.form.get('posttext')
        print(title, pretext, posttext)
        if title and pretext and posttext:
            prompt['title'] = title
            prompt['pretext'] = pretext
            prompt['posttext'] = posttext
            write_prompts(prompts)
            flash('Prompt updated successfully!')
            return redirect(url_for('prompts'))
        else:
            flash('Prompt text cannot be empty.')
    
    return render_template('prompt_form.html', action='Edit', prompt=prompt)

# Route to delete a prompt
@app.route('/delete/<int:prompt_id>')
def delete_prompt(prompt_id):
    prompts = read_prompts()
    prompt = next((p for p in prompts if p['id'] == prompt_id), None)
    
    if prompt:
        prompts = [p for p in prompts if p['id'] != prompt_id]
        write_prompts(prompts)
        flash('Prompt deleted successfully!')
    else:
        flash('Prompt not found.')
    
    return redirect(url_for('prompts'))

# Helper function to read prompts from JSON file
def read_prompts():
    if not os.path.exists(PROMPT_FILE):
        return []
    with open(PROMPT_FILE, 'r') as file:
        return json.load(file)


# Route for prompt page
@app.route('/prompts')
def prompts():
    # If user is not logged in, redirect to login page
    if not is_logged_in():
        return redirect(url_for('login'))
    
    prompts = read_prompts()
    return render_template('prompts.html', prompts=prompts)

# Run the Flask app on localhost
if __name__ == '__main__':
    # Ensure the upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(host='0.0.0.0', port=8080, debug=True)
    
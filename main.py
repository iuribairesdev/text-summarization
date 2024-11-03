import os
from flask import Flask, jsonify, request, redirect, render_template, url_for, session
from werkzeug.utils import secure_filename
from contract import Contract
import dill

from settings import settings_page
from auth import is_logged_in, login, logout
from prompts import edit_prompt, create_prompt, read_prompts, delete_prompt, prompts_page

# Initialize Flask application
app = Flask(__name__)

# Secret key to encrypt session data
app.secret_key = os.environ.get('SECRET_KEY')

# Define the folder to save uploaded files
UPLOAD_FOLDER = './uploaded_files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed Extensions
ALLOWED_EXTENSIONS = {'pdf'}




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
@app.route('/result', methods=['GET', 'POST'])
def result():
    # If user is not logged in, redirect to login page
    if not is_logged_in():
        return redirect(url_for('login'))

    result = 'No response from ChatGPT '
    if request.method == 'POST':
        if 'confirm' in request.form:

            filename = request.form['filename']
            # client_name = request.form['client_name']
            # prompt_id = request.form.get('prompt_id')

            # Validate and convert search_string to a list
            # is_valid, str_list = validate_string(client_name)
            # if not is_valid:
            #     return jsonify({"error": "search_string must be a comma-separated list of strings"}), 400

            # prompts = read_prompts()
            # prompt = next((p for p in prompts if str(p['id']) == prompt_id), None)
            # pretext = prompt['pretext']
            # posttext = prompt['posttext']
            # print('pretext', pretext)
            # print('posttext', posttext)

            # Load the object from the file
            with open(f"{os.path.join('./objects/',filename)}.pkl", 'rb') as file:
                contract = dill.load(file)

            # result = contract.postext
            # contract = Contract(os.path.join(app.config['UPLOAD_FOLDER']), str_list, pretext, posttext)
            # contract.save_object()

            if contract:
                result = contract.send_to_openai()
            
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
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])   
            filename = secure_filename(file.filename).split(".")[0]
            file.save(f"{os.path.join(app.config['UPLOAD_FOLDER'], filename)}.pdf")
            print('File successfully uploaded!')        
 
            prompts = read_prompts()
            prompt = next((p for p in prompts if str(p['id']) == prompt_id), None)
            pretext = prompt['pretext']
            posttext = prompt['posttext']

            contract = Contract(os.path.join(app.config['UPLOAD_FOLDER']), str_list, pretext, posttext)
            contract.save_object(filename)
    
    return render_template('preview.html', filename=filename, client_name=client_name, prompt_id=prompt_id, contract=contract)
 



### 
# Prompts
###
# Route to edit an existing prompt
# @app.route('/edit/<int:prompt_id>', methods=['GET', 'POST'])
app.add_url_rule('/edit/<int:prompt_id>', 'edit_prompt', edit_prompt, methods=['GET', 'POST'])


# Route for create_prompt page
# @app.route('/create', methods=['GET', 'POST'])
app.add_url_rule('/create', 'create_prompt', create_prompt, methods=['GET', 'POST'])

# Route to delete a prompt
# @app.route('/delete/<int:prompt_id>')
app.add_url_rule('/delete/<int:prompt_id>', 'delete_prompt', delete_prompt)

# Route for prompt page
# @app.route('/prompts')
app.add_url_rule('/prompts', 'prompts', prompts_page)




### 
# Settings
###
# Route to display the settings page
# @app.route('/settings', methods=['GET', 'POST'])
# Route for the settings page
app.add_url_rule('/settings', 'settings', settings_page, methods=['GET', 'POST'])


# Route for the login page
app.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])


# Route for logging out
app.add_url_rule('/logout', 'logout', logout)



# Route to handle the home page and file uploads
@app.route('/', methods=['GET', 'POST'])
def home():
    # If user is not logged in, redirect to login page
    if not is_logged_in():
        return redirect(url_for('login'))
 
    session.pop('_flashes', None)
    # GET request renders the upload form
    return render_template('home.html', prompts=read_prompts())



# Run the Flask app on localhost
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
    
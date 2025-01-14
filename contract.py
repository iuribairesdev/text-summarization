# contract.py
 
import os
import re 
import openai 
import json
import unicodedata
from dataclasses import dataclass, field
from typing import Optional
from pypdf import PdfReader
import dill
import pyperclip
from dotenv import load_dotenv
import spacy

import pymupdf
from PIL import Image
import io

import pytesseract

#install https://github.com/UB-Mannheim/tesseract/wiki
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

SETTINGS_FILE = 'settings.json'
# Define the folder to save uploaded files
UPLOAD_FOLDER = './uploaded_files'

#### HELPER FUNCTIONS ####
def flatten(xss):
    return [x for xs in xss for x in xs]




def replace_substrings_case_insensitive(text, old_word, new_word):
    # Replace any whitespace (e.g., newlines) within the old_word using \s*
    # re.escape ensures special characters in the old_word are escaped
    pattern = re.compile(re.escape(old_word).replace(r'\ ', r'\s*'), re.IGNORECASE)
    replaced_text = pattern.sub(new_word, text)

    return replaced_text

@dataclass
class Contract:
    path: str # path to folder with contract
    client_name: list[str] #if there's more than one name to be masked in the contract
    pretext: Optional[str] = field(repr=False, default='')
    postext: Optional[str] = field(repr=False, default='')
    
    def __post_init__(self) -> None:
        load_dotenv()
        self.file_texts = []
        for file in os.listdir(self.path):
            file_path = os.path.join(self.path, file)
            self.file_texts.append(self._get_file_text(file_path))

        self.contracts_text:str = '\n'.join(self.file_texts)

        self.contracts_text:str = unicodedata.normalize('NFKC', self.contracts_text)
        self.contracts_text:str = self._replace_client_name()
        self.contracts_text:str = self._mask_email()
        self.contracts_text:str = self._mask_phone() 
        self.contracts_text:str = self._mask_person_names()
        # self.contracts_text:str = self._mask_address() 
        
        self.contracts_text:str = self._replace_bairesdev()
        self.contracts_text_with_prepost = self.pretext + '\n' + self.contracts_text + '\n' + self.postext
        self.text_chunks:list[str] = self._split_text_into_chunks()

        return self.contracts_text


    def edit_contract_text(self, text) -> None:
        self.contract_text:str = text
        return self.contracts_text


    def paste_text(self) -> None:
        return self.contracts_text_with_prepost

    def paste_chunks_to_clipboard_loop(self) -> None:
        number_of_chunks = len(self.text_chunks)
        for chunk_i in range(number_of_chunks):
            pyperclip.copy(self.text_chunks[chunk_i])
            user_input = input(f'''Chunk {chunk_i+1} of {number_of_chunks} has been copied to your clipboard. Paste it in ChatGPT.
Press Enter to copy the next chunk to clipboard or input q to quit\n>>> ''')
            if user_input=='q':
                break

    # def _get_file_text(self, file_path) -> str:
    #     reader = PdfReader(file_path)
    #     return '\n'.join([page.extract_text() for page in reader.pages])

    def _get_file_text(self, file_path) -> str:
        """
        Extracts text from a PDF using PyMuPDF. If the extracted text for a page 
        is below 'threshold' characters, it attempts OCR on that page.
        """
        doc = pymupdf.open(file_path)
        pages_text = []
        threshold = 100  # Adjust as needed
        document = file_path.split('\\')[-1]
    
        for page_index in range(len(doc)):
            page = doc[page_index]
            
            # 1) Attempt direct text extraction
            extracted_text = page.get_text()
    
            # 2) Fallback to OCR if text is None or suspiciously short
            if not extracted_text or len(extracted_text) < threshold:
                print(f'Could not find the text on page {page_index} on file {document}. Trying OCR...')
                # Render page as an image (300 DPI is a typical choice)
                pix = page.get_pixmap(dpi=300)
                img_data = pix.tobytes("png")
    
                # Convert image bytes to a PIL Image
                pil_img = Image.open(io.BytesIO(img_data))
    
                # Perform OCR with Tesseract
                ocr_text = pytesseract.image_to_string(pil_img)
                pages_text.append(ocr_text)
            else:
                pages_text.append(extracted_text)
    
        return "\n".join(pages_text)
    
    def _split_text_into_chunks(self, maximum_len=8000) -> list[str]:
        contract_lenght = len(self.contracts_text_with_prepost)
        self.text_chunks = []
        if contract_lenght>maximum_len:

            number_of_chunks = int(contract_lenght / maximum_len) + (contract_lenght % maximum_len > 0) #rounding up
            self.text_chunks.append(
'''The total length of the content that I want to send you is too large to send in only one piece.

For sending you that content, I will follow this rule:

[START PART 1/10]
this is the content of the part 1 out of 10 in total
[END PART 1/10]

Then you just answer: "Received part 1/10"

And when I tell you "ALL PARTS SENT", then you can continue processing the data and answering my requests.''')
            for chunk_i in range(number_of_chunks):
                lower_bound = maximum_len*chunk_i
                upper_bound = maximum_len*(chunk_i+1)
                current_chunk_text = self.contracts_text_with_prepost[lower_bound:min(upper_bound,contract_lenght)]
                # current_chunk_text = self.contracts_text[lower_bound:min(upper_bound,contract_lenght)]

                pre_chunk_text = f'''
Do not answer yet. This is just another part of the text I want to send you. Just receive and acknowledge as "Part {chunk_i+1}/{number_of_chunks} received" and wait for the next part.
[START PART {chunk_i+1}/{number_of_chunks}]
'''
                if chunk_i != number_of_chunks-1:
                    post_chunk_text = f'''
[END PART {chunk_i+1}/{number_of_chunks}]
Remember not answering yet. Just acknowledge you received this part with the message "Part {chunk_i+1}/{number_of_chunks} received" and wait for the next part.
'''

                else:
                    post_chunk_text = f'''
[END PART {chunk_i+1}/{number_of_chunks}]
ALL PARTS SENT. Now you can continue processing the request.
'''

                current_chunk_text = pre_chunk_text + '\n' + current_chunk_text + '\n' + post_chunk_text

                self.text_chunks.append(current_chunk_text)
            return self.text_chunks

        self.text_chunks.append(self.contracts_text_with_prepost)
        return self.text_chunks

    def _replace_client_name(self) -> str:
        client_names = self.client_name
        client_names_wo_spaces = []
        for name in self.client_name:
            client_names_wo_spaces.append(name.replace(' ','')) #removes spaces - useful for removing instances where compound names might appear together, like in the e-mail
        for name in self.client_name:
            client_names_wo_spaces.append(name.replace(' ','_'))
        client_names = client_names + client_names_wo_spaces
        client_names = list(set(client_names)) # removes duplicates
        for variation in client_names:
            self.contracts_text = replace_substrings_case_insensitive(self.contracts_text,variation, 'CLIENT')
        return self.contracts_text


    def _mask_email(self) -> str:
        pattern = r'[\w\.-]+@[\w\.-]+'  # Regex pattern to find emails
        return re.sub(pattern, lambda match: self._mask_email_pattern(match.group()), self.contracts_text)

    def _mask_email_pattern(self, match):
        local_part, domain_part = match.split('@')
        masked_local = 'X' * len(local_part)  # Mask the local part with 'X'
        return f'{masked_local}@{domain_part}'

    # Function to mask phone numbers
    def _mask_phone(self):
        # Patterns and replacements for masking
        patterns = [
            (r"(\+1\s?\(\d{3}\)\s?)\d{3}[\­\- ]\d{4}", r"\1***-****"),  # US number with +1
            (r"(1\s?\(\d{3}\)\s?)\d{3}[\­\- ]\d{4}", r"\1***-****"),    # US number with 1
            (r"(\+54\s?9\s?\d{2}\s?)\d{4}[\­\- ]\d{4}", r"\1**** ****"), # International number with +54
            (r"(\+\d+\s?\(?\d{1,4}\)?[\s\-]?)\d{2,4}[\­\- ]\d{2,4}[\­\- ]\d{2,4}", r"\1*** **** ****")
        ]
    
        # Apply masking for each pattern
        for pattern, replacement in patterns:
            self.contracts_text = re.sub(pattern, replacement, self.contracts_text)

        return self.contracts_text


    # research AI model available on Google to replace Spacy spacy Python. 
    # The goal is mask persona names with more accuracy
    # Google AI model: o1-2024-12


    def _mask_person_names(self):

        """
            Mask person names in the input text using SpaCy NER and custom regex rules.
            :param text: Input string containing text to be masked.
            :return: Masked string with person names replaced.
        """
        nlp = spacy.load("en_core_web_sm")

        # Custom patterns for names (optional enhancement for SpaCy)
        NAME_PATTERNS = [
            r"Mr\.?\s+[A-Z][a-z]+"  # Match "Mr. John"
            ,r"Ms\.?\s+[A-Z][a-z]+"  # Match "Ms. Jane"
            ,r"Dr\.?\s+[A-Z][a-z]+"  # Match "Dr. Smith"
            #,r"[A-Z][a-z]+\s+[A-Z][a-z]+"  # Match "John Smith"
        ]

        # Step 1: Use SpaCy NER to identify person entities
        doc = nlp(self.contracts_text)
        masked_text = self.contracts_text

        # Replace names identified by SpaCy with a mask
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                masked_text = re.sub(
                    re.escape(ent.text), "[MASKED NAME]", masked_text, flags=re.IGNORECASE
                )

        # Step 2: Apply custom regex rules for additional patterns
        for pattern in NAME_PATTERNS:
            masked_text = re.sub(pattern, "[MASKED NAME]", masked_text)

        return masked_text

    # Function to mask street addresses
    def _mask_address(self):
        # Address pattern to match various street addresses
        pattern = r'\d+\s+[A-Za-z]+\s+[A-Za-z]+\s*\w*(?:\s+\w+)?(?:,\s*\w+\s*\w{2})?'
        return re.sub(pattern, lambda match: self._mask_address_pattern(match.group()), self.contracts_text)

    # Function to mask the address pattern
    def _mask_address_pattern(self, match):
        masked_address = re.sub(r'\w', 'X', match[:-7])  # Mask all characters except last 7 (for city/state)
        return masked_address + match[-7:]  # Append the last 7 characters (for city and state)

    # TODO: mask personal names and amounts $$

    def _replace_bairesdev(self) -> str:
        return replace_substrings_case_insensitive(self.contracts_text, 'bairesdev', 'CONTRACTOR')

    def save_object(self, filename, user, path_obj='./objects') -> None:         
        if not os.path.exists(os.path.join(path_obj,user)):
            os.makedirs(os.path.join(path_obj,user))

        with open(f"{os.path.join(os.path.join(path_obj,user),filename)}.pkl", "wb") as dill_file:
            print(f"{os.path.join(os.path.join(path_obj,user),filename)}.pkl")
            dill.dump(self, dill_file)

        return
   
    def _post_to_openai(self, message, model, tokens, temperature) -> None:
        # print('Running _post_to_ai')
        openai.api_key = os.environ.get('OPENAI_API_KEY')
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.pretext},
                    {"role": "user", "content": message}
                ],
                max_tokens=tokens,  # how long the completion to be
                temperature=temperature, # creativity level
                # response_format={"type": "json_object"}
            )
            response = response['choices'][0]['message']['content'].strip()
        except openai.error.OpenAIError as e:
            print(f"An error occurred: {e}")
            response = f"An error occurred: {e}"

        # print('API response',response)
        return response
    
    def paste_chunks_to_openai(self, model, tokens, temperature, max_len=8_000) -> None:
        # print('Running paste_chunks_to_openai')
        contract_length = len(self.contracts_text_with_prepost)
        
        # print('LEN', contract_length, max_len)
        if contract_length<=max_len:
            # print(self.contracts_text_with_prepost)    
            self._post_to_openai(self.contracts_text + "\n\n" + self.postext, model, tokens, temperature)
        else:
            # print('chunks #: ', len(self.text_chunks))
            for chunk_i in range(len(self.text_chunks)):
                # print(chunk_i, '#######', self.text_chunks[chunk_i])                
                resp = self._post_to_openai(self.text_chunks[chunk_i], model, tokens, temperature)
                # print('RESP',resp)
        return resp



    def send_to_openai(self) -> None:
        # print('Running send_to_openai')
        with open(SETTINGS_FILE, 'r') as file:
            settings = json.load(file)
        resp = 'NO results from GPT API!'
        if settings['model'] == 'gpt-4o': 
            # print('settings', self.contract_text)
            resp = self._post_to_openai(self.contract_text + "\n\n" + self.postext, settings['model'], settings['tokens'], settings['temperature'])
        else:
            resp = self.paste_chunks_to_openai(settings['model'], settings['tokens'], settings['temperature'])
        print('RESP', resp)
        return resp
    


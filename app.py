import os
import yaml
from openai import OpenAI
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from frontend

# OpenAI API setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Google API setup
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'genresume-254e5f3980a3.json'
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

docs_service = build('docs', 'v1', credentials=credentials)

# Load YAML resume data
with open('resume_data.yaml', 'r') as file:
    resume_data = yaml.safe_load(file)

# Route for optimizing resume
@app.route('/optimize_resume', methods=['POST'])
def optimize_resume():
    # Extract job description from user input
    data = request.get_json()
    job_description = data['job_description']
    template_doc_id = '12HYi4bEj2KwLwFzb753KBsOXzC7RD-EUU1jBUBhVUXY'  # Google Docs template document ID

    # Combine resume data into a single resume text
    resume_text = f"{resume_data['name']}, {resume_data['location']} | P: {resume_data['phone']} | {resume_data['email']}\n\n"
    resume_text += "EDUCATION\n\n"
    for edu in resume_data['education']:
        resume_text += f"{edu['institution']}\t{edu['location']}\n{edu['degree']}\t{edu['date']}\n{edu['details']}\n\n"
    resume_text += "WORK EXPERIENCE\n\n"
    for work in resume_data['work_experience']:
        resume_text += f"{work['company']}\t{work['location']}\n{work['position']}\t{work['dates']}\n{work['details']}\n\n"
    resume_text += "PROJECTS\n\n"
    for project in resume_data['projects']:
        resume_text += f"{project['name']}\t{project['date']}\n{project['details']}\n\n"
    resume_text += "ACTIVITIES\n\n"
    for activity in resume_data['activities']:
        resume_text += f"{activity['name']}\t{activity['dates']}\n{activity['details']}\n\n"
    resume_text += "ADDITIONAL\n\n"
    resume_text += f"Technical Skills: {resume_data['skills']}\nLanguages: {resume_data['languages']}\nCertifications & Training: {resume_data['certifications']}\nAwards: {resume_data['awards']}\n"

    # Analyze job description with OpenAI
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": (
                "You are to output a resume based on the information given. "
                "Do not add any additional comments, notes, or styling that is not part of the core content. "
                "Do not bold any sections unless explicitly indicated in the text. "
                "Only provide the resume content, formatted precisely as described in the provided resume text. "
                "The sections include EDUCATION, WORK EXPERIENCE, PROJECTS, ACTIVITIES, and ADDITIONAL.\n\n"
                f"Job Description:\n{job_description}\n\nResume:\n{resume_text}\n\nOptimized Resume:"
            )}
        ]
    )
    optimized_resume = completion.choices[0].message.content.strip()

    # Create a new Google Doc from the template and insert the optimized resume
    try:
        # Make a copy of the template document
        copy_title = "Optimized Resume"
        body = {
            'name': copy_title
        }
        drive_service = build('drive', 'v3', credentials=credentials)
        copied_doc = drive_service.files().copy(fileId=template_doc_id, body=body).execute()
        copied_doc_id = copied_doc.get('id')
        # Update the permissions of the copied document to make it accessible
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        drive_service.permissions().create(
            fileId=copied_doc_id,
            body=permission,
        ).execute()

        # Update the copied document with the optimized resume content
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1
                    },
                    'text': optimized_resume
                }
            }
        ]
        docs_service.documents().batchUpdate(documentId=copied_doc_id, body={'requests': requests}).execute()

        # Return the link to the newly created document
        document_link = f"https://docs.google.com/document/d/{copied_doc_id}/edit"
        return jsonify({'optimized_resume_link': document_link})

    except HttpError as error:
        return jsonify({'error': f'An error occurred: {error}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
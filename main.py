import os
import requests
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

app = FastAPI()

# --- 1. Security: Enable CORS for your website ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://scprefrigeration.coepi.co", "http://localhost:5173", "http://fcsog8800kcksss4840oogww.154.12.252.28.sslip.io"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. Configuration (Use Environment Variables in Coolify) ---
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
# This will be the content of your service_account.json
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON") 

@app.post("/apply")
async def handle_application(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    position: str = Form(...),
    experience: str = Form(...),
    message: str = Form(""),
    resume: UploadFile = None
):
    try:
        # 3. Authenticate with Google
        creds = service_account.Credentials.from_service_account_info(
            eval(GOOGLE_CREDS_JSON)
        )
        drive_service = build('drive', 'v3', credentials=creds)

# 4. Upload File to Drive
        file_metadata = {
            'name': f"RESUME_{name.replace(' ', '_')}",
            'parents': [DRIVE_FOLDER_ID]
        }
        
        # ADD THIS LINE to the create() call below:
        # supportsAllDrives=True 
        
        media = MediaIoBaseUpload(resume.file, mimetype=resume.content_type, resumable=True)
        drive_file = drive_service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, webViewLink',
            supportsAllDrives=True # <--- ADD THIS
        ).execute()
        
        resume_url = drive_file.get('webViewLink')

        # 5. Ping n8n with clean JSON
        n8n_payload = {
            "name": name,
            "email": email,
            "phone": phone,
            "position": position,
            "experience": experience,
            "message": message,
            "resume_url": resume_url,
            "submitted_at": str(os.getenv("COOLIFY_DEPLOYED_AT", "just now"))
        }
        
        requests.post(N8N_WEBHOOK_URL, json=n8n_payload)

        return {"status": "success", "message": "Application processed"}

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

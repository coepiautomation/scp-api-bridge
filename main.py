import os
import requests
import base64
from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://scprefrigeration.coepi.co", "http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

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
        # 1. Read the file and convert to Base64 string
        file_content = await resume.read()
        base64_file = base64.b64encode(file_content).decode('utf-8')

        # 2. Package everything into a JSON payload
        payload = {
            "name": name,
            "email": email,
            "phone": phone,
            "position": position,
            "experience": experience,
            "message": message,
            "file_base64": base64_file,
            "file_name": f"RESUME_{name.replace(' ', '_')}.pdf",
            "file_mime": resume.content_type
        }
        
        # 3. Ship it to n8n
        response = requests.post(N8N_WEBHOOK_URL, json=payload)
        response.raise_for_status()

        return {"status": "success", "message": "Application forwarded to n8n"}

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

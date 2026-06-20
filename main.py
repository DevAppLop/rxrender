import os
import requests
from flask import Flask, request, render_template_string, jsonify
from google import genai

app = Flask(__name__)

# --- CONFIGURATION ---
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
BULKGATE_API_URL = "https://portal.bulkgate.com/api/1.0/viber/transactional" 
BULKGATE_TOKEN = "YOUR_BULKGATE_APPLICATION_TOKEN"

ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Simple HTML layout for a mobile upload button
UPLOAD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>Rx Cloud Verifier</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 20px; background-color: #f4f6f9; }
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 400px; margin: 0 auto; }
        input[type="file"] { margin: 20px 0; }
        button { background: #6f42c1; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-size: 16px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <h2>📷 Upload Prescription</h2>
        <p>The AI analysis will be typed directly into your team's Viber group.</p>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="rx_image" accept="image/*" required><br>
            <button type="submit">Verify & Send to Viber</button>
        </form>
    </div>
</body>
</html>
"""

MEDICAL_INSTRUCTIONS = """
You are an expert pharmaceutical assistant. Analyze this prescription image.
List out:
1. Patient Name 
2. Medication Name & Strength
3. Frequency instructions
State if it looks clear and accurate, highlighting any errors in bold.
"""

def send_to_viber_group(text_report):
    """Uses BulkGate / Automation platform to push text back to your team group."""
    payload = {
        "application_id": "YOUR_APP_ID",
        "application_token": BULKGATE_TOKEN,
        "number": "YOUR_GROUP_OR_PHARMACIST_NUMBER",
        "text": f"--- AUTOMATED RX EVALUATION ---\n{text_report}"
    }
    requests.post(BULKGATE_API_URL, json=payload)

@app.route('/')
def home():
    return render_template_string(UPLOAD_HTML)

@app.route('/upload', methods=['POST'])
def upload():
    if 'rx_image' not in request.files:
        return "No image uploaded", 400
        
    file = request.files['rx_image']
    local_path = "temp_cloud_rx.jpg"
    file.save(local_path)
    
    try:
        # Step 2: Process with Gemini AI
        uploaded_file = ai_client.files.upload(file=local_path)
        response = ai_client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[uploaded_file, MEDICAL_INSTRUCTIONS]
        )
        ai_client.files.delete(name=uploaded_file.name)
        
        # Step 3: Broadcast results straight into the Viber Chat
        send_to_viber_group(response.text)
        
        return "<h3>Success! The analysis has been sent directly to your Viber group chat. You can close this tab.</h3>"
    except Exception as e:
        return f"Error: {str(e)}", 500
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
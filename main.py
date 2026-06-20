import os
from flask import Flask, request, render_template_string, redirect, url_for
from google import genai

app = Flask(__name__)

# Fetch the key securely from Render's Environment settings
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize the Google Gemini Client safely using the new google-genai SDK
if GEMINI_API_KEY:
    ai_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    ai_client = None

# A clean, mobile-friendly landing page layout
UPLOAD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <title>Rx Cloud Verifier</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; text-align: center; padding: 20px; background-color: #f8f9fa; color: #333; }
        .card { background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); max-width: 450px; margin: 40px auto 0 auto; }
        h2 { color: #6f42c1; margin-bottom: 8px; }
        p { color: #666; font-size: 14px; margin-bottom: 24px; }
        .file-input-wrapper { margin: 20px 0; }
        button { background: #6f42c1; color: white; border: none; padding: 14px 28px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; width: 100%; transition: background 0.2s; }
        button:hover { background: #5a32a3; }
    </style>
</head>
<body>
    <div class="card">
        <h2>📷 Rx Verification Tool</h2>
        <p>Upload a clear photo of the prescription or medication container label for an instant validation check.</p>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <div class="file-input-wrapper">
                <input type="file" name="rx_image" accept="image/*" required style="font-size: 14px;">
            </div>
            <button type="submit">Analyze Prescription</button>
        </form>
    </div>
</body>
</html>
"""

MEDICAL_INSTRUCTIONS = """
You are an advanced pharmaceutical assistant AI. Carefully look at the uploaded image.
Extract and verify:
1. Patient Name 
2. Medication Name (accounting for brand vs generic variants)
3. Dosage and strength
4. Frequency/Directions for use

List your evaluation clearly using itemized bullet points. If you detect any discrepancies, potential errors, or unclear handwriting, highlight them in bold text.
Always end your reply with this disclaimer:
"DISCLAIMER: This analysis is AI-generated for educational reference only and does not replace a pharmacist's physical validation. Always verify with a medical professional before dispensing or consuming medication."
"""

@app.route('/')
def home():
    return render_template_string(UPLOAD_HTML)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    # Fix for image_cac2ec.png: If a user refreshes their result page or 
    # directly visits the URL via a GET request, gracefully redirect them home.
    if request.method == 'GET':
        return redirect(url_for('home'))

    if not ai_client:
        return "<h3>Error: GEMINI_API_KEY is not set in Render Environment Variables.</h3>", 500

    if 'rx_image' not in request.files:
        return "No image uploaded", 400
        
    file = request.files['rx_image']
    if file.filename == '':
        return "No selected file", 400

    local_path = "temp_cloud_rx.jpg"
    file.save(local_path)
    
    try:
        # Upload the temporary image to Gemini File API
        uploaded_file = ai_client.files.upload(file=local_path)
        
        # Request evaluation report using the proper standard endpoint schema with the correct model format
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[uploaded_file, MEDICAL_INSTRUCTIONS]
        )
        
        # Clean up the remote file footprint from Google Cloud
        ai_client.files.delete(name=uploaded_file.name)
        
        # Return a beautifully formatted verification report page straight to the screen
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name='viewport' content='width=device-width, initial-scale=1.0'>
            <title>Verification Report</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; padding: 20px; background-color: #f8f9fa; color: #333; }}
                .report-card {{ background: white; padding: 24px; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); max-width: 550px; margin: 20px auto; text-align: left; }}
                h2 {{ color: #28a745; text-align: center; margin-top: 0; }}
                hr {{ border: 0; border-top: 1px solid #eee; margin: 16px 0; }}
                .content {{ white-space: pre-wrap; line-height: 1.6; font-size: 15px; }}
                .back-btn {{ display: block; text-align: center; background: #6f42c1; color: white; text-decoration: none; padding: 12px; border-radius: 8px; font-weight: bold; margin-top: 24px; }}
            </style>
        </head>
        <body>
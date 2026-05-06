from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil, os, re, requests
import pandas as pd
import pdfplumber

app = FastAPI()

os.makedirs("uploads", exist_ok=True)
os.makedirs("data", exist_ok=True)

EXCEL_FILE = "data/invoices.xlsx"
OCR_API_KEY = os.getenv("OCR_API_KEY")


@app.get("/")
def home():
    return {"message": "KR InvoiceHub OCR API Running 🚀"}


# 📄 Read PDF text first
def read_pdf(path):
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except:
        pass
    return text


# 🌐 OCR API fallback
def read_with_ocr_api(path):
    try:
        with open(path, 'rb') as f:
            response = requests.post(
                'https://api.ocr.space/parse/image',
                files={'file': f},
                data={
                    'apikey': OCR_API_KEY,
                    'language': 'eng'
                }
            )
        result = response.json()
        return result['ParsedResults'][0]['ParsedText']
    except:
        return ""


# 🔍 Extract data
def extract_data(text):
    def find(pattern):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    return {
        "invoice_number": find(r"invoice.*?([A-Z0-9\-]{5,})"),
        "invoice_date": find(r"date[:\s]*([\d\/\-]+)"),
        "pnr": find(r"pnr[:\s]*([A-Z0-9]+)"),
        "ticket_number": find(r"ticket[:\s]*([\d]+)"),
        "buyer_gst": find(r"gstin[:\s]*([A-Z0-9]+)"),
        "buyer_name": "",
        "seller_gst": "",
        "seller_name": "",
        "basic_fare": find(r"fare[:\s]*([\d\.]+)"),
        "other_charges": find(r"charges[:\s]*([\d\.]+)"),
        "cgst": find(r"cgst[:\s]*([\d\.]+)"),
        "sgst": find(r"sgst[:\s]*([\d\.]+)"),
        "igst": find(r"igst[:\s]*([\d\.]+)"),
        "total_amount": find(r"total[:\s]*([\d\.]+)")
    }


@app.post("/upload/")
async def upload_invoice(file: UploadFile = File(...)):
    try:
        path = f"uploads/{file.filename}"

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        text = read_pdf(path)

        # 👉 If PDF text empty → use OCR API
        if not text.strip():
            text = read_with_ocr_api(path)

        if not text.strip():
            return {"status": "failed", "message": "Could not extract text"}

        data = extract_data(text)

        df = pd.DataFrame([data])

        if os.path.exists(EXCEL_FILE):
            old = pd.read_excel(EXCEL_FILE)
            df = pd.concat([old, df])

        df.to_excel(EXCEL_FILE, index=False)

        return {
            "status": "processed",
            "preview": text[:500],
            "data": data
        }

    except Exception as e:
        return {"error": str(e)}


@app.get("/download/")
def download_excel():
    if os.path.exists(EXCEL_FILE):
        return FileResponse(EXCEL_FILE, filename="invoices.xlsx")
    return {"error": "No file found"}

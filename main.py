from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil, os, re, requests
import pandas as pd
import pdfplumber

app = FastAPI()

# folders
os.makedirs("uploads", exist_ok=True)
os.makedirs("data", exist_ok=True)

EXCEL_FILE = "data/invoices.xlsx"
OCR_API_KEY = os.getenv("OCR_API_KEY")


@app.get("/")
def home():
    return {"message": "KR InvoiceHub Running 🚀"}


# 📄 Read text-based PDF
def read_pdf(path):
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except:
        pass
    return text


# 🌐 OCR API (for scanned PDFs/images)
def read_with_ocr_api(path):
    try:
        with open(path, 'rb') as f:
            response = requests.post(
                "https://api.ocr.space/parse/image",
                files={"file": f},
                data={
                    "apikey": OCR_API_KEY,
                    "language": "eng"
                }
            )
        result = response.json()

        if result.get("ParsedResults"):
            return result["ParsedResults"][0]["ParsedText"]
    except:
        pass

    return ""


# 🔍 Improved extraction
def extract_data(text):
    def find(pattern):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    return {
        "invoice_number": find(r"Invoice\s*Number\s*:\s*([A-Z0-9]+)"),
        "invoice_date": find(r"Invoice\s*Date\s*:\s*([\d\-\/]+)"),
        "pnr": find(r"PNR\s*No\s*:\s*([A-Z0-9]+)"),
        "ticket_number": find(r"Ticket\s*No\s*:\s*([\d]+)"),
        "buyer_gst": find(r"GSTIN\s*of\s*Customer\s*:\s*([A-Z0-9]+)"),
        "buyer_name": find(r"Passenger\s*Name\s*:\s*([A-Z\s]+)"),
        "seller_gst": find(r"GSTN\s*:\s*([A-Z0-9]+)"),
        "seller_name": "AIR INDIA EXPRESS LIMITED",
        "basic_fare": find(r"Basic\s*Fare\s*:\s*([\d\.]+)"),
        "other_charges": find(r"Charges\s*:\s*([\d\.]+)"),
        "cgst": find(r"CGST\s*:\s*([\d\.]+)"),
        "sgst": find(r"SGST\s*:\s*([\d\.]+)"),
        "igst": find(r"IGST\s*:\s*([\d\.]+)"),
        "total_amount": find(r"Total\s*:\s*([\d\.]+)")
    }


@app.post("/upload/")
async def upload_invoice(file: UploadFile = File(...)):
    try:
        path = f"uploads/{file.filename}"

        # save file
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # try PDF text first
        text = read_pdf(path)

        # fallback to OCR
        if not text.strip():
            text = read_with_ocr_api(path)

        if not text.strip():
            return {"status": "failed", "message": "No text extracted"}

        # extract data
        data = extract_data(text)

        # save to excel
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


# 📥 download excel
@app.get("/download/")
def download_excel():
    if os.path.exists(EXCEL_FILE):
        return FileResponse(EXCEL_FILE, filename="invoices.xlsx")
    return {"error": "No file found"}

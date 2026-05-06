from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil, os, re
import pandas as pd
import pdfplumber

app = FastAPI()

os.makedirs("uploads", exist_ok=True)
os.makedirs("data", exist_ok=True)

EXCEL_FILE = "data/invoices.xlsx"


@app.get("/")
def home():
    return {"message": "KR InvoiceHub Running 🚀"}


# 📄 Read PDF or text file
def read_file(path):
    text = ""

    if path.endswith(".pdf"):
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        except:
            pass
    else:
        try:
            text = open(path, "r", errors="ignore").read()
        except:
            pass

    return text


# 🔍 Extract invoice fields
def extract_data(text):
    def find(pattern):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    return {
        "invoice_number": find(r"invoice\s*(no|number)[:\s]*([A-Z0-9\-]+)"),
        "invoice_date": find(r"(date)[:\s]*([\d\/\-]+)"),
        "pnr": find(r"(pnr)[:\s]*([A-Z0-9]+)"),
        "ticket_number": find(r"(ticket\s*no)[:\s]*([\d]+)"),
        "buyer_gst": find(r"(gstin)[:\s]*([A-Z0-9]+)"),
        "buyer_name": "Not Found",
        "seller_gst": "",
        "seller_name": "",
        "basic_fare": find(r"(basic\s*fare)[:\s]*([\d\.]+)"),
        "other_charges": find(r"(charges|fees)[:\s]*([\d\.]+)"),
        "cgst": find(r"(cgst)[:\s]*([\d\.]+)"),
        "sgst": find(r"(sgst)[:\s]*([\d\.]+)"),
        "igst": find(r"(igst)[:\s]*([\d\.]+)"),
        "total_amount": find(r"(total)[:\s]*([\d\.]+)")
    }


@app.post("/upload/")
async def upload_invoice(file: UploadFile = File(...)):
    try:
        path = f"uploads/{file.filename}"

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        text = read_file(path)

        data = extract_data(text)

        df = pd.DataFrame([data])

        if os.path.exists(EXCEL_FILE):
            old = pd.read_excel(EXCEL_FILE)
            df = pd.concat([old, df])

        df.to_excel(EXCEL_FILE, index=False)

        return {
            "status": "processed",
            "extracted_text_preview": text[:500],
            "data": data
        }

    except Exception as e:
        return {"error": str(e)}


# 📥 Download Excel
@app.get("/download/")
def download_excel():
    if os.path.exists(EXCEL_FILE):
        return FileResponse(EXCEL_FILE, filename="invoices.xlsx")
    return {"error": "No file found"}

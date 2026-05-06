from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil, os, re
import pandas as pd

app = FastAPI()

os.makedirs("uploads", exist_ok=True)
os.makedirs("data", exist_ok=True)

EXCEL_FILE = "data/invoices.xlsx"


@app.get("/")
def home():
    return {"message": "KR InvoiceHub Running 🚀"}


# 🔍 Simple extraction (no AI, works offline)
def extract_data(text):
    def find(pattern):
        match = re.search(pattern, text)
        return match.group(1) if match else ""

    return {
        "invoice_number": find(r"Invoice\s*No[:\s]*([A-Z0-9\-]+)"),
        "invoice_date": find(r"Date[:\s]*([\d\-\/]+)"),
        "pnr": find(r"PNR[:\s]*([A-Z0-9]+)"),
        "ticket_number": find(r"Ticket\s*No[:\s]*([\d]+)"),
        "buyer_gst": find(r"GSTIN[:\s]*([A-Z0-9]+)"),
        "buyer_name": "Not Found",
        "seller_gst": "",
        "seller_name": "",
        "basic_fare": find(r"Basic Fare[:\s]*([\d\.]+)"),
        "other_charges": find(r"Charges[:\s]*([\d\.]+)"),
        "cgst": find(r"CGST[:\s]*([\d\.]+)"),
        "sgst": find(r"SGST[:\s]*([\d\.]+)"),
        "igst": find(r"IGST[:\s]*([\d\.]+)"),
        "total_amount": find(r"Total[:\s]*([\d\.]+)")
    }


@app.post("/upload/")
async def upload_invoice(file: UploadFile = File(...)):
    try:
        path = f"uploads/{file.filename}"

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Try reading as text (basic)
        try:
            text = open(path, "r", errors="ignore").read()
        except:
            text = ""

        data = extract_data(text)

        df = pd.DataFrame([data])

        if os.path.exists(EXCEL_FILE):
            old = pd.read_excel(EXCEL_FILE)
            df = pd.concat([old, df])

        df.to_excel(EXCEL_FILE, index=False)

        return {"status": "processed", "data": data}

    except Exception as e:
        return {"error": str(e)}


# 📥 Download Excel
@app.get("/download/")
def download_excel():
    if os.path.exists(EXCEL_FILE):
        return FileResponse(EXCEL_FILE, filename="invoices.xlsx")
    return {"error": "No file found"}

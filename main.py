from fastapi import FastAPI, UploadFile, File
import shutil, os
import pandas as pd
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

if not os.path.exists("uploads"):
    os.makedirs("uploads")

if not os.path.exists("data"):
    os.makedirs("data")

@app.get("/")
def home():
    return {"message": "KR InvoiceHub Running 🚀"}

def extract_data(text):
    prompt = f"""
Extract airline invoice data:

invoice_number
invoice_date
pnr
ticket_number
buyer_gst
buyer_name
seller_gst
seller_name
basic_fare
other_charges
cgst
sgst
igst
total_amount

Return JSON only.

{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    import json
    return json.loads(response.choices[0].message.content)

@app.post("/upload/")
async def upload_invoice(file: UploadFile = File(...)):
    path = f"uploads/{file.filename}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # read file text (basic version)
    text = ""
    try:
        text = open(path, "r", errors="ignore").read()
    except:
        text = "invoice text"

    data = extract_data(text)

    df = pd.DataFrame([data])

    file_path = "data/invoices.xlsx"

    if os.path.exists(file_path):
        old = pd.read_excel(file_path)
        df = pd.concat([old, df])

    df.to_excel(file_path, index=False)

    return {"status": "processed", "data": data}

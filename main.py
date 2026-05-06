from fastapi import FastAPI, UploadFile, File
import shutil, os, json
import pandas as pd

app = FastAPI()

os.makedirs("uploads", exist_ok=True)
os.makedirs("data", exist_ok=True)

@app.get("/")
def home():
    return {"message": "KR InvoiceHub Running 🚀"}


def extract_data(text):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"""
Extract airline invoice data and return JSON with:
invoice_number, invoice_date, pnr, ticket_number,
buyer_gst, buyer_name, seller_gst, seller_name,
basic_fare, other_charges, cgst, sgst, igst, total_amount
{text}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        return {"error": str(e)}


@app.post("/upload/")
async def upload_invoice(file: UploadFile = File(...)):
    try:
        path = f"uploads/{file.filename}"

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        text = "invoice data"

        data = extract_data(text)

        file_path = "data/invoices.xlsx"
        df = pd.DataFrame([data])

        if os.path.exists(file_path):
            old = pd.read_excel(file_path)
            df = pd.concat([old, df])

        df.to_excel(file_path, index=False)

        return {"status": "processed", "data": data}

    except Exception as e:
        return {"error": str(e)}

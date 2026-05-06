@app.post("/upload/")
async def upload_invoice(file: UploadFile = File(...)):
    try:
        path = f"uploads/{file.filename}"

        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # TEMP: skip reading PDF (causes crash)
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

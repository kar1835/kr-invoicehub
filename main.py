from fastapi import FastAPI, UploadFile, File
import shutil
import os

app = FastAPI()

if not os.path.exists("uploads"):
    os.makedirs("uploads")

@app.get("/")
def home():
    return {"message": "KR InvoiceHub Backend Running 🚀"}

@app.post("/upload/")
async def upload_invoice(file: UploadFile = File(...)):
    file_location = f"uploads/{file.filename}"
    
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": file.filename, "status": "uploaded"}

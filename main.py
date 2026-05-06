from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "KR InvoiceHub Backend Running 🚀"}

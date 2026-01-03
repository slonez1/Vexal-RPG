from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Test API endpoint
@app.get("/api/test")
async def test_api():
    return {"message": "FastAPI is working!"}

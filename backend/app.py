import os
import sys
from fastapi import FastAPI
from fastapi.routing import APIRoute

app = FastAPI()

# Print environment debugging information
print("DEBUG: Current working directory:", os.getcwd())
print("DEBUG: Current files in app directory:", os.listdir("."))
print("DEBUG: Files in backend directory:", os.listdir("./backend"))
print("DEBUG: Python PATH:", sys.path)

@app.on_event("startup")
async def log_routes():
    print("DEBUG: Registered Routes:")
    for route in app.router.routes:
        if isinstance(route, APIRoute):
            print(f"DEBUG: {route.path} -> {route.methods}")

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI! The app is running."}

@app.get("/api/test")
async def test_api():
    return {"message": "FastAPI is working!"}

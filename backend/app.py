from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from fastapi.routing import APIRoute

app = FastAPI()

# Log all routes
@app.on_event("startup")
async def log_startup():
    print("Registering FastAPI Routes:")
    for route in app.router.routes:
        if isinstance(route, APIRoute):
            print(f"- Path: {route.path}, Methods: {route.methods}")

# Test API endpoint
@app.get("/api/test")
async def test_api():
    return {"message": "FastAPI is working!"}

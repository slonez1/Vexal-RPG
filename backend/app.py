import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.routing import APIRoute

app = FastAPI()

# Log all registered routes at startup
@app.on_event("startup")
async def log_routes():
    print("Registered Routes:")
    for route in app.router.routes:
        if isinstance(route, APIRoute):
            print(f"{route.path} -> {route.methods}")

# Test API endpoint
@app.get("/api/test")
async def test_api():
    return {"message": "FastAPI is working!"}

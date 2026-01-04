import os
import sys
from fastapi import FastAPI
from fastapi.routing import APIRoute
import logging

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Debugging: Log environment and directory info at the start
logger.info("DEBUG: Current working directory: %s", os.getcwd())
logger.info("DEBUG: Current files in app directory: %s", os.listdir("."))
if os.path.exists("./backend"):
    logger.info("DEBUG: Files in backend directory: %s", os.listdir("./backend"))
else:
    logger.info("DEBUG: Backend directory not found!")
logger.info("DEBUG: Python PATH: %s", sys.path)

# Log all routes when the app starts
@app.on_event("startup")
async def log_routes():
    logger.info("DEBUG: Registered Routes:")
    for route in app.router.routes:
        if isinstance(route, APIRoute):
            logger.info("DEBUG: %s -> %s", route.path, route.methods)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI! The app is running."}

# Test endpoint
@app.get("/api/test")
async def test_api():
    return {"message": "FastAPI is working!"}

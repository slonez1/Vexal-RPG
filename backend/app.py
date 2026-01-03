<<<<<<< HEAD
from fastapi import FastAPI, WebSocket, HTTPException
from pydantic import BaseModel

# Initialize app
=======
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

<<<<<<< HEAD
from fastapi import FastAPI, WebSocket, HTTPException
from pydantic import BaseModel

# Initialize app
=======
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

>>>>>>> 9f02796 (Added backend folder with FastAPI app)
app = FastAPI()

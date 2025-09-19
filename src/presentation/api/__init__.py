from fastapi import APIRouter
from src.presentation.api.v1 import websocket

v1_router = APIRouter()
v1_router.include_router(websocket.router)

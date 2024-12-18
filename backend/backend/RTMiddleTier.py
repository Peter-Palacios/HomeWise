import asyncio
import json
from typing import Optional, Callable, Any
import aiohttp
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from settings import AZURE_OPENAI_WS_ENDPOINT, AZURE_OPENAI_API_KEY

#open ws connection





class RealTimeWS:
    def __init__(self,
                 aoai_endpoint: str,
                 api_key: str,
                 model_deployment: str):
        self.aoai_endpoint = aoai_endpoint
        self.api_key = api_key
        self.model_deployment = model_deployment
        self.session = None
        self.ws = None
        self._reconnect = False

    async def connect(self):
        ws_url = f"{self.aoai_endpoint}/openai/realtime"
        params = {
            "api-version": "2024-10-01-preview",
            "deployment": self.model_deployment
        }
        headers = {
            "api-key": self.api_key
        }

        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(ws_url, params=params, headers=headers)
        print("Connected to Azure OpenAI Realtime API")

    async def disconnect(self):
        if self.ws and not self.ws.closed:
            await self.ws.close()
        if self.session:
            await self.session.close()
        self.ws = None
        self.session = None
        print("Disconnected from Azure OpenAI Realtime API")

    async def send_json_message(self, msg: Any):
        if self.ws and not self.ws.closed:
            await self.ws.send_json(msg)

    async def start_session(self, enable_input_audio_transcription: bool = False):
        command = {
            "type": "session.update",
            "session": {
                "turn_detection": {
                    "type": "server_vad"
                }
            }
        }
        if enable_input_audio_transcription:
            command["session"]["input_audio_transcription"] = {"model": "whisper-1"}

        await self.send_json_message(command)

    async def add_user_audio(self, base64_audio: str):
        command = {
            "type": "input_audio_buffer.append",
            "audio": base64_audio
        }
        await self.send_json_message(command)

    async def clear_input_audio_buffer(self):
        command = {
            "type": "input_audio_buffer.clear"
        }
        await self.send_json_message(command)

# Instantiate the RealTimeConnection
rtc = RealTimeWS(
    aoai_endpoint="", 
    api_key="", 
    model_deployment="gpt-4o-realtime-preview-1001"
)



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:

    except WebSocketDisconnect:
        print("Client disconnected from /ws")
    # Construct the base URL and query parameters for the realtime endpoint

    # async def setup_ws_connection():
    #     ws_url = f"{AZURE_OPENAI_WS_ENDPOINT}/openai/realtime"
    #     params = {
    #         "api-version": "2024-10-01-preview",
    #         "deployment": "gpt-4o-realtime-preview-1001"
    #     }
    #     headers = {
    #         "api-key": AZURE_OPENAI_API_KEY
    #     }

    #     # Create a ClientSession and establish the WebSocket connection
    #     async with aiohttp.ClientSession() as session:
    #         async with session.ws_connect(ws_url, params=params, headers=headers) as ws:
    #             print("WebSocket connection opened to Azure OpenAI Realtime API")

    #             # Optionally, send a message to the server
    #             await ws.send_json({"type": "hello", "content": "Hello from client!"})

    #             # Listen for messages
    #             async for msg in ws:
    #                 if msg.type == aiohttp.WSMsgType.TEXT:
    #                     print("Message received:", msg.data)
    #                 elif msg.type == aiohttp.WSMsgType.CLOSED:
    #                     print("WebSocket closed by the server")
    #                     break
    #                 elif msg.type == aiohttp.WSMsgType.ERROR:
    #                     print("WebSocket error:", msg.data)
    #                     break



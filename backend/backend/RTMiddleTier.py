import asyncio
import base64
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import aiohttp
from settings import AZURE_OPENAI_WS_ENDPOINT, AZURE_OPENAI_API_KEY

app = FastAPI()

class RealTimeWS:
    def __init__(self, aoai_endpoint: str, api_key: str, model_deployment: str):
        self.aoai_endpoint = aoai_endpoint
        self.api_key = api_key
        self.model_deployment = model_deployment
        self.session = None
        self.ws = None

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

    async def send_json_message(self, msg: dict):
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

rtc = RealTimeWS(
    aoai_endpoint=AZURE_OPENAI_WS_ENDPOINT, 
    api_key=AZURE_OPENAI_API_KEY, 
    model_deployment="gpt-4o-realtime-preview-1001"
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Accept connection from React front-end
    await websocket.accept()
    
    # Connect to Azure OpenAI realtime WebSocket
    await rtc.connect()
    # Start the session. Set enable_input_audio_transcription to True if you want transcription.
    await rtc.start_session(enable_input_audio_transcription=True)

    async def forward(react_ws: WebSocket, azure_rtc: RealTimeWS):
        # Forward data from React client to Azure endpoint
        # We assume React client sends raw binary audio chunks
        while True:
            try:
                data = await react_ws.receive_bytes()
            except WebSocketDisconnect:
                print("Client disconnected from /ws")
                break

            # Convert raw audio to base64 before sending to Azure
            base64_data = base64.b64encode(data).decode('utf-8')
            await azure_rtc.add_user_audio(base64_data)

    async def reverse(react_ws: WebSocket, azure_rtc: RealTimeWS):
        # Receive responses from Azure endpoint and forward to React
        async for msg in azure_rtc.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                await react_ws.send_text(msg.data)
            elif msg.type == aiohttp.WSMsgType.BINARY:
                # If Azure ever sends binary data, forward it as is
                await react_ws.send_bytes(msg.data)
            elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                # Exit on closed or error
                break

    fwd_task = asyncio.create_task(forward(websocket, rtc))
    rev_task = asyncio.create_task(reverse(websocket, rtc))

    await asyncio.gather(fwd_task, rev_task, return_exceptions=True)

    # await rtc.disconnect()

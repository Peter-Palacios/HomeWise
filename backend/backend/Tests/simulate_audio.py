import asyncio
import websockets
import base64

async def send_audio():
    async with websockets.connect("ws://localhost:8000/ws") as websocket:
        print("Connected to WebSocket server")

        audio_file_path = "recording.m4a"
        with open(audio_file_path, "rb") as audio_file:
            audio_data = audio_file.read()

        #send in chunks
        chunk_size = 1024 
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            base64_chunk = base64.b64encode(chunk).decode("utf-8")

            await websocket.send(chunk)

        print("All audio chunks sent")

        try:
            while True:
                response = await websocket.recv()
                print(f"Received from server: {response}")
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")

asyncio.run(send_audio())

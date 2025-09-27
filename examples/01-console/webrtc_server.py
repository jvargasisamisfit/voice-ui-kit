#!/usr/bin/env python
"""
Small WebRTC server for Pipecat bot
"""
import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMMessagesFrame, EndFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.network.small_webrtc import SmallWebRTCTransport, SmallWebRTCConnection

from dotenv import load_dotenv

load_dotenv()

# Create FastAPI app
app = FastAPI()

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# System prompt
system_prompt = """You are a helpful and friendly AI voice assistant.
Your responses should be natural, conversational, and concise.
You should engage with warmth and personality, while being helpful and informative."""

async def run_bot(webrtc_connection):
    """Run the bot with the WebRTC connection"""

    # Create transport
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            video_in_enabled=False,
            video_out_enabled=False,
            vad_analyzer=SileroVADAnalyzer(params={"stop_secs": 0.2}),
        ),
    )

    # Create services
    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
    )

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="79a125e8-cd45-4c13-8a67-188112f4dd22",  # British Lady
    )

    # Initial messages
    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # Create pipeline
    pipeline = Pipeline([
        transport.input(),
        stt,
        llm,
        tts,
        transport.output(),
    ])

    # Create task
    task = PipelineTask(pipeline)

    # Handle events
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        # Send initial message
        await task.queue_frames([
            LLMMessagesFrame(messages + [
                {"role": "assistant", "content": "Hello! I'm your AI assistant. How can I help you today?"}
            ])
        ])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.queue_frames([EndFrame()])

    # Run the task
    runner = PipelineRunner()
    await runner.run(task)

@app.post("/")
async def handle_webrtc(request: Request):
    """Handle WebRTC offer/answer negotiation"""
    try:
        data = await request.json()
        logger.info(f"Received WebRTC request: {data.get('type', 'unknown')}")

        # Create WebRTC connection
        webrtc_connection = SmallWebRTCConnection(
            ice_servers=["stun:stun.l.google.com:19302"]
        )

        # Handle the offer/answer
        if "sdp" in data:
            # This is an offer from the client
            answer = await webrtc_connection.answer(data["sdp"])

            # Start the bot in the background
            asyncio.create_task(run_bot(webrtc_connection))

            # Return the answer
            return {
                "type": "answer",
                "sdp": answer
            }
        else:
            logger.error("No SDP in request")
            return {"error": "No SDP provided"}, 400

    except Exception as e:
        logger.error(f"Error handling WebRTC: {e}")
        return {"error": str(e)}, 500

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    logger.info("Starting Small WebRTC server...")
    uvicorn.run(app, host="0.0.0.0", port=7860)
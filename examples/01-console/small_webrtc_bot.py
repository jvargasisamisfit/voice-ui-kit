#!/usr/bin/env python
"""
Small WebRTC bot server that works with Voice UI Kit frontend
"""
import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.aggregators.turn_detector import LocalSmartTurnAnalyzerV3
from pipecat.frames.frames import LLMMessagesFrame, EndFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport, SmallWebRTCCallbacks

from dotenv import load_dotenv

load_dotenv()

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:7860"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# System prompt
system_prompt = """You are Mandy, a helpful and friendly AI voice assistant.
Your responses should be natural, conversational, and concise.
You should engage with warmth and personality, while being helpful and informative."""

async def run_bot(transport: SmallWebRTCTransport):
    """Run the bot with the Small WebRTC transport"""

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

    # Queue initial message
    await task.queue_frames([
        LLMMessagesFrame(messages + [
            {"role": "assistant", "content": "Hello! I'm Mandy, your AI assistant. How can I help you today?"}
        ])
    ])

    # Run the task
    runner = PipelineRunner()
    await runner.run(task)

@app.post("/offer")
async def handle_offer(request: Request):
    """Handle WebRTC offer from Voice UI Kit frontend"""
    try:
        data = await request.json()
        logger.info("Received offer from Voice UI Kit")

        # Create transport with Small WebRTC callbacks
        callbacks = SmallWebRTCCallbacks(
            on_offer=lambda offer: offer,  # Just return the offer
            on_answer=lambda answer: None,  # We'll handle this differently
        )

        transport = SmallWebRTCTransport(
            params=TransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                video_in_enabled=False,
                video_out_enabled=False,
                vad_analyzer=SileroVADAnalyzer(params={"stop_secs": 0.2}),
                turn_detector=LocalSmartTurnAnalyzerV3(),
            ),
            callbacks=callbacks,
        )

        # Process the offer and get an answer
        answer = await transport.receive_offer(data)

        # Start the bot in the background
        asyncio.create_task(run_bot(transport))

        # Return the answer
        return answer

    except Exception as e:
        logger.error(f"Error handling offer: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 500

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

# Serve the built-in client UI
@app.get("/")
async def root():
    """Redirect to client UI"""
    return FileResponse("index.html") if os.path.exists("index.html") else {"message": "Small WebRTC Bot Server"}

if __name__ == "__main__":
    logger.info("Starting Small WebRTC Bot Server on port 7860...")
    logger.info("Frontend should connect to: http://localhost:7860/offer")
    uvicorn.run(app, host="0.0.0.0", port=7860)
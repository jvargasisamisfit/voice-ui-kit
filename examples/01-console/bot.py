#!/usr/bin/env python
"""
Pipecat bot that works with Voice UI Kit frontend using SmallWebRTC transport.
Run with: python bot.py -t webrtc
This will start the server on http://localhost:7860 with the /api/offer endpoint
"""

import os
import asyncio
from loguru import logger
from dotenv import load_dotenv

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.frames.frames import LLMMessagesFrame

# Import RTVI components
from pipecat.processors.frameworks.rtvi import RTVIProcessor, RTVIConfig
from pipecat.processors.frameworks.rtvi import RTVIObserver

# Import transport types for runner
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.transports.base_transport import TransportParams
from pipecat.runner.types import RunnerArguments, SmallWebRTCRunnerArguments

load_dotenv()

# System prompt
system_prompt = """You are Mandi, a helpful and friendly AI voice assistant.
Your responses should be natural, conversational, and concise.
You should engage with warmth and personality, while being helpful and informative."""

async def run_bot(transport):
    """Core bot logic that works with the transport."""

    # Initialize services
    stt = DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY"),
    )

    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
    )

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="79a125e8-cd45-4c13-8a67-188112f4dd22",  # British Lady
    )

    # Create RTVI processor for Voice UI Kit integration
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # Create context and aggregator
    messages = [
        {"role": "system", "content": system_prompt},
    ]

    context = OpenAILLMContext(messages=messages)
    context_aggregator = llm.create_context_aggregator(context)

    # Build the pipeline with RTVI processor
    pipeline = Pipeline([
        transport.input(),              # Receive audio from client
        rtvi,                          # RTVI protocol handler (processes client messages)
        stt,                           # Convert speech to text
        context_aggregator.user(),     # Add user messages to context
        llm,                           # Process with LLM
        tts,                           # Convert response to speech
        transport.output(),            # Send audio back to client
        context_aggregator.assistant(), # Add assistant messages to context
    ])

    # Create task with RTVI observer
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],  # RTVI observer for protocol messages
    )

    # Handle client ready event
    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        logger.info("Client connected and ready")
        # Signal bot is ready to receive messages
        await rtvi.set_bot_ready()
        # Queue initial greeting
        await task.queue_frames([
            LLMMessagesFrame(messages + [
                {"role": "assistant", "content": "Hello! I'm Mandi, your AI assistant. How can I help you today?"}
            ])
        ])

    runner = PipelineRunner()
    await runner.run(task)

async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat runner."""

    logger.info(f"Starting bot with runner args type: {type(runner_args)}")

    if isinstance(runner_args, SmallWebRTCRunnerArguments):
        # Create SmallWebRTC transport for Voice UI Kit
        transport = SmallWebRTCTransport(
            params=TransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                video_in_enabled=False,
                video_out_enabled=False,
                vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.3)),
            ),
            webrtc_connection=runner_args.webrtc_connection,
        )

        await run_bot(transport)
    else:
        logger.error(f"Unsupported runner arguments type: {type(runner_args)}")
        return

if __name__ == "__main__":
    # Use Pipecat's runner which sets up the server automatically
    from pipecat.runner.run import main
    main()
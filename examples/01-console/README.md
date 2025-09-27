# Voice AI Console - Pipecat + Voice UI Kit

A complete voice AI application with both backend (Pipecat) and frontend (Voice UI Kit) for real-time conversational AI. This setup provides a working voice assistant with speech recognition, AI responses, and natural voice synthesis.

## Features

- 🎙️ **Real-time voice conversations** with AI
- 📹 **Camera toggle** (OFF by default, user-controlled)
- 🎨 **Customizable React UI** with Tailwind CSS
- 🔊 **High-quality voice synthesis** via Cartesia
- 🧠 **Powered by OpenAI GPT** for intelligent responses
- 🎯 **Low-latency speech recognition** with Deepgram

## Architecture

```
┌─────────────────────────┐     ┌─────────────────────────┐
│   Next.js Frontend      │────▶│   Pipecat Backend       │
│   (React + TypeScript)  │     │   (Python)              │
│   Port: 3001           │     │   Port: 7860           │
└─────────────────────────┘     └─────────────────────────┘
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    │                     │                     │
            ┌───────▼────────┐   ┌───────▼────────┐   ┌────────▼───────┐
            │   Deepgram     │   │    OpenAI      │   │    Cartesia    │
            │   (STT)        │   │    (LLM)       │   │    (TTS)       │
            └────────────────┘   └────────────────┘   └────────────────┘
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) package manager
- API Keys:
  - [Deepgram](https://console.deepgram.com/signup) - Speech-to-Text
  - [OpenAI](https://platform.openai.com/api-keys) - LLM
  - [Cartesia](https://play.cartesia.ai/sign-up) - Text-to-Speech

## Installation

1. **Install dependencies:**

   ```bash
   # Python dependencies
   uv sync

   # Node.js dependencies
   npm install
   ```

2. **Configure API keys:**

   The `.env` file should contain:
   ```
   DEEPGRAM_API_KEY=your_deepgram_key
   OPENAI_API_KEY=your_openai_key
   CARTESIA_API_KEY=your_cartesia_key
   ```

## Quick Start

### 1. Start the Backend (Pipecat Bot)

```bash
# Run the voice AI backend with WebRTC transport
uv run bot.py -t webrtc
```

The backend will start on http://localhost:7860 with RTVI protocol support

### 2. Access the Voice Interface

Open your browser and navigate to:
```
http://localhost:7860/client
```

### 3. Connect and Start Talking

1. Click the **"Connect"** button
2. Allow microphone access when prompted
3. Start speaking - the AI will respond naturally!

## Alternative: Voice UI Kit Frontend

For a more advanced UI with the custom Voice UI Kit frontend:

```bash
# In a new terminal
npm run dev
```

Then open http://localhost:3000 in your browser.

The Voice UI Kit frontend works seamlessly with the SmallWebRTC transport and RTVI protocol for:
- Real-time message display in the conversation area
- Proper agent status updates
- Complete integration between frontend and backend

## How It Works

When you connect:
1. WebRTC establishes a peer-to-peer connection
2. Your speech is captured and sent to Deepgram for transcription
3. The transcript is processed by OpenAI GPT for intelligent responses
4. Responses are synthesized to speech using Cartesia's natural voices
5. Audio streams back to you in real-time with low latency

## Project Structure

```
01-console/
├── bot.py                 # Pipecat backend with RTVI support
├── .env                    # API keys and configuration
├── .env.local             # Frontend environment variables
├── pyproject.toml         # Python dependencies
├── package.json           # Node.js dependencies
├── src/
│   └── app/
│       ├── page.tsx       # Main React component (Voice UI Kit)
│       └── api/
│           └── offer/     # WebRTC connection endpoint
└── README.md             # This file
```

## Customization

### Backend (bot.py)

- **Change the AI personality**: Modify the system prompt in the `messages` array
- **Adjust voice settings**: Change the `voice_id` in CartesiaTTSService
- **Add custom functions**: Implement function calling for specific tasks
- **Modify audio settings**: Adjust VAD parameters, sample rates, etc.

### Frontend (React)

- **UI Components**: Modify components in `src/app/page.tsx`
- **Styling**: Use Tailwind CSS classes or modify the theme
- **Camera Settings**: The `noUserVideo` prop controls camera visibility
- **Connection Parameters**: Update WebRTC settings in `connectParams`

## Known Issues

### Camera/Webcam Activation
**Issue**: The browser may request camera permissions even though video is disabled in the backend.

**Reason**: The built-in Pipecat client UI requests both microphone and camera permissions by default, even when `video_in_enabled=False` is set in the backend.

**Workaround**:
- Deny camera access when prompted - the voice chat will still work perfectly
- Or use browser settings to block camera access for localhost:7860
- The backend doesn't use video, so denying camera access has no impact on functionality

### Audio Configuration
- **VAD (Voice Activity Detection)**: Silero VAD with 0.2 second stop threshold
- **Turn Detection**: LocalSmartTurnAnalyzerV3 for conversation flow
- **Sample Rate**: Configurable in transport parameters

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   - Backend defaults to port 7860
   - Frontend will auto-select next available port (3001 if 3000 is busy)

2. **API Key Errors**
   - Verify all keys in `.env` are correct
   - Check API key quotas and limits

3. **Microphone Not Working**
   - Ensure browser has microphone permissions
   - Check system audio settings
   - Try a different browser

4. **Connection Failed**
   - Verify both services are running
   - Check `.env.local` points to correct backend URL
   - Ensure no firewall blocking localhost connections

### Debug Mode

To see detailed logs:
```bash
# Backend with debug logging
LOGURU_LEVEL=DEBUG uv run custom_bot.py

# Frontend with verbose output
npm run dev -- --verbose
```

## API Endpoints

- **Backend WebRTC Offer**: `http://localhost:7860/offer`
- **Frontend API Proxy**: `http://localhost:3001/api/offer`
- **Static Client**: `http://localhost:7860/client` (if using default client)

## Contributing

Feel free to customize and extend this project:
- Add new AI capabilities
- Implement custom UI components
- Integrate additional services
- Improve conversation flow

## License

This project uses:
- [Pipecat](https://github.com/pipecat-ai/pipecat) - BSD 2-Clause License
- [Voice UI Kit](https://github.com/pipecat-ai/voice-ui-kit) - Check repository for license

## Support

For issues or questions:
- Pipecat Discord: https://discord.gg/pipecat
- Documentation: https://docs.pipecat.ai/
- Voice UI Kit Docs: https://voiceuikit.pipecat.ai
# Autonomous Local YouTube Video Factory

An end-to-end, 100% local, free, and autonomous video production pipeline designed for Apple Silicon (MacBook Air M4 16GB+). This system automatically processes a queue of topics, generates scripts, synthesizes human-grade voiceovers, creates dark-mode tech visuals, compiles slide animations, interpolates frames via optical flow, and uploads finished videos to YouTube—all without human intervention.

---

## Architecture Overview

```
[ topics.json ]
       │
       ▼
1. Script & Prompts   ──► Ollama (Qwen 2.5 Coder 7B)
       │                  (Model unloaded after execution)
       ▼
2. Voiceover Synthesis ──► mlx-audio (Kokoro-82M)
       │                  (Generates voiceover.wav)
       ▼
3. Visual Generation  ──► FLUX.1-schnell (Local API / Draw Things / SD WebUI)
       │                  (Batch renders 15 dark-mode presentation slides)
       ▼
4. Video Composition  ──► Remotion (Headless CLI render at 18 FPS)
       │
       ▼
5. Optical Flow Pass  ──► FFmpeg (minterpolate 18 FPS -> 60 FPS -> 24 FPS Master)
       │
       ▼
6. YouTube Upload     ──► YouTube Data API v3 (google-api-python-client)

```

---

## Hardware & System Requirements

* **Machine:** Apple Silicon Mac (MacBook Air M4, M3, or M2 with 16GB Unified Memory minimum).
* **OS:** macOS Sonoma or macOS Sequoia.
* **Storage:** 20 GB free SSD space for temporary video workspace and model weights.
* **Power:** Mac must be connected to power during automated overnight batch rendering.

---

## Prerequisites & Installation

### 1. Core System Dependencies

Install Homebrew, Python, Node.js, and FFmpeg via your terminal:

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.11, Node.js, and FFmpeg
brew install python@3.11 node ffmpeg

```

### 2. Ollama & Scripting LLM

Install Ollama to run the scriptwriting LLM locally:

```bash
# Install Ollama
brew install ollama

# Start Ollama server
ollama serve

# Pull the Qwen 2.5 Coder 7B model (in a separate terminal)
ollama pull qwen2.5-coder:7b

```

### 3. Audio Engine (`mlx-audio` + Kokoro TTS)

Install Apple Silicon optimized `mlx-audio` for local voiceover generation:

```bash
pip install mlx-audio requests google-api-python-client

```

### 4. Local Image Generation API (FLUX.1-schnell)

Set up a local diffusion server listening on `http://localhost:7860`:

* **Option A (Draw Things):** Install Draw Things from the macOS App Store, load **FLUX.1-schnell**, and enable the API server under Settings.
* **Option B (AUTOMATIC1111 / ComfyUI):** Launch your WebUI with `--api` enabled on port `7860`.

### 5. Remotion Video Framework

Initialize the Remotion video engine inside your project root:

```bash
# Initialize Remotion template inside your repository folder
npx create-video@latest --template=helloworld .
npm install

```

---

## Directory Structure

Ensure your project folder is organized as follows:

```text
local-youtube-factory/
├── autovideo.py         # Master Python orchestrator script
├── topics.json          # Queue of video topics
├── credentials.json     # Optional: YouTube Data API v3 OAuth client secret
├── package.json         # Node.js dependencies for Remotion
├── src/                 # Remotion React component templates
│   ├── Root.tsx         # Video timeline configuration
│   └── MainVideo.tsx    # Slide layout component
└── video_workspace/     # Auto-created temporary build directory

```

---

## Configuration Files

### 1. `topics.json`

Create a JSON file containing the queue of topics you want the system to produce:

```json
[
  "Can a 16GB Mac Run Local LLMs for Coding?",
  "Ollama vs MLX: Which Apple Silicon Engine is Faster?",
  "How to Replace Cursor with Void IDE and Qwen 7B for Free",
  "Running DeepSeek R1 Locally on Apple Silicon M4"
]

```

### 2. Remotion Root (`src/Root.tsx`)

Configure your Remotion setup to render at 18 FPS:

```tsx
import { Composition } from 'remotion';
import { MainVideo } from './MainVideo';

export const RemotionRoot = () => {
  return (
    <Composition
      id="MainVideo"
      component={MainVideo}
      durationInFrames={18 * 120} // 2-minute video at 18 FPS
      fps={18}
      width={1280}
      height={720}
      defaultProps={{
        title: "Default Title",
        voiceover_text: ""
      }}
    />
  );
};

```

---

## Running the Autonomous Pipeline

To run the pipeline continuously without your Mac going to sleep or thermal throttling, execute the orchestrator wrapped in macOS `caffeinate`:

```bash
caffeinate -i python3 autovideo.py

```

### Execution Steps Executed per Topic:

1. **Queue Selection:** Reads the top item from `topics.json`.
2. **Script Generation:** Calls Ollama (`qwen2.5-coder:7b`) to generate narrative JSON and unloads the model immediately.
3. **Audio Generation:** Calls `mlx-audio-tts` to generate `voiceover.wav` using Kokoro-82M.
4. **Visual Batching:** Pings local API (`http://localhost:7860`) to generate 15 FLUX presentation slides.
5. **Headless Render:** Compiles the base video at 18 FPS using `npx remotion render`.
6. **Motion Smoothing:** Applies FFmpeg `minterpolate` optical flow filters (18 FPS ➔ 60 FPS ➔ 24 FPS Master).
7. **YouTube Upload:** Uploads via YouTube Data API v3 and marks the topic as completed in `topics.json`.

---

## Optimization & Troubleshooting

* **Memory Management:** The orchestrator runs `ollama stop qwen2.5-coder:7b` after scripting to ensure 100% of Unified RAM is available for FLUX image generation and Remotion compilation.
* **Thermal Throttling:** On fanless M-series laptops, running sequentially keeps thermal generation low. If throttling occurs, insert a 60-second `time.sleep(60)` between video loops.
* **Fallback Visuals:** If the local image generation server is offline, the script automatically falls back to generating solid dark-mode placeholder background slides using FFmpeg.

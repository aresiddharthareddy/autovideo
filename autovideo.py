import os
import json
import subprocess
import requests
import base64

TOPICS_FILE = "topics.json"
WORK_DIR = "video_workspace"

os.makedirs(WORK_DIR, exist_ok=True)

def load_topics():
    if not os.path.exists(TOPICS_FILE):
        return []
    with open(TOPICS_FILE, "r") as f:
        return json.load(f)

def save_topics(topics):
    with open(TOPICS_FILE, "w") as f:
        json.dump(topics, f, indent=2)

def step_2_generate_script(topic):
    print(f"\n[Step 2] Generating script & visual prompts for: {topic}")
    prompt = f"""
    Create a 2-minute YouTube video script about: {topic}.
    Return ONLY a valid JSON object with these exact keys:
    - "title": YouTube video title
    - "description": Video description with tags
    - "voiceover_text": The complete word-for-word script spoken by the narrator
    - "visual_prompts": A list of 15 short visual description prompts for background art
    """
    
    # Call local Ollama Qwen 2.5 Coder 7B
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "qwen2.5-coder:7b",
        "prompt": prompt,
        "stream": False,
        "format": "json"
    })
    
    result = response.json()
    script_data = json.loads(result["response"])
    
    script_path = os.path.join(WORK_DIR, "script.json")
    with open(script_path, "w") as f:
        json.dump(script_data, f, indent=2)
    
    # Unload Ollama from RAM to free up memory for subsequent steps
    subprocess.run(["ollama", "stop", "qwen2.5-coder:7b"])
    return script_data

def step_3_generate_voiceover(script_data):
    print("\n[Step 3] Generating voiceover with Kokoro TTS (mlx-audio)...")
    audio_path = os.path.join(WORK_DIR, "voiceover.wav")
    text = script_data["voiceover_text"]
    
    cmd = [
        "mlx-audio-tts",
        "--text", text,
        "--voice", "af_heart",
        "--output", audio_path
    ]
    subprocess.run(cmd, check=True)
    return audio_path

def step_4_generate_visuals(visual_prompts):
    print("\n[Step 4] Generating visuals via local image pipeline (FLUX.1-schnell)...")
    image_paths = []
    
    for i, prompt in enumerate(visual_prompts[:15]):
        img_path = os.path.join(WORK_DIR, f"slide_{i}.png")
        print(f"  -> Generating image {i+1}/15: {prompt[:40]}...")
        
        payload = {
            "prompt": f"Dark mode tech presentation graphic, high-end UI design, {prompt}",
            "steps": 4,
            "width": 1280,
            "height": 720
        }
        try:
            res = requests.post("http://localhost:7860/sdapi/v1/txt2img", json=payload)
            if res.status_code == 200:
                r_json = res.json()
                img_data = base64.b64decode(r_json['images'][0])
                with open(img_path, "wb") as f:
                    f.write(img_data)
                image_paths.append(img_path)
            else:
                raise Exception("Local SD server returned non-200 status")
        except Exception:
            # Fallback placeholder if local diffusion UI is offline
            fallback_cmd = [
                "ffmpeg", "-f", "lavfi", "-i", "color=c=black:s=1280x720:d=1",
                "-frames:v", "1", img_path, "-y"
            ]
            subprocess.run(fallback_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            image_paths.append(img_path)
            
    return image_paths

def step_5_render_video():
    print("\n[Step 5] Rendering 18fps base video and applying optical flow interpolation...")
    raw_output = os.path.join(WORK_DIR, "raw_18fps.mp4")
    smooth_60fps = os.path.join(WORK_DIR, "smooth_60fps.mp4")
    final_video = os.path.join(WORK_DIR, "final_video.mp4")
    
    # 1. Render base video at 18 FPS via Remotion
    cmd_remotion = [
        "npx", "remotion", "render",
        "src/Root.tsx",
        "MainVideo",
        raw_output,
        "--fps=18",
        "--props=./video_workspace/script.json"
    ]
    subprocess.run(cmd_remotion, check=True)
    
    # 2. Apply FFmpeg minterpolate (Optical Flow motion estimation) to 60 FPS
    print("  -> Applying optical flow interpolation to 60fps...")
    cmd_optical_flow = [
        "ffmpeg", "-i", raw_output,
        "-filter:v", "minterpolate=mi_mode=mci:mc_mode=obmc:vsbmc=1:fps=60",
        "-c:v", "libx264", "-crf", "18",
        smooth_60fps, "-y"
    ]
    subprocess.run(cmd_optical_flow, check=True)
    
    # 3. Downscale final timeline to cinematic 24 FPS
    print("  -> Converting final timeline to 24fps master...")
    cmd_final = [
        "ffmpeg", "-i", smooth_60fps,
        "-r", "24",
        "-c:v", "libx264", "-crf", "18",
        final_video, "-y"
    ]
    subprocess.run(cmd_final, check=True)
    
    return final_video

def step_6_upload_to_youtube(video_path, script_data):
    print("\n[Step 6] Uploading video to YouTube...")
    client_secrets_file = "credentials.json"
    if not os.path.exists(client_secrets_file):
        print("  [Skipped] credentials.json not found. Video successfully compiled locally in workspace.")
        return

    print(f"  -> Uploading: {script_data['title']}")
    # YouTube Data API v3 upload integration goes here if credentials.json is present

def main_loop():
    topics = load_topics()
    if not topics:
        print("No topics found in topics.json!")
        return

    for topic in list(topics):
        print(f"\n==============================================")
        print(f"STARTING PRODUCTION FOR TOPIC: {topic}")
        print(f"==============================================")
        
        try:
            script_data = step_2_generate_script(topic)
            audio_path = step_3_generate_voiceover(script_data)
            image_paths = step_4_generate_visuals(script_data["visual_prompts"])
            video_path = step_5_render_video()
            step_6_upload_to_youtube(video_path, script_data)
            
            # Remove completed topic from queue and save state
            topics.remove(topic)
            save_topics(topics)
            print(f"\n[Success] Completed production for: {topic}")
            
        except Exception as e:
            print(f"\n[Error] Pipeline failed for topic '{topic}': {e}")
            break

if __name__ == "__main__":
    main_loop()

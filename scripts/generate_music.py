"""
ENOMETA BGM 생성기
- ACE-Step 1.5 (instrumental, Max Cooper 스타일)
- 출력: audio/bgm.wav
- RTX 3060 6GB: DiT only 모드 or 0.6B LM + CPU offload
"""

import sys
import os
import subprocess
import json
import time

# ACE-Step 1.5 프로젝트 경로 (junction 사용: 한국어 경로 우회)
ACESTEP_DIR = r"C:\ACE-Step"
ACESTEP_UV = os.path.join(ACESTEP_DIR, ".venv", "Scripts", "python.exe")

# BGM 프리셋
PRESETS = {
    "contemplative": {
        "prompt": "ambient electronic, soft piano, gentle pads, contemplative mood, minimal beats, Max Cooper style generative music, atmospheric textures, 80 bpm",
        "bpm": 80,
        "duration": 35,
    },
    "noir_mystery": {
        "prompt": "dark jazz noir, soft brushed drums, muted trumpet, upright bass, vintage vinyl atmosphere, mysterious contemplative mood, 75 bpm",
        "bpm": 75,
        "duration": 35,
    },
    "hopeful_dawn": {
        "prompt": "hopeful ambient, warm synth pads, gentle arpeggios, ascending melody, sunrise atmosphere, calm inspirational, 85 bpm",
        "bpm": 85,
        "duration": 35,
    },
    "tension": {
        "prompt": "dark ambient tension, low drones, sparse percussion, dissonant textures, building pressure, industrial undertones, 70 bpm",
        "bpm": 70,
        "duration": 35,
    },
}


def generate_bgm_via_api(
    prompt: str,
    output_path: str,
    duration: int = 35,
    bpm: int = 80,
):
    """ACE-Step 1.5 REST API를 호출하여 BGM 생성 (서버가 실행 중이어야 함)"""
    import requests

    response = requests.post("http://localhost:8001/release_task", json={
        "prompt": prompt,
        "lyrics": "[inst]",
        "audio_duration": duration,
        "audio_format": "wav",
        "batch_size": 1,
        "bpm": bpm,
        "inference_steps": 8,
        "thinking": False,
        "seed": -1,
    }, timeout=300)

    result = response.json()
    if "error" in result:
        raise RuntimeError(f"ACE-Step API error: {result['error']}")

    # 오디오 다운로드
    audio_url = result.get("audio_url") or result.get("url")
    if audio_url:
        audio_response = requests.get(f"http://localhost:8001{audio_url}")
        with open(output_path, "wb") as f:
            f.write(audio_response.content)
    else:
        print(f"Warning: No audio URL in response. Full response: {json.dumps(result, indent=2)}")
        return None

    return output_path


def generate_bgm_via_cli(
    prompt: str,
    output_path: str,
    duration: int = 35,
    bpm: int = 80,
):
    """ACE-Step 1.5 CLI로 BGM 생성 (API 서버 없이 직접 실행)"""

    # ACE-Step venv의 Python으로 인라인 스크립트 실행
    script = f"""
import sys, os
os.chdir(r'{ACESTEP_DIR}')

from acestep.handler import AceStepHandler
import torch
import soundfile as sf
import numpy as np

project_root = r'{ACESTEP_DIR}'

handler = AceStepHandler()
handler.initialize_service(
    project_root=project_root,
    config_path='acestep-v15-turbo',
    device='auto',
    offload_to_cpu=True,
)

result = handler.generate_music(
    captions={json.dumps(prompt)},
    lyrics="[inst]",
    audio_duration={duration},
    bpm={bpm},
    inference_steps=8,
    guidance_scale=3.0,
    batch_size=1,
    seed=-1,
)

# result는 dict
print(f"Result keys: {{list(result.keys())}}")

if 'audio' in result:
    sr = result.get('sample_rate', 48000)
    audio = result['audio']
elif 'audios' in result:
    sr = result.get('sample_rate', 48000)
    audio = result['audios'][0]
elif 'wav' in result:
    sr = result.get('sample_rate', 48000)
    audio = result['wav']
else:
    # 가능한 키 출력 후 첫 번째 numpy/tensor 값 사용
    for k, v in result.items():
        print(f"  {{k}}: {{type(v)}}")
        if hasattr(v, 'shape'):
            print(f"    shape: {{v.shape}}")
    raise RuntimeError(f"Cannot find audio in result keys: {{list(result.keys())}}")

if isinstance(audio, torch.Tensor):
    audio = audio.cpu().numpy()

if audio.ndim > 1:
    audio = audio.T if audio.shape[0] < audio.shape[1] else audio
    if audio.ndim > 1:
        audio = audio[:, 0]

sf.write(r'{output_path}', audio, sr)
print(f"Saved: {{r'{output_path}'}} (sr={{sr}}, duration={{len(audio)/sr:.1f}}s)")

# VRAM 해제
del handler
torch.cuda.empty_cache()
"""

    print(f"Running ACE-Step 1.5 via CLI...")
    print(f"Prompt: {prompt[:80]}...")

    result = subprocess.run(
        [ACESTEP_UV, "-c", script],
        capture_output=True,
        text=True,
        cwd=ACESTEP_DIR,
        timeout=1800,
    )

    if result.returncode != 0:
        print(f"STDERR: {result.stderr}")
        raise RuntimeError(f"ACE-Step CLI failed: {result.stderr[-500:]}")

    print(result.stdout)
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python generate_music.py <preset_name> [output.wav]")
        print("  python generate_music.py --prompt '<custom prompt>' [output.wav] [duration] [bpm]")
        print()
        print("Presets:", ", ".join(PRESETS.keys()))
        sys.exit(1)

    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if sys.argv[1] == "--prompt":
        prompt = sys.argv[2]
        output = sys.argv[3] if len(sys.argv) > 3 else os.path.join(project_dir, "audio", "bgm.wav")
        duration = int(sys.argv[4]) if len(sys.argv) > 4 else 35
        bpm = int(sys.argv[5]) if len(sys.argv) > 5 else 80
    elif sys.argv[1] in PRESETS:
        preset = PRESETS[sys.argv[1]]
        prompt = preset["prompt"]
        output = sys.argv[2] if len(sys.argv) > 2 else os.path.join(project_dir, "audio", "bgm.wav")
        duration = preset["duration"]
        bpm = preset["bpm"]
    else:
        print(f"Unknown preset: {sys.argv[1]}")
        print("Available:", ", ".join(PRESETS.keys()))
        sys.exit(1)

    os.makedirs(os.path.dirname(output), exist_ok=True)

    start = time.time()
    generate_bgm_via_cli(prompt, output, duration, bpm)
    elapsed = time.time() - start
    print(f"Total time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()

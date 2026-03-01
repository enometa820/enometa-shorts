"""
ENOMETA 마스터 파이프라인
대본 + 제목 → 완성된 쇼츠 MP4

사용법:
  python scripts/enometa_render.py --title "각성" --script episodes/ep001/script.txt
  python scripts/enometa_render.py --title "각성" --script episodes/ep001/script.txt --step tts
  python scripts/enometa_render.py --title "각성" --script episodes/ep001/script.txt --bgm-preset noir_mystery

GPU 도구(TTS, BGM)는 순차 실행 (6GB VRAM 동시 사용 불가)
"""

import sys
import os
import json
import time
import argparse
import subprocess

# 프로젝트 루트
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")
AUDIO_DIR = os.path.join(PROJECT_DIR, "audio")
CONFIG_DIR = os.path.join(PROJECT_DIR, "config")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "output")

# Python 경로
PYTHON = os.path.join(
    os.path.expanduser("~"),
    "AppData", "Local", "Programs", "Python", "Python311", "python.exe",
)

# ACE-Step venv Python
ACESTEP_DIR = os.path.join(os.path.dirname(PROJECT_DIR), "ACE-Step-1.5")
ACESTEP_PYTHON = os.path.join(ACESTEP_DIR, ".venv", "Scripts", "python.exe")


def ensure_dirs():
    """필요한 디렉토리 생성"""
    for d in [AUDIO_DIR, CONFIG_DIR, OUTPUT_DIR,
              os.path.join(AUDIO_DIR, "segments")]:
        os.makedirs(d, exist_ok=True)


def load_status(episode_dir: str) -> dict:
    """상태 파일 로드"""
    status_path = os.path.join(episode_dir, "status.json")
    if os.path.exists(status_path):
        with open(status_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_status(episode_dir: str, status: dict):
    """상태 파일 저장"""
    status_path = os.path.join(episode_dir, "status.json")
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def step_tts(episode_dir: str, script_text: str, force: bool = False):
    """[2] TTS 나레이션 생성 (Chatterbox Multilingual)"""
    output = os.path.join(episode_dir, "narration.wav")
    if os.path.exists(output) and not force:
        print(f"  [skip] narration.wav already exists")
        return output

    voice_ref = os.path.join(PROJECT_DIR, "assets", "voice_ref.wav")
    if not os.path.exists(voice_ref):
        raise FileNotFoundError(f"Voice reference not found: {voice_ref}")

    print(f"  Generating TTS...")
    cmd = [
        PYTHON, os.path.join(SCRIPTS_DIR, "generate_voice.py"),
        script_text, output, voice_ref,
    ]
    result = subprocess.run(cmd, cwd=PROJECT_DIR, timeout=600)
    if result.returncode != 0:
        raise RuntimeError("TTS generation failed")

    return output


def step_bgm(episode_dir: str, preset: str = "contemplative", force: bool = False):
    """[3] BGM 생성 (ACE-Step 1.5)"""
    output = os.path.join(episode_dir, "bgm.wav")
    if os.path.exists(output) and not force:
        print(f"  [skip] bgm.wav already exists")
        return output

    print(f"  Generating BGM (preset: {preset})...")
    cmd = [
        ACESTEP_PYTHON,
        os.path.join(SCRIPTS_DIR, "generate_music.py"),
        preset, output,
    ]
    result = subprocess.run(cmd, cwd=ACESTEP_DIR, timeout=600)
    if result.returncode != 0:
        raise RuntimeError("BGM generation failed")

    return output


def step_mix(episode_dir: str, narration_path: str, bgm_path: str, force: bool = False):
    """[4] 오디오 믹싱 (ffmpeg)"""
    output = os.path.join(episode_dir, "mixed.wav")
    if os.path.exists(output) and not force:
        print(f"  [skip] mixed.wav already exists")
        return output

    print(f"  Mixing audio...")
    cmd = [
        PYTHON, os.path.join(SCRIPTS_DIR, "audio_mixer.py"),
        narration_path, bgm_path, output,
    ]
    result = subprocess.run(cmd, cwd=PROJECT_DIR, timeout=120)
    if result.returncode != 0:
        raise RuntimeError("Audio mixing failed")

    return output


def step_analyze(episode_dir: str, audio_path: str, force: bool = False):
    """[5] 오디오 FFT 분석 (numpy)"""
    output = os.path.join(episode_dir, "audio_analysis.json")
    if os.path.exists(output) and not force:
        print(f"  [skip] audio_analysis.json already exists")
        return output

    print(f"  Analyzing audio...")
    cmd = [
        PYTHON, os.path.join(SCRIPTS_DIR, "audio_analyzer.py"),
        audio_path, output, "30",
    ]
    result = subprocess.run(cmd, cwd=PROJECT_DIR, timeout=120)
    if result.returncode != 0:
        raise RuntimeError("Audio analysis failed")

    return output


def step_render(episode_dir: str, title: str, force: bool = False):
    """[8] Remotion 렌더링"""
    output = os.path.join(episode_dir, "output.mp4")
    if os.path.exists(output) and not force:
        print(f"  [skip] output.mp4 already exists")
        return output

    print(f"  Rendering video with Remotion...")
    cmd = [
        "npx", "remotion", "render",
        "src/index.tsx", "EnometaShorts",
        output,
        "--concurrency=2",
    ]
    result = subprocess.run(cmd, cwd=PROJECT_DIR, timeout=600)
    if result.returncode != 0:
        raise RuntimeError("Remotion rendering failed")

    return output


def run_pipeline(
    title: str,
    script_text: str,
    episode_dir: str,
    bgm_preset: str = "contemplative",
    step: str | None = None,
    force: bool = False,
):
    """전체 파이프라인 실행"""

    ensure_dirs()
    os.makedirs(episode_dir, exist_ok=True)

    status = load_status(episode_dir)
    steps_completed = []

    print(f"\n{'='*60}")
    print(f"  ENOMETA Shorts Pipeline")
    print(f"  Title: {title}")
    print(f"  Episode: {episode_dir}")
    print(f"{'='*60}\n")

    try:
        # [2] TTS
        if step is None or step == "tts":
            print("[2/8] TTS 나레이션 생성")
            narration = step_tts(episode_dir, script_text, force)
            status["tts"] = "done"
            save_status(episode_dir, status)
            steps_completed.append("tts")
            if step == "tts":
                return

        narration = os.path.join(episode_dir, "narration.wav")

        # [3] BGM
        if step is None or step == "bgm":
            print("[3/8] BGM 생성")
            bgm = step_bgm(episode_dir, bgm_preset, force)
            status["bgm"] = "done"
            save_status(episode_dir, status)
            steps_completed.append("bgm")
            if step == "bgm":
                return

        bgm = os.path.join(episode_dir, "bgm.wav")

        # [4] 믹싱
        if step is None or step == "mix":
            print("[4/8] 오디오 믹싱")
            mixed = step_mix(episode_dir, narration, bgm, force)
            status["mix"] = "done"
            save_status(episode_dir, status)
            steps_completed.append("mix")
            if step == "mix":
                return

        mixed = os.path.join(episode_dir, "mixed.wav")

        # [5] 분석
        if step is None or step == "analyze":
            print("[5/8] 오디오 분석")
            analysis = step_analyze(episode_dir, mixed, force)
            status["analyze"] = "done"
            save_status(episode_dir, status)
            steps_completed.append("analyze")
            if step == "analyze":
                return

        # [8] 렌더링
        if step is None or step == "render":
            print("[8/8] Remotion 렌더링")
            output = step_render(episode_dir, title, force)
            status["render"] = "done"
            save_status(episode_dir, status)
            steps_completed.append("render")

        print(f"\n{'='*60}")
        print(f"  Pipeline complete!")
        print(f"  Steps: {', '.join(steps_completed)}")
        print(f"  Output: {os.path.join(episode_dir, 'output.mp4')}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        status["error"] = str(e)
        save_status(episode_dir, status)
        raise


def main():
    parser = argparse.ArgumentParser(description="ENOMETA Shorts Pipeline")
    parser.add_argument("--title", required=True, help="쇼츠 제목")
    parser.add_argument("--script", required=True, help="대본 텍스트 파일 경로")
    parser.add_argument("--episode-dir", default=None, help="에피소드 디렉토리 (기본: episodes/ep_<timestamp>)")
    parser.add_argument("--bgm-preset", default="contemplative",
                        choices=["contemplative", "noir_mystery", "hopeful_dawn", "tension"],
                        help="BGM 프리셋")
    parser.add_argument("--step", default=None,
                        choices=["tts", "bgm", "mix", "analyze", "render"],
                        help="특정 단계만 실행")
    parser.add_argument("--force", action="store_true", help="기존 파일 덮어쓰기")

    args = parser.parse_args()

    # 대본 읽기
    with open(args.script, "r", encoding="utf-8") as f:
        script_text = f.read().strip()

    # 에피소드 디렉토리
    if args.episode_dir:
        episode_dir = args.episode_dir
    else:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        episode_dir = os.path.join(PROJECT_DIR, "episodes", f"ep_{timestamp}")

    run_pipeline(
        title=args.title,
        script_text=script_text,
        episode_dir=episode_dir,
        bgm_preset=args.bgm_preset,
        step=args.step,
        force=args.force,
    )


if __name__ == "__main__":
    main()

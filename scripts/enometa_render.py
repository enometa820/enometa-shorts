"""
ENOMETA 마스터 파이프라인 v2
narration_timing.json → 완성된 쇼츠 MP4

전제조건:
  - episodes/<id>/narration_timing.json 존재 (대본 세그먼트 포함)

파이프라인:
  [2] TTS          generate_voice_edge.py    → narration.wav
  [3] script_data  script_data_extractor.py  → script_data.json
  [4] visual_script visual_script_generator.py → visual_script.json
  [5] BGM          enometa_music_engine.py   → bgm.wav + bgm_raw_visual_data.npz
  [6] mix          audio_mixer.py            → mixed.wav
  [7] python_frames visual_renderer.py       → frames/
  [8] render        Remotion                 → output.mp4

사용법:
  py scripts/enometa_render.py episodes/ep006 --title "제목" --palette phantom
  py scripts/enometa_render.py episodes/ep006 --title "제목" --step bgm
  py scripts/enometa_render.py episodes/ep006 --title "제목" --force

GPU(TTS/BGM)는 6GB VRAM 한계로 순차 실행.
"""

import sys
import os
import json
import argparse
import subprocess

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_DIR, "scripts")

PYTHON = "py"

STEPS = ["tts", "script_data", "visual_script", "bgm", "mix", "python_frames", "render"]


def run(cmd: list, label: str, cwd: str | None = None, timeout: int = 900):
    """subprocess 실행 + 실패 시 예외"""
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or PROJECT_DIR, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"{label} 실패 (exit {result.returncode})")


def load_status(episode_dir: str) -> dict:
    path = os.path.join(episode_dir, "status.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_status(episode_dir: str, status: dict):
    path = os.path.join(episode_dir, "status.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


# ── 단계별 함수 ────────────────────────────────────────────────


def step_tts(episode_dir: str, force: bool = False):
    """[2] Edge-TTS 나레이션 생성"""
    timing = os.path.join(episode_dir, "narration_timing.json")
    output = os.path.join(episode_dir, "narration.wav")

    if not os.path.exists(timing):
        raise FileNotFoundError(f"narration_timing.json 없음: {timing}")
    if os.path.exists(output) and not force:
        print("  [skip] narration.wav 이미 존재")
        return output

    print("  Edge-TTS 생성 중...")
    run([PYTHON, os.path.join(SCRIPTS_DIR, "generate_voice_edge.py"),
         timing, output], "TTS")
    return output


def step_script_data(episode_dir: str, force: bool = False):
    """[3] script_data.json 생성"""
    timing = os.path.join(episode_dir, "narration_timing.json")
    output = os.path.join(episode_dir, "script_data.json")

    if not os.path.exists(timing):
        raise FileNotFoundError(f"narration_timing.json 없음: {timing}")
    if os.path.exists(output) and not force:
        print("  [skip] script_data.json 이미 존재")
        return output

    print("  Script data 추출 중...")
    run([PYTHON, os.path.join(SCRIPTS_DIR, "script_data_extractor.py"),
         timing, output], "script_data")
    return output


def step_visual_script(episode_dir: str, title: str, episode_id: str,
                       palette: str = "phantom", force: bool = False):
    """[4] visual_script.json 생성"""
    timing = os.path.join(episode_dir, "narration_timing.json")
    output = os.path.join(episode_dir, "visual_script.json")

    if not os.path.exists(timing):
        raise FileNotFoundError(f"narration_timing.json 없음: {timing}")
    if os.path.exists(output) and not force:
        print("  [skip] visual_script.json 이미 존재")
        return output

    print(f"  Visual script 생성 중 (palette: {palette})...")
    cmd = [PYTHON, os.path.join(SCRIPTS_DIR, "visual_script_generator.py"),
           timing, output,
           "--palette", palette,
           "--episode", episode_id,
           "--title", title]
    run(cmd, "visual_script")
    return output


def step_bgm(episode_dir: str, episode_id: str, force: bool = False):
    """[5] BGM 생성 (enometa, from visual_script)"""
    visual = os.path.join(episode_dir, "visual_script.json")
    script_data = os.path.join(episode_dir, "script_data.json")
    output = os.path.join(episode_dir, "bgm.wav")

    if not os.path.exists(visual):
        raise FileNotFoundError(f"visual_script.json 없음: {visual}")
    if os.path.exists(output) and not force:
        print("  [skip] bgm.wav 이미 존재")
        return output

    print("  BGM 생성 중 (enometa, from-visual)...")
    cmd = [PYTHON, os.path.join(SCRIPTS_DIR, "enometa_music_engine.py"),
           visual, output,
           "--from-visual",
           "--export-raw",
           "--episode", episode_id]
    if os.path.exists(script_data):
        cmd += ["--script-data", script_data]
    run(cmd, "BGM")
    return output


def step_mix(episode_dir: str, force: bool = False):
    """[6] 오디오 믹싱 (narration 90% + BGM 100%, loudnorm -14 LUFS)"""
    narration = os.path.join(episode_dir, "narration.wav")
    bgm = os.path.join(episode_dir, "bgm.wav")
    output = os.path.join(episode_dir, "mixed.wav")

    for f, name in [(narration, "narration.wav"), (bgm, "bgm.wav")]:
        if not os.path.exists(f):
            raise FileNotFoundError(f"{name} 없음: {f}")
    if os.path.exists(output) and not force:
        print("  [skip] mixed.wav 이미 존재")
        return output

    print("  오디오 믹싱 중 (narration 0.90 / bgm 1.0, loudnorm -14 LUFS)...")
    cmd = [PYTHON, os.path.join(SCRIPTS_DIR, "audio_mixer.py"),
           narration, bgm, output,
           "--bgm-volume", "1.0"]
    run(cmd, "mix")
    return output


def step_python_frames(episode_dir: str, force: bool = False):
    """[7] Python 비주얼 프레임 렌더링"""
    frames_dir = os.path.join(episode_dir, "frames")

    if os.path.exists(frames_dir) and os.listdir(frames_dir) and not force:
        print("  [skip] frames/ 이미 존재")
        return frames_dir

    print("  Python 비주얼 프레임 렌더링 중 (enometa)...")
    cmd = [PYTHON, os.path.join(SCRIPTS_DIR, "visual_renderer.py"),
           episode_dir, "--genre", "enometa"]
    run(cmd, "python_frames", timeout=3600)  # 최대 1시간 (120초 영상 기준 ~20분)
    return frames_dir


def step_render(episode_dir: str, force: bool = False):
    """[8] Remotion 렌더링"""
    output = os.path.join(episode_dir, "output.mp4")

    if os.path.exists(output) and not force:
        print("  [skip] output.mp4 이미 존재")
        return output

    print("  Remotion 렌더링 중...")
    cmd = ["npx", "remotion", "render",
           "src/index.tsx", "EnometaShorts",
           output,
           "--concurrency=2"]
    run(cmd, "Remotion render")
    return output


# ── 전체 파이프라인 ───────────────────────────────────────────


def run_pipeline(
    episode_dir: str,
    title: str,
    episode_id: str,
    palette: str = "phantom",
    step: str | None = None,
    force: bool = False,
):
    os.makedirs(episode_dir, exist_ok=True)
    status = load_status(episode_dir)
    completed = []

    print(f"\n{'='*60}")
    print(f"  ENOMETA Shorts Pipeline v2")
    print(f"  Episode: {episode_id}")
    print(f"  Title:   {title}")
    print(f"  Dir:     {episode_dir}")
    print(f"{'='*60}\n")

    def do(name: str, fn):
        if step is not None and step != name:
            return
        label_map = {
            "tts": "[2/8] TTS 나레이션",
            "script_data": "[3/8] Script data",
            "visual_script": "[4/8] Visual script",
            "bgm": "[5/8] BGM",
            "mix": "[6/8] 오디오 믹싱",
            "python_frames": "[7/8] Python 프레임",
            "render": "[8/8] Remotion 렌더링",
        }
        print(label_map.get(name, name))
        fn()
        status[name] = "done"
        save_status(episode_dir, status)
        completed.append(name)

    try:
        do("tts",          lambda: step_tts(episode_dir, force))
        do("script_data",  lambda: step_script_data(episode_dir, force))
        do("visual_script",lambda: step_visual_script(episode_dir, title, episode_id, palette, force))
        do("bgm",          lambda: step_bgm(episode_dir, episode_id, force))
        do("mix",          lambda: step_mix(episode_dir, force))
        do("python_frames",lambda: step_python_frames(episode_dir, force))
        do("render",       lambda: step_render(episode_dir, force))

    except Exception as e:
        print(f"\n[ERROR] {e}")
        status["error"] = str(e)
        save_status(episode_dir, status)
        raise

    if completed:
        print(f"\n{'='*60}")
        print(f"  완료: {', '.join(completed)}")
        if "render" in completed:
            print(f"  출력: {os.path.join(episode_dir, 'output.mp4')}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="ENOMETA Shorts Pipeline v2",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("episode_dir",
                        help="에피소드 디렉토리 (narration_timing.json 있어야 함)\n예: episodes/ep006")
    parser.add_argument("--title", required=True, help="쇼츠 제목")
    parser.add_argument("--episode", default=None,
                        help="에피소드 ID (기본: 디렉토리 이름)")
    parser.add_argument("--palette", default="phantom",
                        choices=["phantom", "neon_noir", "cold_steel", "ember", "synapse", "gameboy", "c64"],
                        help="비주얼 팔레트 (기본: phantom)")
    parser.add_argument("--step", default=None, choices=STEPS,
                        help="특정 단계만 실행")
    parser.add_argument("--force", action="store_true", help="기존 파일 덮어쓰기")

    args = parser.parse_args()

    episode_dir = os.path.abspath(args.episode_dir)
    episode_id = args.episode or os.path.basename(episode_dir)

    run_pipeline(
        episode_dir=episode_dir,
        title=args.title,
        episode_id=episode_id,
        palette=args.palette,
        step=args.step,
        force=args.force,
    )


if __name__ == "__main__":
    main()

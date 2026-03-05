"""
ENOMETA 마스터 파이프라인 v2
narration_timing.json → 완성된 쇼츠 MP4

전제조건:
  - episodes/<id>/narration_timing.json 존재 (대본 세그먼트 포함)
  - 또는 episodes/<id>/script.txt 존재 → gen_timing.py가 자동 생성

파이프라인:
  [1] gen_timing     gen_timing.py             → narration_timing.json (script.txt 있고 json 없을 때만)
  [2] TTS            generate_voice_edge.py    → narration.wav
  [3] script_data    script_data_extractor.py  → script_data.json
  [4] visual_script  visual_script_generator.py → visual_script.json
  [5] BGM            enometa_music_engine.py   → bgm.wav + bgm_raw_visual_data.npz
  [6] mix            audio_mixer.py            → mixed.wav
  [7] audio_analysis audio_analyzer.py         → audio_analysis.json
  [8] python_frames  visual_renderer.py        → frames/
  [9] render         Remotion                  → output.mp4

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

STEPS = ["gen_timing", "tts", "script_data", "visual_script", "bgm", "mix", "audio_analysis", "python_frames", "render"]


def run(cmd: list, label: str, cwd: str | None = None, timeout: int = 900, shell: bool = False):
    """subprocess 실행 + 실패 시 예외"""
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or PROJECT_DIR, timeout=timeout, shell=shell)
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


def step_gen_timing(episode_dir: str, bpm: float = 135, music_mood: str = "raw",
                    visual_mood: str | None = None, drum: bool | None = None):
    """[1] 마디 기반 타이밍 생성 (script.txt → narration_timing.json)
    조건: script.txt 있고 narration_timing.json 없을 때만 실행
    """
    script_txt = os.path.join(episode_dir, "script.txt")
    timing_json = os.path.join(episode_dir, "narration_timing.json")

    if not os.path.exists(script_txt):
        print("  [skip] script.txt 없음 — narration_timing.json 직접 사용")
        return
    if os.path.exists(timing_json):
        print("  [skip] narration_timing.json 이미 존재")
        return

    print(f"  script.txt → narration_timing.json (BPM={bpm}, mood={music_mood})")
    cmd = [PYTHON, os.path.join(SCRIPTS_DIR, "gen_timing.py"),
           script_txt, "--bpm", str(bpm), "--music-mood", music_mood]
    if visual_mood:
        cmd += ["--visual-mood", visual_mood]
    if drum is True:
        cmd += ["--drum"]
    elif drum is False:
        cmd += ["--no-drum"]
    run(cmd, "gen_timing")


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
                       palette: str = "phantom", force: bool = False,
                       visual_mood: str = ""):
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
    if visual_mood:
        cmd += ["--visual-mood", visual_mood]
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


def step_audio_analysis(episode_dir: str, force: bool = False):
    """[6.5] 오디오 분석 (mixed.wav → audio_analysis.json)"""
    mixed = os.path.join(episode_dir, "mixed.wav")
    output = os.path.join(episode_dir, "audio_analysis.json")

    if not os.path.exists(mixed):
        raise FileNotFoundError(f"mixed.wav 없음: {mixed}")
    if os.path.exists(output) and not force:
        print("  [skip] audio_analysis.json 이미 존재")
        return output

    print("  오디오 분석 중 (FFT → audio_analysis.json)...")
    run([PYTHON, os.path.join(SCRIPTS_DIR, "audio_analyzer.py"),
         mixed, output], "audio_analysis")
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


def step_copy_public(episode_dir: str, episode_id: str):
    """[7.5] public 디렉토리에 frames + mixed.wav 복사 (Remotion용)"""
    import shutil
    public_dir = os.path.join(PROJECT_DIR, "public", episode_id)
    os.makedirs(public_dir, exist_ok=True)

    # mixed.wav 복사
    mixed_src = os.path.join(episode_dir, "mixed.wav")
    mixed_dst = os.path.join(public_dir, "mixed.wav")
    if os.path.exists(mixed_src) and not os.path.exists(mixed_dst):
        shutil.copy2(mixed_src, mixed_dst)
        print(f"  copied mixed.wav → public/{episode_id}/")

    # frames 복사
    frames_src = os.path.join(episode_dir, "frames")
    frames_dst = os.path.join(public_dir, "frames")
    if os.path.isdir(frames_src) and not os.path.isdir(frames_dst):
        shutil.copytree(frames_src, frames_dst)
        n = len(os.listdir(frames_dst))
        print(f"  copied frames ({n} files) → public/{episode_id}/frames/")


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
    run(cmd, "Remotion render", shell=True)
    return output


# ── 전체 파이프라인 ───────────────────────────────────────────


def run_pipeline(
    episode_dir: str,
    title: str,
    episode_id: str,
    palette: str = "phantom",
    step: str | None = None,
    force: bool = False,
    bpm: float = 135,
    music_mood: str = "raw",
    visual_mood: str | None = None,
    drum: bool | None = None,
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
            "gen_timing":    "[1/9] 마디 타이밍 생성",
            "tts":           "[2/9] TTS 나레이션",
            "script_data":   "[3/9] Script data",
            "visual_script": "[4/9] Visual script",
            "bgm":           "[5/9] BGM",
            "mix":           "[6/9] 오디오 믹싱",
            "audio_analysis":"[7/9] 오디오 분석",
            "python_frames": "[8/9] Python 프레임",
            "render":        "[9/9] Remotion 렌더링",
        }
        print(label_map.get(name, name))
        fn()
        status[name] = "done"
        save_status(episode_dir, status)
        completed.append(name)

    try:
        do("gen_timing",   lambda: step_gen_timing(episode_dir, bpm, music_mood, visual_mood, drum))
        do("tts",          lambda: step_tts(episode_dir, force))
        do("script_data",  lambda: step_script_data(episode_dir, force))
        do("visual_script",lambda: step_visual_script(episode_dir, title, episode_id, palette, force, visual_mood or ""))
        do("bgm",          lambda: step_bgm(episode_dir, episode_id, force))
        do("mix",            lambda: step_mix(episode_dir, force))
        do("audio_analysis", lambda: step_audio_analysis(episode_dir, force))
        do("python_frames",  lambda: step_python_frames(episode_dir, force))
        step_copy_public(episode_dir, episode_id)
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
    parser.add_argument("--bpm", type=float, default=135,
                        help="gen_timing BPM (기본: 135)")
    parser.add_argument("--music-mood", default="raw",
                        choices=["ambient", "ikeda", "experimental", "minimal", "chill", "glitch", "raw", "intense"],
                        help="음악 무드 (기본: raw)")
    parser.add_argument("--visual-mood", default=None,
                        choices=["ikeda", "cooper", "abstract", "data"],
                        help="비주얼 무드 (선택)")
    parser.add_argument("--drum", action="store_true", default=None,
                        help="드럼 강제 ON")
    parser.add_argument("--no-drum", action="store_true",
                        help="드럼 강제 OFF")

    args = parser.parse_args()

    episode_dir = os.path.abspath(args.episode_dir)
    episode_id = args.episode or os.path.basename(episode_dir)

    drum = False if args.no_drum else (True if args.drum else None)

    run_pipeline(
        episode_dir=episode_dir,
        title=args.title,
        episode_id=episode_id,
        palette=args.palette,
        step=args.step,
        force=args.force,
        bpm=args.bpm,
        music_mood=args.music_mood,
        visual_mood=args.visual_mood,
        drum=drum,
    )


if __name__ == "__main__":
    main()

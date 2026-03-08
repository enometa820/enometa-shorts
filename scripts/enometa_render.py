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


def step_gen_timing(episode_dir: str, bpm: float = 135, music_mood: str = "acid",
                    visual_mood: str | None = None, drum_mode: str = "default",
                    gap: float = 0.3, paragraph_gap: float = 0.8):
    """[1] TTS 실측 기반 타이밍 생성 (script.txt -> narration_timing.json)
    조건: script.txt 있고 narration_timing.json 없을 때만 실행
    """
    script_txt = os.path.join(episode_dir, "script.txt")
    timing_json = os.path.join(episode_dir, "narration_timing.json")

    if not os.path.exists(script_txt):
        print("  [skip] script.txt 없음 - narration_timing.json 직접 사용")
        return
    if os.path.exists(timing_json):
        print("  [skip] narration_timing.json 이미 존재")
        return

    print(f"  script.txt -> narration_timing.json (BPM={bpm}, mood={music_mood}, gap={gap}s)")
    cmd = [PYTHON, os.path.join(SCRIPTS_DIR, "gen_timing.py"),
           script_txt, "--bpm", str(bpm), "--music-mood", music_mood,
           "--gap", str(gap), "--paragraph-gap", str(paragraph_gap)]
    if visual_mood:
        cmd += ["--visual-mood", visual_mood]
    if drum_mode != "default":
        cmd += ["--drum-mode", drum_mode]
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
           "--script-data", script_data,
           "--visual-script", visual,
           "--export-raw",
           output]
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


def step_python_frames(episode_dir: str, force: bool = False, visual_mood: str = ""):
    """[7] Python 비주얼 프레임 렌더링"""
    frames_dir = os.path.join(episode_dir, "frames")

    if os.path.exists(frames_dir) and os.listdir(frames_dir) and not force:
        print("  [skip] frames/ 이미 존재")
        return frames_dir

    # visual_mood 인자가 없으면 visual_script.json에서 자동 읽기
    if visual_mood in ("cooper", "abstract", "data", "enometa"):
        genre = visual_mood
    else:
        visual_script_path = os.path.join(episode_dir, "visual_script.json")
        try:
            import json as _json
            with open(visual_script_path, encoding="utf-8") as _f:
                _vs = _json.load(_f)
            genre = _vs.get("meta", {}).get("genre", "enometa")
            if genre not in ("cooper", "abstract", "data", "enometa"):
                genre = "enometa"
        except Exception:
            genre = "enometa"
    print(f"  Python 비주얼 프레임 렌더링 중 (genre={genre})...")
    cmd = [PYTHON, os.path.join(SCRIPTS_DIR, "visual_renderer.py"),
           episode_dir, "--genre", genre]
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
    ep_num = os.path.basename(episode_dir).upper()  # ep010 → EP010
    cmd = ["npx", "remotion", "render",
           "src/index.tsx", ep_num,
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
    music_mood: str = "acid",
    visual_mood: str | None = None,
    drum_mode: str = "default",
    gap: float = 0.3,
    paragraph_gap: float = 0.8,
    stop_after: str | None = None,
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

    _stop_requested = [False]

    def do(name: str, fn):
        if _stop_requested[0]:
            return
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
        if stop_after and name == stop_after:
            _stop_requested[0] = True
            STEP_ORDER = ["gen_timing", "tts", "script_data", "visual_script",
                          "bgm", "mix", "audio_analysis", "python_frames", "render"]
            idx = STEP_ORDER.index(stop_after)
            next_step = STEP_ORDER[idx + 1] if idx + 1 < len(STEP_ORDER) else None
            print(f"\n{'='*60}")
            print(f"  [PAUSE] --stop-after {stop_after}: 파이프라인 중단됨")
            if next_step:
                print(f"  확인 후 다음 단계 실행:")
                print(f"  py scripts/enometa_render.py {episode_dir} --title \"{title}\" --step {next_step}")
            print(f"{'='*60}\n")

    try:
        do("gen_timing",   lambda: step_gen_timing(episode_dir, bpm, music_mood, visual_mood, drum_mode, gap, paragraph_gap))
        do("tts",          lambda: step_tts(episode_dir, force))
        do("script_data",  lambda: step_script_data(episode_dir, force))
        do("visual_script",lambda: step_visual_script(episode_dir, title, episode_id, palette, force, visual_mood or ""))
        do("bgm",          lambda: step_bgm(episode_dir, episode_id, force))
        do("mix",            lambda: step_mix(episode_dir, force))
        do("audio_analysis", lambda: step_audio_analysis(episode_dir, force))
        do("python_frames",  lambda: step_python_frames(episode_dir, force, visual_mood or ""))
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


PALETTE_CHOICES = ["phantom", "neon_noir", "cold_steel", "ember", "synapse", "gameboy", "c64", "enometa"]
PALETTE_DESC = {
    "phantom":    "어두운 보라/청색 (기본)",
    "neon_noir":  "핑크/붉은 네온",
    "cold_steel": "차가운 청록",
    "ember":      "붉은/주황",
    "synapse":    "파란/신경망",
    "gameboy":    "8비트 초록",
    "c64":        "레트로 보라",
    "enometa":    "흑백 모노크롬",
}

MUSIC_MOOD_CHOICES = ["acid", "ambient", "microsound", "IDM", "minimal", "dub", "glitch", "industrial", "techno"]
MUSIC_MOOD_DESC = {
    "acid":         "TB-303 애시드 (기본)",
    "ambient":      "잔잔한 배경",
    "microsound":   "Ikeda/Alva Noto 마이크로사운드",
    "IDM":          "Aphex/Autechre 복잡 비트",
    "minimal":      "미니멀",
    "dub":          "Basic Channel 딥 코드+딜레이",
    "glitch":       "글리치/노이즈",
    "industrial":   "Perc/Ansome 디스토션 킥",
    "techno":       "4-on-the-floor 킥 + FM베이스",
}

VISUAL_MOOD_CHOICES = [None, "ikeda", "cooper", "abstract", "data"]
VISUAL_MOOD_DESC = {
    None:       "무드 자동 (기본)",
    "ikeda":    "디지털 라인",
    "cooper":   "기하학적",
    "abstract": "추상",
    "data":     "데이터 시각화",
}


def _pick(prompt, choices, descriptions, default_idx=0):
    """번호 선택 헬퍼. 빈 입력 = 기본값(default_idx)."""
    for i, c in enumerate(choices, 1):
        marker = "  ← 기본" if i - 1 == default_idx else ""
        label = descriptions.get(c, c) if isinstance(descriptions, dict) else descriptions[i - 1]
        name = c if c is not None else "(자동)"
        print(f"  {i}. {str(name):<14} {label}{marker}")
    while True:
        raw = input("→ ").strip()
        if raw == "":
            return choices[default_idx]
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        print(f"  1~{len(choices)} 사이 번호를 입력하세요.")


def run_interactive(args):
    """--interactive 모드: 터미널에서 번호 선택으로 옵션 설정"""
    print("\n" + "=" * 48)
    print("  ENOMETA 에피소드 제작 설정")
    print("=" * 48)

    # 1. 팔레트
    print("\n[1] 팔레트:")
    args.palette = _pick("", PALETTE_CHOICES, PALETTE_DESC)

    # 2. 음악 무드
    print("\n[2] 음악 무드:")
    args.music_mood = _pick("", MUSIC_MOOD_CHOICES, MUSIC_MOOD_DESC)

    # 3. 비주얼 무드
    print("\n[3] 비주얼 무드:")
    args.visual_mood = _pick("", VISUAL_MOOD_CHOICES, VISUAL_MOOD_DESC)

    # 4. 드럼 모드
    print("\n[4] 드럼 모드:")
    drum_choices = ["default", "on", "off", "simple", "dynamic"]
    drum_desc = [
        "무드 기본값",
        "풀 드럼 강제 ON",
        "드럼 강제 OFF",
        "킥+하이햇만, 필인 최소 (영상 전체 2회)",
        "풀 드럼+SI 최대+필인 2배",
    ]
    drum_sel = _pick("", drum_choices, drum_desc)
    args.drum_mode = drum_sel

    # 5. 제목
    print("\n[5] 제목:")
    while True:
        title = input("→ ").strip()
        if title:
            break
        print("  제목을 입력해주세요.")
    args.title = title

    # 제목 키워드 추출 (kiwipiepy)
    try:
        from kiwipiepy import Kiwi
        kiwi = Kiwi()
        tokens = kiwi.tokenize(title)
        candidates = [t.form for t in tokens if t.tag in ("NNG", "NNP", "VV", "VA")][:3]
        if candidates:
            print(f"\n  키워드 후보: {candidates}")
            print("  확인 (엔터) 또는 직접 입력 (쉼표 구분):")
            kw_raw = input("→ ").strip()
            if kw_raw:
                candidates = [k.strip() for k in kw_raw.split(",") if k.strip()]
    except Exception:
        candidates = []

    # 최종 명령어 출력
    cmd_parts = [f'py scripts/enometa_render.py "{args.episode_dir}"',
                 f'--title "{args.title}"']
    if args.palette != "phantom":
        cmd_parts.append(f"--palette {args.palette}")
    if args.music_mood != "acid":
        cmd_parts.append(f"--music-mood {args.music_mood}")
    if args.visual_mood:
        cmd_parts.append(f"--visual-mood {args.visual_mood}")
    if args.drum is True:
        cmd_parts.append("--drum")
    elif getattr(args, "no_drum", False):
        cmd_parts.append("--no-drum")

    print("\n" + "-" * 48)
    print("실행 명령:")
    print("  " + " \\\n  ".join(cmd_parts))
    if candidates:
        print(f"  (하이라이트 키워드: {candidates})")
    print("-" * 48)

    confirm = input("\n실행할까요? (y/n) → ").strip().lower()
    if confirm != "y":
        print("취소됨.")
        sys.exit(0)

    return args


def main():
    parser = argparse.ArgumentParser(
        description="ENOMETA Shorts Pipeline v2",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("episode_dir",
                        help="에피소드 디렉토리 (narration_timing.json 있어야 함)\n예: episodes/ep006")
    parser.add_argument("--title", default=None, help="쇼츠 제목 (--interactive 시 생략 가능)")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="인터랙티브 옵션 선택 모드 (번호로 선택)")
    parser.add_argument("--episode", default=None,
                        help="에피소드 ID (기본: 디렉토리 이름)")
    parser.add_argument("--palette", default="phantom",
                        choices=PALETTE_CHOICES,
                        help="비주얼 팔레트 (기본: phantom)")
    parser.add_argument("--step", default=None, choices=STEPS,
                        help="특정 단계만 실행")
    parser.add_argument("--force", action="store_true", help="기존 파일 덮어쓰기")
    parser.add_argument("--bpm", type=float, default=135,
                        help="gen_timing BPM (기본: 135)")
    parser.add_argument("--music-mood", default="acid",
                        choices=["ambient", "microsound", "IDM", "minimal", "dub", "glitch", "acid", "industrial", "techno"],
                        help="음악 장르 (기본: acid)")
    parser.add_argument("--visual-mood", default=None,
                        choices=["ikeda", "cooper", "abstract", "data"],
                        help="비주얼 무드 (선택)")
    parser.add_argument("--drum-mode", default="default",
                        choices=["default", "on", "off", "simple", "dynamic"],
                        help="드럼 모드 (기본: default=무드 기본값)")
    # deprecated alias (하위호환)
    parser.add_argument("--drum", action="store_true", default=False,
                        help="[deprecated] --drum-mode on 과 동일")
    parser.add_argument("--no-drum", action="store_true",
                        help="[deprecated] --drum-mode off 와 동일")
    parser.add_argument("--stop-after", default=None,
                        choices=["gen_timing", "tts", "script_data", "visual_script",
                                 "bgm", "mix", "audio_analysis", "python_frames"],
                        help="지정 단계 완료 후 파이프라인 중단 (사용자 확인용)")
    parser.add_argument("--gap", type=float, default=0.3,
                        help="문장 간 갭 (초, 기본: 0.3)")
    parser.add_argument("--paragraph-gap", type=float, default=0.8,
                        help="문단 간 갭 (초, 기본: 0.8)")

    args = parser.parse_args()

    if args.interactive:
        args = run_interactive(args)
    elif not args.title:
        parser.error("--title 은 필수입니다 (또는 --interactive/-i 사용)")

    episode_dir = os.path.abspath(args.episode_dir)
    episode_id = args.episode or os.path.basename(episode_dir)

    # drum_mode 결정: --drum-mode 우선, deprecated --drum/--no-drum 하위호환
    if args.no_drum:
        drum_mode = "off"
    elif args.drum:
        drum_mode = "on"
    else:
        drum_mode = args.drum_mode

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
        drum_mode=drum_mode,
        gap=args.gap,
        paragraph_gap=args.paragraph_gap,
        stop_after=args.stop_after,
    )


if __name__ == "__main__":
    main()

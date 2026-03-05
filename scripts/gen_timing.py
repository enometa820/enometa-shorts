"""
ENOMETA 마디 기반 타이밍 생성기
- script.txt (1줄=1문장, 빈줄=드롭) → narration_timing.json
- TTS 실측 → ceil(actual_dur / SEC_PER_BAR) 마디로 snap
- 드롭(빈줄) = 1마디 공백, drops[] 필드에 기록

사용법:
  py scripts/gen_timing.py episodes/ep009/script.txt
  py scripts/gen_timing.py episodes/ep009/script.txt --bpm 120
  py scripts/gen_timing.py episodes/ep009/script.txt --music-mood ikeda --visual-mood ikeda
  py scripts/gen_timing.py episodes/ep009/script.txt --no-drum
"""

import asyncio
import sys
import os
import json
import math
import wave
import subprocess
import shutil
import tempfile
import argparse

import edge_tts

DEFAULT_VOICE = "ko-KR-SunHiNeural"
DEFAULT_RATE = "+5%"
DEFAULT_BPM = 135
BEATS_PER_BAR = 4


def sec_per_bar(bpm: float) -> float:
    return 60.0 / bpm * BEATS_PER_BAR


async def tts_to_wav(text: str, voice: str, rate: str, wav_path: str):
    """텍스트 → mp3 → wav, 실측 duration 반환"""
    tmp_mp3 = wav_path.replace(".wav", ".mp3")
    tts = edge_tts.Communicate(text, voice=voice, rate=rate)
    await tts.save(tmp_mp3)

    result = subprocess.run(
        ["ffmpeg", "-y", "-i", tmp_mp3, wav_path],
        capture_output=True
    )
    os.unlink(tmp_mp3)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 변환 실패: {result.stderr.decode()}")

    with wave.open(wav_path, "rb") as wf:
        return wf.getnframes() / wf.getframerate()


async def generate(
    script_path: str,
    bpm: float = DEFAULT_BPM,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    music_mood: str = "raw",
    visual_mood: str | None = None,
    drum: bool | None = None,
):
    spb = sec_per_bar(bpm)

    with open(script_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    tmp_dir = tempfile.mkdtemp()
    segments = []
    drops = []
    current_sec = 0.0
    seg_index = 0

    print(f"BPM={bpm}, SEC_PER_BAR={spb:.4f}s")
    print(f"Lines: {len(lines)}")

    try:
        for line in lines:
            text = line.strip()

            if not text:
                # 드롭: 1마디 공백
                drop_start = current_sec
                drop_end = current_sec + spb
                drops.append({"start_sec": round(drop_start, 4), "end_sec": round(drop_end, 4)})
                print(f"  [drop] {drop_start:.3f}s ~ {drop_end:.3f}s")
                current_sec = drop_end
                continue

            # TTS 실측
            wav_path = os.path.join(tmp_dir, f"seg_{seg_index:03d}.wav")
            actual_dur = await tts_to_wav(text, voice, rate, wav_path)

            # 마디 snap: ceil(actual / SEC_PER_BAR) × SEC_PER_BAR
            bars = max(1, math.ceil(actual_dur / spb))
            snapped_dur = bars * spb

            start_sec = current_sec
            end_sec = current_sec + snapped_dur
            current_sec = end_sec

            segments.append({
                "index": seg_index,
                "text": text,
                "start_sec": round(start_sec, 4),
                "end_sec": round(end_sec, 4),
                "duration_sec": round(snapped_dur, 4),
                "actual_tts_sec": round(actual_dur, 4),
                "bars": bars,
            })

            print(f"  [{seg_index}] {text[:30]}... | actual={actual_dur:.3f}s → {bars}bar={snapped_dur:.3f}s | @{start_sec:.3f}s")
            seg_index += 1

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    total_duration_sec = round(current_sec, 4)

    output = {
        "voice": voice,
        "rate": rate,
        "bpm": bpm,
        "sec_per_bar": round(spb, 6),
        "total_duration_sec": total_duration_sec,
        "music_mood": music_mood,
        "segments": segments,
        "drops": drops,
    }

    if visual_mood is not None:
        output["visual_mood"] = visual_mood

    # drum 필드: None이면 생략(무드 기본값 따름), 명시적이면 기록
    if drum is not None:
        output["drum"] = drum

    return output


def main():
    parser = argparse.ArgumentParser(description="ENOMETA 마디 기반 타이밍 생성기")
    parser.add_argument("script", help="script.txt 경로 (에피소드 디렉토리 내)")
    parser.add_argument("--output", default=None, help="출력 JSON 경로 (기본: script와 같은 디렉토리의 narration_timing.json)")
    parser.add_argument("--bpm", type=float, default=DEFAULT_BPM, help=f"BPM (기본: {DEFAULT_BPM})")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--rate", default=DEFAULT_RATE)
    parser.add_argument("--music-mood", default="raw",
                        choices=["ambient", "ikeda", "experimental", "minimal", "chill", "glitch", "raw", "intense"])
    parser.add_argument("--visual-mood", default=None,
                        choices=["ikeda", "cooper", "abstract", "data"])
    parser.add_argument("--drum", action="store_true", default=None,
                        help="드럼 강제 ON")
    parser.add_argument("--no-drum", action="store_true",
                        help="드럼 강제 OFF")
    args = parser.parse_args()

    script_path = os.path.abspath(args.script)
    if not os.path.exists(script_path):
        print(f"오류: script 파일 없음: {script_path}")
        sys.exit(1)

    # drum 처리: --drum / --no-drum / 미지정(None)
    if args.no_drum:
        drum = False
    elif args.drum:
        drum = True
    else:
        drum = None

    output_path = args.output or os.path.join(os.path.dirname(script_path), "narration_timing.json")

    data = asyncio.run(generate(
        script_path=script_path,
        bpm=args.bpm,
        voice=args.voice,
        rate=args.rate,
        music_mood=args.music_mood,
        visual_mood=args.visual_mood,
        drum=drum,
    ))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n[완료] {output_path}")
    print(f"  segments: {len(data['segments'])}, drops: {len(data['drops'])}")
    print(f"  total: {data['total_duration_sec']:.3f}s ({data['total_duration_sec']/data['sec_per_bar']:.1f} bars)")
    print(f"  music_mood: {data['music_mood']}, drum: {data.get('drum', '(무드 기본값)')}")

    # start_sec 마디 정렬 검증
    spb = data["sec_per_bar"]
    errors = []
    for seg in data["segments"]:
        ratio = seg["start_sec"] / spb
        if abs(ratio - round(ratio)) > 0.01:
            errors.append(f"  [경고] seg {seg['index']}: start_sec={seg['start_sec']} (ratio={ratio:.4f})")
    if errors:
        print("\n[마디 정렬 경고]")
        for e in errors:
            print(e)
    else:
        print("  [OK] 모든 start_sec이 마디 경계에 정렬됨")


if __name__ == "__main__":
    main()

"""
ENOMETA Edge-TTS 생성기
- Microsoft Edge TTS (ko-KR-SunHiNeural)
- narration_timing.json에서 세그먼트 읽기
- 세그먼트별 개별 생성 → 연결 → 실측 타이밍으로 JSON 업데이트
"""

import asyncio
import sys
import os
import json
import wave
import subprocess
import shutil
import tempfile

import edge_tts

DEFAULT_VOICE = "ko-KR-SunHiNeural"
DEFAULT_RATE = "+5%"
SILENCE_BETWEEN = 0.25  # 세그먼트 간 묵음 (초)


async def gen_one(text: str, output_path: str, voice: str, rate: str):
    """단일 텍스트를 mp3로 저장"""
    tts = edge_tts.Communicate(text, voice=voice, rate=rate)
    await tts.save(output_path)


def mp3_to_wav(mp3_path: str, wav_path: str):
    """ffmpeg으로 mp3 → wav 변환"""
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", mp3_path, wav_path],
        capture_output=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 변환 실패: {result.stderr.decode()}")


def get_wav_duration(wav_path: str) -> float:
    with wave.open(wav_path, "rb") as wf:
        return wf.getnframes() / wf.getframerate()


def concat_wavs(wav_files: list, silence_sec: float, output_path: str):
    """WAV 파일들을 묵음과 함께 연결"""
    with wave.open(wav_files[0], "rb") as wf:
        nchannels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()

    silence_data = b"\x00" * int(silence_sec * framerate * nchannels * sampwidth)

    with wave.open(output_path, "wb") as out:
        out.setnchannels(nchannels)
        out.setsampwidth(sampwidth)
        out.setframerate(framerate)
        for i, wav_path in enumerate(wav_files):
            with wave.open(wav_path, "rb") as wf:
                out.writeframes(wf.readframes(wf.getnframes()))
            if i < len(wav_files) - 1:
                out.writeframes(silence_data)


async def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_voice_edge.py <narration_timing.json> <output.wav>")
        print("       [--voice ko-KR-SunHiNeural] [--rate +5%]")
        sys.exit(1)

    timing_path = sys.argv[1]
    output_wav = sys.argv[2]

    voice = DEFAULT_VOICE
    rate = DEFAULT_RATE
    for i, arg in enumerate(sys.argv[3:], start=3):
        if arg == "--voice" and i + 1 < len(sys.argv):
            voice = sys.argv[i + 1]
        elif arg == "--rate" and i + 1 < len(sys.argv):
            rate = sys.argv[i + 1]

    with open(timing_path, "r", encoding="utf-8") as f:
        timing_data = json.load(f)

    segments = timing_data["segments"]
    print(f"Voice: {voice} ({rate})")
    print(f"Segments: {len(segments)}")

    tmp_dir = tempfile.mkdtemp()
    wav_files = []
    actual_durations = []

    try:
        for i, seg in enumerate(segments):
            text = seg["text"]
            mp3_path = os.path.join(tmp_dir, f"seg_{i:03d}.mp3")
            wav_path = os.path.join(tmp_dir, f"seg_{i:03d}.wav")

            print(f"[{i+1}/{len(segments)}] {text}")
            await gen_one(text, mp3_path, voice, rate)
            mp3_to_wav(mp3_path, wav_path)

            dur = get_wav_duration(wav_path)
            actual_durations.append(dur)
            wav_files.append(wav_path)
            print(f"  -> {dur:.3f}s")

        # 타이밍 계산 (실측)
        current = 0.0
        new_segments = []
        for i, seg in enumerate(segments):
            dur = actual_durations[i]
            new_seg = dict(seg)
            new_seg["start_sec"] = round(current, 3)
            new_seg["end_sec"] = round(current + dur, 3)
            new_seg["duration_sec"] = round(dur, 3)
            new_segments.append(new_seg)
            current += dur + SILENCE_BETWEEN

        total_dur = current - SILENCE_BETWEEN  # 마지막 묵음 제외

        # WAV 연결
        os.makedirs(os.path.dirname(os.path.abspath(output_wav)), exist_ok=True)
        concat_wavs(wav_files, SILENCE_BETWEEN, output_wav)
        print(f"\nSaved: {output_wav} ({total_dur:.3f}s)")

        # narration_timing.json 업데이트 (실측 타이밍)
        timing_data["voice"] = voice
        timing_data["rate"] = rate
        timing_data["total_duration_sec"] = round(total_dur, 3)
        timing_data["segments"] = new_segments

        with open(timing_path, "w", encoding="utf-8") as f:
            json.dump(timing_data, f, ensure_ascii=False, indent=2)
        print(f"Updated: {timing_path} (total: {total_dur:.3f}s)")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())

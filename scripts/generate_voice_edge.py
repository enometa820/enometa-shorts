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

def assemble_quantized_wav(segments_info: list, total_dur: float, output_path: str, tmp_dir: str):
    """
    각 TTS 오디오를 지정된 start_sec에 정확히 배치 (ffmpeg 믹싱 활용)
    """
    if not segments_info:
        # 빈 오디오 생성
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo", "-t", str(total_dur), output_path], capture_output=True)
        return

    # FFmpeg의 amix 필터는 여러 입력을 한번에 믹스함.
    # 각 오디오 입력 앞에 delay를 추가하는 방식: [1:a]adelay=delay_ms|delay_ms[a1]
    
    inputs = []
    filter_complex = []
    mix_inputs = []

    # 0번 입력: 전체 길이에 해당하는 빈 오디오 배경 (lavfi anullsrc)
    inputs.extend(["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo"])
    # 0번 입력은 믹스용 베이스 오디오로 사용
    mix_inputs.append("[0:a]")

    for idx, info in enumerate(segments_info):
        wav_path = info["wav"]
        start_sec = info["start_sec"]
        
        inputs.extend(["-i", wav_path])
        input_idx = idx + 1 # anullsrc가 0번
        
        delay_ms = int(start_sec * 1000)
        filter_str = f"[{input_idx}:a]adelay={delay_ms}|{delay_ms}[a{input_idx}]"
        filter_complex.append(filter_str)
        mix_inputs.append(f"[a{input_idx}]")

    # amix 필터로 모두 믹싱
    mix_str = "".join(mix_inputs) + f"amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=2:normalize=0[out]"
    filter_complex.append(mix_str)

    # 출력 길이 제한 적용 (atrim)
    final_filter = ";".join(filter_complex) + f";[out]atrim=0:{total_dur}[final_out]"

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", final_filter,
        "-map", "[final_out]",
        "-ac", "2",
        "-ar", "44100",
        output_path
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"ffmpeg error: {res.stderr}")
        raise RuntimeError("WAV 조립 실패")


async def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_voice_edge.py <script_data.json> <output.wav>")
        print("       [--voice ko-KR-SunHiNeural] [--rate +5%]")
        sys.exit(1)

    script_path = sys.argv[1]
    output_wav = sys.argv[2]

    voice = DEFAULT_VOICE
    rate = DEFAULT_RATE
    for i, arg in enumerate(sys.argv[3:], start=3):
        if arg == "--voice" and i + 1 < len(sys.argv):
            voice = sys.argv[i + 1]
        elif arg == "--rate" and i + 1 < len(sys.argv):
            rate = sys.argv[i + 1]

    with open(script_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)

    segments = script_data.get("segments", [])
    total_dur = script_data.get("global", {}).get("total_duration_sec", 60.0)
    
    print(f"Voice: {voice} ({rate})")
    print(f"Segments: {len(segments)}")
    print(f"Target Total Duration: {total_dur:.3f}s")

    tmp_dir = tempfile.mkdtemp()
    segments_info = []

    try:
        for i, seg in enumerate(segments):
            text = seg.get("text", "").strip()
            if not text:
                continue
                
            start_sec = seg.get("start_sec", 0.0)
            end_sec = seg.get("end_sec", 0.0)
            target_dur = end_sec - start_sec

            mp3_path = os.path.join(tmp_dir, f"seg_{i:03d}.mp3")
            wav_path = os.path.join(tmp_dir, f"seg_{i:03d}.wav")

            print(f"[{i+1}/{len(segments)}] @{start_sec:.2f}s ({target_dur:.2f}s): {text}")
            await gen_one(text, mp3_path, voice, rate)
            mp3_to_wav(mp3_path, wav_path)

            actual_dur = get_wav_duration(wav_path)
            if actual_dur > target_dur + 0.1:
                print(f"  [Warning] TTS length ({actual_dur:.2f}s) exceeds bar length ({target_dur:.2f}s)! Text might be overlapping.")
            else:
                print(f"  -> {actual_dur:.3f}s (Fits within {target_dur:.2f}s)")
                
            segments_info.append({
                "wav": wav_path,
                "start_sec": start_sec,
                "actual_dur": actual_dur
            })

        # 지정된 시간에 맞춰 조립
        os.makedirs(os.path.dirname(os.path.abspath(output_wav)) or ".", exist_ok=True)
        assemble_quantized_wav(segments_info, total_dur, output_wav, tmp_dir)
        print(f"\nSaved Assembly: {output_wav} ({total_dur:.3f}s)")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    asyncio.run(main())

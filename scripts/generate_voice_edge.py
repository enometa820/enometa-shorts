"""
ENOMETA TTS 생성기 (Edge-TTS)
- Microsoft Edge TTS (한국어)
- 문장별 생성 → 정확한 타이밍 → 자막 싱크
- GPU 불필요, 빠른 생성
"""

import sys
import os
import json
import asyncio
import wave
import struct
import time
import subprocess

import edge_tts


# 한국어 보이스 옵션
VOICES = {
    "female_calm": "ko-KR-SunHiNeural",     # 차분한 여성
    "female_bright": "ko-KR-SoonBokNeural",  # 밝은 여성
    "male_calm": "ko-KR-InJoonNeural",       # 차분한 남성
    "male_bright": "ko-KR-BongJinNeural",    # 밝은 남성
    "female_hyun": "ko-KR-HyunsuNeural",     # 현수 (여성스러운)
}

DEFAULT_VOICE = "ko-KR-SunHiNeural"


def get_wav_duration(path: str) -> float:
    """WAV 파일의 길이(초)를 반환"""
    with wave.open(path, 'rb') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / rate


def mp3_to_wav(mp3_path: str, wav_path: str):
    """ffmpeg로 MP3→WAV 변환"""
    subprocess.run(
        ["ffmpeg", "-y", "-i", mp3_path, "-ar", "24000", "-ac", "1", wav_path],
        capture_output=True, timeout=30,
    )


async def generate_segment(text: str, output_path: str, voice: str, rate: str = "-5%"):
    """단일 문장 TTS 생성 (MP3→WAV 변환 포함)"""
    mp3_path = output_path.replace(".wav", ".mp3")
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(mp3_path)
    mp3_to_wav(mp3_path, output_path)
    os.remove(mp3_path)


def generate_silence(duration_sec: float, output_path: str, sr: int = 24000):
    """무음 WAV 생성"""
    num_samples = int(sr * duration_sec)
    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(b'\x00\x00' * num_samples)


def concat_wavs(wav_files: list, output_path: str):
    """여러 WAV 파일을 순서대로 연결"""
    if not wav_files:
        return

    # 첫 파일에서 파라미터 읽기
    with wave.open(wav_files[0], 'rb') as wf:
        params = wf.getparams()
        sr = wf.getframerate()
        sw = wf.getsampwidth()
        ch = wf.getnchannels()

    all_frames = b''
    for f in wav_files:
        with wave.open(f, 'rb') as wf:
            # 파라미터가 다르면 ffmpeg로 변환 필요하지만 edge-tts는 일관된 파라미터 사용
            all_frames += wf.readframes(wf.getnframes())

    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(ch)
        wf.setsampwidth(sw)
        wf.setframerate(sr)
        wf.writeframes(all_frames)


async def generate_narration(
    sentences: list[str],
    output_path: str,
    voice: str = DEFAULT_VOICE,
    rate: str = "-5%",
    pause_sec: float = 0.15,
):
    """문장별 TTS 생성 → 연결 → 타이밍 데이터 반환"""

    temp_dir = os.path.join(os.path.dirname(output_path), "_tts_temp")
    os.makedirs(temp_dir, exist_ok=True)

    timing_data = []
    wav_files = []
    current_time = 0.0

    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if not sentence:
            continue

        seg_path = os.path.join(temp_dir, f"seg_{i:03d}.wav")
        print(f"  [{i+1}/{len(sentences)}] {sentence[:40]}...", flush=True)

        await generate_segment(sentence, seg_path, voice, rate)

        duration = get_wav_duration(seg_path)

        timing_data.append({
            "index": i,
            "text": sentence,
            "start_sec": round(current_time, 3),
            "end_sec": round(current_time + duration, 3),
            "duration_sec": round(duration, 3),
        })

        wav_files.append(seg_path)
        current_time += duration

        # 문장 사이 휴지
        if i < len(sentences) - 1 and pause_sec > 0:
            silence_path = os.path.join(temp_dir, f"pause_{i:03d}.wav")
            # edge-tts의 샘플레이트에 맞춤
            with wave.open(seg_path, 'rb') as wf:
                seg_sr = wf.getframerate()
            generate_silence(pause_sec, silence_path, sr=seg_sr)
            wav_files.append(silence_path)
            current_time += pause_sec

    # 연결
    print(f"\n  Concatenating {len(wav_files)} segments...", flush=True)
    concat_wavs(wav_files, output_path)

    total_duration = get_wav_duration(output_path)
    print(f"  Total duration: {total_duration:.2f}s")
    print(f"  Saved: {output_path}")

    # 임시 파일 정리
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    return timing_data, total_duration


def parse_script(script_path: str) -> list[str]:
    """대본 파일에서 문장 목록 추출"""
    with open(script_path, 'r', encoding='utf-8') as f:
        lines = f.read().strip().split('\n')

    # 빈 줄 제거, 각 줄을 하나의 문장으로
    sentences = [line.strip() for line in lines if line.strip()]
    return sentences


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python generate_voice_edge.py <script.txt> [output.wav] [voice] [rate]")
        print()
        print("Voices:", ", ".join(VOICES.keys()))
        print("Rate: -10% (slower), +0% (normal), +10% (faster)")
        sys.exit(1)

    script_path = sys.argv[1]
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    output = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(script_path), "narration.wav"
    )
    voice_key = sys.argv[3] if len(sys.argv) > 3 else "female_calm"
    rate = sys.argv[4] if len(sys.argv) > 4 else "-5%"

    voice = VOICES.get(voice_key, voice_key)

    print(f"Script: {script_path}")
    print(f"Voice: {voice} ({voice_key})")
    print(f"Rate: {rate}")
    print()

    sentences = parse_script(script_path)
    print(f"Sentences: {len(sentences)}")
    print()

    start = time.time()
    timing_data, total_duration = asyncio.run(
        generate_narration(sentences, output, voice, rate, pause_sec=0.15)
    )
    elapsed = time.time() - start

    # 타이밍 데이터 저장
    timing_path = os.path.splitext(output)[0] + "_timing.json"
    with open(timing_path, 'w', encoding='utf-8') as f:
        json.dump({
            "voice": voice,
            "rate": rate,
            "total_duration_sec": total_duration,
            "segments": timing_data,
        }, f, ensure_ascii=False, indent=2)

    print(f"\nTiming saved: {timing_path}")
    print(f"Total generation time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()

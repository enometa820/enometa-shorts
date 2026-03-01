"""
ENOMETA 오디오 분석기
- WAV 파일을 프레임별로 FFT 분석
- bass/mid/high/rms/onset 추출
- audio_analysis.json 생성 (Remotion에서 사용)
"""

import sys
import json
import wave
import struct
import math
import os

import numpy as np


def analyze_audio(wav_path: str, fps: int = 30) -> dict:
    """WAV 파일을 분석하여 프레임별 오디오 데이터를 생성"""

    # WAV 읽기
    with wave.open(wav_path, 'rb') as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        raw_data = wf.readframes(n_frames)

    # 바이트 → numpy array
    if sample_width == 2:
        dtype = np.int16
    elif sample_width == 4:
        dtype = np.int32
    else:
        raise ValueError(f"Unsupported sample width: {sample_width}")

    samples = np.frombuffer(raw_data, dtype=dtype).astype(np.float64)

    # 스테레오 → 모노 변환
    if n_channels == 2:
        samples = samples.reshape(-1, 2).mean(axis=1)
    elif n_channels > 2:
        samples = samples.reshape(-1, n_channels).mean(axis=1)

    # 정규화 (-1 ~ 1)
    max_val = np.iinfo(dtype).max
    samples = samples / max_val

    duration_sec = len(samples) / sample_rate
    total_video_frames = int(duration_sec * fps)

    # 프레임별 윈도우 크기
    samples_per_frame = sample_rate // fps

    # 주파수 대역 경계 (Hz)
    bass_range = (20, 250)
    mid_range = (250, 4000)
    high_range = (4000, 20000)

    frames_data = []
    prev_rms = 0
    onset_threshold = 0.15  # RMS 변화량 기반 onset 감지

    for i in range(total_video_frames):
        start = i * samples_per_frame
        end = start + samples_per_frame

        if end > len(samples):
            # 남은 샘플이 부족하면 패딩
            chunk = np.zeros(samples_per_frame)
            available = len(samples) - start
            if available > 0:
                chunk[:available] = samples[start:start + available]
        else:
            chunk = samples[start:end]

        # RMS (전체 볼륨)
        rms = float(np.sqrt(np.mean(chunk ** 2)))

        # FFT
        fft = np.fft.rfft(chunk)
        magnitudes = np.abs(fft) / len(chunk)
        freqs = np.fft.rfftfreq(len(chunk), 1.0 / sample_rate)

        # 주파수 대역별 에너지
        def band_energy(low: int, high: int) -> float:
            mask = (freqs >= low) & (freqs < high)
            if not np.any(mask):
                return 0.0
            return float(np.mean(magnitudes[mask]))

        bass = band_energy(*bass_range)
        mid = band_energy(*mid_range)
        high_val = band_energy(*high_range)

        # 온셋 감지 (RMS 급변)
        rms_delta = rms - prev_rms
        onset = rms_delta > onset_threshold
        prev_rms = rms

        # 정규화 (0~1 범위로 클램핑)
        bass_norm = min(bass * 15, 1.0)  # 스케일링 팩터
        mid_norm = min(mid * 30, 1.0)
        high_norm = min(high_val * 60, 1.0)
        rms_norm = min(rms * 3, 1.0)

        frames_data.append({
            "bass": round(bass_norm, 4),
            "mid": round(mid_norm, 4),
            "high": round(high_norm, 4),
            "rms": round(rms_norm, 4),
            "onset": onset,
        })

    return {
        "fps": fps,
        "duration_sec": round(duration_sec, 3),
        "sample_rate": sample_rate,
        "total_frames": total_video_frames,
        "frames": frames_data,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python audio_analyzer.py <input.wav> [output.json] [fps]")
        print("  input.wav   : 분석할 WAV 파일")
        print("  output.json : 출력 JSON (기본: audio_analysis.json)")
        print("  fps         : 비디오 FPS (기본: 30)")
        sys.exit(1)

    wav_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "audio_analysis.json"
    fps = int(sys.argv[3]) if len(sys.argv) > 3 else 30

    if not os.path.exists(wav_path):
        print(f"Error: {wav_path} not found")
        sys.exit(1)

    print(f"Analyzing: {wav_path}")
    print(f"FPS: {fps}")

    result = analyze_audio(wav_path, fps)

    print(f"Duration: {result['duration_sec']}s")
    print(f"Frames: {result['total_frames']}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()

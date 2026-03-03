"""
ENOMETA 오디오 믹서
- 나레이션 + BGM → mixed.wav
- ffmpeg 기반
- narration 90% + BGM 100%, 사이드체인 없음
- EBU R128 loudnorm (-14 LUFS) 최종 정규화
"""

import sys
import os
import json
import subprocess
import argparse


def mix_audio(
    narration_path: str,
    bgm_path: str,
    output_path: str,
    narration_volume: float = 0.90,
    bgm_volume: float = 1.0,
    sidechain_path: str = None,
):
    """나레이션과 BGM을 믹싱 (선택적 사이드체인 덕킹)
    BGM이 나레이션보다 길면 엔드카드까지 BGM이 이어짐.
    """

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # 나레이션 길이 구하기
    probe_cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        narration_path,
    ]
    duration = float(subprocess.check_output(probe_cmd).decode().strip())
    print(f"Narration duration: {duration:.2f}s")

    # BGM 길이 구하기 (엔드카드까지 이어지도록)
    bgm_probe_cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        bgm_path,
    ]
    bgm_duration = float(subprocess.check_output(bgm_probe_cmd).decode().strip())
    # 출력 길이: BGM이 더 길면 BGM 길이 사용 (엔드카드 포함)
    output_duration = max(duration, bgm_duration)
    print(f"BGM duration: {bgm_duration:.2f}s, output duration: {output_duration:.2f}s")

    if sidechain_path:
        # 사이드체인 덕킹: narration_timing.json 기반 볼륨 오토메이션
        print(f"Sidechain ducking from: {sidechain_path}")
        with open(sidechain_path, 'r', encoding='utf-8') as f:
            timing = json.load(f)

        duck_ratio = 0.707  # -3dB
        segments = timing.get("segments", [])

        vol_parts = []
        bgm_ducked = round(bgm_volume * duck_ratio, 3)

        for seg in segments:
            s = seg.get("start_sec", 0)
            e = seg.get("end_sec", 0)
            vol_parts.append(f"between(t,{s:.3f},{e:.3f})")

        if vol_parts:
            nar_condition = "+".join(vol_parts)
            vol_expr = f"if({nar_condition},{bgm_ducked},{bgm_volume})"
        else:
            vol_expr = str(bgm_volume)

        # narraiton을 output_duration까지 패딩 (엔드카드 구간은 무음)
        cmd = [
            "ffmpeg", "-y",
            "-i", narration_path,
            "-i", bgm_path,
            "-filter_complex",
            (
                f"[0:a]volume={narration_volume},apad=whole_dur={output_duration}[nar];"
                f"[1:a]atrim=0:{output_duration},volume='{vol_expr}':eval=frame[bgm];"
                f"[nar][bgm]amix=inputs=2:duration=longest:dropout_transition=2:normalize=0[mixed];"
                f"[mixed]atrim=0:{output_duration},loudnorm=I=-14:TP=-1.5:LRA=11[out]"
            ),
            "-map", "[out]",
            "-ar", "44100",
            "-ac", "2",
            output_path,
        ]
    else:
        # 고정 볼륨 믹싱 — BGM이 나레이션보다 길면 엔드카드까지 이어짐
        cmd = [
            "ffmpeg", "-y",
            "-i", narration_path,
            "-i", bgm_path,
            "-filter_complex",
            (
                f"[0:a]volume={narration_volume},apad=whole_dur={output_duration}[nar];"
                f"[1:a]atrim=0:{output_duration},volume={bgm_volume}[bgm];"
                f"[nar][bgm]amix=inputs=2:duration=longest:dropout_transition=2:normalize=0[mixed];"
                f"[mixed]atrim=0:{output_duration},loudnorm=I=-14:TP=-1.5:LRA=11[out]"
            ),
            "-map", "[out]",
            "-ar", "44100",
            "-ac", "2",
            output_path,
        ]

    print(f"Mixing: narration({narration_volume*100:.0f}%) + BGM({bgm_volume*100:.0f}%)"
          + (f" [sidechain ducking]" if sidechain_path else ""))
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr}")
        raise RuntimeError("Audio mixing failed")

    print(f"Mixed: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="ENOMETA Audio Mixer")
    parser.add_argument("narration", help="나레이션 WAV 경로")
    parser.add_argument("bgm", help="BGM WAV 경로")
    parser.add_argument("output", nargs="?", default="audio/mixed.wav",
                        help="출력 WAV 경로 (기본: audio/mixed.wav)")
    parser.add_argument("--bgm-volume", type=float, default=1.0,
                        help="BGM 볼륨 (0-2, 기본 1.0)")
    parser.add_argument("--sidechain", dest="sidechain",
                        help="narration_timing.json 경로 (사이드체인 덕킹)")
    args = parser.parse_args()

    mix_audio(args.narration, args.bgm, args.output,
              narration_volume=0.90,
              bgm_volume=args.bgm_volume,
              sidechain_path=args.sidechain)


if __name__ == "__main__":
    main()

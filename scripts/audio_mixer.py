"""
ENOMETA 오디오 믹서
- 나레이션 + BGM → mixed.wav
- ffmpeg 기반
- 나레이션 100% + BGM 50%
"""

import sys
import os
import subprocess


def mix_audio(
    narration_path: str,
    bgm_path: str,
    output_path: str,
    narration_volume: float = 1.0,
    bgm_volume: float = 0.50,
):
    """나레이션과 BGM을 믹싱"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # BGM을 나레이션 길이에 맞추고 볼륨 조절 후 믹싱
    cmd = [
        "ffmpeg", "-y",
        "-i", narration_path,
        "-i", bgm_path,
        "-filter_complex",
        (
            f"[0:a]volume={narration_volume}[nar];"
            f"[1:a]volume={bgm_volume},aloop=loop=-1:size=2e+09[bgm_loop];"
            f"[bgm_loop]atrim=end='stream(0,duration)'[bgm_trimmed];"
            f"[nar][bgm_trimmed]amix=inputs=2:duration=first:dropout_transition=2[out]"
        ),
        "-map", "[out]",
        "-ar", "22050",
        "-ac", "1",
        output_path,
    ]

    # 위 filter가 복잡하므로 간단한 2단계 접근
    # 1단계: BGM 볼륨 조절 + 나레이션 길이에 맞추기
    # 2단계: 믹싱

    # 나레이션 길이 구하기
    probe_cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        narration_path,
    ]
    duration = float(subprocess.check_output(probe_cmd).decode().strip())
    print(f"Narration duration: {duration:.2f}s")

    # 간단한 방식: amix로 믹싱
    cmd = [
        "ffmpeg", "-y",
        "-i", narration_path,
        "-i", bgm_path,
        "-filter_complex",
        (
            f"[0:a]volume={narration_volume}[nar];"
            f"[1:a]atrim=0:{duration},volume={bgm_volume}[bgm];"
            f"[nar][bgm]amix=inputs=2:duration=first:dropout_transition=1[out]"
        ),
        "-map", "[out]",
        "-ar", "22050",
        "-ac", "1",
        output_path,
    ]

    print(f"Mixing: narration({narration_volume*100:.0f}%) + BGM({bgm_volume*100:.0f}%)")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"ffmpeg error: {result.stderr}")
        raise RuntimeError("Audio mixing failed")

    print(f"Mixed: {output_path}")
    return output_path


def main():
    if len(sys.argv) < 3:
        print("Usage: python audio_mixer.py <narration.wav> <bgm.wav> [output.wav]")
        sys.exit(1)

    narration = sys.argv[1]
    bgm = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) > 3 else "audio/mixed.wav"

    mix_audio(narration, bgm, output)


if __name__ == "__main__":
    main()

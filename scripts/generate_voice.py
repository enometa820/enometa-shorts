"""
ENOMETA TTS 생성기
- Chatterbox Multilingual TTS (한국어)
- 보이스 클로닝: assets/voice_ref.wav 참조
- 출력: audio/narration.wav
"""

import sys
import os
import json
import time

import torch
import torchaudio as ta

# Windows 심볼릭 링크 문제 방지
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# 로컬 모델 경로 (심볼릭 링크 없이 다운로드됨)
MODEL_LOCAL_DIR = os.path.join(os.path.expanduser("~"), ".cache", "chatterbox_model")


def generate_voice(
    text: str,
    output_path: str,
    voice_ref_path: str,
    language: str = "ko",
    device: str = "cuda",
):
    """Chatterbox Multilingual TTS로 한국어 나레이션 생성"""

    print(f"Loading Chatterbox Multilingual TTS on {device}...")
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    from pathlib import Path
    model = ChatterboxMultilingualTTS.from_local(
        Path(MODEL_LOCAL_DIR), device=device,
    )

    print(f"Text: {text[:80]}...")
    print(f"Voice ref: {voice_ref_path}")
    print(f"Language: {language}")

    start = time.time()
    wav = model.generate(
        text,
        audio_prompt_path=voice_ref_path,
        language_id=language,
    )
    elapsed = time.time() - start

    # 저장
    ta.save(output_path, wav, model.sr)
    print(f"Saved: {output_path} ({elapsed:.1f}s)")

    # VRAM 해제
    del model
    torch.cuda.empty_cache()

    return output_path


def generate_voice_segments(
    segments: list[dict],
    output_dir: str,
    voice_ref_path: str,
    language: str = "ko",
    device: str = "cuda",
):
    """여러 문장을 개별 WAV로 생성 + 타이밍 정보 반환"""

    print(f"Loading Chatterbox Multilingual TTS on {device}...")
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS

    from pathlib import Path
    model = ChatterboxMultilingualTTS.from_local(
        Path(MODEL_LOCAL_DIR), device=device,
    )

    os.makedirs(output_dir, exist_ok=True)
    timing_data = []

    for i, seg in enumerate(segments):
        text = seg["text"]
        print(f"[{i+1}/{len(segments)}] Generating: {text[:50]}...")

        start = time.time()
        wav = model.generate(
            text,
            audio_prompt_path=voice_ref_path,
            language_id=language,
        )
        elapsed = time.time() - start

        filename = f"seg_{i:03d}.wav"
        filepath = os.path.join(output_dir, filename)
        ta.save(filepath, wav, model.sr)

        duration = wav.shape[1] / model.sr
        timing_data.append({
            "index": i,
            "text": text,
            "file": filename,
            "duration_sec": round(duration, 3),
            "generation_time_sec": round(elapsed, 1),
        })
        print(f"  -> {filename} ({duration:.2f}s, generated in {elapsed:.1f}s)")

    # VRAM 해제
    del model
    torch.cuda.empty_cache()

    return timing_data


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python generate_voice.py <text> [output.wav] [voice_ref.wav]")
        print("  python generate_voice.py --script <script.json> [output_dir] [voice_ref.wav]")
        sys.exit(1)

    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_ref = os.path.join(project_dir, "assets", "voice_ref.wav")

    if sys.argv[1] == "--script":
        # 스크립트 모드: JSON 파일에서 문장 목록 읽기
        script_path = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.join(project_dir, "audio", "segments")
        voice_ref = sys.argv[4] if len(sys.argv) > 4 else default_ref

        with open(script_path, "r", encoding="utf-8") as f:
            script = json.load(f)

        segments = script.get("segments", script.get("scenes", []))
        if not segments:
            print("Error: No segments found in script")
            sys.exit(1)

        # 텍스트 추출
        seg_list = []
        for s in segments:
            text = s.get("text") or s.get("sentence") or s.get("narration", "")
            if text:
                seg_list.append({"text": text})

        timing = generate_voice_segments(seg_list, output_dir, voice_ref)

        # 타이밍 저장
        timing_path = os.path.join(output_dir, "timing.json")
        with open(timing_path, "w", encoding="utf-8") as f:
            json.dump(timing, f, ensure_ascii=False, indent=2)
        print(f"\nTiming saved: {timing_path}")

    else:
        # 단일 텍스트 모드
        text = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else os.path.join(project_dir, "audio", "narration.wav")
        voice_ref = sys.argv[3] if len(sys.argv) > 3 else default_ref

        os.makedirs(os.path.dirname(output), exist_ok=True)
        generate_voice(text, output, voice_ref)


if __name__ == "__main__":
    main()

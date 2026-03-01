"""
Placeholder ambient BGM generator (pure Python + numpy)
ACE-Step VRAM 문제 해결 전까지 사용
"""
import numpy as np
import struct
import os
import sys

def generate_ambient_bgm(output_path, duration=45, sr=48000):
    t = np.linspace(0, duration, sr * duration, dtype=np.float32)

    # Ambient pad layers
    pad1 = 0.15 * np.sin(2 * np.pi * 110 * t)   # A2
    pad2 = 0.10 * np.sin(2 * np.pi * 165 * t)   # E3
    pad3 = 0.08 * np.sin(2 * np.pi * 220 * t)   # A3
    pad4 = 0.05 * np.sin(2 * np.pi * 330 * t)   # E4

    # Slow LFO modulation
    lfo1 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.1 * t)
    lfo2 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t)
    lfo3 = 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t)

    audio = pad1 * lfo1 + pad2 * lfo2 + pad3 * lfo3 + pad4 * lfo1 * lfo2

    # Filtered noise layer
    np.random.seed(42)
    noise = np.random.randn(len(t)).astype(np.float32) * 0.02
    kernel = np.ones(200) / 200
    noise_filtered = np.convolve(noise, kernel, mode='same')
    audio += noise_filtered * 3.0

    # Gentle arpeggio
    for note_freq in [220, 277.18, 329.63, 440]:
        for beat in range(int(duration * 2)):
            start = int(beat * 0.5 * sr)
            env_len = int(0.4 * sr)
            if start + env_len > len(t):
                break
            env = np.exp(-np.linspace(0, 5, env_len))
            note = 0.03 * np.sin(2 * np.pi * note_freq * t[start:start+env_len]) * env
            if (beat + int(note_freq / 110)) % 8 in [0, 3, 5]:
                audio[start:start+env_len] += note

    # Fade in/out (3 seconds)
    fade_samples = int(3 * sr)
    audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.7

    # Write WAV 16-bit mono
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    samples_16 = (audio * 32767).astype(np.int16)
    data_size = len(samples_16) * 2
    with open(output_path, 'wb') as f:
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))
        f.write(struct.pack('<H', 1))    # PCM
        f.write(struct.pack('<H', 1))    # mono
        f.write(struct.pack('<I', sr))
        f.write(struct.pack('<I', sr * 2))
        f.write(struct.pack('<H', 2))
        f.write(struct.pack('<H', 16))
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        f.write(samples_16.tobytes())

    print(f"Generated: {output_path}")
    print(f"Duration: {duration}s, SR: {sr}Hz, Size: {os.path.getsize(output_path)} bytes")

if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "episodes", "ep001", "bgm.wav"
    )
    dur = int(sys.argv[2]) if len(sys.argv) > 2 else 45
    generate_ambient_bgm(output, duration=dur)

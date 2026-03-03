# ENOMETA Hybrid Visual Architecture — Claude Code 구현 명세서

Python이 데이터 비주얼을 그리고, Remotion이 자막/제목/오버레이를 합성한다. 음악과 영상이 같은 numpy 배열을 공유하는 퓨어 컴퓨팅 아트 아키텍처. 의존 문서: ENOMETA_SYSTEM_SNAPSHOT_v6.md, ENOMETA_Visual_Differentiation_Spec.md (v2.0) 프로젝트 경로: C:\옵시디언\enometa\enometa-shorts\
> v8 업데이트: **Legacy 모드 제거** + **ikeda 단일 장르** + **Hybrid 전용화**
> v9 업데이트: **SI_INTENSITY_SCALE** (레이어 강도 동적 조절) + **visual_script SI 연동** (reactivity/max_layers 동적 결정)
> **last_updated**: 2026-03-04 — EP007 완료 (변경 없음, 문서 최신 상태 확인)

## 핵심 사상

현재 파이프라인의 구조적 문제:

```
음악 (Python/numpy) → wav → ffmpeg → JSON(FFT 요약) → 비주얼 (React/JS)
                                         ↑
                              여기서 원본 데이터가 소실된다
                              bass/mid/high/rms 4개 숫자로 압축됨
```

변경 후:

```
음악 (Python/numpy) ─┬→ wav (오디오 출력)
                     └→ raw_visual_data (원본 그대로)
                          ↓
                     Python 비주얼 엔진 (같은 numpy 배열로 프레임 생성)
                          ↓
                     frame_0001.png ~ frame_NNNN.png
                          ↓
                     Remotion (프레임 배경 + 제목 + 자막 + PostProcess)
                          ↓
                     output.mp4
```

원칙: 데이터가 소리가 되는 바로 그 수학이 화면도 만든다.

## 역할 분담

| 레이어 | 담당 | 이유 |
|--------|------|------|
| 데이터 비주얼 (배경 1080x1080) | Python (numpy + Pillow) | 음악 엔진과 같은 데이터를 직접 공유 |
| 제목 텍스트 (상단 190px) | Remotion (React) | CSS 타이포그래피가 압도적으로 편함 |
| 자막 2줄 (하단) | Remotion (React) | 타이밍 동기화 + 스타일링 |
| PostProcess (비네트/스캔라인) | Remotion (React) | 기존 컴포넌트 재활용 |
| 최종 합성 (9:16 1080x1920) | Remotion | 프레임 시퀀스 + 오버레이 → MP4 |

## 변경된 파이프라인

```
입력: script.txt + title + genre(선택)

[1] TTS 생성 → narration.wav + narration_timing.json
[2] ★ 대본 데이터 추출 → script_data.json (v6 — 숫자/바이트/semantic_intensity)
[3] 자막 그룹핑 → subtitle_groups.json (2줄씩)
[4] 비주얼 스크립트 → visual_script.json (v8: 항상 ikeda + hybrid 자동 설정)
[5] BGM 생성 → bgm.wav + raw_visual_data.npz (★ --export-raw --script-data)
[6] ★ Python 비주얼 렌더링 → frames/000000.png ~ NNNNNN.png
[7] 오디오 믹싱 → mixed.wav (TTS:BGM = 4:6, 나레이션 67% + BGM 100% + 사이드체인 덕킹)
[8] Remotion 합성 → output.mp4 (Python 배경 + vocab 오버레이 + 제목 + 자막 + PostProcess)

출력: 1080x1920 MP4
```

기존 대비 변경점:
* [3]에서 raw_visual_data.npz 추가 출력
* [5] 완전 신규 단계
* [6] Remotion이 vocab 컴포넌트 대신 Python 프레임 시퀀스를 배경으로 사용

## 1. 음악 엔진 출력 확장 (enometa_music_engine.py 수정)

### 1-1. raw_visual_data.npz 스펙

음악 엔진이 wav와 함께 프레임별 원본 데이터를 저장한다.

```python
def export_raw_visual_data(
    output_path: str,
    audio_buffer: np.ndarray,
    sample_rate: int,
    fps: int,
    engine_state: dict
):
    """음악 엔진의 원본 데이터를 비주얼 엔진에 전달"""

    total_frames = int(len(audio_buffer) / sample_rate * fps)
    samples_per_frame = sample_rate // fps

    frame_data = {
        "audio_chunks": np.zeros((total_frames, samples_per_frame)),
        "bytebeat_values": np.zeros((total_frames, samples_per_frame)),
        "instrument_energies": np.zeros((total_frames, len(engine_state["instruments"]))),
        "instrument_names": np.array(list(engine_state["instruments"].keys())),
        "synthesis_params": {
            "bit_depth": engine_state.get("bit_depth", 16),
            "wavefold_amount": np.zeros(total_frames),
            "feedback_level": np.zeros(total_frames),
        },
        "euclidean_pattern": engine_state.get("euclidean_pattern", np.array([])),
        "bpm": engine_state["bpm"],
        "genre": engine_state["genre"],
        "sample_rate": sample_rate,
        "fps": fps,
    }
    # ... 프레임별 데이터 수집 루프 ...
    np.savez_compressed(output_path, **frame_data)
```

### 1-2. 기존 코드 수정 위치

enometa_music_engine.py의 메인 렌더링 함수 끝에 호출 추가:

```python
# 기존: wav만 저장
sf.write(output_wav_path, audio_buffer, sample_rate)

# 추가: raw_visual_data도 저장
raw_path = output_wav_path.replace(".wav", "_raw_visual_data.npz")
export_raw_visual_data(raw_path, audio_buffer, sample_rate, 30, engine_state)
```

bytebeat 합성 시 원본 보존 (중요): 현재 bytebeat 합성 함수에서 & 0xFF 하기 전 값도 별도 버퍼에 저장해야 한다.

## 2. Python 비주얼 엔진 (신규: visual_renderer.py)

### 2-1. 파일 위치

```
scripts/script_data_extractor.py  # v6: 대본 데이터 추출 (숫자/화학물질/바이트/semantic_intensity)
scripts/visual_renderer.py        # 메인 렌더러
scripts/visual_layers/            # 비주얼 레이어 모듈 (9개 + 공유 이펙트)
  ├── __init__.py                 # tts_effects 임포트 포함
  ├── bytebeat_layer.py           # bytebeat 공식 → 픽셀
  ├── waveform_layer.py           # 오디오 파형 직접 그리기
  ├── particle_layer.py           # 파티클 (numpy 벡터 연산)
  ├── data_matrix_layer.py        # 데이터 매트릭스/비트 시각화
  ├── feedback_layer.py           # 피드백 루프 시각화
  ├── sine_wave_layer.py          # v6: 오실로스코프 사인파 (ikeda)
  ├── barcode_layer.py            # v6: UTF-8 바이트 바코드 (v6.2 si 다이나믹 리라이트)
  ├── data_stream_layer.py        # v6: 데이터 스트림 스크롤 (v6.2 si 다이나믹 리라이트)
  ├── text_data_layer.py          # v6: 터미널 텍스트 카드 (v6.2 si 다이나믹 리라이트)
  ├── tts_effects.py              # v6.2 신규: 10개 공유 이펙트 함수
  └── composite.py                # 레이어 합성
```

### 2-2. 메인 렌더러 구조

VisualRenderer 클래스가 장르별 레이어 조합을 결정하고, 각 레이어가 raw_data를 직접 소비하여 프레임을 생성.

**v6.2 ctx 확장**: 각 레이어의 `render()` 메서드에 전달되는 ctx dict에 다음 필드 추가:
- `semantic_intensity` (float, 0-1): 현재 TTS 세그먼트의 의미 강도
- `current_keywords` (list): 현재 활성 키워드 리스트
- `reactive_level` (float): semantic_intensity 기반 계산된 반응 레벨

### 2-2b. SI 기반 레이어 강도 동적 조절 (v9 신규)

`render_frame()` 매 프레임마다 `semantic_intensity`로 각 레이어의 `intensity`를 실시간 스케일.

```python
SI_INTENSITY_SCALE = {
    "SineWaveLayer":   lambda si: max(0.35, 1.0 - si*0.45),  # 배경→서브 (si 낮을수록 강함)
    "WaveformLayer":   lambda si: 0.25 + si*0.75,             # si 비례 (완만)
    "ParticleLayer":   lambda si: max(0.05, si**1.5),         # si 비례 (민감, si=1→1.0)
    "TextDataLayer":   lambda si: 0.45 + si*0.55,
    "BarcodeLayer":    lambda si: 0.35 + si*0.55,
    "DataStreamLayer": lambda si: 0.25 + si*0.65,
    "DataMatrixLayer": lambda si: max(0.10, si**1.2),
}
# 적용: layer.intensity = layer._base_intensity * scale_fn(si)
```

효과: si=0.2 구간(조용한 대사) → 파티클 거의 안 보임, 사인파 배경 강함
      si=0.9 구간(극적 대사) → 파티클 폭발, 사인파 서브로 밀림

### 2-3~2-7. 비주얼 레이어 모듈

- **BytebeatLayer**: bytebeat 공식의 원본 값이 직접 픽셀이 되는 레이어
- **WaveformLayer**: FFT 요약이 아닌 실제 오디오 샘플값을 사용한 파형 렌더링 (SI 비례 강도)
- **ParticleLayer**: numpy 벡터 연산으로 파티클 시뮬레이션 (SI^1.5 민감 반응)
- **DataMatrixLayer**: 악기별 에너지를 매트릭스/그리드로 직접 시각화 (Ryoji Ikeda 스타일)
- **FeedbackLayer**: 이전 프레임이 다음 프레임에 영향하는 자기참조 구조

### 2-8. visual_script_generator SI 연동 (v9 신규)

`build_scene(si=...)` 파라미터로 씬별 SI 값이 전달되어 reactivity와 레이어 수를 동적 결정.

```
SI 기반 reactivity 오버라이드:
  si ≥ 0.88 → "max"  (audio_reactive: particle_size="bass*7+1", glow="bass*7")
  si ≥ 0.72 → +1 boost (pool 기본값에서 한 단계 상향)
  si ≤ 0.25 → "low"  (audio_reactive: particle_size="bass*3+1", glow="rms*0.8")

SI 기반 max_layers 조절:
  si_max_layers = int(si * 3.5)  → si=0.25→1레이어, si=0.5→1~2, si=0.75+→2~3
  실제 적용: min(strategy.max_layers, si_max_layers)

세그먼트 합칠 때 SI 평균 계산:
  merged_scene["si"] = sum(seg.si for seg in group) / count
```

### 2-8. 레이어 합성 (composite.py)

- `composite_layers()`: additive blend로 여러 레이어를 하나의 프레임으로 합성
- `composite_dual_source()`: (v6.1) TTS/Music 레이어 독립 합성
  - `arc_energy`가 음악 레이어 강도를 변조 (기승전결 반영)
  - `blend_ratio`로 TTS/Music 가중치 제어 (0=TTS 전용, 1=Music 전용)
  - oversaturation 방지: total_weight > 1.5 시 정규화

## 3. Remotion 수정 — 프레임 시퀀스 배경 모드

### 3-1. PythonFrameBackground.tsx (신규)

프레임 번호에 해당하는 PNG를 읽어서 배경으로 표시.

### 3-2. VisualSection.tsx — Hybrid 전용 (v8)

v8에서 legacy 모드 완전 제거. `meta.render_mode`는 항상 `"hybrid"`.
- `frames_dir` / `total_frames` 필수 — 미설정 시 에러 표시
- 렌더 순서: PythonFrameBackground → vocab 시맨틱 오버레이 → PostProcess

### 3-3. LogoEndcard v2 — 파티클 수렴 엔드카드 (타이밍 + 다이나미즘 강화)

| 파라미터 | v1 | v2 | 효과 |
|---------|-----|-----|------|
| scatterEnd | 0.15초 | 0.03초 | 검정 화면 대폭 축소 |
| 초기 radius | 672~1072px | 384~584px | 파티클 더 빨리 보임 |
| 초기 alpha | 0.15 | 0.35 | 파티클 즉시 가시화 |
| convergeDuration | 2.5초 | 2.0초 | 수렴 가속 |
| 태그라인 등장 | 4.2초 | 2.8초 | 더 빠른 노출 |
| 태그라인 max opacity | 0.35 | 0.5 | 가독성 향상 |
| 태그라인 풀 노출 | 0.2초 | 1.7초 | 충분한 노출 시간 |
| 호흡 진폭 | 0.6px | 2.5px | 파티클 생동감 |
| 글로우 반경 | 6x | 8x | 강화된 발광 |
| 글로우 alpha | 0.035 | 0.06 | 더 밝은 글로우 |
| 연결선 거리 | 70px | 90px | 더 넓은 연결망 |
| 연결선 alpha | 0.05 | 0.08 | 더 선명한 연결선 |

**v2 추가 효과**: 웨이브 효과(pp>0.9), 크기 펄스(±30%), 색상 깜빡임, 액센트 비율 8→12%

### 3-4. TitleSection — endcardStartFrame fade-out 연동

- `endcardStartFrame` prop 추가 → EnometaShorts.tsx에서 전달
- 엔드카드 시작 1초(30프레임) 전부터 제목 opacity 0으로 fade-out
- 엔드카드 종료 후 제목이 다시 보이는 버그 수정

### ✅ Hybrid Vocab Overlay (EP005 피드백 → v6.6 구현 완료)
- VisualSection.tsx hybrid 모드에서 **vocab 시맨틱 레이어 오버레이 활성화 완료**
- Python 프레임 배경 위에 visual_script.json의 씬별 vocab entries가 자동으로 렌더링됨
- 렌더 순서: PythonFrameBackground → vocab 시맨틱 오버레이 → PostProcess
- 씬이 없는 구간에서는 Python 배경 + PostProcess만 표시 (graceful fallback)
- meta에 `render_mode: "hybrid"`, `frames_dir`, `total_frames` 3개 필드 모두 필수

## 4. 장르별 레이어 조합 레지스트리 (v8: ikeda 전용)

> **v8**: 5개 장르 제거, ikeda만 유지. GENRE_LAYER_PRESETS는 ikeda 단일 프리셋.

| 장르 | Music Layers (리드+보조) | TTS Layers (강조+기본) | blend_ratio |
|------|------------------------|----------------------|-------------|
| **ikeda** | SineWaveLayer(0.7), WaveformLayer(0.4), ParticleLayer(0.3) | TextDataLayer(0.7), BarcodeLayer(0.6), DataStreamLayer(0.5), DataMatrixLayer(0.4) | **0.45** |

### v8 변경 요약
- 5개 장르(techno/bytebeat/algorave/harsh_noise/chiptune) 프리셋 제거
- ikeda 프리셋만 유지: Music 3 + TTS 4 = 7레이어
- Legacy 모드 코드 경로 완전 삭제

### v6.2 TTS 레이어 다이나믹 스펙 (semantic_intensity 연동)

| 레이어 | 속성 | si=0.1 (조용) | si=0.5 (중간) | si=0.9 (극적) |
|--------|------|-------------|-------------|-------------|
| **TextDataLayer** | 폰트 | 24px | 36px | 48px |
| | 카드 높이 | ~110px | ~155px | ~200px |
| | 이펙트 | 없음 | scanlines + glow | scanlines + chromatic + glitch + wave + data_click |
| **DataStreamLayer** | 폰트 | 18px | 27px | 36px |
| | 스크롤 속도 | 1x | 2.5x | 5x |
| | 이펙트 | 없음 | scanlines | scanlines + chromatic + glow |
| **BarcodeLayer** | 선폭 | ~4px | ~8px | ~12px |
| | 선높이 | 60% | 80% | 100% |
| | 이펙트 | 없음 | scanlines | scanlines + chromatic + glitch |

> 모든 TTS 레이어는 `tts_effects.py`의 공유 함수를 사용하여 일관된 이펙트 품질을 보장한다.

> **Dual-Source 합성 흐름**: Music layers → composite_layers() → music_composite / TTS layers → composite_layers() → tts_composite → composite_dual_source(bg, music, tts, blend_ratio, arc_energy)

## 5. 구현 순서

### Phase A — 음악 엔진 출력 확장 ✅ 완료
1. ✅ export_raw_visual_data() 함수 추가
2. ✅ bytebeat 합성 시 클리핑 전 원본 보존 (return_raw=True)
3. ✅ --export-raw CLI 옵션 추가

### Phase B — Python 비주얼 엔진 구축 ✅ 완료
1. ✅ visual_layers/ 디렉토리 (5 레이어 + composite)
2. ✅ 각 레이어 모듈 구현 (Bytebeat, Waveform, Particle, DataMatrix, Feedback)
3. ✅ visual_renderer.py 메인 렌더러 (VisualRenderer 클래스)

### Phase C — Remotion 하이브리드 모드 ✅ 완료
1. ✅ PythonFrameBackground.tsx 신규 (staticFile 프레임 로드)
2. ✅ VisualSection.tsx render_mode 분기 (hybrid/legacy)
3. ✅ types.ts에 VisualScriptMeta 인터페이스 추가
4. ✅ EnometaShorts.tsx에서 meta prop 전달
5. ✅ 하위 호환 확인 (기존 EP001~004 legacy 정상)

### Phase D — Dual-Source + Song Arc ✅ 완료
1. ✅ `composite_dual_source()` 함수 추가 (composite.py)
2. ✅ Song Arc 시스템 (enometa_music_engine.py): SONG_ARC_PRESETS, _compute_song_arc(), --arc CLI
3. ✅ raw_visual_data.npz에 arc_energy/arc_phases 배열 추가
4. ✅ GENRE_LAYER_PRESETS → Dual-Source dict 구조 (music_layers/tts_layers/blend_ratio)
5. ✅ visual_renderer.py: _init_layers() dict, render_frame() dual-source 합성
6. ✅ 하위호환: flat list 입력 시 자동으로 music_layers로 취급, arc 데이터 없으면 energy=1.0

### Phase D — 통합 테스트 ✅ 완료
- ✅ TypeScript 빌드 에러 0
- ✅ Python visual_layers import 정상

### Phase 4 — semantic_intensity TTS 다이나믹 비주얼 ✅ 구현 완료
1. ✅ `scripts/script_data_extractor.py`: `compute_semantic_intensity()` 추가
   - VERB_ENERGY 26개 동사 에너지 사전
   - EMOTION_INTENSITY 18개 감정어 강도 사전
   - 4요소 가중합산: verb(0.35) + emotion(0.3) + sentence_structure(0.2) + byte_variance(0.15)
   - 키워드별 `intensity` 필드 자동 부여
2. ✅ `scripts/visual_renderer.py`: ctx 확장
   - `semantic_intensity` (0-1): 현재 세그먼트의 의미 강도
   - `current_keywords`: 현재 키워드 리스트
   - `reactive_level`: si 기반 계산된 반응 레벨
3. ✅ `scripts/visual_layers/tts_effects.py`: 10개 공유 이펙트 함수 (신규)
   - `get_scaled_font(base_size, si)` — si 비례 폰트 크기
   - `intensity_color(base_rgb, si)` — si→HSV 밝기/채도 변조
   - `hue_shift_color(base_rgb, si)` — si 비례 hue 시프트
   - `chromatic_aberration(img, si)` — R/B 채널 오프셋 (si > 0.4)
   - `scanlines(img, si)` — 수평 스캔라인 오버레이 (si > 0.3)
   - `glitch_blocks(img, si)` — 랜덤 블록 글리치 (si > 0.6)
   - `text_glow(draw, xy, text, font, color, si)` — 텍스트 발광 효과
   - `vertical_wave_distortion(img, si)` — 수직 웨이브 왜곡
   - `scale_pulse(base, si, bpm, frame)` — BPM 동기 맥동
   - `data_click_explosion(draw, xy, si)` — 데이터 클릭 폭발 파티클
4. ✅ TTS 레이어 3종 전면 리라이트:
   - **TextDataLayer**: 폰트 16→48px, 카드 90→200px, 색상/jitter/glow/scanlines/chromatic/glitch/wave/data_click
   - **DataStreamLayer**: 폰트 16→36px, 행별 jitter, 스크롤 si 비례 가속, glow/scanlines/chromatic
   - **BarcodeLayer**: 선폭 2→12px, BPM 맥동, 선높이 60~100%, scanlines/chromatic/glitch
5. ✅ `scripts/visual_layers/__init__.py`: tts_effects 임포트 추가

## 6. 성능 예상

| 항목 | 값 |
|------|-----|
| 해상도 | 1080x1080 |
| FPS | 30 |
| 60초 영상 프레임 수 | 1,800 |
| 프레임당 Python 렌더 시간 | 0.1 ~ 0.5초 (CPU numpy) |
| 전체 Python 렌더 시간 | 3 ~ 15분 |
| Remotion 합성 시간 | 5 ~ 10분 |

## 7. 확장 로드맵

```
Phase A-D  [완료] Python+Remotion 하이브리드
Phase 4    [완료] semantic_intensity TTS 다이나믹 비주얼 + tts_effects 공유 모듈
Phase E    moderngl GPU 가속 레이어 추가 (RTX 3060 활용)
Phase F    pygame 실시간 프리뷰 모드
Phase G    Remotion 완전 제거 → Python만으로 최종 MP4 출력
Phase H    TouchDesigner 연동 (OSC)
```

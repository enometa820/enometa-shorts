# ENOMETA 비주얼 차별화 시스템 명세서 (2026-03-04)

> 최종 업데이트: 2026-03-04
> 상태: **Phase 1~4 구현 완료** / v11 enometa 단일 장르 (구 ikeda)
> **last_updated**: 2026-03-04 — v11 ikeda→enometa 리네이밍, Lissajous vocab, z-order 시스템, EMOTION_VOCAB_POOL lissajous 추가

---

## 개요

ENOMETA의 핵심 철학 "매 에피소드가 시스템을 성장시킨다"를 실현하기 위한 3단계 비주얼 차별화 시스템.
같은 vocab 컴포넌트를 사용하더라도, **variant + strategy + history** 조합으로 매번 다른 시각적 경험을 생성한다.

---

## Phase 1: Variant 시스템

### 1.1 개념
하나의 vocab 컴포넌트가 여러 시각적 변형(variant)을 가진다.
- `ParticleBirth` → default / triangles_rise / lines_scatter / dots_grid
- variant는 `visual_script.json`의 `VocabEntry`에 `variant` 필드로 지정

### 1.2 데이터 플로우
```
visual_script.json → VocabEntry.variant → VisualSection.tsx → Component(variant prop)
```

### 1.3 Variant Registry (9개 컴포넌트, ~28 variants)

| 컴포넌트 | variants | 핵심 변경 |
|---------|----------|----------|
| ParticleBirth | default, triangles_rise, lines_scatter, dots_grid | 파티클 형태+생성 위치 분기 |
| ParticleScatter | default, directional_wind, spiral_out | 확산 방향/궤적 분기 |
| ParticleConverge | default, multi_point, collapse_line | 수렴 타겟 분기 |
| ParticleOrbit | default, ellipse_drift, figure_eight | 궤도 형태 분기 |
| ParticleEscape | default, chain_break, explosion | 이탈 방식 분기 |
| FractalCrack | default, edge_shatter, web_crack | 균열 시작점/패턴 분기 |
| NeuralNetwork | default, tree_branch, constellation | 노드 배치+연결 방식 분기 |
| FlowField | default, vortex, opposing | 노이즈 각도 계산 분기 |
| GridMorph | default, wave_propagation, pixel_dissolve | 변형 방식 분기 |

### 1.4 하위 호환
- variant 미지정(undefined) → `"default"` 동작
- EP001~004 기존 visual_script.json은 수정 불필요

---

## Phase 2: 비주얼 전략 프리셋

### 2.1 개념
에피소드 전체의 비주얼 밀도/리듬/구성을 결정하는 상위 전략.

### 2.2 전략 6종

| 전략 | 설명 | 레이어 수 | 파티클 밀도 | 특성 |
|------|------|----------|-----------|------|
| dense | 빽빽한 입자+레이어 | 3~4 | 높음 | 압도적 시각 밀도 |
| breathing | 여백 + 느린 호흡 | 1~2 | 낮음 | 명상적, 미니멀 |
| collision | 충돌/분열 중심 | 2~3 | 중간 | 대비+충격 |
| layered | 배경-중경-전경 분리 | 3 | 중간 | 깊이감 |
| minimal | 단일 포커스 | 1 | 최소 | 집중력 |
| glitch | 글리치+노이즈 | 2~3 | 변동 | 불안정+긴장감 |

### 2.3 장르 → 기본 전략 매핑 (v11: enometa 단일)

| 장르 | 기본 전략 |
|------|----------|
| **enometa** | **enometa** |

> v11: ikeda→enometa 리네이밍. 모든 에피소드가 enometa 전략 사용. (하위호환: "ikeda" → 자동 매핑)

### 2.5 v6 enometa 전략

| 속성 | 값 | 비고 |
|------|-----|------|
| max_semantic_layers | 2 | 최소 레이어 |
| particle_density | 0.0 | 파티클 없음 (Python 레이어가 대체) |
| text_chance | 0.9 | 텍스트 데이터 중심 |
| prefer_vocabs | text_reveal, lissajous | Remotion 텍스트 애니메이션 + Lissajous 곡선 |
| avoid_vocabs | particle_birth/scatter, color_bloom, neural_network, light_source, fractal_crack, data_bar, counter_up | 비데이터아트 배제 |
| inject_vocabs | pixel_grid_rain, pixel_grid_life, pixel_waveform_cascade, **lissajous** | 25% 확률 주입 |

**Python 레이어 9종 — Dual-Source 분류 (v6.1)**:

| 분류 | 레이어 | 역할 |
|------|--------|------|
| **Music** | SineWaveLayer | 오실로스코프 사인파 (sine_interference_values → 파형) |
| **Music** | WaveformLayer | 오디오 파형 직접 렌더링 |
| **Music** | ParticleLayer | 파티클 시뮬레이션 (오디오 에너지 → 물리) |
| **Music** | BytebeatLayer | bytebeat 공식 → 픽셀 (v11 enometa 미사용) |
| **Music** | FeedbackLayer | 자기참조 피드백 루프 (v11 enometa 미사용) |
| **TTS** | BarcodeLayer | UTF-8 바이트 → 바코드 스트라이프 |
| **TTS** | DataStreamLayer | 데이터 스트림 수평 스크롤 |
| **TTS** | TextDataLayer | 터미널 스타일 텍스트 카드 |
| **TTS** | DataMatrixLayer | 악기별 에너지 매트릭스/그리드 |

> Music 레이어는 `arc_energy`에 의해 강도가 변조됨 (기승전결 반영)
> TTS 레이어는 대본 데이터(script_data)에 반응, 아크 영향 없음

**GENRE_LAYER_PRESETS (v11: enometa 전용)**:

| 장르 | Music 리드 | Music 보조 | TTS 강조 | TTS 기본 | blend |
|------|-----------|-----------|---------|---------|-------|
| enometa | SineWave(0.7) | Waveform(0.4)+Particle(0.3) | TextData(0.7) | Barcode(0.6)+DataStream(0.5)+DataMatrix(0.4) | 0.45 |

### 2.4 CLI 사용 (v11)
```bash
py scripts/visual_script_generator.py episodes/epXXX/narration_timing.json \
  --strategy enometa --episode epXXX --title "제목"
# v11: --genre 옵션 제거 (항상 enometa)
```

---

## Phase 3: Vocab 이력 추적 + 중복 회피

### 3.1 개념
최근 N개 에피소드에서 사용된 vocab+variant 조합을 추적하여 중복 회피.

### 3.2 vocab_history.json 구조
```json
{
  "episodes": {
    "ep004": {
      "scenes": [
        {"vocab": "particle_birth", "variant": "default"},
        {"vocab": "counter_up", "variant": null},
        ...
      ],
      "strategy": "dense",
      "genre": "techno",
      "palette": "neon_noir"
    }
  }
}
```

### 3.3 중복 회피 로직
- `lookback_window = 2` (최근 2개 에피소드)
- 최근 사용된 vocab+variant 조합은 후순위로 처리
- 완전 차단이 아닌 가중치 감소 (선택지가 충분할 때만 회피)

---

## Phase 부록: 자막 2줄 그룹핑

### 개념
나레이션 세그먼트를 2줄씩 묶어 화면에 동시 표시.

### scripts/subtitle_grouper.py
- 입력: `narration_timing.json`
- 출력: `subtitle_groups.json`
- 규칙: 인접 세그먼트를 2개씩 묶되, 총 글자수 40자 초과 시 분리

---

## Phase 4: 리액티비티 규칙 (v6 신규, EP005 피드백) — ✅ 구현 완료

### 4.1 문제
현재 오디오 리액티비티(rms 기반)가 너무 민감하여 대부분 프레임이 최대치에 포화됨 → 모든 패턴이 동일 강도로 보임.

### 4.2 semantic_intensity 기반 다이나믹 레인지 — ✅ 구현 완료
- `script_data_extractor.py`에서 세그먼트별 `semantic_intensity` (0-1) 추출 **구현됨**
- `compute_semantic_intensity()` 함수: 4요소 가중합산
- **의미 강도가 기본 레벨 결정**: 조용한 대사 → 작고 어두운 패턴 / 극적인 대사 → 크고 밝은 패턴
- **rms는 미세 변조만**: 기본 레벨 위에서 ±20% 변동
- 공식: `final_level = semantic_intensity × 0.8 + rms_modulation × 0.2`
- `visual_renderer.py`에서 ctx에 `semantic_intensity`, `current_keywords`, `reactive_level` 주입

### 4.3 강도 결정 요소 — ✅ 구현됨
- **VERB_ENERGY** (26개): "폭발하다"(0.95) > "깨어나다"(0.85) > "오르다"(0.6) > "스며들다"(0.3) > "있다"(0.1)
- **EMOTION_INTENSITY** (18개): "공포"(0.9) > "불안"(0.6) > "긴장"(0.4) > "평온"(0.1)
- **문장 구조**: 짧은 문장 = 급박(+0.2), 느낌표 = 강조(+0.15), 물음표 = 탐색(+0.1)
- **byte_variance**: 정규화된 바이트 분산 (0-1)
- **가중합산**: verb(0.35) + emotion(0.3) + sentence(0.2) + byte_variance(0.15)

### 4.4 TTS 다이나믹 비주얼 — ✅ 구현됨

**tts_effects.py** 공유 이펙트 모듈 (10개 함수):
| 함수 | 설명 | 활성 임계값 |
|------|------|-----------|
| `get_scaled_font(base, si)` | si 비례 폰트 크기 | 항상 |
| `intensity_color(rgb, si)` | HSV 밝기/채도 변조 | 항상 |
| `hue_shift_color(rgb, si)` | si 비례 hue 시프트 | 항상 |
| `chromatic_aberration(img, si)` | R/B 채널 오프셋 | si > 0.4 |
| `scanlines(img, si)` | 수평 스캔라인 | si > 0.3 |
| `glitch_blocks(img, si)` | 랜덤 블록 글리치 | si > 0.6 |
| `text_glow(draw, xy, text, font, color, si)` | 텍스트 발광 | si > 0.3 |
| `vertical_wave_distortion(img, si)` | 수직 웨이브 왜곡 | si > 0.5 |
| `scale_pulse(base, si, bpm, frame)` | BPM 동기 맥동 | 항상 |
| `data_click_explosion(draw, xy, si)` | 데이터 클릭 폭발 파티클 | si > 0.7 |

**TTS 레이어 3종 전면 리라이트**:
| 레이어 | 핵심 변경 |
|--------|----------|
| **TextDataLayer** | 폰트 16→48px, 카드 90→200px, intensity 연동 색상/jitter/glow/scanlines/chromatic/glitch/wave/data_click |
| **DataStreamLayer** | 폰트 16→36px, 행별 jitter, 스크롤 si 비례 가속, glow/scanlines/chromatic |
| **BarcodeLayer** | 선폭 2→12px, BPM 맥동, 선높이 60~100%, scanlines/chromatic/glitch |

---

## Phase 부록 2: z-order 시스템 (EP007 신규)

vocab 컴포넌트 간 렌더링 우선순위를 명시적 zIndex로 관리.

| 레이어 | zIndex | 비고 |
|--------|--------|------|
| 일반 vocab | auto | DOM 순서 기본 |
| PixelGrid | 5 | 코드 비주얼 부각 |
| PostProcess | 10 | 최상위 포스트프로세싱 |

## Phase 부록 3: Lissajous vocab (EP007 신규)

수학적 기하학 패턴 — 두 사인파의 위상차로 기하학적 곡선 생성.

| 속성 | 설명 |
|------|------|
| 파일 | `src/components/vocab/Lissajous.tsx` |
| 렌더링 | Canvas 2D, `useCurrentFrame()` 기반 |
| Props | ratioA, ratioB, phaseOffset, color, lineWidth, trailLength |
| 오디오 리액티브 | rms → 선 굵기/글로우, bass → 위상 속도 |
| EMOTION_VOCAB_POOL | neutral_analytical, transcendent_open, awakening_spark (secondary) |
| inject_vocabs | enometa 25% 확률 주입 |

---

*이 문서는 ENOMETA 비주얼 차별화 시스템의 설계 명세서이다.*
*Phase 1~4 + 부록 2~3 구현 완료. 구현 상태는 MEMORY.md에서 추적한다.*

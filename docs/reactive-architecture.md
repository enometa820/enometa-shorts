# 리액티브 아키텍처 — 대본 × 음악 × 비주얼

> 2026-03-10 기준 시스템 현황. 코드 분석 기반.

## 데이터 흐름도

```
script.txt
    │
    ▼
script_data.json ─── SI (Semantic Intensity, 0.05~1.0)
    │                    │                      │
    │              ┌─────┴──────┐               │
    │              ▼            ▼               │
    │         음악 엔진     비주얼 스크립트      │
    │         (약한 반응)   (구조적 반응)        │
    │              │            │               │
    │              ▼            │               │
    │          bgm.wav          │               │
    │              │            │               │
    │              ▼            ▼               │
    │        mixed.wav    visual_script.json    │
    │              │            │               │
    │              ▼            │               │
    │     audio_analysis.json   │               │
    │         (bass/rms/onset)  │               │
    │              │            │               │
    │              ▼            ▼               │
    │         React Vocab    Python 배경        │
    │         (강한 반응)    (SI 기반 intensity) │
    │              │            │               │
    │              └─────┬──────┘               │
    │                    ▼                      │
    │              최종 영상 (MP4)               │
    └───────────────────────────────────────────┘
```

---

## 세 경로 요약

### 경로 1: 대본 → 음악 (약함)

| 데이터 소스 | 파라미터 | 실제 효과 |
|------------|---------|----------|
| SI → `si_modulation` | 마스터 볼륨 | 0.95~1.00 (±5%) |
| SI → `si_gate` | 연속 악기(드론/패드) 볼륨 | 0.25~1.0 |
| SI → Sine Interference | 변조율 | 20Hz~200Hz |
| SI → FM Bass | 드라이브 | 1.5~4.5 |
| SI → 스터터 | 분할 속도 | 4분음표~32분음표 |
| SI → Adaptive Song Arc | climax 위치 | 구조적 결정 |

**SI가 바꾸지 못하는 것**: BPM, 레이어 ON/OFF, 패턴 시퀀스, 멜로디 음정, 드럼 기본 구조 — 이것들은 ep_seed + 장르 스펙(ARRANGEMENT_TABLE, _GENRE_SPECS)이 결정.

**한계**: SI의 음악 영향은 대부분 볼륨 변조(±5%, 게이트)에 집중. CLAUDE.md의 "에너지는 볼륨이 아닌 레이어 추가/제거로" 원칙과 충돌. v16에서 의도적으로 SI 역할이 축소됨 — 코드 주석: "ARRANGEMENT_TABLE이 에너지 주도, SI는 마스터 레벨만".

---

### 경로 2: 대본 → 비주얼 (구조적)

| 데이터 소스 | 파라미터 | 실제 효과 |
|------------|---------|----------|
| SI → `build_scene()` | 레이어 개수 | 1개(SI=0.25) ~ 3개(SI=0.75+) |
| SI → reactivity | 오디오 반응 감도 | rms_scale 0.3(low) ~ 1.2(max) |
| SI → `promote_strategy_by_si()` | 비주얼 전략 | breathing → enometa → dense |
| SI → ShapeMotion | 도형 개수/속도 | 1~2개, 속도 0.7~1.5 |
| SI → `SI_INTENSITY_SCALE` | Python 배경 레이어 intensity | 레이어별 개별 곡선 |

**SI가 바꾸지 못하는 것**: Vocab 종류 선택(text_reveal vs symbol_morph 등), 팔레트 색상, 감정(emotion) 분류 — 이것들은 전략/감정 감지/장르 매핑이 결정.

**강점**: SI가 **전략 자체를 교체**함 (si≥0.80 → breathing→enometa, si≥0.85 → enometa→dense). 이것은 12개 이상의 파라미터가 동시에 바뀌는 구조적 변화.

---

### 경로 3: 음악 → 비주얼 (가장 활발)

**데이터 소스**: `mixed.wav` → `audio_analyzer.py` → `audio_analysis.json`

프레임별 추출 데이터:
- `bass` (0~1): 저주파 20~250Hz 에너지
- `mid` (0~1): 중주파 250~4000Hz
- `high` (0~1): 고주파 4000~20000Hz
- `rms` (0~1): 전체 볼륨
- `onset` (bool): RMS 급변 감지 (임계값 0.15)

| 컴포넌트 | bass | rms | onset |
|---------|------|-----|-------|
| **TextReveal** | 웨이브 진폭 (+40px) | 글로우 크기 (+25~50) | 글리치 발동 (80%) |
| **PostProcess** | 비네트 강도 (+0.3) | 스캔라인 (+0.15), 플래시 강도 | 흰색 플래시 + CRT 티어링 |
| **Lissajous** | 위상 변조, 교차점 수 | 선 굵기 (+3), 트레일 알파 | 교차점 강조 |
| **PixelGrid** | 활성화 범위 (×0.6) | 패턴 충전 (×0.5) | 충격파 |
| **DataBar** | 링 크기 펄스 (+5px) | — | — |

**이 경로가 가장 체감되는 이유**: 프레임 단위(30fps) 실시간 반응. 킥→플래시, 베이스→픽셀 채움, onset→글리치. 시청자가 "음악에 맞춰 화면이 반응한다"고 느끼는 건 이 경로 덕분.

---

## SI (Semantic Intensity) 계산 방식

```
SI = 동사 에너지(30%) + 감정어 강도(30%) + 문장 구조(20%) + 데이터 밀도(20%)
```

- **동사 에너지**: VERB_ENERGY 룩업 97개 어간 ("폭발"→0.9, "존재하"→0.1)
- **감정어 강도**: EMOTION_INTENSITY 룩업 100+개 ("공포"→0.9, "고요"→0.1)
- **문장 구조**: 짧은 문장(+0.3), 느낌표(+0.15), 물음표(+0.1)
- **데이터 밀도**: 숫자+과학용어 비율

범위: 0.05~1.0. 저장: `script_data.json` → `segments[i].analysis.semantic_intensity`

---

## 체감도 비교

| 경로 | 체감도 | 이유 |
|------|--------|------|
| 대본→음악 | **약** | 볼륨 ±5%, 음색 미세 변화. 대부분 인지 불가 |
| 대본→비주얼 | **중** | 레이어 수/전략 변화는 구조적이나, 씬 단위라 전환 빈도 낮음 |
| 음악→비주얼 | **강** | 프레임 단위 실시간 반응. 킥/베이스/onset이 시각적 이벤트로 직결 |

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `scripts/script_data_extractor.py` | SI 계산 (compute_semantic_intensity) |
| `scripts/enometa_music_engine.py` | SI → 음악 변조 (_build_si_envelope, _build_si_gate) |
| `scripts/visual_script_generator.py` | SI → 비주얼 구조 (build_scene, promote_strategy_by_si) |
| `scripts/visual_renderer.py` | SI → Python 배경 intensity (SI_INTENSITY_SCALE) |
| `scripts/audio_analyzer.py` | mixed.wav → audio_analysis.json |
| `src/hooks/useAudioData.ts` | audio_analysis.json → React 컴포넌트 |
| `src/VisualSection.tsx` | Vocab 컴포넌트에 audio 데이터 전달 |

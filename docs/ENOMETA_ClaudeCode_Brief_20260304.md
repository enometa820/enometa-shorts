# ENOMETA Shorts Pipeline — Claude Code 실행 기획안 (2026-03-04)

> **역할**: Brief=실전 매뉴얼 (CLI 명령, 검증 체크리스트). 설계도는 SNAPSHOT 참조.
> 이 문서를 Claude Code에 전달하면 에피소드 제작을 시작할 수 있다.
> 상세 시스템 문서: ENOMETA_SYSTEM_SNAPSHOT_20260304.md 참조
> 음악 엔진 상세: ENOMETA_Music_Engine_Spec_20260304.md 참조
> **last_updated**: 2026-03-04 — v11 패턴 엔진: ikeda→enometa 리네이밍, DRUM_PATTERNS 10종, 바 카운팅+필/드롭, SAW_PATTERNS 로테이션, 호흡 시스템, SI 80~105%, si_gate min 0.25

---

## 프로젝트 개요

> 상세: SYSTEM_SNAPSHOT Sec.1 참조

대본 + 제목만 입력하면 Claude Code가 나머지 전부를 처리한다.
**핵심**: 3중 리액티브 비주얼 (시간 x 오디오 x 의미), enometa 단일 장르 (대본 리액티브 댄스 뮤직), Hybrid 전용

---

## 기술 스택

| 역할 | 도구 | 비고 |
|------|------|------|
| 영상 프레임워크 | Remotion (React) | 코드 기반 영상 생성, CPU |
| TTS 나레이션 | Edge-TTS | 무료, ko-KR-SunHiNeural |
| BGM 생성 | enometa_music_engine.py v11 | Pure Python, enometa 10레이어 + 패턴 엔진(DRUM_PATTERNS/SAW_PATTERNS) + 호흡 + SI 변조(80~105%) |
| 비주얼 엔진 | Canvas 2D + SVG (Remotion) + Python (numpy+Pillow) | Hybrid: Python 배경 + Remotion 오버레이 |
| 오디오 분석 | numpy FFT | 프레임별 bass/mid/high/rms/onset |
| 오디오 믹싱 | ffmpeg | narration 90% + BGM 100%, output=max(nar,bgm), loudnorm -14 LUFS, 엔드카드 BGM 자동 연장 |
| 대본 데이터 | script_data_extractor.py | 숫자/화학물질/바이트 인코딩 + **semantic_intensity** (v11.1: VERB 101개+EMOTION 68개+SCIENCE 85개+CHEM 19개+BODY 30개) + custom_dictionary.json 자동 로드 + 미등록 단어 감지 |
| 비주얼 스크립트 | visual_script_generator.py | 대본+장르 → 씬 → 감정 → vocab 자동 매핑 |
| 대본 분석 | Claude Code 자체 | Claude Max 포함, API 비용 없음 |

---

## 파이프라인 실행 순서

### 사전 단계: 글쓰기 스킬 v11 워크플로우
```
[STEP 0] 주제 추천 → 3~5개 (도메인 교차점 + 핵심 팩트 + 추천 이유) — "글쓰기 시작하자" 시 자동
[STEP 1] 대본 작성 → 본문 + 시스템 최적화 점수(100점) 자동 첨부 (제목/음악 제안 금지)
[STEP 2] ★ 글 컨펌 게이트 ★ → 사용자 명시적 승인 대기
         승인: "좋아/컨펌/OK/확정/진행해"
         수정: 수정 후 STEP 1 재제출 (재채점)
         ⚠ 컨펌 없이 아래 제작 단계 진행 절대 금지
[STEP 3] 제목 5개 제시 → 사용자 선택
[STEP 4] ★ publish.md 생성 ★ — 제목 선택 직후, 제작 파이프라인 전
         → episodes/epXXX/publish.md (제목 / 대본 / 설명란 / 고정댓글 / 해시태그)
[STEP 5] 제작 파이프라인 진행
```

### 제작 파이프라인 (컨펌 후)
```
입력: episodes/epXXX/narration_timing.json (대본 세그먼트 포함) + title

단일 명령으로 전체 자동 실행:
  py scripts/enometa_render.py episodes/epXXX --title "에피소드 제목" --palette phantom

내부 단계 (자동):
[2] TTS 생성          → narration.wav + narration_timing.json 업데이트 (Edge-TTS)
[3] 대본 데이터 추출  → script_data.json (semantic_intensity / data_density / numbers)
[4] 비주얼 스크립트   → visual_script.json (SI 기반 reactivity/max_layers 자동 조절)
[5] BGM 생성          → bgm.wav + bgm_raw_visual_data.npz (v11: 패턴 엔진 + 10레이어 + 호흡 + SI 80~105%)
[6] 오디오 믹싱       → mixed.wav (narration 90% + BGM 100%, output=max(nar,bgm), loudnorm -14 LUFS)
[7] Python 비주얼     → frames/*.png (SI 기반 레이어 강도 동적 조절)
[8] Remotion 합성     → output.mp4 (hybrid: Python 배경 + vocab 오버레이 + 제목/자막)

출력: 1080x1920 MP4

특정 단계만 실행:
  py scripts/enometa_render.py episodes/epXXX --title "제목" --step bgm
  (step: tts | script_data | visual_script | bgm | mix | python_frames | render)

강제 재실행:
  py scripts/enometa_render.py episodes/epXXX --title "제목" --force
```

---

## 비주얼/음악/팔레트 상세

> 24개 vocab 컴포넌트 목록: SYSTEM_SNAPSHOT Sec.4 참조
> 음악 엔진 악기 26종 + 합성법 10종: Music_Engine_Spec 참조
> 컬러 팔레트 8종: SYSTEM_SNAPSHOT Sec.7 참조
> visual_script_generator가 자동 선택. v11: enometa 팔레트 기본 + PixelGrid/PixelWaveform 25% 확률 주입
> `--palette` 옵션으로 다른 팔레트 선택 가능 (8bit vocab 색상도 자동 연동)

---

## 에피소드 제작 실행

### 통합 실행 (권장)

```bash
# 전체 파이프라인 단일 명령
# 전제: episodes/epXXX/narration_timing.json 존재 (대본 세그먼트 포함)
py -X utf8 scripts/enometa_render.py episodes/epXXX \
  --title "에피소드 실제 제목" \
  --palette phantom \
  --episode epXXX

# 특정 단계만 재실행
py -X utf8 scripts/enometa_render.py episodes/epXXX --title "제목" --step bgm
py -X utf8 scripts/enometa_render.py episodes/epXXX --title "제목" --step python_frames

# 기존 파일 강제 덮어쓰기
py -X utf8 scripts/enometa_render.py episodes/epXXX --title "제목" --force
```

### 개별 실행 (디버깅용)

```bash
# [TTS] Edge-TTS (Chatterbox 절대 금지)
py -X utf8 scripts/generate_voice_edge.py \
  episodes/epXXX/narration_timing.json \
  episodes/epXXX/narration.wav

# [script_data] 대본 데이터 추출
py -X utf8 scripts/script_data_extractor.py \
  episodes/epXXX/narration_timing.json
# → semantic_intensity 0.1~0.9 범위 분포 확인 필수
# → 미등록 단어 감지: --update-dict 옵션으로 사전 추가

# [visual_script] SI 기반 vocab/reactivity/max_layers 자동 결정
py -X utf8 scripts/visual_script_generator.py \
  episodes/epXXX/narration_timing.json \
  episodes/epXXX/visual_script.json \
  --episode epXXX --title "에피소드 실제 제목" --palette phantom

# [BGM] v11 enometa 패턴 엔진 (--from-visual, --export-raw 필수)
py -X utf8 scripts/enometa_music_engine.py \
  episodes/epXXX/visual_script.json \
  episodes/epXXX/bgm.wav \
  --from-visual --export-raw \
  --script-data episodes/epXXX/script_data.json \
  --episode epXXX
# → 패턴 전환 로그 확인 (바별 drum_pattern/fill/drop 이벤트)
# --arc: narrative(기승전결) | crescendo | flat | adaptive — 기본 narrative

# [python_frames] SI 기반 레이어 강도 동적 조절
py -X utf8 scripts/visual_renderer.py \
  episodes/epXXX --genre enometa
# → v11: SI_INTENSITY_SCALE 실시간 적용 (si 높을수록 Particle/Waveform 강해짐)

# [mix] 오디오 믹싱 (narration 90% + BGM 100%, 엔드카드 BGM 연장, loudnorm -14 LUFS)
py -X utf8 scripts/audio_mixer.py \
  episodes/epXXX/narration.wav \
  episodes/epXXX/bgm.wav \
  episodes/epXXX/mixed.wav

# [render] Remotion 합성 (Root.tsx durationInFrames 업데이트 후)
npx remotion render src/index.tsx EnometaShorts \
  episodes/epXXX/output.mp4 --concurrency=2
```

---

## 업로드 메타데이터 생성 (publish.md)

**제목 선택 직후** (제작 파이프라인 전) `episodes/epXXX/publish.md` 생성.
구성: **제목 / 대본 / YouTube 설명란 / 고정 댓글 / 해시태그** 5개 섹션만.

```markdown
# EPXXX — "에피소드 제목"

## 제목
에피소드 제목

## 대본
(확정된 전체 대본 텍스트)

## YouTube 설명란
(2~3문장. 핵심 메시지 압축. "왜 봐야 하는가"에 답하는 문장)

─────────────────────────
ENOMETA | 데이터아트 × 철학
존재와 사유, 그 경계를 초월하다

대본의 텍스트는 바이트 시퀀스와 주파수 스펙트럼으로 분해됩니다
추출된 의미 강도(Semantic Intensity)가
음악의 텍스처 밀도와 비주얼의 파티클 거동을 실시간으로 결정합니다
모든 프레임은 시간 × 오디오 × 의미의
3중 리액티브 시스템으로 생성됩니다

코드로 쓰는 철학. 데이터로 그리는 존재론.

## 고정 댓글
(대본에서 가장 강한 문장 1~2줄 + 시청자 질문 1개)

─────────────────────────
ENOMETA | 데이터아트 × 철학
존재와 사유, 그 경계를 초월하다

대본의 텍스트는 바이트 시퀀스와 주파수 스펙트럼으로 분해됩니다
추출된 의미 강도(Semantic Intensity)가
음악의 텍스처 밀도와 비주얼의 파티클 거동을 실시간으로 결정합니다
모든 프레임은 시간 × 오디오 × 의미의
3중 리액티브 시스템으로 생성됩니다

코드로 쓰는 철학. 데이터로 그리는 존재론.

## 해시태그
#태그1 #태그2 #태그3 #태그4 #태그5
```

### 태그 규칙
- 주제 기반 **5개만** (카테고리 상위)
- **절대 포함 금지**: `#쇼츠` `#shorts` `#ENOMETA` `#이노메타` `#데이터아트`

### 고정 멘트 규칙
- 설명란/고정댓글 각각 본문 아래 `─────────────────────────` 구분선 후 삽입
- 고정 멘트 문구 변경 불가

---

## v11 검증 체크리스트

```
□ script_data.json에 segments[].semantic_intensity 필드 존재 (0.1~0.9 분포)
□ BGM 생성 로그에 "SI modulation: range X.XX~X.XX" 확인 (v11: 0.80~1.05, v10보다 넓은 범위)
□ BGM 생성 로그에 "Tempo curve: XXX~XXX BPM" 확인 (변화 없으면 실패)
□ BGM 생성 로그에 드럼 패턴 전환 이벤트 확인 (bar별 pattern/fill/drop)
□ Python 렌더링 프레임에서 조용한 대사(si≈0.2)↔극적 대사(si≈0.9) 시각 차이 확인
  - SineWaveLayer: si 낮을 때 강하고 si 높을 때 약해짐 (배경 역할)
  - ParticleLayer: si 높을 때 폭발적 (si^1.5 비례)
  - TextDataLayer(0.95)/BarcodeLayer(0.65): v10 상향된 intensity 적용
□ visual_script.json 씬별 reactivity 값 확인
  - si≥0.88 구간 → "max" reactivity
  - si≤0.25 구간 → "low" reactivity + layers=1
□ visual_script.json TextReveal position에 "bottom" 없음 확인 ("upper"/"center"/"top"만 허용)
□ mixed.wav 음량 확인: -14 LUFS 근처, TP 최대 -1.5dB (loudnorm 정상 작동)
□ Remotion 자막: SubtitleSection 문장 단위 표시, 35자 초과 시 마침표 분할, smartLineBreak(18), fadeIn/Out 0.2s
□ Remotion 타이포: TextReveal 4모드(typewriter/wave/glitch/scatter) 색상/크기 다양성 확인
□ Remotion ShapeMotion: 비주얼 영역(y=370~1450) 내 도형 표시, emotion별 패턴 작동 확인
□ Remotion z-order: PixelGrid(zIndex 5) 다른 vocab 위에 부각, PostProcess(zIndex 10) 최상위
□ 엔드카드: BGM이 마지막까지 이어지는지 확인 (output_duration=max(nar,bgm))
□ 엔드카드: 태그라인 가독성 (fontSize 48, fontWeight 700, 스태거+밑줄+파티클)
□ Root.tsx calculateMetadata: durationInFrames = (audioAnalysis.duration_sec + 6) × 30 자동 계산 확인
```

---

*이 기획안을 Claude Code에 전달하면 에피소드 제작이 시작된다.*

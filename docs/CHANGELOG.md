# ENOMETA 시스템 변경 이력

> 시스템 변경 시 반드시 이 파일에 기록한다.
> 빠진 문서가 있으면 즉시 보인다.

---

## 2026-03-08 — SymbolMotion: 품사 기반 추상 도형 모션그래픽

### Added
- `src/components/vocab/SymbolMotion.tsx`: 키워드 품사(POS)에 따라 추상 도형으로 시각화하는 새 vocab 컴포넌트. noun→육각형, verb→화살표, adjective→물결, science→동심원, philosophy→이중원. 오디오 리액티브 + 라벨 표시
- `scripts/visual_script_generator.py`: `symbol_morph` vocab 파라미터 생성 + `_map_pos_type()` 품사 매핑 함수. 40% 확률로 text_reveal 대신 symbol_morph 사용
- `scripts/visual_script_generator.py`: `script_data_keywords`에 품사 타입 정보 포함 (`{text, type}` 딕트 리스트로 변경)

### Changed
- `src/components/VisualSection.tsx`: VOCAB_MAP에 `symbol_morph` 등록

---

## 2026-03-08 — 다양성 시스템 v19 + 고정화 버그 수정

### Fixed
- `scripts/enometa_music_engine.py`: `seq_config`가 `music_script.json`에 누락되어 모든 에피소드가 seed 42로 동일한 드럼/음색/패턴을 사용하던 치명적 버그 수정. ep_seed 기반 `derive_episode_sequences()` → `dataclasses.asdict()` → metadata 포함
- `scripts/enometa_music_engine.py`: fallback seed 42 → episode_id MD5 해시로 변경 (안전장치 강화)
- `scripts/visual_script_generator.py`: `_MOOD_TO_VISUAL_GENRE` 매핑을 README와 통일 (microsound→cooper, techno→data, industrial→data)
- `scripts/enometa_render.py`: `--visual-mood` choices에서 deprecated `ikeda` 제거, `enometa` 추가

### Added
- `scripts/visual_strategies.py`: `promote_strategy_by_si()` 함수 — SI≥0.80에서 전략 자동 승격 (breathing→enometa→dense)
- `scripts/visual_strategies.py`: genre→strategy 동적 매핑 (cooper→breathing, abstract→collision, data→dense)
- `scripts/visual_script_generator.py`: 씬 빌드 루프에서 SI 기반 전략 승격 적용

### Changed
- `scripts/visual_strategies.py`: "enometa" 전략 제약 완화 — avoid_vocabs 15→7개, max_semantic_layers 2→3, prefer_vocabs 다양화
- `src/components/TitleSection.tsx`: `text-wrap: balance` 추가 (2줄 제목 균등 분배)
- `src/components/LogoEndcard.tsx`: 태그라인 줄 간격 gap 8→20
- `.claude/skills/enometa-produce.md`: 옵션 수집 시 전체 테이블 의무 표시

---

## 2026-03-08 — EP011 추가 + script_data_extractor 버그 수정

### Fixed
- `scripts/script_data_extractor.py`: kiwipiepy가 "억", "만" 등 한국어 숫자 단위를 `SN` 태그로 분류할 때 `float()` 변환 실패하던 문제 수정 (2곳 — `analyze_sentence`, keyword loop)

### Added
- `src/ep011Script.ts`: EP011 데이터 import/export
- `src/Root.tsx`: EP011 Composition 등록

---

## 2026-03-08 — Terra Vision 3D 비주얼 시스템 추가

### Added
- `@remotion/three` + `three` 패키지 설치 — Remotion에서 Three.js 3D 렌더링 지원
- `src/components/vocab/three/ThreeVocabWrapper.tsx`: ThreeCanvas + 조명 공통 래퍼
- `src/components/vocab/three/TerraGlobe.tsx`: 로우폴리 와이어프레임 지구 회전 + 데이터 포인트 (`terra_globe`, `terra_globe_data`)
- `src/components/vocab/three/TerraFlythrough.tsx`: 무한 와이어프레임 터널 / 줌인 효과 (`terra_flythrough`, `terra_tunnel`)
- `src/components/vocab/three/TerraTerrain.tsx`: 높이맵 기반 3D 지형 + 데이터 바 (`terra_terrain`, `terra_terrain_bars`)
- `scripts/visual_script_generator.py`: VOCAB_CATEGORIES에 `"terra"` 카테고리 + EMOTION_VOCAB_POOL 4개 감정에 terra vocab 배치 + generate_vocab_params() terra 파라미터 + 씬당 terra_* 최대 1개 제약

### Changed
- `src/components/VisualSection.tsx`: VOCAB_MAP에 6개 terra 키 등록
- `CLAUDE.md`: vocab 목록에 3D/Terra 카테고리 추가, 의존성 목록 업데이트

---

## 2026-03-07 — DataBar 애니메이션 강화 + TextDataLayer 가시성 개선

### Changed
- `src/components/vocab/DataBar.tsx`: 오디오 리액티브 대폭 강화
  - bass bounce: `bass * 3` → `bass * 14` (4.7배)
  - **onset surge**: onset 감지 시 바 길이 +7% 순간 서지
  - **glow**: `rms*20` → `rms*40 + (onset ? +30)` — onset 플래시
  - **scan sweep**: 바 채워지는 선단에 흰 빛이 흐르는 스위프 효과
  - **선단 글로우 닷**: 바 끝 흰 점 + bass 박자 연동 pulse
- `scripts/visual_layers/text_data_layer.py`: 카드 가시성 개선
  - **카드 배경 fill 추가**: outline만 → 어두운 솔리드 fill (컬러 틴트) — 배경에 묻히지 않음
- `scripts/visual_renderer.py`: enometa preset TextDataLayer intensity `0.95 → 1.2`

---

## 2026-03-07 — 오디오 1:1 균형 + 고정 해시태그 정책 + 고정 댓글 개선

### Changed
- `scripts/audio_mixer.py`: narration_volume 0.90 → **1.0** (BGM과 1:1 균형, TTS 묻힘 현상 해소)
- `.claude/skills/enometa-publish.md`: 태그 정책 개정
  - **완전 금지**: `#쇼츠` `#shorts` `#ENOMETA` `#이노메타` (어디에도 사용 불가)
  - **고정 해시태그** 신설: `#데이터아트` `#전자음악` `#오디오비주얼` → 해시태그 섹션 항상 8개
- `episodes/ep010/publish.md`: 고정 댓글 1단/2단/3단 구조로 전면 개선 (인용→맥락→성찰 질문)

---

## 2026-03-07 — NLP 강화: soynlp 전처리 + kiwipiepy 사전 확장 + 품사별 색상

### Added
- `scripts/script_data_extractor.py`: soynlp `repeat_normalize` 전처리 — 텍스트 노이즈 정규화 (`pip install soynlp`)
- `scripts/script_data_extractor.py`: `_KIWI_USER_WORDS` 50+ 도메인 용어 확장 (뇌과학 구조/신경전달물질, 철학 인식론/윤리, 데이터사이언스, 사회/인문학 — kiwipiepy 미등록 복합명사 사전 등록)
- `scripts/visual_layers/text_data_layer.py`: 품사 타입별 카드 색상 분기 — noun/verb/science/chemical/body/number 각각 다른 hue 채널 (`_TYPE_HUE_SHIFT` 테이블, `type_color()` 함수)

### Changed
- `scripts/visual_layers/text_data_layer.py`: 카드 `kw_color` → `type_color(kw_type, kw_intensity)` 로 교체 (기존 accent 단색 → 품사별 hue 분기)

---

## 2026-03-07 — TextDataLayer 강화 + 비주얼 다양성 + 엔드카드 개선

### Added
- `scripts/visual_layers/text_data_layer.py`: 타이핑 애니메이션(30글자/초) + BPM 동기 커서(`▌`) + 카운트업 애니메이션(TOKENS/BYTES/SI/FREQ/VAR, 0.4s/0.5s)
- `scripts/visual_renderer.py`: `GENRE_LAYER_PRESETS` v9 — visual_mood별 Python 레이어 프리셋 4종 (enometa/cooper/abstract/data) 독립 구성
- `scripts/enometa_render.py`: `step_python_frames`에 `visual_mood` 파라미터 연동 → `--visual-mood` 옵션이 Python 배경 프레임에도 반영

### Changed
- `scripts/visual_layers/text_data_layer.py`: `SI_INTENSITY_SCALE["TextDataLayer"]` 0.70+si*0.30 → 0.88+si*0.12 (기본 불투명도 강화)
- `src/components/LogoEndcard.tsx`: 태그라인 기본값 `"존재와 사유\n그 경계를 초월하다"` — `\n` 줄바꿈 지원, 멀티라인 스태거 애니메이션

---

## 2026-03-07 — v18 장르 시스템 오버하울 + 파이프라인 버그 수정

### Added
- `scripts/enometa_music_engine.py`: 3개 신규 합성 함수 — `tape_delay()` (dub), `distorted_kick()` (industrial), `chord_stab()` (dub)
- `scripts/script_data_extractor.py`: `music_mood`, `drum_mode` 필드를 narration_timing → script_data로 전달 (이전 누락 버그 수정)
- `scripts/visual_script_generator.py`: `mood_override` 파라미터 추가 (visual_mood가 씬 레벨까지 전달)

### Changed
- **장르 리네이밍**: raw→acid, ikeda→microsound, experimental→IDM, chill→dub, intense→industrial (하위호환 자동 변환)
- `scripts/enometa_music_engine.py`: 9개 `_MOOD_LAYERS` 전면 재설계 — 장르별 고유 악기+리듬+BPM 정체성 확보
- `scripts/enometa_music_engine.py`: `generate()` 전 렌더러 게이팅 확장 — bass_drone/sine/pulse_train/ultrahigh/gate_stutter/gap_burst 장르별 ON/OFF
- `scripts/enometa_music_engine.py`: 장르별 BPM 범위 (ambient 72~90 ~ industrial 138~155)
- `scripts/enometa_render.py`, `scripts/gen_timing.py`: CLI choices 9장르 반영
- `CLAUDE.md`, `.claude/skills/enometa-produce.md`: 장르 목록 최신화

---

## 2026-03-06 — EP009 피드백 반영: 엔드카드 버그 수정 + 비주얼 개선

### Fixed
- `src/Root.tsx`: calcMeta `Math.ceil` → `Math.round` 기반 계산 (엔드카드 이후 1프레임 flash 제거)
- `src/components/LogoEndcard.tsx`: 태그라인 `right: 120` (YouTube Shorts 우측 UI 안전 영역 확보)

### Changed
- `src/components/LogoEndcard.tsx`: fadeIn 0.1s → 1.5s (엔드카드 진입 여운)
- `src/EnometaShorts.tsx`: Audio volume 콜백 추가 — 엔드카드 구간에만 BGM 1→0 페이드 아웃
- `scripts/visual_script_generator.py`: text_reveal 색상 풀 개선 (어두운 glow/colors[0] 제거 → 가시성 보장)
- `.claude/skills/enometa-feedback.md`: 음악 세부 항목 + 시스템 이슈 질문 추가

---

## 2026-03-06 — Claude 워크플로우: pre-commit hook + produce 스킬 개선

### Added
- `.claude/hooks/pre_commit_check.py`: feat:/fix:/refactor: 커밋 전 CHANGELOG staged 확인 강제 + decisions remind
- `.claude/settings.json`: PreToolUse hook 연결 (Bash 도구 → pre_commit_check.py)

### Changed
- `.claude/skills/enometa-produce.md`: 인터랙티브 모드(--interactive) → 대화로 옵션 수집 후 비인터랙티브 실행 방식으로 변경

---

## 2026-03-06 — v16: kiwipiepy 형태소 분석 + TTS 실측 타이밍 + 음악 엔진 개선

### Added
- `kiwipiepy` 형태소 분석 도입: `tokenize_korean()` 정규식 간이 토크나이저 → kiwipiepy 기반
  - 동사/명사 오분류 근본 해결 ("저랬을까" → verb, "전전두엽" → 단일 명사)
  - kiwi 사용자 사전에 ENOMETA 전문용어 등록 (전전두엽, 메타인지 등)
  - ENOMETA 도메인 사전(CHEMICALS/BODY_PARTS/SCIENCE_TERMS) 오버라이드 유지
- 다운비트 사운드 7종: noise_hit, ping_pong, sine_pop, sub_boom, open_hat, crash, reverse_crash
  - 마디 계층 배치: 매 마디(noise/ping교대) → 2마디(sine_pop) → 4마디(crash+boom+ohat) → 16마디(reverse_crash)
- `gen_timing.py`: TTS 실측 기반 연속 배치 (마디 snap 제거), paragraph_breaks[] 필드
- 음악 무드 9종: techno 추가 (4-on-the-floor + TB-303 arp + FM bass)
- `visual_script_generator.py`: TextReveal 동사 어미 필터(`_verb_suffixes`)

### Changed
- 콜앤리스폰스 비활성: 2바 주기 75%↔100% 볼륨 교대 제거 (v16 볼륨 고정 원칙)
- 마스터 페이드 제거: 2s fade-in + 3s fade-out → 5ms anti-click만
- `Root.tsx` calcMeta: `audioAnalysis.duration_sec` → `lastScene.end_sec + endcard` 기준
  (BGM이 엔드카드보다 길어도 영상이 정확히 엔드카드에서 종료)
- BGM 길이 제한: `_plan_song_structure` strict bar count + `total_dur` 캡핑

### Dependencies
- `kiwipiepy` 0.22.2 추가 (pip install kiwipiepy)

---

## 2026-03-05 — v15: 마디 동기화 + 음악 무드 8종 + visual_mood 4종 + 시스템 다이어트

### Added
- `scripts/gen_timing.py`: TTS 실측 → ceil(actual/SEC_PER_BAR) 마디 snap → narration_timing.json. 빈줄=드롭, drops[] 필드 기록
- `scripts/enometa_music/tables.py`: MUSIC_MOOD_PRESETS 8종(ambient/ikeda/experimental/minimal/chill/glitch/raw/intense), CRASH_RULES, FILL_RULES, GAP_FILL_INTENSITY
- `scripts/enometa_music/engine.py`: `_insert_gap_events()`, `apply_mood_to_sections()` 메서드
- `scripts/enometa_music_engine.py`: 동일 메서드 + drum 오버라이드 로직
- `scripts/visual_script_generator.py`: VISUAL_MOOD_OVERRIDES 4종(ikeda/cooper/abstract/data), `--visual-mood` CLI 옵션
- `CLAUDE.md`: 커밋 & 푸시 규칙 섹션 추가
- `CLAUDE.md`: v15 시스템 철학 (마디 동기화 3원칙)

### Changed
- `enometa_music_engine.py`: SI 볼륨 변조 0.80+0.25 → 0.85+0.15 (±15% 이내, 레이어 ON/OFF 에너지 주도)
- `enometa_render.py`: gen_timing 스텝 추가, visual_mood/music_mood/drum 파라미터 전달
- `.claude/rules/master-docs.md`: 마스터 문서 3종으로 축소

### Removed
- `docs/ENOMETA_Audiovisual_Reference_20260304.md` (코드로 통합)
- `docs/ENOMETA_Creative_Freedom_Audit_20260304.md` (감사 완료, git 보존)
- `docs/ENOMETA_Music_Engine_Spec_20260304.md` (코드가 진실의 소스)
- `docs/ENOMETA_Visual_Differentiation_Spec_20260304.md` (코드로 통합)
- `scripts/generate_music.py`, `scripts/subtitle_grouper.py` (레거시 제거)

---

## 2026-03-04 — v11 D섹션: 글쓰기 3종 구조 + 도메인 5+5 + SI 커브 7종 + 동적 믹싱

### 글쓰기 스킬 변경

**`skills/enometa-writing.md`** — D-1~D-3a 구현
- **D-1**: "유일한 구조" → 3종 선택 시스템 (A: 3단계 변환 / B: 역순 각성 / C: 이중 나선)
- **D-2**: 5대 → 5+5 도메인 (확장: 물리학/생물학/수학/경제학/예술, 코어 1개 필수)
- **D-3a**: SI 커브 3→7종 (추가: 파동/충격파/계단/미니멀)
- 채점: "3단계 전환"→"구조 설계" 리네이밍, 구조별 채점 기준 추가
- 체크리스트: 구조 선택/도메인 확장/SI 커브 7종 항목 추가

### 코드 변경

**`scripts/enometa_music_engine.py`** — D-3b
- SONG_ARC_PRESETS 4→7종: wave(이중 피크), shockwave(충격→감쇠), staircase(계단식 상승) 추가
- `--arc` CLI 자동 확장 (choices=list(SONG_ARC_PRESETS.keys()))

**`scripts/audio_mixer.py`** — D-4
- `_build_dynamic_bgm_expr()`: script_data SI → ffmpeg 볼륨 수식 (BGM×(1.0-0.15×si))
- `--dynamic-mix` CLI 옵션 (기본 OFF, narration 0.90 절대 고정)
- 2초 스무딩, 나레이션 없는 구간 BGM 100% 유지

### 마스터 문서 5종 최신화

| 문서 | 변경 |
|------|------|
| SYSTEM_SNAPSHOT_20260304 | Song Arc 7종, 오디오 동적 믹싱, 진화 로그 v11-D |
| ClaudeCode_Brief_20260304 | --arc 7종, --dynamic-mix CLI, 검증 체크리스트 |
| Music_Engine_Spec_20260304 | Song Arc 테이블 7종, CLI --arc 확장 |
| Hybrid_Visual_Architecture_20260304 | audio_mixer 동적 믹싱 섹션 |
| Visual_Differentiation_Spec_20260304 | 헤더만 (비주얼 변경 없음) |
| CHANGELOG | 이 항목 |
| MEMORY.md | 글쓰기 v11 D섹션 업데이트 |

---

## 2026-03-04 — v11 패턴 엔진 (창작 자유도 감사 F섹션) + ikeda→enometa 리네이밍

### 코드 변경 (commit 077a291)

**`scripts/enometa_music_engine.py`** — F-0~F-8 전체 구현
- **F-0**: ikeda → enometa 리네이밍 (GENRE_PRESETS, is_ikeda→is_enometa, 하위호환 자동 매핑)
- **F-1**: `snare_drum()` 합성 함수 (톤 바디 200→120Hz + 노이즈 테일 + 어택 클릭) — 합성 함수 10번째
- **F-2**: `DRUM_PATTERNS` 10종 (four_on_floor, offbeat, euclidean_3_8/5_16, minimal, driving, fill_buildup, fill_snare_roll, drop_silence, drop_impact)
- **F-3**: `_render_continuous_rhythm()` 전면 리팩터 — 바 카운팅 + 섹션별 패턴 선택 + 필(4/8바) + 드롭(SI 급상승)
- **F-4**: `SAW_PATTERNS` 확장 (레벨별 2~3패턴) + 4바마다 로테이션
- **F-5**: `_compute_breath_envelope()` — 8/16바 주기 에너지 딥(0.85/0.70), 0.3s 스무딩
- **F-6**: highlight_words → 음악 악센트 (kick×1.5 + snare×1.2)
- **F-7**: Call & Response — 2바 교대 drum/melody gain 엔벨로프 (SI 0.3~0.7)
- **F-8**: 크로스페이드 linear → raised cosine, 0.5s → 1.0s, 15% → 20%
- SI 변조: 0.95+si*0.1 → 0.80+si*0.25 (80~105%)
- si_gate: min 0.45 → min 0.25
- ARP_PATTERNS: 5종 → 10종

**`scripts/enometa_render.py`** — ikeda→enometa
**`scripts/visual_script_generator.py`** — ikeda→enometa
**`scripts/visual_renderer.py`** — ikeda→enometa (_get_ikeda_accent→_get_enometa_accent)
**`scripts/visual_strategies.py`** — ikeda→enometa

### 마스터 문서 5종 최신화

| 문서 | 변경 |
|------|------|
| SYSTEM_SNAPSHOT_20260304 | v10→v11, ikeda→enometa 전체, 합성 함수 10종, 패턴 엔진, 진화 로그 v11 |
| ClaudeCode_Brief_20260304 | v10→v11, 기술 스택 enometa, CLI 예시, 검증 체크리스트 v11 |
| Music_Engine_Spec_20260304 | v10→v11 전면 리라이트 — DRUM_PATTERNS, 바 카운팅, SAW_PATTERNS, 호흡, highlight_words, call&response |
| Hybrid_Visual_Architecture_20260304 | v8→v11, 장르 레지스트리 enometa, GENRE_LAYER_PRESETS |
| Visual_Differentiation_Spec_20260304 | v8→v11, 전략 매핑 enometa, GENRE_LAYER_PRESETS, CLI |
| CHANGELOG | 이 항목 |
| MEMORY.md | v10→v11, 음악 엔진 섹션 전면 갱신 |

---

## 2026-03-04 — EP007 추가 피드백 4건 + Lissajous vocab + 피드백 로그 신설

### 피드백 반영 (F07-09~12)

**`scripts/visual_script_generator.py`**
- TextReveal position `"bottom"` → `"upper"` 교체 (L582, L594)
- Lissajous vocab 파라미터 생성 블록 추가
- ikeda `inject_vocabs`에 `"lissajous"` 추가
- EMOTION_VOCAB_POOL 3개 감정에 `"lissajous"` secondary 추가

**`src/components/vocab/TextReveal.tsx`**
- `"upper"` 위치 추가 (h*0.32), `"bottom"` 안전 클램프 (h*0.55)

**`src/components/vocab/PixelGrid.tsx`**
- 외부 div에 `zIndex: 5` 추가

**`src/components/vocab/PostProcess.tsx`**
- Fragment `<>` → `<div>` 래퍼 (`zIndex: 10`)

**`src/components/LogoEndcard.tsx`**
- 태그라인 전면 강화: 글자별 2프레임 스태거, SVG 밑줄 드로잉, 180개 파티클
- fontSize 30→48, fontWeight 400→700

**`scripts/enometa_music_engine.py`**
- `_build_si_gate()`: 계단 함수 → 연속 함수 (min 0.45, 1.0s 스무딩)

### 신규 컴포넌트

**`src/components/vocab/Lissajous.tsx`** — Lissajous 곡선 vocab
- Canvas 2D, `x=sin(at+δ), y=cos(bt)` 수학적 패턴
- 오디오 리액티브 (rms→선 굵기, bass→위상, onset→교차점 글로우)
- sceneProgress 기반 점진적 복잡도 증가

**`src/components/VisualSection.tsx`**
- VOCAB_MAP에 `lissajous`, `lissajous_complex` 추가

### 문서 신설/업데이트

| 문서 | 변경 |
|------|------|
| `docs/FEEDBACK_LOG.md` | 신규 — 전 에피소드 피드백 통합 로그 |
| `docs/ENOMETA_Audiovisual_Reference.md` | 신규 — 오디오비주얼 아트 레퍼런스 복사 |
| `scripts/feedback_defaults.json` | text_reveal_rules, z_order_rules, si_gate_rules 추가 |
| `episodes/ep007/feedback.json` | F07-09~12 항목 추가 |
| `docs/CHANGELOG.md` | 이 항목 |
| `memory/MEMORY.md` | EP007 추가 교훈 + ikeda 다양성 + si_gate 수정 |

---

## 2026-03-04 — 마스터 문서 5종 전면 최신화 + 날짜 기반 리네이밍 + 규칙 체계 신설

### 마스터 문서 리네이밍

버전 기반(`_v6`) → 날짜 기반(`_YYYYMMDD`) 네이밍으로 전환:

| 이전 파일명 | 새 파일명 |
|------------|----------|
| `ENOMETA_SYSTEM_SNAPSHOT_v6.md` | `ENOMETA_SYSTEM_SNAPSHOT_20260304.md` |
| `ENOMETA_ClaudeCode_Brief_v6.md` | `ENOMETA_ClaudeCode_Brief_20260304.md` |
| `ENOMETA_Music_Engine_Spec_v6.md` | `ENOMETA_Music_Engine_Spec_20260304.md` |
| `ENOMETA_Hybrid_Visual_Architecture.md` | `ENOMETA_Hybrid_Visual_Architecture_20260304.md` |
| `ENOMETA_Visual_Differentiation_Spec.md` | `ENOMETA_Visual_Differentiation_Spec_20260304.md` |

### 마스터 문서 최신화 내용

**SYSTEM_SNAPSHOT**: Vocab 24종 + z-order 시스템 + VOCAB_MAP 38+ + 오디오 파라미터 수정 + LogoEndcard v3 + si_gate 연속함수 + EP007 진화 로그 확장

**ClaudeCode_Brief**: 검증 체크리스트 v10 (TextReveal position/z-order/엔드카드 검증 항목 추가)

**Hybrid_Visual_Architecture**: SubtitleSection fadeIn/Out 0.2s + TextReveal posY 매핑 테이블 + LogoEndcard v3 + z-order 시스템 섹션

**Music_Engine_Spec**: v10.2 si_gate 연속 함수 (min 0.45, 1.0s 스무딩) + 금지 사항 명시

**Visual_Differentiation_Spec**: Lissajous vocab + z-order 부록 + ikeda inject_vocabs 업데이트

### 규칙 체계 신설

**`.claude/rules/master-docs.md`** — 신규
- 마스터 문서 목록 테이블 + 네이밍 규칙
- 최신화 트리거 5가지 조건
- 최신화 체크리스트 (마스터 5종 + 보조 5종)
- 상호 참조 규칙 + 커밋 규칙

### 상호 참조 점검

- 마스터 문서 간 상호 참조: 신규 파일명으로 업데이트 완료
- `memory/MEMORY.md`: 문서 테이블 + 네이밍 규칙 업데이트
- 코드 파일(ts/tsx/py/json): 마스터 문서 참조 없음 (깨짐 없음)
- `CHANGELOG.md` 역사적 기록: 의도적 보존 (과거 파일명 유지)

---

## 2026-03-04 — EP007 피드백 반영: 자막/볼륨/모션 전면 업그레이드

### 코드 변경

**`src/components/SubtitleSection.tsx`** (STEP 1+3 통합)
- **자막 붕괴 수정**: `segmentsToWordCaptions` (단어별 선형 분할) → `segmentsToCaptions` (문장 단위 1:1 매핑)
  - 이유: 단어 간 타이밍 누적 오차 → 페이지 경계 어긋남 + Infinity clamp 미흡 해결
- **페이지 전환 간격**: `combineTokensWithinMilliseconds 1500` → `4000` (2~3문장 자연 묶기)
- **durationInFrames 안전화**: `Infinity` 상한 → `totalFrames` 클램프 추가
- **premountFor={fps}** 추가 (Sequence 사전 로드)
- **4종 모션 패턴 추가** (emotion별 분기):
  - A: 슬라이드 업 — intro, resolution, default (spring translateY)
  - B: 스케일 인 — tension, climax (spring scale)
  - C: 타이프라이터 — awakening (string slice, CSS animation 금지 준수)
  - D: 플래시 컷 — buildup (frame % 기반 opacity/translateX)
- **emotion별 색상/위치/크기 매핑** (EMOTION_COLORS 상수 테이블)

**`scripts/audio_mixer.py`** (STEP 2)
- `narration_volume`: `0.55` → `0.90` (TTS:BGM ≈ 1:1 균형)
- `bgm_volume` 기본값: `1.5` → `1.0`
- 함수 기본값 `0.67` → `0.90` 동기화
- 주석: "narration 55% + BGM 150%" → "narration 90% + BGM 100%"

**`src/components/ShapeMotion.tsx`** (STEP 4 신규)
- emotion별 기하학적 도형 레이어 (EnometaShorts 자막 위에 오버레이)
  - tension: 사각형 테두리 (spring scale + 회전)
  - climax: 원형 펄스 (opacity 파동 + scale, frame % 기반)
  - awakening: 수평선 2개 (좌→우 spring scaleX)
  - intro: 점 3개 stagger 페이드인
- 모든 애니메이션 `useCurrentFrame()` 기반 (CSS animation 금지 준수)

**`src/EnometaShorts.tsx`**
- `ShapeMotion` import + SubtitleSection 하단에 렌더링 추가

**`skills/enometa-publish.md`** (규칙 업그레이드)
- 설명란: 2~3문장 → **5~7문장** (훅/철학/ENOMETA 관점 3단 구조)
- 고정댓글: "1~2줄 + 질문 1개" → **인용 + 맥락 2~3줄 + 질문 1~2개** 3단 구조

**`episodes/ep007/publish.md`** — 새 규칙 소급 적용 (설명란 4문장, 고정댓글 5줄)

### 반영 문서
| 문서 | 반영 내용 |
|------|----------|
| SYSTEM_SNAPSHOT_v6 | Remotion 컴포넌트 섹션 업데이트 (ShapeMotion, SubtitleSection v2) |
| CHANGELOG | 이 항목 |
| MEMORY.md | 오디오 믹싱 절대 규칙 + Remotion 컴포넌트 현황 업데이트 |
| skills/enometa-publish.md | 설명란/고정댓글 가이드라인 풍부화 |
| episodes/ep007/publish.md | 새 규칙 소급 적용 |

---

## 2026-03-04 — EP007 완료 + publish.md 워크플로우 변경

### 에피소드
- **EP007** "알고리즘은 쌓지 않는다. 덜어낸다" — 제작 완료
  - 이진 탐색(컴퓨팅) × 내려놓음의 공포(철학) × 나아감의 패러다임(인문학)
  - 시스템 최적화 점수 98/100 (최고점)
  - custom_dictionary.json 대폭 확장 (탐색/내려놓음/잠식/섀넌 등 신규 어휘)
  - 132.344초, ikeda D_minor 135BPM, 16씬 vocab 11종, SI 0.06~0.61
  - durationInFrames: 4170, highlightWords: ["탐색", "덜어낸다"]

### 시스템 변경
- **publish.md 워크플로우**: 제작 완료 후 → **제목 선택 직후** (제작 파이프라인 전)
  - 구성 단순화: 제목 / 대본 / YouTube 설명란 / 고정 댓글 / 해시태그 5개 섹션만
  - 기존 "제목 후보", "스타일", "키워드 하이라이트" 등 불필요 항목 제거
- **skills/enometa-writing.md**: STEP 4 추가 (제목 선택 직후 publish.md 자동 생성)
- **skills/enometa-publish.md**: 전제 조건 변경 + 템플릿 단순화

### 반영 문서
| 문서 | 반영 내용 |
|------|----------|
| SYSTEM_SNAPSHOT_v6 | EP006/EP007 에피소드 로그, 워크플로우 STEP 5 publish.md 수정, v10 음악 엔진/마스터링, 오디오 믹싱 |
| ClaudeCode_Brief_v6 | 사전 단계 STEP 4 publish.md 추가, 업로드 메타데이터 섹션 전면 개정 |
| CHANGELOG | 이 항목 |
| MEMORY.md | EP007 에피소드 로그, publish.md 절대 규칙 업데이트 |
| skills/enometa-writing.md | STEP 4 publish.md 생성 단계 추가 |
| skills/enometa-publish.md | 전제 조건 + 템플릿 단순화 |
| episodes/ep007/publish.md | EP007 퍼블리시 문서 신규 생성 |

---

## 2026-03-04 — 오디오 믹싱: 사이드체인 덕킹 제거 + narration_volume 0.55

### 코드 변경
- **`audio_mixer.py`**: narration_volume 기본값 `0.67` → `0.55`
  - 이유: 나레이션 구간 대부분(90초+)이 덕킹 상태라 BGM 악기/리듬이 묻힌 문제 해결
  - loudnorm (-14 LUFS)이 TTS/BGM 전체 균형 자동 처리하므로 TTS는 여전히 명확
- **`scripts/enometa_render.py`** `step_mix()`: 사이드체인 덕킹 비활성화
  - `--sidechain narration_timing.json` 옵션 제거
  - 결과: 나레이션 전 구간에서 BGM 리듬/멜로디 존재감 유지
- **`src/components/SubtitleSection.tsx`**: TikTokPage 타이밍 계산 버그 수정
  - `page.durationMs` 기반 → Remotion 공식 `nextPage.startMs` 기반으로 교체
  - 모든 자막이 동시에 표시되던 현상 해결

### 반영 문서
| 문서 | 반영 내용 |
|------|----------|
| MEMORY.md | 오디오 절대 규칙, 음악 엔진 v10 섹션 업데이트 |
| CHANGELOG | 이 항목 |
| ClaudeCode_Brief_v6 | 오디오 믹싱 섹션, mix 개별 실행 명령 |

---

## 2026-03-03 — 음악 엔진 v10 + audio loudnorm + Remotion @remotion/captions + fitText + calculateMetadata

### 코드 변경
- **`enometa_music_engine.py` v9→v10**: 음량 과도 감쇠 3요소 동시 완화
  - SI 변조: `0.7 + si*0.6` → `0.95 + si*0.1` (변동폭 70~130% → 95~105%)
  - density_scale: `si^1.5` (si=0.2→0.7%) → `max(0.6, si)` (최소 60% 보장)
  - tanh drive: `1.2` → `3.0` (더 강한 디스토션 → 실제 음량 증가)
  - RMS target: `-10dB` → `-6dB` (마스터 출력 +4dB)
  - Song arc narrative 에너지 전체 상향: intro 0.25~0.45→0.7~0.9, buildup 0.45~0.85→0.9~1.2, climax 0.85~1.2→1.2~1.5
  - 킥 볼륨: `si_g * 1.2` → `si_g * 2.5`, 하이햇: `si_g * 1.0` → `si_g * 1.8`
  - saw_sequence default 볼륨: `0.4` → `0.7`
- **`audio_mixer.py`**: EBU R128 loudnorm 정규화 추가 + bgm_volume 기본값 상향
  - ffmpeg 필터에 `[mixed]loudnorm=I=-14:TP=-1.5:LRA=11[out]` 추가 (클리핑 방지)
  - bgm_volume CLI default: `1.0` → `1.5`
  - **버그 수정**: `-ar 22050 -ac 1` → `-ar 44100 -ac 2` (22050Hz 모노 → 44100Hz 스테레오)
- **`src/components/SubtitleSection.tsx`**: @remotion/captions 전면 도입
  - `createTikTokStyleCaptions()` — 단어 단위 타이밍 자동 분할
  - `TikTokPage` (durationMs, startMs, tokens) 기반 단어 하이라이트
  - 잘리던 단어 오버플로우 문제 근본 해결
- **`src/components/TitleSection.tsx`**: @remotion/layout-utils fitText 도입
  - `fitText({ text, withinWidth: 920, fontFamily, fontWeight })` → 자동 fontSize
  - 최대 72px 상한 유지 (긴 제목도 자동 축소)
- **`src/Root.tsx`**: calculateMetadata 자동 duration 계산
  - `CalculateMetadataFunction<any>` — `audioAnalysis.duration_sec + endcardDurationSec` 기반
  - EP001~EP006 모든 Composition에 `calculateMetadata={calcMeta}` 적용
- **`scripts/visual_renderer.py`**: TTS 레이어 SI_INTENSITY_SCALE 상향
  - 기존: TextData 0.70, DataStream 0.50, Barcode 0.40
  - 신규: TextData 0.95, DataStream 0.75, Barcode 0.65

### 반영 문서
| 문서 | 반영 내용 |
|------|----------|
| MEMORY.md | 음악 엔진 v9→v10, Remotion 변경, EP006 완료 로그 |
| CHANGELOG | 이 항목 |
| ClaudeCode_Brief_v6 | last_updated, bgm_volume 1.5, loudnorm, @remotion/captions, fitText |
| Music_Engine_Spec_v6 | v10 변경사항 (SI 변조/density/마스터링/song arc/킥하이햇/saw) |

---

## 2026-03-03 — 파이프라인 v2 + SI 비주얼 연동 + 음악 엔진 레이어 10

### 코드 변경
- **`enometa_render.py` v2 전면 재작성**: 단일 명령 통합 파이프라인
  - 구버전: Chatterbox TTS + ACE-Step BGM + 개별 CLI 명령 조합
  - 신버전: `py scripts/enometa_render.py <episode_dir> --title "제목" --palette phantom`
  - 내부 단계: TTS → script_data → visual_script → BGM → mix → python_frames → Remotion
  - `py` 명령 통일 (Python311 하드코딩 제거), Chatterbox/ACE-Step 완전 제거
- **`enometa_music_engine.py`**: 레이어 10 `_render_gap_stutter_burst()` 추가
  - 나레이션 세그먼트 사이 무음 구간(≥30ms) 감지 → 쏘우+스퀘어 brutal burst 삽입
  - drive 5.0~10.0 (burst_energy 비례), 32분음표 게이트, vol 0.5~0.85
  - 이전+다음 세그먼트 SI 평균 → burst_energy 결정
- **`visual_renderer.py`**: SI 기반 레이어 강도 동적 조절 (`SI_INTENSITY_SCALE`)
  - render_frame() 매 프레임마다 SI값으로 레이어 intensity 실시간 스케일
  - SineWaveLayer: `max(0.35, 1-si*0.45)` (배경→서브), Particle: `si^1.5` (민감)
  - `_init_layers()`에서 `_base_intensity` 저장 → 프레임마다 동적 적용
- **`visual_script_generator.py`**: SI → vocab/reactivity/max_layers 연동
  - `build_scene(si=...)` 파라미터 추가
  - SI 기반 reactivity: si≥0.88→max, si≥0.72→high, si≤0.25→low
  - SI 기반 max_layers: `int(si*3.5)` 기준 (si=0.25→1, si=0.75+→3)
  - 세그먼트 합칠 때 평균 SI 계산 → scene에 전달

### 반영 문서
| 문서 | 반영 내용 |
|------|----------|
| MEMORY.md | 음악 엔진 v9 레이어 수 8→10, render v2, SI 비주얼 연동 섹션 추가 |
| CHANGELOG | 이 항목 |
| ClaudeCode_Brief_v6 | 파이프라인 CLI enometa_render.py v2로 통합, 검증 체크리스트 갱신 |
| Music_Engine_Spec_v6 | 레이어 10 gap_stutter_burst 설명 추가, BPM 135, v9 합성 함수 추가 |
| Hybrid_Visual_Architecture | SI_INTENSITY_SCALE, SI 기반 reactivity/max_layers 섹션 추가 |

---

## 2026-03-03 — PixelGrid/PixelWaveform ikeda 통합 + 레거시 클린업

### 코드 변경
- **`visual_script_generator.py`**: PALETTES에 ikeda 팔레트 추가 (기존: phantom 폴백 → 해결)
- **`visual_script_generator.py`**: ikeda inject_vocabs 활성화 (`pixel_grid_rain`, `pixel_grid_life`, `pixel_waveform_cascade`, 25% 확률)

### 문서 레거시 클린업
- **SNAPSHOT Sec.4**: PixelGrid/PixelWaveform "v8 ikeda 팔레트 연동" 표시, VOCAB_MAP 활성 vocab 명시
- **SNAPSHOT Sec.4**: 비주얼 전략 "techno→dense, algorave→collision" 장르 매핑 제거
- **SNAPSHOT Sec.3-1**: v5 bytebeat 설명 → v8 ikeda 기준으로 갱신
- **SNAPSHOT Sec.7**: 팔레트 테이블 ikeda 최상단 + "8종 선택 가능" 구조로 변경
- **SNAPSHOT Sec.8**: 파일 구조 코멘트 v8 기준 업데이트
- **Visual_Diff Spec**: BytebeatLayer/FeedbackLayer "(v8 ikeda 미사용)" 표시

### 반영 문서
| 문서 | 반영 내용 |
|------|----------|
| SYSTEM_SNAPSHOT | ikeda 팔레트 통합, 레거시 클린업 (Sec.3-1, 4, 7, 8) |
| ClaudeCode_Brief | ikeda 팔레트 + PixelGrid 통합 반영 |
| Visual_Diff_Spec | BytebeatLayer/FeedbackLayer v8 미사용 표시 |
| CHANGELOG | 이 항목 |

---

## 2026-03-03 — 문서 시스템 리팩토링 (토큰 최적화)

### 변경 내용
- **MEMORY.md 슬림화**: 206줄 → 74줄 (-64%)
  - 마스터 문서와 100% 중복되는 12개 섹션 삭제
  - 분산 규칙을 "절대 규칙 모음" 8항목으로 통합
  - 프로토콜/업로드 규칙을 별도 파일로 분리
- **memory/protocols.md 신규**: 문서 업데이트 프로토콜 + 범위별 선택적 Read 규칙 + 보고 규칙
- **memory/publish-rules.md 신규**: 태그 규칙 + 고정 멘트 전문 + 삽입 규칙
- **ClaudeCode_Brief 중복 제거**: 276줄 → 210줄 (-24%)
  - 비주얼 어휘 22개 목록, 음악 엔진 악기/합성법, 컬러 팔레트 테이블 → 1줄 참조로 대체
  - 프로젝트 개요 슬림화
- **SNAPSHOT 최적화**: 502줄 → 495줄
  - Sec.10 환경 테이블 → Brief 참조로 대체
  - 역할 헤더 추가 (SNAPSHOT=설계도 / Brief=실전 매뉴얼)
- **Upgrade Plan 아카이브**: 856줄 docs/ → docs/archive/ 이동 (9/9 완료, 순수 히스토리)
- **업데이트 프로토콜 최적화**: "7개 전부 Read" → 범위별 선택적 Read (평균 3-4개)

### 반영 문서
| 문서 | 반영 내용 |
|------|----------|
| MEMORY.md | 206→74줄 대폭 슬림화 + 절대 규칙 모음 + 프로토콜/업로드 참조 |
| SYSTEM_SNAPSHOT | 역할 헤더 추가 + 환경 테이블 Brief 참조 |
| ClaudeCode_Brief | 역할 헤더 추가 + 3개 섹션 참조 대체 + 개요 슬림화 |
| CHANGELOG | 이 항목 |

### 효과
| 항목 | Before | After |
|------|--------|-------|
| MEMORY.md (자동 로드) | 206줄 | 74줄 |
| 활성 문서 합계 | 3,377줄 | ~2,420줄 (-28%) |
| 세션당 평균 Read | ~3,377줄 | ~1,200줄 (-64%) |

---

## 2026-03-02 — script_data_extractor v2: 사전 대폭 확장 + 미등록 단어 감지 시스템

### 변경 내용
- **script_data_extractor.py v2 — 사전 대폭 확장**:
  - VERB_ENERGY: 41 → **101개** (파괴/변혁/인지/상태 전 범위)
  - EMOTION_INTENSITY: 28 → **68개** (극단~잔잔함 5단계)
  - SCIENCE_TERMS: 35 → **85개** (컴퓨팅/데이터/뇌과학/철학)
  - CHEMICALS: 9 → **19개**, BODY_PARTS: 10 → **30개**
- **custom_dictionary.json 시스템**:
  - 사용자 추가 단어 외부 사전 파일 신규
  - 모듈 로드 시 자동 머지 (`load_custom_dictionary()`)
  - `save_to_custom_dictionary()`: 미등록 단어 JSON 영구 저장
- **미등록 단어 감지 시스템**:
  - `detect_unregistered_words()`: 대본 분석 시 사전에 없는 단어 자동 감지
  - `print_unregistered_report()`: 미등록 동사/명사 빈도순 리포트
  - `interactive_dict_update()`: 대화형으로 분류(동사/감정/과학/화학/신체) + 점수 매기기
  - CLI 옵션: `--update-dict` (대화형 업데이트), `--report-only` (리포트만)
- 사전 수 출력: 실행 시 `Dictionaries: VERB=101 EMOTION=68 SCIENCE=85 CHEM=19 BODY=30`

### 반영 문서
| 문서 | 반영 |
|------|------|
| ENOMETA_SYSTEM_SNAPSHOT_v6.md | script_data v2 수치 갱신 + custom_dictionary + 미등록 감지 |
| ENOMETA_ClaudeCode_Brief_v6.md | script_data v2 CLI 옵션 + 사전 수치 갱신 |
| ENOMETA_Music_Engine_Spec_v6.md | semantic_intensity 사전 수치 갱신 + custom_dictionary |
| ENOMETA_Hybrid_Visual_Architecture.md | last_updated (script_data v2 연동) |
| ENOMETA_Visual_Differentiation_Spec.md | last_updated (EMOTION 68개 감정 태그 매핑 고도화) |
| MEMORY.md | script_data v2 수치 + custom_dictionary + 미등록 단어 감지 |
| CHANGELOG.md | 이 항목 |

---

## 2026-03-02 — 글쓰기 스킬 v11 시스템 최적화 + script_data_extractor 1차 확장

### 변경 내용
- **글쓰기 스킬 v10.1 → v11 전면 리라이트** (488줄):
  - 4가지 글쓰기 유형 → **데이터아트형 단일 구조** (에세이/독백/대화 삭제)
  - "팩트로 위로하는" 철학 (Comfort Through Facts) 섹션 신규
  - **5대 콘텐츠 도메인** + 교차점 공식 (뇌과학/데이터분석/철학/인문학/컴퓨팅)
  - **3단계 데이터 변환** 유일 구조: 데이터→철학→각성 (30/40/30%)
  - **SI 안무 가이드**: 계산 공식, 레벨별 글쓰기 전략, 커브 템플릿, 고SI 레시피
  - **비주얼 vocab 30종+ 매핑**: 문장 패턴 × 트리거 비주얼 × 감정 태그
  - **음악-글쓰기 연동**: 감정→멜로디, SI→텍스처 밀도 가이드
  - **시스템 최적화 점수**: 7개 카테고리 100점 자동 채점 + 보고 형식
  - **주제 추천 시스템**: STEP 0 — "글쓰기 시작하자" → 3~5개 주제 추천
  - 고에너지 동사 18개 + 감정어 11개 사전 (SI 부스터)
- **script_data_extractor.py 1차 확장**:
  - VERB_ENERGY: 26개 → 41개 (+15 철학/인문학/컴퓨팅 동사)
  - EMOTION_INTENSITY: 18개 → 28개 (+10 인문학/철학 감정)
  - SCIENCE_TERMS: 12개 → 35개 (+23 컴퓨팅/철학 용어)
- 스킬 동기화: `enometa-writing-skill.md` → `enometa-shorts/skills/enometa-writing.md`

### 반영 문서
| 문서 | 반영 |
|------|------|
| ENOMETA_SYSTEM_SNAPSHOT_v6.md | 워크플로우 v11 반영, script_data 수치 갱신 |
| ENOMETA_ClaudeCode_Brief_v6.md | 글쓰기 워크플로우 v11, script_data 스펙 갱신 |
| ENOMETA_Music_Engine_Spec_v6.md | last_updated (VERB/EMOTION 확장 연동 기록) |
| ENOMETA_Hybrid_Visual_Architecture.md | last_updated (비주얼 vocab 30종 매핑 연동) |
| ENOMETA_Visual_Differentiation_Spec.md | last_updated (감정 태그 매핑 확장) |
| MEMORY.md | 글쓰기 스킬 v11 반영, script_data 수치 갱신 |
| CHANGELOG.md | 이 항목 |

---

## 2026-03-02 — v8 ikeda 단일 장르 + Hybrid 전용화 + ikeda 확장

### 변경 내용
- **Legacy 모드 완전 제거**: `VisualSection.tsx`에서 legacy 렌더링 경로(~80행) 삭제, hybrid만 유지
- **Hybrid 전용화**: `visual_script_generator.py` 항상 `render_mode: "hybrid"` 설정 + `frames_dir`/`total_frames` 자동 계산
- **types.ts**: `render_mode?: "hybrid" | "legacy"` → `render_mode?: "hybrid"` 타입 단순화
- **5개 장르 제거**: techno/bytebeat/algorave/harsh_noise/chiptune GENRE_PRESETS 삭제 → ikeda만 유지
- **ikeda 확장 (다른 장르 요소 흡수)**:
  - **유클리드 리듬** (from algorave): `rhythm_mode: "euclidean"` synthesis_override
  - **피드백 텍스처** (from harsh_noise): 고긴장 구간(tension_peak/awakening_climax)에서 제한적 피드백 활성화
  - **Bytebeat 미세 텍스처** (from bytebeat): 극저볼륨(0.08) 디지털 배경 텍스처
  - **킥/리듬 백본** (from techno): 극저볼륨 서브킥(0.2) + 하이햇(0.1), si 기반 활성화
  - **멜로딕 사인 시퀀스**: SINE_MELODY_SEQUENCES 5종 + EMOTION_TO_MELODY 22감정 매핑, 4마디마다 주파수쌍 전환
  - **텍스처 모듈 시스템**: TEXTURE_MODULES 5종, `_select_texture_modules_from_history()` 에피소드별 자동 조합 선택
- **음악 엔진 마스터링 단순화**: 비-ikeda 분기(wavefold_master, bit_depth) 제거, 항상 tanh(1.2) RMS -10dB
- **비주얼 렌더러**: GENRE_LAYER_PRESETS 5개 장르 제거, GENRE_PALETTE ikeda만 유지
- **visual_script_generator.py**: `--genre` 옵션 무시 (항상 ikeda), 장르→전략 매핑 단순화

### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `src/components/VisualSection.tsx` | legacy 코드 블록 삭제(~80행), hybrid 전용, 에러 가드 추가 |
| `src/types.ts` | `render_mode?: "hybrid"` 타입 단순화 |
| `scripts/visual_script_generator.py` | 항상 hybrid + ikeda, frames_dir/total_frames 자동 계산 |
| `scripts/enometa_music_engine.py` | 5개 장르 GENRE_PRESETS 제거, ikeda 확장(텍스처 모듈 흡수), 마스터링 단순화, SINE_MELODY_SEQUENCES, TEXTURE_MODULES |
| `scripts/visual_renderer.py` | GENRE_LAYER_PRESETS 5개 장르 제거, GENRE_PALETTE ikeda 단일화 |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — v8 진화로그, 장르 단일화, legacy 제거
- [x] ENOMETA_Hybrid_Visual_Architecture.md — legacy 모드 제거, 장르 테이블 단순화
- [x] ENOMETA_Music_Engine_Spec_v6.md — 장르 6→1, ikeda 확장, SINE_MELODY_SEQUENCES
- [x] ENOMETA_ClaudeCode_Brief_v6.md — CLI 업데이트, 장르 단일화
- [x] ENOMETA_Visual_Differentiation_Spec.md — GENRE_LAYER_PRESETS ikeda 전용
- [x] MEMORY.md — v8 상태 반영
- [x] CHANGELOG.md (이 파일)

---

## 2026-03-02 — v6.6 Hybrid Vocab Overlay 활성화: VisualSection.tsx hybrid 모드 vocab 오버레이

### 변경 내용
- **EP005 피드백 해결**: hybrid 모드에서 Python 배경만 렌더하던 문제 수정
- `VisualSection.tsx` hybrid 블록에 vocab 시맨틱 레이어 오버레이 추가
- 렌더 순서: PythonFrameBackground → vocab 시맨틱 오버레이 (씬 기반) → PostProcess
- 씬이 없는 구간에서는 Python 배경 + PostProcess만 표시 (graceful fallback)
- visual_script.json의 씬별 vocab entries가 Python 프레임 위에 자동으로 렌더링됨
- TypeScript 빌드 에러 0 확인

### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `src/components/VisualSection.tsx` | hybrid 블록에 activeScene 찾기 + sceneProgress 계산 + vocab semantic.map 렌더링 추가 |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — hybrid 규칙 ⚠→✅, 파일구조 설명, 진화로그 v6.6
- [x] ENOMETA_Hybrid_Visual_Architecture.md — 섹션 3-2 모드 설명 + ⚠→✅ 구현 완료, 렌더 순서 문서화
- [x] ENOMETA_Music_Engine_Spec_v6.md — last_updated (음악 코드 변경 없음)
- [x] ENOMETA_ClaudeCode_Brief_v6.md — last_updated
- [x] ENOMETA_Visual_Differentiation_Spec.md — last_updated
- [x] MEMORY.md — EP005 교훈 → ✅ 구현 완료로 갱신
- [x] CHANGELOG.md (이 파일)

---

## 2026-03-02 — v7-P6 가변 BPM: si 기반 섹션별 ±15% 템포 변조 (v7 음악 엔진 9/9 완료)

### 변경 내용
- `_compute_tempo_curve()` 신규: si 기반 섹션별 BPM 변조 곡선 (si=0→85%, si=1→115%)
- `_section_bpm(section)` 헬퍼: 섹션 평균 BPM 조회
- `_render_continuous_rhythm()` 전면 재작성: 정적 타일링 → 이벤트 기반 가변 간격 배치
  - 표준(4-on-the-floor) + 유클리드 모드 모두 가변 BPM 지원
- `_render_section_textures()`: acid_bass, chiptune_drum, stutter_gate에 섹션별 BPM 적용
- `generate()`: si_gate 후 `self._tempo_curve = self._compute_tempo_curve()` 계산 + 로그 출력
- `export_raw_visual_data()`: `tempo_curve` 프레임별 BPM 배열 추가 (npz)
- 하위호환: script_data 없으면 base_bpm 균일 (무변조)

### 검증 결과
- 6개 전 장르 렌더링 성공: 모두 ±15% 범위 내 BPM 변조 확인
- 조용한 구간(si=0.15) → 115 BPM, 격렬한 구간(si=0.85) → 140 BPM (base=128)
- 하위호환: script_data 없을 때 uniform BPM 확인
- export: tempo_curve 프레임별 배열 정상 출력

### 반영 문서
- [x] ENOMETA_Music_Engine_Spec_v6.md — 가변 BPM 시스템 섹션 추가
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — v7-P6 진화로그
- [x] ENOMETA_ClaudeCode_Brief_v6.md — last_updated
- [x] ENOMETA_Hybrid_Visual_Architecture.md — last_updated
- [x] ENOMETA_Visual_Differentiation_Spec.md — last_updated
- [x] MEMORY.md — 업그레이드 상태 완료 갱신
- [x] CHANGELOG.md — 이 항목
- [x] ENOMETA_Music_Engine_Upgrade_Plan.md — 문제 6 ✅ + 대시보드 9/9

---

## 2026-03-02 — v7-P7 에피소드 간 음악 이력 추적: KEY_PRESETS + music_history.json

### 변경 내용
- **Problem 7 해결**: `music_history.json`으로 에피소드별 음악 특성 추적 + 키/패턴 자동 다양화
- `KEY_PRESETS` 딕셔너리 (7키: C~Bb minor), `KEY_PRIORITY` 선택 우선순위
- `ARP_PATTERNS` 5종 아르페지오 패턴 변형
- `_load_music_history()` / `_save_music_history()` — music_history.json I/O
- `_select_key_from_history()`: lookback=2, 최근 에피소드와 다른 키 자동 선택
- `_select_arp_pattern_from_history()`: 최근 에피소드와 다른 패턴 선택
- `generate_music_script()` 확장: `episode`, `project_dir` 매개변수 + palette 동적 생성
- `--episode ep006` CLI 옵션 추가
- 하드코딩 `"key": "E_minor"` → KEY_PRESETS 기반 동적 선택
- 하드코딩 `"arp_pattern"` → ARP_PATTERNS 기반 동적 선택
- `import os` 모듈 상단 추가

### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | KEY_PRESETS/ARP_PATTERNS, _load/_save_music_history, _select_key/arp_from_history, generate_music_script 확장, --episode CLI |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — v7-P7 진화로그
- [x] ENOMETA_Music_Engine_Spec_v6.md — 에피소드 간 음악 이력 섹션 추가
- [x] ENOMETA_Hybrid_Visual_Architecture.md — last_updated
- [x] ENOMETA_ClaudeCode_Brief_v6.md — last_updated
- [x] ENOMETA_Visual_Differentiation_Spec.md — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md (이 파일)

---

## 2026-03-02 — v7-P8 연속 악기 si 게이트: 조용한 구간 연속 악기 자동 감쇠

### 변경 내용
- **Problem 8 해결**: 연속 악기(bass, arp, rhythm, sine_interference, ultrahigh)에 si 기반 게이트 적용
- `_build_si_gate()` 신규: si<0.15→0.1, si<0.30→0.4, si≥0.30→1.0 + 0.3초 cumsum 스무딩
- `generate()`에서 si_modulation 직후 `self._si_gate` 계산
- 7개 연속 렌더러 전부에 si_gate 적용 (bass, fm_bass, rhythm, sub_pulse, arpeggio, sine_interference, ultrahigh)
- 테스트 결과: quiet(si=0.1) RMS=0.0068 vs loud(si=0.9) RMS=0.3105 → **45.59x 다이나믹 레인지**

### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `_build_si_gate()` 신규, `generate()` si_gate 계산, 7개 `_render_continuous_*()` si_gate 적용 |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — v7-P8 진화로그
- [x] ENOMETA_Music_Engine_Spec_v6.md — 연속 악기 si 게이트 섹션 추가
- [x] ENOMETA_Hybrid_Visual_Architecture.md — last_updated
- [x] ENOMETA_ClaudeCode_Brief_v6.md — last_updated
- [x] ENOMETA_Visual_Differentiation_Spec.md — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md (이 파일)

---

## 2026-03-02 — v7-P9 Pulse Train / Granular 합성: ikeda 펄스 트레인 + 그래뉼러 클라우드

### 변경 내용
- **Problem 9 해결**: `pulse_train()` + `granular_cloud()` 합성 함수 2종 신규
- `_render_continuous_pulse_train()` 연속 렌더러 — ikeda 모드 전용
- si 연동 가변 반복 속도: si=0 → 20Hz 느린 클릭, si=1 → 200Hz 급속 버즈
- 대본 숫자 → click_freq 매핑 (중앙값 기반)
- GENRE_PRESETS["ikeda"]에 pulse_train force_active 추가
- EMOTION_MAP 5개 감정에 pulse_train 볼륨 차등 설정
- `generate_music_script()` 악기 키 리스트에 "pulse_train" 추가

### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `pulse_train()`, `granular_cloud()` 합성 함수, `_render_continuous_pulse_train()`, GENRE_PRESETS/EMOTION_MAP/generate_music_script 확장 |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — v7-P9 진화로그
- [x] ENOMETA_Music_Engine_Spec_v6.md — Pulse Train/Granular 섹션 추가
- [x] ENOMETA_Hybrid_Visual_Architecture.md — last_updated
- [x] ENOMETA_ClaudeCode_Brief_v6.md — last_updated
- [x] ENOMETA_Visual_Differentiation_Spec.md — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md (이 파일)

---

## 2026-03-02 — v7-P3 script_data 전장르 활용: 6개 장르 대본 데이터 기반 악기 변조

### 변경 내용
- **Problem 3 해결**: `_script_data_enrichment(sections)` 신규 — ikeda만 쓰던 script_data를 6개 장르 전부에서 활용
- techno: numbers → synth_lead pattern ratios, data_density → clicks density
- bytebeat: numbers 합 → bytebeat formula 인덱스 선택
- algorave: data_density → metallic_hit density
- harsh_noise: si → feedback gain(0.5~0.95) + iterations(4~12)
- chiptune: numbers → chiptune_lead pattern ratios
- `generate()` 에서 si_env 빌드 후, arc 계산 전에 호출

### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `_script_data_enrichment()` 신규, `generate()` 호출 삽입 |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — v7-P3 진화로그
- [x] ENOMETA_Music_Engine_Spec_v6.md — script_data 전장르 활용 섹션 추가
- [x] ENOMETA_Hybrid_Visual_Architecture.md — last_updated
- [x] ENOMETA_ClaudeCode_Brief_v6.md — last_updated
- [x] ENOMETA_Visual_Differentiation_Spec.md — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md (이 파일)

---

## 2026-03-02 — v7-P5 감정 전환 크로스페이드: 텍스처 delta fade-in/fade-out

### 변경 내용
- **Problem 5 해결**: 섹션 텍스처 악기의 기여분(delta)에만 fade-in/fade-out 적용
- 연속 악기(bass, arp 등)는 영향받지 않음 — 텍스처 기여분만 정밀 페이드
- `fade_duration = min(0.5, dur × 0.15)` — 최대 0.5초 또는 섹션 15%
- 구현: 렌더 전 마스터 스냅샷 → 렌더 후 delta 추출 → fade 적용 → 복원

### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `_render_section_textures()` 시작/끝에 스냅샷+delta fade 로직 |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — v7-P5 진화로그
- [x] ENOMETA_Music_Engine_Spec_v6.md — 크로스페이드 섹션 추가
- [x] ENOMETA_Hybrid_Visual_Architecture.md — last_updated
- [x] ENOMETA_ClaudeCode_Brief_v6.md — last_updated
- [x] ENOMETA_Visual_Differentiation_Spec.md — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md (이 파일)

---

## 2026-03-02 — v7-P2 Adaptive Song Arc: si 곡선 기반 적응형 기승전결

### 변경 내용
- **Problem 2 해결**: 고정 비율 Song Arc(narrative 15/30/35/20%) 대신 si 곡선에서 내러티브 구조를 자동 추출
- `_compute_adaptive_arc()` 신규: 3s heavy smoothing → 글로벌 피크 탐지 → 동적 phase 경계
- `_build_arc_from_phases()` 분리: phase→에너지 엔벨로프 공통 로직
- si 다이나믹 레인지 < 0.08 → narrative fallback (플랫 대본 보호)
- script_data 없으면 → narrative fallback (하위호환)
- `SONG_ARC_PRESETS`에 `"adaptive"` 마커 추가
- `_get_arc_phase_at()` adaptive phases 지원
- `generate()`에서 si_env 빌드 순서를 arc 계산 전으로 이동

### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `_compute_adaptive_arc()` 신규, `_build_arc_from_phases()` 분리, `SONG_ARC_PRESETS["adaptive"]` 추가, `generate()` 순서 변경 |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — v7-P2 섹션 + 진화로그
- [x] ENOMETA_Music_Engine_Spec_v6.md — Adaptive Song Arc 섹션 + 아크 테이블
- [x] ENOMETA_Hybrid_Visual_Architecture.md — last_updated
- [x] ENOMETA_ClaudeCode_Brief_v6.md — --arc adaptive CLI 옵션 추가
- [x] ENOMETA_Visual_Differentiation_Spec.md — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md (이 파일)

---

## 2026-03-02 — v7-P1 si→음악 연동: semantic_intensity 음악 에너지 변조

### 변경 내용
- **Problem 1 해결**: script_data의 semantic_intensity(0~1)로 음악 에너지 실시간 변조
- 마스터 버퍼 볼륨 변조: `0.7 + si × 0.6` (si=0→70%, si=1→130%)
- 텍스처 밀도 변조: `0.5 + si` (클릭/글리치/노이즈/메탈릭)
- `_build_si_envelope()` 신규: segments → 시간 도메인 배열, 0.5초 cumsum 스무딩
- script_data 없으면 si=0.5(neutral) → 무변조 (하위호환)
- **음악-비주얼-대사 삼위일체 달성**: 비주얼과 동일한 si 소스를 음악이 공유

### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `_build_si_envelope()` 신규, `generate()` si 적용, `_render_section_textures()` density 변조 |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — v7-P1 섹션 + 진화로그
- [x] ENOMETA_Music_Engine_Spec_v6.md — si 변조 시스템 섹션
- [x] ENOMETA_Hybrid_Visual_Architecture.md — last_updated (삼위일체)
- [x] ENOMETA_ClaudeCode_Brief_v6.md — last_updated
- [x] ENOMETA_Visual_Differentiation_Spec.md — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md (이 파일)
- [x] ENOMETA_Music_Engine_Upgrade_Plan.md — 대시보드 ✅ + 구현 이력

---

## 2026-03-02 — v7-P4 박자 정렬: 음악 섹션 마디 경계 퀀타이즈

### 변경 내용
- **Problem 4 해결**: `generate_music_script()`에서 음악 섹션 경계를 마디(bar) 경계로 퀀타이즈
- 비주얼 씬 경계는 그대로 유지 (나레이션 타이밍 정확), 음악 섹션만 마디 단위 정렬
- `_quantize_to_bar(time_sec, bar_duration)` 헬퍼 함수 신규
- 4/4 박자 기준: techno=1.875s, ikeda=4.0s, chiptune=2.0s 등 6개 전 장르 지원
- 원본 경계 보존 (`_original_start_sec`, `_original_end_sec`), 인접 섹션 연속성 보장, 최소 1마디 보장
- 음악 엔진 v7 업그레이드 9대 문제 중 1번째 해결 (Phase A #1)

### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | `import math`, `_quantize_to_bar()` 신규, `generate_music_script()` 박자 정렬 |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — v7-P4 박자 정렬 섹션 + 진화로그
- [x] ENOMETA_Hybrid_Visual_Architecture.md — last_updated
- [x] ENOMETA_Music_Engine_Spec_v6.md — 박자 정렬 시스템 섹션 신규
- [x] ENOMETA_ClaudeCode_Brief_v6.md — last_updated
- [x] ENOMETA_Visual_Differentiation_Spec.md — last_updated
- [x] MEMORY.md — 업그레이드 상태 갱신
- [x] CHANGELOG.md (이 파일)
- [x] ENOMETA_Music_Engine_Upgrade_Plan.md — 대시보드 ✅ + 구현 이력

---

## 2026-03-02 — 볼륨 밸런스 변경: TTS:BGM = 4:6

### 변경 내용
- TTS:BGM 비율을 기존 1.0:0.50 (TTS 우세) → 0.67:1.0 (BGM 우세)로 변경
- 음악이 더 큰 비율로 재생 (사용자 요청: "TTS가 4라면 음악이 6")
- audio_mixer.py 기본값 변경: narration_volume 1.0→0.67, bgm_volume 0.50→1.0
- feedback_defaults.json mixing_defaults 업데이트

### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/audio_mixer.py` | narration_volume 0.67, bgm_volume 1.0, CLI default 업데이트 |
| `scripts/feedback_defaults.json` | mixing_defaults: bgm_volume 1.0, narration_volume 0.67 |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — 섹션 3-5 믹싱 비율 업데이트, 진화로그 v6.5
- [x] ENOMETA_Hybrid_Visual_Architecture.md — 파이프라인 [7] 믹싱 비율 업데이트
- [x] ENOMETA_Music_Engine_Spec_v6.md — last_updated 갱신
- [x] ENOMETA_ClaudeCode_Brief_v6.md — 기술 스택 테이블 + 파이프라인 [6] + CLI 예시 업데이트
- [x] ENOMETA_Visual_Differentiation_Spec.md — last_updated 갱신
- [x] MEMORY.md — 오디오 믹싱 v6.5 섹션 추가
- [x] CHANGELOG.md (이 파일)

---

## 2026-03-02 — LogoEndcard v2 — 타이밍 + 파티클 다이나미즘 강화

### LogoEndcard v2 — 타이밍 + 파티클 다이나미즘 강화
- 검정 화면 축소: scatterEnd 0.15→0.03초, 초기 radius/alpha 조정
- 수렴 가속: 2.5→2.0초
- 태그라인 풀 노출: 0.2→1.7초 (등장 4.2→2.8초, max opacity 0.35→0.5)
- 파티클 다이나미즘: 웨이브+크기펄스+색상깜빡임+글로우강화+연결선강화
- 엔드카드 종료 후 제목 노출 버그 수정 (TitleSection fade-out 추가)
- 반영 문서: SYSTEM_SNAPSHOT, Hybrid_Visual, MEMORY.md, CHANGELOG.md

### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `src/components/LogoEndcard.tsx` | v2 — 타이밍 리디자인 + 파티클 다이나미즘 강화 |
| `src/components/TitleSection.tsx` | endcardStartFrame prop + 엔드카드 시작 전 fade-out |
| `src/components/EnometaShorts.tsx` | TitleSection에 endcardStartFrame prop 전달 |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — Remotion 섹션에 LogoEndcard v2 상세, 파일구조, 진화로그 v6.4
- [x] ENOMETA_Hybrid_Visual_Architecture.md — 섹션 3-3/3-4 LogoEndcard v2 + TitleSection fade-out 추가
- [x] ENOMETA_Music_Engine_Spec_v6.md — 엔드카드 관련 내용 없음 (변경 없음)
- [x] ENOMETA_ClaudeCode_Brief_v6.md — 엔드카드 관련 내용 없음 (변경 없음)
- [x] ENOMETA_Visual_Differentiation_Spec.md — 엔드카드 관련 내용 없음 (변경 없음)
- [x] MEMORY.md — LogoEndcard v2 섹션 추가
- [x] CHANGELOG.md (이 파일)

---

## 2026-03-02 — GENRE_LAYER_PRESETS v2 리디자인
- 모든 6개 장르에 TTS 4레이어(Barcode/DataStream/TextData/DataMatrix) 기본 장착
- 음악 레이어 3개로 확장 (장르별 리드 + 범용 보조 2개)
- 장르별 평균 레이어: 2.7개 → 7.0개 (78% 활용률)
- blend_ratio 전면 재조정 (0.45~0.6)
- 장르 차별화: intensity 분배 + blend_ratio + palette 기반 (레이어 유무가 아닌)
- 반영 문서: SYSTEM_SNAPSHOT, Hybrid_Visual, Music_Engine, ClaudeCode_Brief, Visual_Differentiation, MEMORY.md, CHANGELOG.md

### 장르별 변경 상세
| 장르 | v1 | v2 | blend v1→v2 |
|------|-----|-----|-------------|
| techno | 2M+1T=3 | 3M+4T=7 | 0.6→0.55 |
| bytebeat | 2M+0T=2 | 3M+4T=7 | 0.8→0.6 |
| algorave | 2M+1T=3 | 3M+4T=7 | 0.6→0.5 |
| harsh_noise | 2M+0T=2 | 3M+4T=7 | 0.8→0.55 |
| chiptune | 2M+0T=2 | 3M+4T=7 | 0.8→0.55 |
| ikeda | 1M+3T=4 | 3M+4T=7 | 0.5→0.45 |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — 장르→비주얼 연동 테이블 v2 교체, 진화로그 v6.3 추가
- [x] ENOMETA_Hybrid_Visual_Architecture.md — 섹션 4 레이어 레지스트리 v2 교체, 변경 요약
- [x] ENOMETA_Music_Engine_Spec_v6.md — 장르별 비주얼 레이어 연동 섹션 추가
- [x] ENOMETA_ClaudeCode_Brief_v6.md — 비주얼 렌더링 코멘트 v6.3 업데이트
- [x] ENOMETA_Visual_Differentiation_Spec.md — GENRE_LAYER_PRESETS v2 장르별 테이블 추가
- [x] MEMORY.md — Hybrid Visual Architecture 섹션 v2 반영
- [x] CHANGELOG.md (이 파일)

---

## 2026-03-02 — semantic_intensity TTS 다이나믹 비주얼 (v6.2)

### 변경 내용
- **semantic_intensity 구현 완료**: script_data_extractor.py에 compute_semantic_intensity() 추가
  - VERB_ENERGY 26개 동사, EMOTION_INTENSITY 18개 감정어, 문장구조, byte_variance
  - 4요소 가중합산 (verb 0.35 + emotion 0.3 + sentence 0.2 + byte_variance 0.15)
- **tts_effects.py 공유 모듈 신규**: 10개 이펙트 함수 (get_scaled_font, intensity_color, hue_shift_color, chromatic_aberration, scanlines, glitch_blocks, text_glow, vertical_wave_distortion, scale_pulse, data_click_explosion)
- **visual_renderer.py ctx 확장**: semantic_intensity, current_keywords, reactive_level 주입
- **TTS 레이어 3종 전면 리라이트**:
  - TextDataLayer: 폰트 16→48px, 카드 90→200px, si 연동 색상/jitter/glow/scanlines/chromatic/glitch/wave/data_click
  - DataStreamLayer: 폰트 16→36px, 행별 jitter, 스크롤 si 비례 가속, glow/scanlines/chromatic
  - BarcodeLayer: 선폭 2→12px, BPM 맥동, 선높이 60~100%, scanlines/chromatic/glitch
- **visual_layers/__init__.py**: tts_effects 임포트 추가

### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/visual_layers/tts_effects.py` | 신규 — 10개 공유 이펙트 함수 |
| `scripts/script_data_extractor.py` | compute_semantic_intensity(), VERB_ENERGY, EMOTION_INTENSITY, keywords[].intensity |
| `scripts/visual_renderer.py` | ctx에 semantic_intensity/current_keywords/reactive_level 주입 |
| `scripts/visual_layers/__init__.py` | tts_effects 임포트 추가 |
| `scripts/visual_layers/text_data_layer.py` | 전면 리라이트 — si 다이나믹 크기/색상/이펙트 |
| `scripts/visual_layers/data_stream_layer.py` | 전면 리라이트 — si 다이나믹 스크롤/폰트/이펙트 |
| `scripts/visual_layers/barcode_layer.py` | 전면 리라이트 — si 다이나믹 선폭/높이/맥동/이펙트 |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md — Phase 4 구현 완료, tts_effects.py, 파일구조, 진화로그
- [x] ENOMETA_Hybrid_Visual_Architecture.md — Phase 4 섹션, TTS 다이나믹 스펙 테이블, ctx 확장, tts_effects
- [x] ENOMETA_Music_Engine_Spec_v6.md — script_data semantic_intensity 출력 형식 문서화
- [x] ENOMETA_ClaudeCode_Brief_v6.md — script_data 검증 가이드, 비주얼 렌더링 검증 체크리스트
- [x] ENOMETA_Visual_Differentiation_Spec.md — Phase 4 전체 구현 완료 반영, tts_effects 테이블
- [x] MEMORY.md — semantic_intensity 시스템 구현 완료 섹션 추가
- [x] CHANGELOG.md (이 파일)

---

## 2026-03-02 — Dual-Source 비주얼 + Song Arc 시스템

### 변경 내용
- **Song Arc 시스템**: 음악 1곡에 기승전결(narrative/crescendo/flat) 매크로 에너지 엔벨로프
- **Dual-Source 비주얼**: TTS 레이어와 Music 레이어 독립 렌더 후 composite_dual_source() 합성
- **자막 크기 증가**: 42→54px, 48→62px, fontWeight 400→500/600→700
- **EP005 타이틀 버그 수정**: "ENOMETA" → "공포와 각성의 화학식은 같다"
- **문서 업데이트 강제 프로토콜**: MEMORY.md에 7개 파일 체크리스트 + last_updated 메타데이터 도입

### 변경 파일 (코드)
| 파일 | 변경 |
|------|------|
| `scripts/enometa_music_engine.py` | SONG_ARC_PRESETS, _compute_song_arc(), --arc CLI, export arc_energy/arc_phases |
| `scripts/visual_renderer.py` | GENRE_LAYER_PRESETS dual-source dict, render_frame() 독립 합성 |
| `scripts/visual_layers/composite.py` | composite_dual_source() 함수 추가 |
| `scripts/visual_layers/__init__.py` | composite_dual_source 임포트 |
| `src/components/SubtitleSection.tsx` | fontSize 54/62, fontWeight 500/700 |
| `episodes/ep005/visual_script.json` | title 수정 |
| `scripts/visual_script_generator.py` | --title 미지정 시 경고 |
| `src/ep005Script.ts` | fallback title 수정 |

### 반영된 마스터 문서
- [x] ENOMETA_SYSTEM_SNAPSHOT_v6.md
- [x] ENOMETA_Hybrid_Visual_Architecture.md
- [x] ENOMETA_Music_Engine_Spec_v6.md — Song Arc 시스템 섹션 + CLI 예시
- [x] ENOMETA_ClaudeCode_Brief_v6.md — --arc CLI 플래그 반영
- [x] ENOMETA_Visual_Differentiation_Spec.md — Dual-Source 레이어 분류 테이블
- [x] MEMORY.md
- [x] CHANGELOG.md (이 파일)

---

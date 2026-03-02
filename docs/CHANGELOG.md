# ENOMETA 시스템 변경 이력

> 시스템 변경 시 반드시 이 파일에 기록한다.
> 빠진 문서가 있으면 즉시 보인다.

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

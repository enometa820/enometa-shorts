# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 학습 목표 — 개발 개념 체득

이 프로젝트를 진행하면서 개발 용어/개념/작업 방식을 학습하고 싶어한다.

Claude는:
- 새로운 기술 개념이 등장하면 **이름과 용어를 1~2줄로 설명**한다
- 작업 완료 후 **"오늘 사용한 개념"** 을 요청하면 표로 정리해 준다
- 처음 등장하는 개발 용어는 괄호 안에 간단 설명을 붙인다
- 왜 이렇게 설계했는지 이유(trade-off)를 짧게 곁들인다

## 절대 규칙

- **환경**: `py` 명령 사용 (`python`은 Windows Store alias 문제). entry point: `src/index.tsx`
- **TTS**: `scripts/generate_voice_edge.py` 전용. `generate_voice.py`(Chatterbox) **절대 금지**
- **글쓰기**: 대본 컨펌 전 제목/음악/비주얼 등 후속 단계 진행 **금지** (글 컨펌 게이트)
- **비주얼**: render_mode 항상 `"hybrid"` (legacy 모드 제거됨). genre→strategy 동적 매핑 (cooper→breathing, abstract→cinematic, data→dense, enometa→enometa). SI 기반 전략 승격
- **음악**: v21 실존 언더그라운드 장르 10종 (acid/ambient/microsound/IDM/minimal/dub/glitch/industrial/techno/**house**). 대본 리액티브 댄스 뮤직. 패턴 엔진 v18 + v19 Vertical Remixing + v21 멜로디 다양성: 장르별 required/optional 레이어 분리 + ep_seed 기반 레이어 조합 자동 변주. 전용 합성 함수 + **ep_seed 기반 seq_config 13개 파라미터**로 에피소드마다 드럼/음색/패턴/멜로디 자동 분화. house 장르: `rhodes_pad()` Rhodes 패드(minor 9 코드) + 4-on-the-floor + 오프비트 하이햇. Gate 2: seq_config 음색 설계 (mood_layers 편집 금지)
- **오디오**: narration_volume=0.90, bgm_volume=1.0 (기본), 사이드체인 없음, loudnorm -14 LUFS, 엔드카드 BGM 자동 연장
- **태그**: 주제 기반 3개 + 고정 5개(`#데이터아트` `#전자음악` `#오디오비주얼` `#철학` `#동기부여`) = 해시태그 항상 8개. **완전 금지** (어디에도 사용 불가): `#쇼츠` `#shorts` `#ENOMETA` `#이노메타`
- **AsciiArt position**: 자막 영역(y≥1230 전체 캔버스) 침범 금지. bottom 위치 = height*0.62. TextReveal과 동일 규칙.

## 빌드 & 실행 명령

```bash
# Remotion Studio (프리뷰)
npx remotion studio --port 3000

# 영상 렌더링 (단일 에피소드)
npx remotion render src/index.tsx EP009 episodes/ep009/output.mp4

# 전체 파이프라인 — Claude가 대화로 옵션 수집 후 아래 형태로 실행
py scripts/enometa_render.py <episode_dir> --title "제목" --palette phantom --music-mood acid

# 전체 파이프라인 — 사용자가 터미널에서 직접 실행할 때만 (input() 때문에 Claude 실행 불가)
py scripts/enometa_render.py <episode_dir> --interactive

# 특정 단계만 재실행
py scripts/enometa_render.py <episode_dir> --title "제목" --step bgm --force

# 개별 스텝
py scripts/generate_voice_edge.py episodes/epXXX/narration_timing.json episodes/epXXX/narration.wav
py scripts/gen_timing.py episodes/epXXX/script.txt episodes/epXXX/narration_timing.json
py scripts/script_data_extractor.py episodes/epXXX/narration_timing.json
py scripts/enometa_music_engine.py --script-data episodes/epXXX/script_data.json episodes/epXXX/bgm.wav
py scripts/audio_mixer.py episodes/epXXX/narration.wav episodes/epXXX/bgm.wav episodes/epXXX/mixed.wav
py scripts/audio_analyzer.py episodes/epXXX/mixed.wav episodes/epXXX/audio_analysis.json 30
py scripts/visual_script_generator.py episodes/epXXX/narration_timing.json --title "제목" --palette phantom
py scripts/visual_renderer.py episodes/epXXX/visual_script.json episodes/epXXX/
```

## 아키텍처 개요

YouTube Shorts 자동 생성 파이프라인. Python(음악/비주얼 데이터) + Remotion(React 영상 합성) 하이브리드.

### 파이프라인 흐름
```
script.txt → gen_timing.py → narration_timing.json
           → generate_voice_edge.py → narration.wav
           → script_data_extractor.py → script_data.json (kiwipiepy 형태소 분석)
           → enometa_music_engine.py → bgm.wav + music_script.json
           → audio_mixer.py → mixed.wav
           → visual_script_generator.py → visual_script.json
           → visual_renderer.py → frames/000000.png~
           → audio_analyzer.py → audio_analysis.json
           → Remotion (src/Root.tsx) → output.mp4
```

### 팔레트
`phantom` / `neon_noir` / `cold_steel` / `ember` / `synapse` / `gameboy` / `c64` / `enometa`

### 음악 장르 (v20)
`acid` / `ambient` / `microsound` / `IDM` / `minimal` / `dub` / `glitch` / `industrial` / `techno` / `house`

### 비주얼 장르 (4종) — 음악 장르에서 자동 매핑
| 비주얼 장르 | 성격 | 팔레트 | 음악 장르 매핑 |
|------------|------|--------|---------------|
| `enometa` | 풀 세트 (데이터아트 기본) | enometa(흑백) | acid, glitch |
| `cooper` | 유기적 미니멀 (Particle 중심) | phantom(보라) | ambient, microsound, dub, house |
| `abstract` | 기하학 정제 (SineWave 극대화) | synapse(청록) | minimal, IDM |
| `data` | 최고 밀도 수치 분석 | cold_steel(철색) | techno, industrial |

### 새 에피소드 추가 절차

1. `episodes/epXXX/` 디렉토리 생성 후 파이프라인 실행
2. `src/epXXXScript.ts` 생성 — ep011Script.ts 패턴 복사 (json import + export 5개)
3. `src/Root.tsx` 상단 import 추가, `<Composition id="EPXXX" ... calcMeta>` 블록 추가
4. `public/epXXX/mixed.wav` 동기화 (`episodes/epXXX/mixed.wav` 복사)

### 사용 가능한 Vocab 문자열 (VisualSection.tsx VOCAB_MAP)

**파티클**: `particle_birth` `particle_scatter` `particle_converge` `particle_orbit` `particle_escape` `particle_chain_awaken` `particle_split_ratio`
**흐름/색**: `flow_field_calm` `flow_field_turbulent` `color_shift` `color_shift_warm` `color_shift_cold` `color_drain` `color_bloom` `brightness_pulse` `light_source`
**데이터/수학**: `counter_up` `neural_network` `loop_ring` `fractal_crack` `data_bar` `data_ring` `grid_morph` `grid_mesh` `waveform` `waveform_spectrum` `waveform_circular` `lissajous` `lissajous_complex`
**텍스트**: `text_reveal` `text_wave` `text_glitch` `text_scatter`
**심볼**: `symbol_morph` (품사 기반 추상 도형 — noun→육각형, verb→화살표, adjective→물결, science→동심원, philosophy→이중원)
**ASCII**: `ascii_block` `ascii_shape` `ascii_matrix` (block: 비트맵 블록 문자, shape: 품사별 ASCII 패턴, matrix: 터미널 데이터 스트림)
**레트로**: `pixel_grid` `pixel_grid_outline` `pixel_grid_life` `pixel_grid_rain` `pixel_waveform` `pixel_waveform_steps` `pixel_waveform_cascade`
**3D/Terra**: `terra_globe` `terra_globe_data` `terra_flythrough` `terra_tunnel` `terra_terrain` `terra_terrain_bars` (씬당 최대 1개, @remotion/three 기반, `.claude/rules/3d.md` 규칙 준수)
**자동 적용**: `post_process` (VisualSection이 항상 렌더링, vocab에 추가 불필요)

### ⚠️ 오디오 경로 주의
Remotion은 `public/epXXX/mixed.wav`를 참조. `episodes/epXXX/mixed.wav`와 **별개**.
mix 단계 후 `public/epXXX/mixed.wav`도 반드시 동기화 필요.
(`enometa_render.py`가 자동 처리하나, 수동 재믹스 시 직접 복사해야 함)

### 의존성
- **Python**: numpy, scipy, Pillow, edge-tts, kiwipiepy, soynlp
- **Node**: remotion, @remotion/cli, @remotion/layout-utils, @remotion/three, three

## 핵심 원칙

- **레이어 ON/OFF + 볼륨 고정**: 에너지는 볼륨 커브가 아닌 레이어 추가/제거로 표현. 콜앤리스폰스/song_arc 비활성. 마스터 페이드 없음 (5ms anti-click만).
- **고정 BPM**: 가변 BPM은 섹션 경계에서 리듬 파괴. 장르 범위 내 단일 BPM 유지.
- **타이밍**: 영상 길이 = `lastScene.end_sec + endcard`. BGM 초과분 자동 잘림. 문장 갭 `--gap 0.3`, 문단 갭 `--paragraph-gap 0.8`.
- **다양성 보장**: ep_seed → seq_config(드럼/음색/패턴/멜로디 13개 파라미터) 에피소드마다 자동 분화. 비주얼 전략은 genre에 따라 동적 선택, SI≥0.80에서 전략 승격. vocab avoid 목록은 최소한만 유지.

### 메모리 과부하 방지

- 에피소드 교훈 → `episodes/epXXX/feedback.json`
- MEMORY.md: 시스템 규칙 + 최신 교훈만 (200줄 이내)
- 아키텍처 결정 이유 → `docs/decisions/NNN-*.md` (ADR)

## 시니어 개발자 관점 — 지적 & 제안 프로토콜

Claude는 아래 상황에서 **실행 전에 반드시 지적하고 대안을 제시**한다.
묻지 않아도 선제적으로 개입한다.

### 컨텍스트 윈도우 낭비 감지
| 위험 신호 | 지적 내용 | 대안 |
|-----------|-----------|------|
| 중복 코드 파일 존재 (모놀리스 + 패키지) | "두 파일이 같은 코드를 가지고 있어 컨텍스트 낭비입니다" | thin wrapper 또는 패키지 통합 |
| 4,000줄 이상 단일 파일 수정 요청 | "전체 파일을 컨텍스트에 올리면 세션 중반에 압박이 옵니다" | 해당 함수/메서드만 타겟 편집 |
| 불필요한 문서 파일 신규 생성 요청 | "코드가 이미 진실의 소스입니다. 문서 추가는 중복입니다" | 기존 CHANGELOG 또는 주석으로 대체 |

### 설계 원칙 위반 감지
| 위험 신호 | 지적 내용 | 대안 |
|-----------|-----------|------|
| 순환 참조 위험 (A→B, B→A) | "순환 import는 런타임 에러를 유발합니다" | 공통 의존성을 synthesis/tables로 내리기 |
| git add . 요청 | "민감 파일(.env, 대용량 wav)이 포함될 수 있습니다" | 명시적 파일 지정으로 안내 |
| 에피소드 산출물을 코드와 같은 커밋 요청 | "목적이 다른 변경을 섞으면 롤백이 어렵습니다" | 2개 커밋으로 분리 제안 |
| 코드 수정 없이 문서만 먼저 업데이트 요청 | "코드보다 문서가 앞서면 곧 불일치가 생깁니다" | 코드 먼저, 문서는 같은 커밋에 |

### 지적 형식
```
⚠️ [시니어 관점] {문제 요약}
   이유: {왜 문제인지 1줄}
   대안: {구체적 다른 방향}
   → 이대로 진행할까요, 아니면 대안으로 갈까요?
```

### 지적하지 않는 경우
- 이미 논의된 트레이드오프를 사용자가 인지하고 명시적으로 승인한 경우
- 실험/테스트 목적임이 명확한 경우
- 단순 조회/읽기 작업

## 커밋 & 푸시 규칙

### 커밋 prefix
| prefix | 사용 상황 |
|--------|-----------|
| `feat:` | 새 기능 (스크립트, 컴포넌트, 파이프라인) |
| `fix:` | 버그 수정 |
| `docs:` | 문서만 변경 (md 파일) |
| `refactor:` | 기능 변화 없는 코드 정리 |
| `ep:` | 에피소드 제작 산출물 (script, timing, feedback 등) |

### 커밋 단위
- **한 가지 목적 = 커밋 하나**
- 코드 변경 + 관련 문서 최신화는 **동일 커밋**에 포함
- 에피소드 산출물(json/wav)은 코드 커밋과 **분리**

### 스테이징 원칙
- `git add .` 금지 — 파일 명시적 지정
- 대용량 바이너리(wav) 제외: `episodes/*/bgm.wav`, `episodes/*/narration.wav`, `episodes/*/mixed.wav`
- 포함 대상: `script.txt`, `narration_timing.json`, `visual_script.json`, `feedback.json`, `script_data.json`

### "커밋해줘" 요청 시 수행 절차
1. `git status`로 변경 파일 확인
2. 변경 성격 판단 → prefix 결정
3. `feat:` / `fix:` / `refactor:` 커밋이면 **`docs/CHANGELOG.md` 상단에 항목 추가** 후 함께 스테이징
4. 관련 파일만 명시적으로 add
5. 메시지 형식: `prefix: 한 줄 요약 (한국어 또는 영어)`
6. 커밋 실행 후 아래 브리핑 출력

CHANGELOG 항목 형식:
```
## [vXX] YYYY-MM-DD
### Added / Changed / Removed
- 변경 내용
```

**커밋 브리핑 형식:**
```
✅ 커밋 완료
├─ [prefix] 메시지
├─ 파일 N개 변경 (+추가 -삭제)
└─ 해시: xxxxxxx
```

### "푸시해줘" 요청 시 수행 절차
1. `git log --oneline`으로 미푸시 커밋 확인
2. 아래 브리핑 형식으로 요약 후 **승인 요청**
3. 승인 후 `git push origin main` 실행

**푸시 전 브리핑 형식:**
```
🚀 푸시 대상 커밋 N개
├─ xxxxxxx feat: ...
├─ xxxxxxx docs: ...
└─ xxxxxxx ep: ...
푸시할까요?
```

**푸시 후 브리핑 형식:**
```
✅ 푸시 완료 → origin/main
└─ N개 커밋 반영
```

## 스킬 라우팅

| 트리거 | 스킬 |
|--------|------|
| "글쓰기 시작" / 대본 작성 | `enometa-writing` |
| "제작 시작" / 파이프라인 | `enometa-produce` |
| "업로드 준비" / publish | `enometa-publish` |
| "피드백" / 리뷰 | `enometa-feedback` |

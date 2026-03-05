# ENOMETA 프로젝트 지침

## 절대 규칙

- **환경**: `py` 명령 사용 (`python`은 Windows Store alias 문제). entry point: `src/index.tsx`
- **TTS**: `scripts/generate_voice_edge.py` 전용. `generate_voice.py`(Chatterbox) **절대 금지**
- **글쓰기**: 대본 컨펌 전 제목/음악/비주얼 등 후속 단계 진행 **금지** (글 컨펌 게이트)
- **비주얼**: render_mode 항상 `"hybrid"` (legacy 모드 제거됨)
- **음악**: enometa 장르 (구 ikeda). 대본 리액티브 댄스 뮤직. 패턴 엔진 v11: 드럼 패턴(킥/스네어/하이햇) + 필/드롭 + 호흡 시스템
- **오디오**: narration_volume=0.90, bgm_volume=1.0, 사이드체인 없음, loudnorm -14 LUFS, 엔드카드 BGM 자동 연장
- **태그**: 주제 기반 5개만. 고정 제외 태그(`#쇼츠` `#shorts` `#ENOMETA` `#이노메타` `#데이터아트`) 포함 금지

## 문서 프로토콜

시스템 변경 시 → `memory/protocols.md` 체크리스트 실행.
SNAPSHOT(설계도) + Brief(실전 매뉴얼) 항상 쌍으로 업데이트.

## v15 시스템 철학 — 음악적 완성도

**최우선 목표**: 음악적 완성도. 처음부터 끝까지 따로 놀지 않는 음악.
TTS / 비주얼 / BGM이 하나의 통합 유기체로 움직여야 한다.

### 3원칙

1. **마디 동기화**: 모든 요소의 시간축은 `SEC_PER_BAR = 1.777s` 기준.
   - `narration_timing.json` start_sec → 항상 SEC_PER_BAR의 배수
   - TTS adelay → 마디 경계 배치 / 비주얼 씬 전환 → 마디 경계
   - BGM 내부 패턴 → 0초 기준, 마디 경계 자동 일치

2. **레이어 ON/OFF**: 에너지 표현은 볼륨 커브가 아닌 레이어 추가/제거.
   - 볼륨 변조 범위: ±15% 이내. 무드별 레이어 조합이 진짜 차별화.

3. **모든 요소의 상호작용**: 음악이 비주얼을 이끌고, 비주얼이 자막을 감싸고,
   자막이 리듬에 맞춰 호흡한다. 하나라도 따로 놀면 실패.

### MEMORY.md 과부하 방지 규칙

- 에피소드 상세 교훈은 `episodes/epXXX/feedback.json` 저장
- MEMORY.md: 시스템 규칙 + 최신 교훈만 (200줄 이내)
- 코드와 CLAUDE.md가 진실의 소스

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
3. 관련 파일만 명시적으로 add
4. 메시지 형식: `prefix: 한 줄 요약 (한국어 또는 영어)`
5. 커밋 실행 후 `git status`로 결과 확인

### "푸시해줘" 요청 시 수행 절차
1. `git log --oneline -5`로 미푸시 커밋 확인
2. 내용 요약 후 **푸시 전 확인 요청** (자동 푸시 없음)
3. 승인 후 `git push origin main`

### CHANGELOG.md 업데이트
시스템 변경(feat/fix/refactor) 커밋 시 `docs/CHANGELOG.md` 상단에 항목 추가:
```
## [vXX] YYYY-MM-DD
### Added / Changed / Removed
- 변경 내용
```

## 스킬 라우팅

| 트리거 | 스킬 |
|--------|------|
| "글쓰기 시작" / 대본 작성 | `enometa-writing` |
| "제작 시작" / 파이프라인 | `enometa-produce` |
| "업로드 준비" / publish | `enometa-publish` |
| "피드백" / 리뷰 | `enometa-feedback` |

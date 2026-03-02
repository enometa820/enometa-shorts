# ENOMETA Shorts Pipeline v6 — Claude Code 실행 기획안

> **역할**: Brief=실전 매뉴얼 (CLI 명령, 검증 체크리스트). 설계도는 SNAPSHOT 참조.
> 이 문서를 Claude Code에 전달하면 에피소드 제작을 시작할 수 있다.
> 상세 시스템 문서: ENOMETA_SYSTEM_SNAPSHOT_v6.md 참조
> 음악 엔진 상세: ENOMETA_Music_Engine_Spec_v6.md 참조
> **last_updated**: 2026-03-03 — 문서 리팩토링 (중복 제거, SNAPSHOT과 역할 분리)

---

## 프로젝트 개요

> 상세: SYSTEM_SNAPSHOT Sec.1 참조

대본 + 제목만 입력하면 Claude Code가 나머지 전부를 처리한다.
**핵심**: 3중 리액티브 비주얼 (시간 x 오디오 x 의미), ikeda 단일 장르, Hybrid 전용 VRAM

---

## 기술 스택

| 역할 | 도구 | 비고 |
|------|------|------|
| 영상 프레임워크 | Remotion (React) | 코드 기반 영상 생성, CPU |
| TTS 나레이션 | Edge-TTS | 무료, ko-KR-SunHiNeural |
| BGM 생성 | enometa_music_engine.py v8 | Pure Python, ikeda 단일 장르 + 텍스처 모듈 확장 |
| 비주얼 엔진 | Canvas 2D + SVG (Remotion) + Python (numpy+Pillow) | Hybrid: Python 배경 + Remotion 오버레이 |
| 오디오 분석 | numpy FFT | 프레임별 bass/mid/high/rms/onset |
| 오디오 믹싱 | ffmpeg | TTS:BGM = 4:6 (나레이션 67% + BGM 100%) + 사이드체인 덕킹 |
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
[STEP 3] 제목 5개 제시 → 사용자 선택 → 제작 파이프라인 진행
```

### 제작 파이프라인 (컨펌 후)
```
입력: script.txt + title

[1] TTS 생성 → narration.wav + narration_timing.json (Edge-TTS)
[2] 대본 데이터 추출 → script_data.json (v6 신규, ikeda 등 데이터 기반 장르용)
[3] 비주얼 스크립트 생성 → visual_script.json (v8: 항상 ikeda + hybrid)
[4] BGM 생성 → bgm.wav + raw_visual_data.npz (v8 --export-raw --script-data, ikeda 단일)
[5] Python 비주얼 렌더링 → frames/*.png (hybrid 모드, v6 9개 레이어)
[6] 오디오 믹싱 → mixed.wav (TTS:BGM = 4:6, 나레이션 67% + BGM 100% + 사이드체인 덕킹)
[7] FFT 분석 → audio_analysis.json (numpy)
[8] Remotion 합성 → output.mp4 (hybrid: Python 배경 + vocab 오버레이 + 제목/자막)

출력: 1080x1920 MP4
```

---

## 비주얼/음악/팔레트 상세

> 22개 vocab 컴포넌트 목록: SYSTEM_SNAPSHOT Sec.4 참조
> 음악 엔진 악기 26종 + 합성법 9종: Music_Engine_Spec 참조
> 컬러 팔레트 8종: SYSTEM_SNAPSHOT Sec.7 참조
> visual_script_generator가 자동 선택하므로 CLI 실행 시 수동 지정 불필요

---

## 에피소드 제작 실행

```bash
# [1] TTS 생성 (Edge-TTS 전용 — Chatterbox 사용 금지)
py scripts/generate_voice_edge.py \
  episodes/epXXX/narration_timing.json \
  episodes/epXXX/narration.wav

# [2] 대본 데이터 추출 (v2 — 사전 대폭 확장 + 미등록 단어 감지)
py scripts/script_data_extractor.py \
  episodes/epXXX/narration_timing.json
# → script_data.json 출력: keywords[].intensity + segments[].semantic_intensity + unregistered_words 포함
# → 검증: JSON 열어서 semantic_intensity 값이 0.1~0.9 범위에 분포하는지 확인
# → 미등록 단어 리포트 자동 출력. 대화형 업데이트: --update-dict 옵션
# → 사전: VERB=101, EMOTION=68, SCIENCE=85, CHEM=19, BODY=30 + custom_dictionary.json

# [3] 비주얼 스크립트 (v8: 항상 ikeda + hybrid)
# ⚠ --title 필수! 미지정 시 "제목 미지정"이 영상에 표시됨
py scripts/visual_script_generator.py \
  episodes/epXXX/narration_timing.json \
  --strategy ikeda --episode epXXX --title "에피소드 실제 제목"

# [4] BGM 생성 (v8 ikeda 단일 + export-raw + script-data + arc)
py scripts/enometa_music_engine.py \
  --from-visual episodes/epXXX/visual_script.json \
  --export-raw --arc narrative \
  --script-data episodes/epXXX/script_data.json \
  --episode epXXX \
  episodes/epXXX/narration_timing.json \
  episodes/epXXX/bgm.wav
# --genre 옵션 제거 (v8: 항상 ikeda)
# ⚠ ikeda: 리듬/멜로디 구조 필수
# --arc: narrative(기승전결) | crescendo(점진) | flat(아크없음) | adaptive(si곡선기반, script-data필수) — 기본 narrative

# [5] Python 비주얼 렌더링 (v8 hybrid 전용, ikeda 레이어)
py scripts/visual_renderer.py \
  episodes/epXXX/visual_script.json \
  episodes/epXXX/raw_visual_data.npz \
  episodes/epXXX/script_data.json \
  episodes/epXXX/frames/
# → frames를 public/epXXX/frames/ 에 복사 (Remotion staticFile용)
# → v8: ikeda 프리셋 7레이어(Music 3+TTS 4), blend_ratio=0.45
# → TTS 레이어가 semantic_intensity에 따라 크기/색상/이펙트 자동 변조
# → 검증: 조용한 대사 프레임(si≈0.1)과 극적 대사 프레임(si≈0.9) 비교하여 시각 차이 확인

# [6] 오디오 믹싱 (TTS:BGM = 4:6, 사이드체인 덕킹)
py scripts/audio_mixer.py \
  episodes/epXXX/narration.wav \
  episodes/epXXX/bgm.wav \
  public/epXXX/mixed.wav \
  --sidechain episodes/epXXX/narration_timing.json

# [7] FFT 분석
py scripts/audio_analyzer.py \
  public/epXXX/mixed.wav \
  episodes/epXXX/audio_analysis.json 30

# [8] Remotion 합성 (hybrid: Python 배경 + vocab 오버레이)
# Root.tsx durationInFrames 업데이트 후:
npx remotion render EP00X episodes/epXXX/output.mp4 --concurrency=4
```

---

## 업로드 메타데이터 생성 (publish.md)

에피소드 제작 완료 후 `episodes/epXXX/publish.md` 생성:

```markdown
# EP0XX — "에피소드 제목"

## 제목
에피소드 제목

## YouTube 설명란
(에피소드 요약 — 2~3문장)

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
(에피소드 핵심 인용구 + 질문)

─────────────────────────
ENOMETA | 데이터아트 × 철학
존재와 사유, 그 경계를 초월하다

대본의 텍스트는 바이트 시퀀스와 주파수 스펙트럼으로 분해됩니다
추출된 의미 강도(Semantic Intensity)가
음악의 텍스처 밀도와 비주얼의 파티클 거동을 실시간으로 결정합니다
모든 프레임은 시간 × 오디오 × 의미의
3중 리액티브 시스템으로 생성됩니다

코드로 쓰는 철학. 데이터로 그리는 존재론.

## 태그
#태그1 #태그2 #태그3 #태그4 #태그5
```

### 태그 규칙
- 에피소드 주제 기반 **카테고리 상위 5개만** 생성
- **고정 제외 태그** (publish.md에 절대 포함 금지):
  - `#쇼츠` `#shorts` `#ENOMETA` `#이노메타` `#데이터아트`
  - 위 태그는 YouTube 업로드 시 별도 처리

### 고정 멘트 규칙 (설명란 + 고정댓글 하단 필수)
- 설명란/고정댓글 각각 본문 아래 `─────────────────────────` 구분선 후 삽입
- 고정 멘트 문구는 변경 불가 (위 템플릿 그대로 사용)

---

## v6.2 semantic_intensity 검증 체크리스트

```
□ script_data.json에 segments[].semantic_intensity 필드 존재
□ keywords[].intensity 필드 존재 (0-1 범위)
□ semantic_intensity 값이 0.1~0.9 범위에 고르게 분포 (전부 0.5 근처면 비정상)
□ Python 렌더링 프레임에서 조용한 대사↔극적 대사 시각 차이 확인
  - TextDataLayer: 카드 크기/색상/이펙트 변화
  - DataStreamLayer: 스크롤 속도/폰트 크기 변화
  - BarcodeLayer: 선폭/높이/맥동 변화
```

---

*이 기획안을 Claude Code에 전달하면 에피소드 제작이 시작된다.*

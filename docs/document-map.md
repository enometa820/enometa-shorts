# 문서 지도 — ENOMETA 프로젝트

> 이 프로젝트의 모든 문서와 역할을 정리한 인덱스.

## 구조

```
enometa-shorts/
├─ CLAUDE.md                          ← 시스템 규칙 (진실의 소스)
├─ README.md                          ← 프로젝트 개요 (외부용)
├─ 메모장.md                           ← 개인 메모
│
├─ .claude/
│  ├─ rules/
│  │  └─ model-switching.md           ← 모델 전환 프로토콜
│  └─ skills/
│     ├─ enometa-writing.md           ← 글쓰기 워크플로우 (v13)
│     ├─ enometa-produce.md           ← 제작 파이프라인
│     ├─ enometa-publish.md           ← 업로드 준비
│     ├─ enometa-feedback.md          ← 피드백 리뷰
│     └─ enometa-finalize.md          ← 마무리/커밋/푸시
│
├─ docs/
│  ├─ document-map.md                 ← 이 파일
│  ├─ reactive-architecture.md        ← 대본×음악×비주얼 리액티브 현황
│  ├─ visual-architecture.md          ← 비주얼 3파트 구조
│  ├─ CHANGELOG.md                    ← 변경 이력
│  ├─ dev-concepts.md                 ← 개발 개념 사전
│  ├─ vision-roadmap.md               ← 비전 로드맵 (제네레이티브+리액티브 목표)
│  └─ decisions/                      ← ADR (설계 결정 기록)
│     ├─ 001-kiwipiepy-vs-konlpy.md
│     ├─ 002-edge-tts.md
│     ├─ 003-hybrid-render.md
│     ├─ 004-fixed-volume-no-cr.md
│     ├─ 005-music-engine-monolith.md
│     └─ 006-genre-rename-v18.md
│
├─ episodes/epXXX/
│  ├─ feedback.json                   ← 에피소드별 피드백
│  └─ publish.md                      ← 업로드용 제목/설명/태그
│
└─ (auto-memory)
   └─ MEMORY.md                       ← 세션 간 기억 (Claude 전용)
```

---

## 역할별 분류

### 규칙 (코드 변경 시 반드시 동기화)

| 문서 | 역할 | 수정 빈도 |
|------|------|----------|
| `CLAUDE.md` | 절대 규칙, 파이프라인 명령, 아키텍처 개요 | 시스템 변경 시 |
| `MEMORY.md` | 세션 간 교훈, 에피소드 로그, 사용자 선호 | 매 세션 자동 |
| `.claude/rules/model-switching.md` | Sonnet/Opus 전환 기준 | 거의 안 바뀜 |

### 워크플로우 (작업 절차)

| 문서 | 트리거 | 수정 빈도 |
|------|--------|----------|
| `enometa-writing.md` | "글쓰기 시작" | 글쓰기 방법론 변경 시 |
| `enometa-produce.md` | "제작 시작" | 파이프라인 변경 시 |
| `enometa-publish.md` | "업로드 준비" | 거의 안 바뀜 |
| `enometa-feedback.md` | "피드백" | 거의 안 바뀜 |
| `enometa-finalize.md` | "마무리" | 거의 안 바뀜 |

### 참조 (이해와 판단을 위한 것)

| 문서 | 역할 | 수정 빈도 |
|------|------|----------|
| `reactive-architecture.md` | 대본→음악→비주얼 데이터 흐름 | 아키텍처 변경 시 |
| `visual-architecture.md` | 비주얼 레이어 구조 | 비주얼 변경 시 |
| `dev-concepts.md` | 개발 용어 사전 | 새 개념 등장 시 |
| `CHANGELOG.md` | 버전별 변경 기록 | 매 커밋 |
| `vision-roadmap.md` | 비전 로드맵 — 제네레이티브+리액티브 목표, 레퍼런스 | 방향성 변경 시 |

### 설계 결정 (한 번 쓰고 거의 안 봄)

| 문서 | 결정 내용 |
|------|----------|
| `001-kiwipiepy-vs-konlpy.md` | 형태소 분석기 → kiwipiepy |
| `002-edge-tts.md` | TTS 엔진 → Edge-TTS |
| `003-hybrid-render.md` | 렌더 방식 → Python+Remotion 하이브리드 |
| `004-fixed-volume-no-cr.md` | 볼륨 고정, 콜앤리스폰스 제거 |
| `005-music-engine-monolith.md` | 음악 엔진 단일 파일 유지 |
| `006-genre-rename-v18.md` | 장르 이름 변경 (v18) |

---

## 동기화 규칙

- **코드 변경** → `CLAUDE.md` + 해당 스킬 파일 + `CHANGELOG.md` 동시 업데이트
- **아키텍처 변경** → `reactive-architecture.md` 또는 `visual-architecture.md` 업데이트
- **새로운 설계 결정** → `docs/decisions/NNN-*.md` 추가
- **에피소드 완료** → `episodes/epXXX/feedback.json` 작성, `MEMORY.md`에 교훈 반영
- **severity=major 피드백** → `CLAUDE.md` 또는 코드에 즉시 반영

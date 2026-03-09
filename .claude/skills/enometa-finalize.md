---
name: enometa-finalize
description: >
  작업 종료 전 문서 동기화 검증 + 커밋/푸시 스킬.
  코드 변경 후 관련 문서가 모두 최신 상태인지 교차 검증한다.
  트리거 키워드 - 마무리, 종료, finalize, 커밋해줘, wrap up
---

# ENOMETA Finalize — 문서 동기화 검증 + 커밋/푸시

## 실행 조건
- 코드 변경이 1개 이상 있을 때
- 사용자가 커밋/푸시를 요청했을 때
- 작업 세션 종료 시

## STEP 1: 변경 파일 스캔

```bash
git status
git diff --name-only HEAD
```

변경된 파일 목록에서 **영향 범위**를 판단한다:

| 변경 영역 | 영향받는 문서 |
|-----------|-------------|
| `src/components/vocab/*.tsx` | CLAUDE.md (vocab 목록), README.md (vocab 테이블), visual-architecture.md |
| `src/components/*.tsx` | README.md (구조도), visual-architecture.md |
| `scripts/enometa_music_engine.py` | CLAUDE.md (음악 규칙), README.md (장르 테이블) |
| `scripts/visual_*.py` | visual-architecture.md, README.md (레이어 테이블) |
| `.claude/skills/*.md` | CLAUDE.md (스킬 라우팅 테이블) |
| `CLAUDE.md` | MEMORY.md (규칙 동기화) |

## STEP 2: 교차 검증 체크리스트

아래 항목을 **자동으로** 검증한다. 불일치 발견 시 표로 보고.

### A. 버전 일관성
- [ ] CHANGELOG.md 최상단 버전 == MEMORY.md 버전 참조
- [ ] visual-architecture.md 버전 헤더가 최신

### B. 숫자 일관성
- [ ] PostProcess 효과 수: visual-architecture.md == README.md == 실제 코드 (PostProcess.tsx JSX 블록 수)
- [ ] Vocab 종수: CLAUDE.md vocab 목록 == README.md vocab 테이블 == VisualSection.tsx VOCAB_MAP 키 수
- [ ] 음악 장르 수: CLAUDE.md == README.md == enometa-produce.md
- [ ] 팔레트 수: CLAUDE.md == README.md == enometa-produce.md

### C. 설명 일관성
- [ ] SymbolMotion 설명: README.md vocab 테이블 == visual-architecture.md (SVG? ASCII? 그리드?)
- [ ] AsciiArt 모드: CLAUDE.md == README.md == 실제 코드
- [ ] 비주얼 장르 매핑: CLAUDE.md == README.md == visual_script_generator.py

### D. 메모리 동기화
- [ ] MEMORY.md가 200줄 이내
- [ ] CLAUDE.md 절대 규칙 변경 시 → MEMORY.md에도 반영됨
- [ ] 새 교훈/패턴 발견 시 → MEMORY.md 또는 하위 파일에 기록됨

## STEP 3: 검증 결과 보고

```
📋 문서 동기화 검증 결과
├─ ✅ 버전 일관성: OK (v22)
├─ ✅ PostProcess 효과 수: 8 (코드=문서)
├─ ⚠️ Vocab 수 불일치: CLAUDE.md(32) ≠ README.md(30)
├─ ✅ 장르/팔레트: OK
├─ ✅ 설명 일관성: OK
└─ ✅ 메모리: 180줄 (200줄 이내)

수정 필요: 1건
→ CLAUDE.md vocab 목록에서 2개 누락 확인. 수정할까요?
```

불일치가 있으면:
1. 구체적 위치(파일:라인)와 불일치 내용 제시
2. 수정 방향 제안
3. 사용자 승인 후 수정

불일치가 없으면 STEP 4로 바로 진행.

## STEP 4: 커밋

CLAUDE.md 커밋 규칙을 따른다:

1. `git status`로 변경 파일 확인
2. 변경 성격 판단 → prefix 결정 (feat/fix/docs/refactor/ep)
3. `feat:` / `fix:` / `refactor:` 커밋이면 CHANGELOG.md 상단에 항목 추가
4. 관련 파일만 명시적으로 `git add` (git add . 금지)
5. 대용량 바이너리 제외 (wav 파일 등)
6. 커밋 실행 + 브리핑 출력

```
✅ 커밋 완료
├─ [prefix] 메시지
├─ 파일 N개 변경 (+추가 -삭제)
└─ 해시: xxxxxxx
```

## STEP 5: 푸시 (사용자 요청 시)

1. 미푸시 커밋 목록 출력
2. 승인 요청
3. 승인 후 `git push origin main`

```
🚀 푸시 대상 커밋 N개
├─ xxxxxxx feat: ...
├─ xxxxxxx docs: ...
└─ xxxxxxx ep: ...
푸시할까요?
```

## 검증 범위 축소 규칙

- `ep:` 커밋 (에피소드 산출물만): STEP 2 스킵 → 바로 커밋
- `docs:` 커밋 (문서만): B/C 숫자/설명 검증만 실행
- `feat:` / `fix:` / `refactor:`: 전체 검증 실행

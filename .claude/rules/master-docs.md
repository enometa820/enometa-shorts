# 마스터 문서 최신화 규칙

## 마스터 문서 목록

| 파일 | 역할 | 위치 |
|------|------|------|
| ENOMETA_SYSTEM_SNAPSHOT_{날짜}.md | 전체 시스템 설계도 | docs/ |
| ENOMETA_ClaudeCode_Brief_{날짜}.md | CLI 실행 매뉴얼 | docs/ |
| ENOMETA_Hybrid_Visual_Architecture_{날짜}.md | Python+Remotion 아키텍처 | docs/ |
| ENOMETA_Music_Engine_Spec_{날짜}.md | 음악 엔진 상세 | docs/ |
| ENOMETA_Visual_Differentiation_Spec_{날짜}.md | 비주얼 차별화 시스템 | docs/ |

## 네이밍 규칙

`ENOMETA_{이름}_{YYYYMMDD}.md` — 버전 번호 대신 날짜로 구분.
날짜는 마지막으로 내용이 수정된 날짜.

## 최신화 트리거

다음 중 하나라도 해당하면 마스터 문서 최신화 필수:

1. **시스템 코드 변경**: vocab 추가/삭제, 컴포넌트 구조 변경, 파이프라인 수정
2. **피드백 반영**: feedback_defaults.json에 새 규칙 추가
3. **음악 엔진 변경**: 합성 함수, 레이어, 마스터링 체인 수정
4. **비주얼 시스템 변경**: z-order, 위치 규칙, 새 패턴
5. **에피소드 완료 후 피드백 처리**: 에피소드별 feedback.json 작성 시

## 최신화 체크리스트

시스템 변경 발생 시 아래 5개 문서를 순회하며 해당 섹션 업데이트:

```
□ SYSTEM_SNAPSHOT — 변경된 컴포넌트/아키텍처 섹션 업데이트 + 진화 로그
□ ClaudeCode_Brief — 검증 체크리스트 + CLI 명령 + 기술 스택 테이블
□ Hybrid_Visual_Architecture — Remotion 컴포넌트 섹션 + 레이어 조합
□ Music_Engine_Spec — 합성 함수/악기/마스터링 + audio_mixer 연동
□ Visual_Differentiation_Spec — EMOTION_VOCAB_POOL + 전략 + z-order
```

추가 문서:
```
□ FEEDBACK_LOG.md — 피드백 처리 시 에피소드 항목 추가
□ CHANGELOG.md — 모든 변경 기록
□ MEMORY.md — 핵심 교훈 + 문서 테이블 이름
□ feedback_defaults.json — 시스템 누적 규칙
□ episodes/epXXX/feedback.json — 에피소드별 피드백 기록
```

## 상호 참조 규칙

- 마스터 문서 파일명 변경 시, 다른 마스터 문서 내 상호 참조도 함께 업데이트
- CHANGELOG.md의 과거 기록은 변경하지 않음 (역사적 기록 유지)
- MEMORY.md의 문서 테이블 이름 업데이트
- CLAUDE.md에는 파일명이 아닌 역할명으로 참조 (변경 불필요)

## 커밋 규칙

- 마스터 문서 최신화는 시스템 코드 변경과 동일 커밋에 포함
- 커밋 메시지에 `docs:` prefix 사용 가능
- 최신화 누락 방지: 코드 변경 완료 후 "마스터 문서 최신화 필요?" 자문

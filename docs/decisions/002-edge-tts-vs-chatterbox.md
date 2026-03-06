# 002. Edge-TTS 선택 — Chatterbox(로컬 AI) 대신

**날짜**: 2026-02-01 (프로젝트 초기)
**상태**: 결정됨

## 컨텍스트

TTS 엔진 선택. Chatterbox(로컬 AI TTS)와 Edge-TTS(Microsoft 클라우드 TTS) 비교.

## 결정

Edge-TTS 전용. Chatterbox 사용 금지.

## 이유

- Chatterbox: GPU 필요, 음질 불안정, 생성 속도 느림, 환경 의존성 복잡
- Edge-TTS: 무료, GPU 불필요, 음질 안정적, `edge-tts` pip 패키지 한 줄
- ko-KR-SunHiNeural 음성이 한국어 콘텐츠에 적합
- 비용 0원 원칙 유지

## 결과

`scripts/generate_voice_edge.py` 단일 스크립트.
`generate_voice.py`(Chatterbox) 파일은 삭제됨. CLAUDE.md에 "절대 금지" 명시.

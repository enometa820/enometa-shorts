# 002. Edge-TTS 선택

**날짜**: 2026-02-01 (프로젝트 초기)
**상태**: 결정됨

## 결정

Edge-TTS (Microsoft 무료 클라우드 TTS) 전용.

## 이유

- 무료, GPU 불필요, 음질 안정적
- `edge-tts` pip 패키지로 설치 간단
- ko-KR-SunHiNeural 음성이 한국어 콘텐츠에 적합
- 비용 0원 원칙 유지

## 결과

`scripts/generate_voice_edge.py` 단일 스크립트.

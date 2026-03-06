# 005. 음악 엔진 모놀리스 유지 — 패키지 분리 포기

**날짜**: 2026-03-06
**상태**: 결정됨

## 컨텍스트

`scripts/enometa_music_engine.py` (~4,382줄 모놀리스)와 `scripts/enometa_music/` 패키지가 동시에 존재했다.
패키지는 모놀리스를 분리하려는 리팩토링 시도였으나 마이그레이션이 미완료 상태였다.

## 결정

`scripts/enometa_music/` 패키지 삭제. 모놀리스 단일 파일 유지.

## 이유

- 패키지는 현재 아무것도 import하지 않는 데드 코드
- v14 악기 업그레이드, v16 CR 비활성 변경사항이 모놀리스에만 반영됨
- 패키지와 모놀리스 sync 맞추는 작업 > 얻는 이득
- `enometa_render.py`가 모놀리스를 subprocess로 직접 실행 → 경로 안정

## 결과

`scripts/enometa_music/` 디렉토리 삭제 (7개 파일, 4,576줄 데드 코드 제거).
`scripts/enometa_music_engine.py` 단독 진실의 소스.

## 향후 리팩토링 조건

모놀리스가 10,000줄을 넘어서 특정 기능 수정이 불가능해질 때 재검토.
그 전까지는 함수/섹션 내 docstring으로 가독성 유지.

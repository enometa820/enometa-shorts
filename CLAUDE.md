# ENOMETA 프로젝트 지침

## 절대 규칙

- **환경**: `py` 명령 사용 (`python`은 Windows Store alias 문제). entry point: `src/index.tsx`
- **TTS**: `scripts/generate_voice_edge.py` 전용. `generate_voice.py`(Chatterbox) **절대 금지**
- **글쓰기**: 대본 컨펌 전 제목/음악/비주얼 등 후속 단계 진행 **금지** (글 컨펌 게이트)
- **비주얼**: render_mode 항상 `"hybrid"` (legacy 모드 제거됨)
- **음악**: ikeda 단일 장르. 순수 노이즈 금지, 리듬+멜로디 최소 구조 필수
- **오디오**: TTS:BGM = 4:6 (narration_volume=0.67, bgm_volume=1.0), 사이드체인 덕킹
- **태그**: 주제 기반 5개만. 고정 제외 태그(`#쇼츠` `#shorts` `#ENOMETA` `#이노메타` `#데이터아트`) 포함 금지

## 문서 프로토콜

시스템 변경 시 → `memory/protocols.md` 체크리스트 실행.
SNAPSHOT(설계도) + Brief(실전 매뉴얼) 항상 쌍으로 업데이트.

## 스킬 라우팅

| 트리거 | 스킬 |
|--------|------|
| "글쓰기 시작" / 대본 작성 | `enometa-writing` |
| "제작 시작" / 파이프라인 | `enometa-produce` |
| "업로드 준비" / publish | `enometa-publish` |
| "피드백" / 리뷰 | `enometa-feedback` |

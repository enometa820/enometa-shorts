# 006. 프로토타입 무드 → 실존 언더그라운드 장르 리네이밍 (v18)

**날짜**: 2026-03-07
**상태**: 결정됨

## 컨텍스트

음악 무드 9종(raw, ambient, ikeda, experimental, minimal, chill, glitch, intense, techno)이
프로토타입 단계에서 감성 형용사로 명명되었다.
EP010에서 EP009와 BGM이 동일하게 들리는 문제를 조사하면서 구조적 한계 발견:

1. **이름이 구현을 안내하지 못함**: "raw"가 뭔지, "intense"가 뭔지 코딩할 때 참조할 레퍼런스가 없음
2. **BPM/악기/리듬이 장르 간 겹침**: 대부분 같은 saw+arp 조합, BPM만 다름
3. **장르 정체성 부재**: "어떤 아티스트/씬의 어떤 소리"라는 구체적 목표 없이 파라미터만 조절

## 결정

5개 프로토타입 무드를 실존 언더그라운드 전자음악 장르로 교체.
4개(ambient, minimal, glitch, techno)는 이미 실존 장르명이므로 유지.

| 이전 | 이후 | 레퍼런스 아티스트/씬 |
|------|------|---------------------|
| raw | acid | Phuture, DJ Pierre, TB-303 |
| ikeda | microsound | Ryoji Ikeda, Alva Noto, Curtis Roads |
| experimental | IDM | Aphex Twin, Autechre, Boards of Canada |
| chill | dub | Basic Channel, Rhythm & Sound, Deepchord |
| intense | industrial | Perc, Ansome, Surgeon |

## 이유

- **코딩 가이드**: "acid"라고 쓰면 TB-303 acid bass가 있어야 하고, "dub"라고 쓰면 tape delay가 있어야 함 → 구현이 자동으로 따라옴
- **3축 분화 강제**: 장르명이 BPM 범위, 고유 악기, 리듬 패턴을 자연스럽게 결정
- **청취 레퍼런스**: 각 장르에 실존 아티스트가 있으므로 "이 음악처럼" 비교 가능

## 하위호환

`_LEGACY_MOOD_MAP` 딕셔너리로 자동 변환:
```python
_LEGACY_MOOD_MAP = {"raw": "acid", "ikeda": "microsound", "experimental": "IDM", "chill": "dub", "intense": "industrial"}
music_mood = _LEGACY_MOOD_MAP.get(music_mood, music_mood)
```
- `generate()` 진입점과 `generate_music_script()` 두 곳에 배치
- 기존 `narration_timing.json`에 이전 무드명이 있어도 정상 동작
- CLI `--music-mood` 선택지는 새 이름만 노출

## 결과

- 신규 합성 함수 3개: `tape_delay()`, `distorted_kick()`, `chord_stab()`
- 9개 `_MOOD_LAYERS` 전면 재설계 (장르별 고유 레이어 스택)
- `generate()` 연속 렌더러 게이팅 확장 (10개 레이어 중 장르별 ON/OFF)
- 검증: glitch(BPM 99, tight kick, no saw/arp) vs dub(BPM 112, boomy kick, no saw/arp) vs techno(BPM 128, punchy kick, full layers) — 확연한 차이 확인

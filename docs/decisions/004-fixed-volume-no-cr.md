# 004. 볼륨 고정 원칙 — CR/song_arc 비활성

**날짜**: 2026-03-06 (v16)
**상태**: 결정됨

## 컨텍스트

BGM에 여러 동적 볼륨 변조 기능이 있었다:
- **Call-and-Response (CR)**: 드럼/멜로디가 2마디 주기로 75%↔100% 교대
- **song_arc**: 섹션별 전체 볼륨 커브
- **SI modulation**: semantic_intensity에 따른 볼륨 변조
- **breath system**: 음악 호흡감을 위한 주기적 볼륨 변동

EP008 피드백: "마디마다 소리가 작아지는 느낌". 원인을 추적한 결과 CR 엔벨로프가 주범.

## 결정

v16부터 모든 동적 볼륨 변조 비활성. 볼륨은 항상 1.0 고정.

```python
# v16
self._cr_drum_env = np.ones(self.total_samples)
self._cr_melody_env = np.ones(self.total_samples)
```

에너지 표현은 레이어 ON/OFF로만 한다.

## 이유

- 볼륨 변조가 여러 겹으로 쌓이면 의도치 않은 감쇠 패턴 발생
- "한 곡의 원칙": 고정 BPM + 고정 패턴 + 고정 볼륨 → 레이어 추가/제거로 에너지 변화
- 5ms anti-click만 유지 (클릭 노이즈 방지)

## 결과

`scripts/enometa_music_engine.py`에서 CR/song_arc/breath/SI modulation 비활성.
마스터 페이드 제거. `[v16] Volume: FIXED` 로그로 확인 가능.

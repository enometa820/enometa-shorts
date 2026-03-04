# ENOMETA 피드백 통합 로그

> 에피소드별 피드백 → 원인 분석 → 해결 내역을 한눈에.
> 기계적 기록은 `episodes/epXXX/feedback.json`, 이 문서는 사람이 읽는 통합 뷰.

---

## EP007 — "알고리즘은 쌓지 않는다. 덜어낸다"

**날짜**: 2026-03-04 | **점수**: 미부여 | **총 12건** (critical 1, major 7, normal 4)

| # | 영역 | 피드백 | 원인 | 해결 | 심각도 |
|---|------|--------|------|------|--------|
| F07-01 | audio | 섀넌 파트 BGM 볼륨 급변 | SI값 낮은 씬 → density/intensity 급감 | v10 SI 변조 95~105% 안정화 | major |
| F07-02 | audio | TTS:BGM 밸런스 — BGM 과다 | narration 0.55, bgm 1.5 (1:2.7) | narration=0.90, bgm=1.0, loudnorm -14 LUFS | major |
| F07-03 | subtitle | 자막 알고리즘 붕괴 — 여러 자막 동시 | EP007 세그먼트 과도하게 김 (max 71자) | EP005 원본 복원 + splitSegmentToSentences() | critical |
| F07-04 | typography | 타이포 모션 단일 패턴 반복 | text_reveal mode=wave 하드코딩 | 4모드 랜덤 + 6색상 + fontSize/position 다양화 | major |
| F07-05 | typography | 타이포 텍스트 범위 고정 | 단어만 사용 | 60% 단어 + 25% 구절 + 15% 짧은 문장 | major |
| F07-06 | typography | 타이포 색상 고정 흰색 | accent 색 하드코딩 | 6색상 풀 랜덤 선택 | normal |
| F07-07 | shapemotion | ShapeMotion 화면 밖 + 모션 단순 | bottom 기반 좌표 오류 + 단일 spring | 5패턴 재구현 + top 기반 비주얼 영역 내 배치 | normal |
| F07-08 | endcard | 엔드카드 BGM 없음 + 태그라인 안보임 | BGM atrim, duration=first, fontSize 18 | output_duration=max, duration=longest, 스타일 개선 | major |
| F07-09 | visual | TextReveal 자막 영역 침범 | position="bottom" → 자막과 겹침 | "bottom"→"upper" + posY 클램프 | major |
| F07-10 | visual | PixelGrid 코드 비주얼 부각 부족 | DOM 순서에 따른 낮은 z-order | zIndex: 5 추가, PostProcess zIndex: 10 래퍼 | normal |
| F07-11 | endcard | 태그라인 크기/화려함 부족 | fontSize 30, fontWeight 400, 파티클 없음 | fontSize 48, 700, 스태거+밑줄+파티클 180개 | major |
| F07-12 | audio | BGM 볼륨 갑자기 급감 (si_gate) | si_gate 계단 함수 (min 0.1, 0.3s 스무딩) | 연속 함수 (min 0.45, 1.0s 스무딩) | major |

### 시스템 변경사항 (F07-01~08)
- `audio_mixer.py`: narration_volume=0.90, bgm_volume=1.0, output_duration=max
- `SubtitleSection.tsx`: EP005 원본 복원 + splitSegmentToSentences()
- `ShapeMotion.tsx`: 5패턴 재구현, 비주얼 영역 내 배치
- `TextReveal.tsx`: 4모드 모션 + 오디오 리액티브 + 결정론적 글리치
- `visual_script_generator.py`: text_reveal 파라미터 다양화
- `enometa_music_engine.py`: BGM duration +8초 (endcard 커버)
- `LogoEndcard.tsx`: 태그라인 스타일 개선

### 시스템 변경사항 (F07-09~12)
- `visual_script_generator.py`: TextReveal "bottom"→"upper", Lissajous vocab 추가
- `TextReveal.tsx`: "upper" 위치 추가, "bottom" 안전 클램프
- `PixelGrid.tsx`: zIndex: 5
- `PostProcess.tsx`: zIndex: 10 div 래퍼
- `LogoEndcard.tsx`: 태그라인 스태거+밑줄+파티클 전면 강화
- `enometa_music_engine.py`: si_gate 연속 함수 (min 0.45, 1.0s 스무딩)
- `Lissajous.tsx`: 신규 vocab 컴포넌트

### 교훈
- SubtitleSection은 EP005 원본 레퍼런스 유지 — @remotion/captions 리라이트는 호환성 파괴 위험
- "텍스트 모션 다양화" = 자막이 아닌 비주얼 타이포그래피(TextReveal) 의미
- ShapeMotion은 top 기반 배치 — bottom 기반 시 YouTube UI에 가려짐
- si_gate는 계단 함수 금지 — 연속 함수 + 충분한 스무딩(≥1.0s) 필수
- TextReveal position="bottom"은 자막 충돌 위험 — "upper"로 대체

---

## EP005 — "공포와 각성의 화학식은 같다"

**날짜**: 2026-03-02 | **점수**: 5/10 | **총 4건** (major 4)

| # | 영역 | 피드백 | 원인 | 해결 | 심각도 |
|---|------|--------|------|------|--------|
| 1 | music | ikeda 음악이 노이즈에 가까움 | sine interference + ultrahigh만으로 음악 아님 | ikeda 리듬/멜로디 최소 구조 필수 규칙 | major |
| 2 | visual | Python 비주얼 단조로운 반복 | SineWave/Barcode/DataStream 패턴 고정 | 다양한 패턴 혼합 + vocab 다양화 | major |
| 3 | visual | hybrid 모드에서 Remotion vocab 미활성 | hybrid 코드에서 vocab 오버레이 누락 | VisualSection hybrid 블록에 vocab 렌더링 추가 | major |
| 4 | visual | Remotion 모션그래픽/텍스트 미활용 | 구현 누락 | TextReveal, ShapeMotion 등 vocab 적극 활용 | major |

### 시스템 변경사항
- `VisualSection.tsx`: hybrid 블록에 vocab 시맨틱 오버레이 추가
- `feedback_defaults.json`: visual_defaults 규칙 3개 + mixing_defaults 추가
- ikeda 장르 규칙: "순수 노이즈 금지, 리듬+멜로디 최소 구조 필수"

### 교훈
- hybrid 모드 = Python 배경 + Remotion 오버레이 동시 사용
- ikeda라도 최소한의 리듬/멜로디 구조 필요
- 씬마다 다른 비주얼 전략 — 단조로운 반복 금지

---

*최종 업데이트: 2026-03-04*

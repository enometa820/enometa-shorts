# EP007 수정 계획
> 작성: 2026-03-04 | 기반: feedback.json EP007

---

## 우선순위 분류

| 단계 | 항목 | 영역 | 상태 |
|------|------|------|------|
| P0 | 자막 알고리즘 붕괴 수정 (F07-03) | SubtitleSection.tsx | 미완 |
| P1 | BGM:TTS 볼륨 밸런스 (F07-02) | audio_mixer.py | 미완 |
| P1 | 섀넌 파트 BGM 급변 (F07-01) | visual_script / music_engine | 미완 |
| P2 | 자막 문장 단위 전환 (F07-05) | SubtitleSection.tsx | P0와 동시 |
| P2 | 텍스트 모션 다양화 (F07-04, F07-06, F07-07) | SubtitleSection.tsx | 미완 |
| P3 | 도형 모션그래픽 추가 (F07-08) | 신규 컴포넌트 | 미완 |

---

## STEP 0 — 사전 진단 (자막 붕괴)

### 원인 분석
현재 `segmentsToWordCaptions`는 segment를 **단어 단위**로 쪼개 Caption 배열을 만든다.
`createTikTokStyleCaptions({ combineTokensWithinMilliseconds: 1500 })`는 이를 다시 1.5초 단위 페이지로 묶는다.

**의심 버그**:
1. `page.durationMs`가 0 또는 undefined인 경우 → `fadeOut` interpolate 폭발
2. Sequence `durationInFrames`가 계산 과정에서 특정 페이지에서 비정상적으로 커지는 경우 (Infinity 클램프 미흡)
3. 단어 간 타이밍 누적 오차로 페이지 경계가 어긋나 중복 렌더링

### 수정 방향
```
segmentsToWordCaptions (단어 단위)
  → segmentsToCaptions (문장 단위, segment 1개 = Caption 1개)
```
각 segment의 text 전체를 하나의 Caption으로 만들면:
- 타이밍 정확도 보장 (narration_timing.json 직접 사용)
- createTikTokStyleCaptions가 여러 segment를 자연스럽게 묶음
- 단어 내 하이라이트는 token.fromMs/toMs 기반으로 유지 가능

---

## STEP 1 — 자막 붕괴 수정 + 문장 단위 전환 (P0+P2)

### 파일: `src/components/SubtitleSection.tsx`

#### 변경 1: Caption 생성 함수 교체
```tsx
// Before: 단어 단위 선형 분할
function segmentsToWordCaptions(segments: NarrationSegment[]): Caption[] { ... }

// After: segment = Caption 1:1 (문장 단위)
function segmentsToCaptions(segments: NarrationSegment[]): Caption[] {
  return segments.map((seg) => ({
    text: seg.text,
    startMs: seg.start_sec * 1000,
    endMs: seg.end_sec * 1000,
    timestampMs: seg.start_sec * 1000,
    confidence: null,
  }));
}
```

#### 변경 2: combineTokensWithinMilliseconds 상향
```tsx
// Before: 1500ms (단어 묶기)
combineTokensWithinMilliseconds: 1500

// After: 4000ms (2~3문장 자연 묶기)
combineTokensWithinMilliseconds: 4000
```

#### 변경 3: durationInFrames 안전화
```tsx
// totalFrames 기반 상한 클램프 추가
const { fps, durationInFrames: totalFrames } = useVideoConfig();
const endFrame = Math.min(
  nextPage ? Math.floor((nextPage.startMs / 1000) * fps) : totalFrames,
  startFrame + Math.ceil((SWITCH_CAPTIONS_EVERY_MS / 1000) * fps),
);
```

#### 변경 4: SWITCH_CAPTIONS_EVERY_MS 상향
```tsx
const SWITCH_CAPTIONS_EVERY_MS = 4000; // 1500 → 4000
```

---

## STEP 2 — 볼륨 밸런스 수정 (P1)

### 파일: `scripts/audio_mixer.py`

```python
# Before
narration_volume: float = 0.67,  # 함수 기본값
# main()에서: narration_volume=0.55, bgm_volume=1.5

# After: TTS:BGM ≈ 1:1
narration_volume=0.90, bgm_volume=1.0
```

loudnorm -14 LUFS는 유지 (최종 정규화 담당).

### 섀넌 파트 급변 대응
- `episodes/ep007/visual_script.json`에서 섀넌 구간 씬 SI값 확인
- 음악 엔진에서 SI 변조 최소값 상향: `max(0.6, si)` → `max(0.75, si)` 검토
- 이 항목은 다음 에피소드 엔진 수정으로 반영 (EP007은 이미 렌더됨)

---

## STEP 3 — 텍스트 모션 다양화 (P2)

### 패턴 풀 (4종)
emotion별로 진입 패턴을 다르게 적용:

| 패턴 | emotion | 설명 |
|------|---------|------|
| A: 슬라이드 업 | intro, resolution | 하단→현재 위치 spring 슬라이드 |
| B: 스케일 인 | tension, climax | 작게→크게 spring scale |
| C: 타이프라이터 | awakening | 문자 하나씩 등장 (slice 기반) |
| D: 플래시 컷 | buildup | 빠른 opacity on/off + 위치 흔들림 |

### 위치 다양화
```tsx
// emotion별 position 변화
const getPosition = (emotion: string, index: number) => {
  if (emotion.includes('awakening')) return { bottom: 400 }; // 중앙
  if (emotion.includes('climax')) return { bottom: 300 };    // 중앙 아래
  return { bottom: 550 };                                     // 기본
};
```

### 컬러 매핑
```tsx
const EMOTION_COLORS: Record<string, { base: string; highlight: string }> = {
  awakening: { base: '#FFFFFF', highlight: '#FFD700' },
  tension:   { base: '#FFCCAA', highlight: '#FF4500' },
  climax:    { base: '#E0E0FF', highlight: '#00FFFF' },
  intro:     { base: '#CCCCCC', highlight: '#FFFFFF' },
  default:   { base: '#FFFFFF', highlight: '#FFD700' },
};
```

### fontSize 동적 변화
```tsx
const fontSize = {
  climax:    72,
  awakening: 66,
  tension:   58,
  default:   52,
}[emotionKey] ?? 52;
```

---

## STEP 4 — 도형 모션그래픽 (P3)

### 새 파일: `src/components/ShapeMotion.tsx`
emotion별 기하학적 도형 레이어:

| emotion | 도형 | 애니메이션 |
|---------|------|-----------|
| tension | 사각형 테두리 | spring scale, rotate |
| climax | 원형 펄스 | opacity 파동, scale |
| awakening | 수평선 2개 | 좌→우 spring 슬라이드 |
| intro | 점 3개 | stagger 페이드인 |

Root.tsx 또는 SubtitleSection 내부에서 씬 emotion 기반 렌더링.

---

## 작업 순서 (에피소드 8 전까지)

```
STEP 0: 자막 붕괴 원인 코드 수준 확인 (진단)
  └─ narration_timing.json으로 SubtitleSection 로컬 테스트
STEP 1: SubtitleSection.tsx 수정 → Remotion Studio 검증
STEP 2: audio_mixer.py 볼륨 수정 → EP007 재믹싱으로 검증
STEP 3: 텍스트 모션 패턴 추가 → Remotion Studio 검증
STEP 4: ShapeMotion.tsx 추가 → 통합 검증
```

---

## 시스템 변경 사항 (다음 에피소드부터 기본 적용)

| 항목 | 이전 | 이후 |
|------|------|------|
| narration_volume | 0.55 | 0.90 |
| bgm_volume | 1.5 | 1.0 |
| 자막 단위 | 단어 | 문장(segment) |
| SWITCH_CAPTIONS_MS | 1500 | 4000 |
| 텍스트 애니메이션 | fadeIn/Out 1종 | 4종 rotation |

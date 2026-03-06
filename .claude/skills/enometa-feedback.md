---
name: enometa-feedback
description: >
  ENOMETA 에피소드 피드백 수집 및 시스템 반영 스킬.
  에피소드 확인 후 구조화된 피드백 수집 → feedback.json 생성 → 패턴 분석 → 시스템 반영.
  트리거 키워드 - 피드백, 리뷰, 평가, feedback, 에피소드 확인
---

# ENOMETA Feedback Collection System

## 전제 조건
- 에피소드 제작 완료 + 사용자가 영상을 확인한 상태

## 워크플로우

### 1단계: 피드백 수집

사용자에게 아래 항목을 질문하여 구두 피드백을 받는다:

- **전체 평점** (1-10)
- **음악**: 좋았던 점 / 나빴던 점 / 평점(1-5)
- **비주얼**: 좋았던 점 / 나빴던 점 / 평점(1-5)
- **나레이션**: 좋았던 점 / 나빴던 점 / 평점(1-5)
- **대본**: 좋았던 점 / 나빴던 점 / 평점(1-5)
- **시스템 개선 제안** (있다면)

### 2단계: feedback.json 생성

`episodes/epXXX/feedback.json` 구조:

```json
{
  "episode": "epXXX",
  "date": "YYYY-MM-DD",
  "overall_rating": 7,
  "music": { "rating": 3, "liked": ["..."], "disliked": ["..."] },
  "visual": { "rating": 4, "liked": ["..."], "disliked": ["..."] },
  "narration": { "rating": 4, "liked": ["..."], "disliked": ["..."] },
  "script": { "rating": 4, "liked": ["..."], "disliked": ["..."] },
  "issues": [
    { "type": "music|visual|narration|script|pipeline", "target": "구체적 대상", "detail": "설명", "severity": "minor|major" }
  ],
  "system_suggestions": ["..."]
}
```

### 3단계: 패턴 분석

이전 에피소드의 feedback.json을 스캔하여 반복 패턴 확인:

```
episodes/ep001/feedback.json
episodes/ep002/feedback.json
...
episodes/epXXX/feedback.json (방금 작성)
```

### 4단계: 시스템 반영

| 조건 | 행동 |
|------|------|
| severity = major | 즉시 `scripts/feedback_defaults.json`에 반영 |
| 같은 issue type+target 2회 이상 반복 | `feedback_defaults.json`에 기본값으로 반영 |
| 사용자가 "항상/절대" 표현 사용 | 즉시 `feedback_defaults.json` + MEMORY.md |

### 5단계: 문서 업데이트

시스템 변경이 발생한 경우 `memory/protocols.md`의 범위별 선택적 Read 규칙에 따라 마스터 문서 업데이트.

### 6단계: 요약 보고

사용자에게 보고:
```
## EP0XX 피드백 요약
- 전체 평점: X/10
- 이번 EP에서 배운 것: ...
- 다음 EP에 반영될 변경: ...
- 시스템 업데이트: (있으면 목록)
```

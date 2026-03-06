# 003. Hybrid 렌더 — Python 프레임 + Remotion 오버레이

**날짜**: 2026-02-15 (EP005 이후)
**상태**: 결정됨

## 컨텍스트

비주얼 렌더링 방식 선택.
- **순수 Remotion**: React 컴포넌트만으로 비주얼 생성
- **순수 Python**: numpy+Pillow로 모든 프레임 생성
- **Hybrid**: Python 배경 프레임 + Remotion 오버레이

## 결정

Hybrid 방식 고정. `render_mode: "hybrid"` 항상.

## 이유

- Python이 수치 계산(FFT, SI 연동, 파형 레이어링)에 유리
- Remotion이 타이포그래피/애니메이션/오디오 싱크에 유리
- 두 가지 장점을 조합: Python이 배경 프레임을 미리 렌더링하고 Remotion이 오버레이
- 순수 Remotion으로 3중 리액티브 비주얼(시간×오디오×의미) 구현은 복잡도가 지나치게 높음

## 결과

- `scripts/visual_renderer.py`: numpy+Pillow 배경 프레임 → `episodes/epXXX/frames/*.png`
- `src/components/PythonFrameBackground.tsx`: 프레임 시퀀스 재생
- `src/components/VisualSection.tsx`: 프레임 배경 위에 Remotion vocab 오버레이
- legacy 모드(순수 Python) 제거됨

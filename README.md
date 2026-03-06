# enometa-shorts

YouTube Shorts 자동 생성 파이프라인.
대본만 쓰면 TTS / BGM / 비주얼 / 영상 렌더링까지 자동 처리된다.

## 빠른 시작

```bash
# 전체 파이프라인 (에피소드 폴더에 script.txt 필요)
py scripts/enometa_render.py episodes/ep009 --title "제목" --palette c64

# Remotion 프리뷰
npx remotion studio --port 3000
```

## 문서

- [파이프라인 구조 / 명령어 / 규칙](CLAUDE.md)
- [아키텍처 결정 기록](docs/decisions/)
- [변경 이력](docs/CHANGELOG.md)

## 스택

- **영상**: Remotion (React)
- **TTS**: Edge-TTS (ko-KR-SunHiNeural)
- **BGM**: numpy 직접 합성 (`scripts/enometa_music_engine.py`)
- **비주얼**: Python (numpy + Pillow) + Remotion 오버레이

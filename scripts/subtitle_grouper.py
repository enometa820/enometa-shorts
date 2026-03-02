"""
ENOMETA 자막 2줄 그루핑
narration_timing.json 세그먼트 → 2줄씩 묶은 subtitle_groups.json 출력

사용법:
  python subtitle_grouper.py <narration_timing.json> [output.json]
"""

import sys
import os
import json
from typing import List, Dict, Any


def group_subtitles(
    segments: List[Dict[str, Any]],
    lines_per_group: int = 2,
    max_chars: int = 40,
) -> List[Dict[str, Any]]:
    """세그먼트를 lines_per_group줄씩 묶어 자막 그룹 생성.

    너무 긴 문장은 단독 그룹으로 처리.
    """
    groups: List[Dict[str, Any]] = []
    buffer: List[Dict[str, Any]] = []

    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue

        buffer.append(seg)

        # 버퍼가 가득 차거나, 현재 문장이 길면 그룹 확정
        total_chars = sum(len(s["text"]) for s in buffer)
        if len(buffer) >= lines_per_group or total_chars > max_chars:
            groups.append(_make_group(buffer, len(groups)))
            buffer = []

    # 나머지
    if buffer:
        groups.append(_make_group(buffer, len(groups)))

    return groups


def _make_group(segs: List[Dict[str, Any]], idx: int) -> Dict[str, Any]:
    """세그먼트 목록 → 하나의 자막 그룹"""
    lines = [s["text"].strip() for s in segs]
    return {
        "id": f"sub_{idx + 1:03d}",
        "start_sec": round(segs[0]["start_sec"], 3),
        "end_sec": round(segs[-1]["end_sec"], 3),
        "lines": lines,
        "text": "\n".join(lines),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python subtitle_grouper.py <narration_timing.json> [output.json]")
        sys.exit(1)

    timing_path = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None

    with open(timing_path, 'r', encoding='utf-8') as f:
        timing_data = json.load(f)

    segments = timing_data["segments"]
    groups = group_subtitles(segments)

    if output is None:
        output = os.path.join(os.path.dirname(timing_path), "subtitle_groups.json")

    with open(output, 'w', encoding='utf-8') as f:
        json.dump({"groups": groups, "total": len(groups)}, f, ensure_ascii=False, indent=2)

    print(f"=== Subtitle Grouper ===")
    print(f"  Segments: {len(segments)} → Groups: {len(groups)}")
    print(f"  Saved: {output}")


if __name__ == "__main__":
    main()

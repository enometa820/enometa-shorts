"""
pre_commit_check.py

ENOMETA 커밋 전 체크리스트 hook
트리거: Bash 도구로 git commit 명령 실행 시

체크 항목:
  1. CHANGELOG  — feat:/fix:/refactor: 커밋 시 docs/CHANGELOG.md staged 필수 (강제 블록)
  2. decisions  — feat:/refactor: 커밋 시 아키텍처 결정 remind (소프트)

exit 0 → 통과
exit 2 → 블록 + stdout 내용을 Claude에게 피드백
"""

import sys
import json
import subprocess
import re
import os

tool_input_str = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
try:
    tool_input = json.loads(tool_input_str)
except Exception:
    sys.exit(0)

command = tool_input.get("command", "")

if "git commit" not in command:
    sys.exit(0)

has_code_prefix = bool(re.search(r"(feat|fix|refactor):", command))
has_decision_prefix = bool(re.search(r"(feat|refactor):", command))

if not has_code_prefix:
    sys.exit(0)

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
result = subprocess.run(
    ["git", "diff", "--cached", "--name-only"],
    capture_output=True, text=True, cwd=repo_root
)
staged = result.stdout

messages = []

# Hook 1: CHANGELOG 강제 체크
if "docs/CHANGELOG.md" not in staged:
    messages.append("[CHANGELOG 누락] docs/CHANGELOG.md 가 staged 에 없습니다.")
    messages.append("  feat:/fix:/refactor: 커밋은 CHANGELOG 업데이트 필수입니다.")
    messages.append("  -> docs/CHANGELOG.md 업데이트 후 git add 하고 다시 커밋하세요.")

# Hook 2: decisions 소프트 remind (CHANGELOG 통과 후에만 표시)
if not messages and has_decision_prefix and "docs/decisions/" not in staged:
    messages.append("[decisions 확인] A vs B 결정 또는 아키텍처 변경이 포함되나요?")
    messages.append("  -> 해당하면: docs/decisions/NNN-*.md 추가 후 다시 커밋")
    messages.append("  -> 해당 없으면: 그냥 다시 커밋하면 통과됩니다")

if messages:
    print("\n".join(messages))
    sys.exit(2)

sys.exit(0)

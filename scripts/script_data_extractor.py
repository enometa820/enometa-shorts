"""
ENOMETA Script Data Extractor

대본 텍스트를 컴퓨터가 해석하는 과정 자체를 데이터로 변환.
음악 엔진과 비주얼 렌더러 양쪽에 공급.

사용법:
  py scripts/script_data_extractor.py episodes/ep005/narration_timing.json
"""

import sys
import os
import json
import re
from functools import reduce
from operator import xor


# ============================================================
# 한글 분해 (Unicode Hangul Decomposition)
# ============================================================
HANGUL_BASE = 0xAC00
CHO_LIST = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
JUNG_LIST = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")
JONG_LIST = [""] + list("ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ")


def hangul_decompose(char):
    """한글 음절 → 초성/중성/종성 분해"""
    code = ord(char)
    if not (0xAC00 <= code <= 0xD7A3):
        return None
    offset = code - HANGUL_BASE
    cho = offset // (21 * 28)
    jung = (offset % (21 * 28)) // 28
    jong = offset % 28
    return {
        "char": char,
        "cho": cho, "cho_name": CHO_LIST[cho],
        "jung": jung, "jung_name": JUNG_LIST[jung],
        "jong": jong, "jong_name": JONG_LIST[jong],
        "has_batchim": jong > 0,
        "complexity": 2 + (1 if jong > 0 else 0),
    }


# ============================================================
# 단어 → 데이터 변환
# ============================================================
def word_to_data(word):
    """단어를 고유 데이터 시그니처로 변환"""
    encoded = word.encode('utf-8')
    raw_bytes = list(encoded)
    byte_sum = sum(raw_bytes)
    byte_var = sum((b - byte_sum / len(raw_bytes)) ** 2 for b in raw_bytes) / len(raw_bytes)
    xor_val = reduce(xor, raw_bytes, 0)

    # 한글 분해
    hangul_info = []
    for ch in word:
        decomp = hangul_decompose(ch)
        if decomp:
            hangul_info.append(decomp)

    return {
        "word": word,
        "raw_bytes": raw_bytes,
        "hex": encoded.hex(),
        "binary": ' '.join(f'{b:08b}' for b in encoded),
        "byte_count": len(encoded),
        "char_count": len(word),
        "bytes_per_char": round(len(encoded) / max(len(word), 1), 2),
        "byte_sum": byte_sum,
        "byte_variance": round(byte_var, 2),
        "xor_hash": xor_val,
        "xor_hex": f"0x{xor_val:02X}",
        "freq_hz": round(byte_sum % 880 + 220, 1),
        "hangul": hangul_info,
    }


def number_to_data(num):
    """숫자를 다중 표현으로 변환"""
    n = float(num)
    int_n = int(n) if n == int(n) else None

    result = {
        "value": n,
        "decimal": str(num),
        "scientific": f"{n:.2e}",
    }

    if int_n is not None and 0 <= int_n <= 65535:
        result["binary"] = f"{int_n:016b}" if int_n > 255 else f"{int_n:08b}"
        result["hex"] = f"0x{int_n:04X}" if int_n > 255 else f"0x{int_n:02X}"
        result["octal"] = f"0o{int_n:o}"
    else:
        # 소수점 표현
        result["binary"] = float_to_binary(n)
        result["hex"] = f"0x{abs(n):.4f}"

    # 주파수/주기 매핑
    if n > 20:
        result["freq_hz"] = round(n, 2)
        result["period_ms"] = round(1000.0 / n, 3) if n > 0 else 0
    elif n > 0:
        result["freq_hz"] = round(1.0 / n, 2)
        result["period_ms"] = round(n * 1000, 3)

    return result


def float_to_binary(n):
    """소수를 이진 근사로 표현"""
    int_part = int(abs(n))
    frac_part = abs(n) - int_part
    int_bin = f"{int_part:08b}"
    frac_bin = ""
    for _ in range(8):
        frac_part *= 2
        if frac_part >= 1:
            frac_bin += "1"
            frac_part -= 1
        else:
            frac_bin += "0"
    return f"{int_bin}.{frac_bin}"


# ============================================================
# 간이 토큰화 (한국어)
# ============================================================
PARTICLES = {"가", "이", "를", "을", "는", "은", "의", "에", "에서", "로", "으로",
             "와", "과", "도", "만", "부터", "까지", "처럼", "보다"}

CHEMICALS = {"코르티솔", "아드레날린", "도파민", "노르에피네프린", "세로토닌",
             "엔도르핀", "옥시토신", "GABA", "글루타메이트"}
BODY_PARTS = {"편도체", "전두엽", "해마", "시상하부", "뇌", "심장", "심박수",
              "호흡", "손바닥", "몸"}
SCIENCE_TERMS = {"화학식", "회로", "신호", "패턴", "수치", "실험", "데이터",
                 "반응", "분비", "급등", "상승", "하강",
                 # 컴퓨팅/시스템 (v11 확장)
                 "알고리즘", "네트워크", "시냅스", "최적화", "시뮬레이션", "변수", "함수",
                 "코드", "연산", "프로세스", "루프", "재귀",
                 # 철학/인문학 (v11 확장)
                 "존재", "본질", "의식", "인식", "자아", "자유의지",
                 "구조", "메커니즘", "역학", "확률", "통계"}

# ============================================================
# Semantic Intensity 룩업 테이블
# ============================================================
VERB_ENERGY = {
    # 최고 에너지 (0.85~0.9)
    "폭발": 0.9, "급등": 0.9, "폭주": 0.9, "분비": 0.85, "터지": 0.85,
    "치솟": 0.85,
    # 고에너지 (0.7~0.8)
    "초월": 0.8, "관통": 0.8, "휩쓸": 0.8, "뒤흔들": 0.8, "쏟아지": 0.8, "돌진": 0.8,
    "해체": 0.75, "전복": 0.75, "찢": 0.75, "질주": 0.75, "가속": 0.75, "각성": 0.75,
    "깨우": 0.7, "오르": 0.7, "상승": 0.7, "올라가": 0.7, "재정의": 0.7, "발산": 0.7,
    # 중고 에너지 (0.5~0.65)
    "밀려오": 0.65, "수렴": 0.65, "작동": 0.6, "최적화": 0.6, "성장": 0.6,
    "연산": 0.55, "탐구": 0.55, "순환": 0.5, "성찰": 0.5, "사유": 0.5, "움직이": 0.5,
    # 중에너지 (0.3~0.45)
    "응시": 0.45, "흐르": 0.45, "퍼지": 0.4, "스며들": 0.3, "감싸": 0.3,
    # 저에너지 (0.1~0.2)
    "같": 0.2, "보이": 0.2, "하": 0.15, "되": 0.15, "있": 0.1,
}

EMOTION_INTENSITY = {
    # 최고 강도 (0.85~0.9)
    "공포": 0.9, "경악": 0.9, "두려움": 0.85, "혼돈": 0.85, "비탄": 0.85,
    # 고강도 (0.7~0.8)
    "전율": 0.8, "경외": 0.8, "숭고": 0.8, "각성": 0.75, "해방": 0.75, "경이": 0.75,
    "흥분": 0.7, "자각": 0.7,
    # 중강도 (0.4~0.65)
    "쾌감": 0.65, "긴장": 0.65, "불안": 0.6, "초조": 0.6, "허무": 0.6,
    "집중": 0.5, "몰입": 0.5, "연민": 0.5, "기대": 0.45, "호기심": 0.4, "체념": 0.4,
    # 저강도 (0.1~0.2)
    "안정": 0.2, "평온": 0.1, "고요": 0.1,
}

# 키워드 타입별 기본 intensity
KEYWORD_TYPE_INTENSITY = {
    "noun": 0.3,
    "verb": 0.5,
    "chemical": 0.7,
    "body": 0.7,
    "science": 0.5,
    "number": 0.6,
}


def tokenize_korean(text):
    """간이 한국어 토큰화"""
    # 숫자, 한글 단어, 문장부호 분리
    pattern = r'(\d+\.?\d*|[가-힣]+|[.!?,;:])'
    raw_tokens = re.findall(pattern, text)

    tokens = []
    for t in raw_tokens:
        if re.match(r'^\d+\.?\d*$', t):
            tokens.append({"text": t, "type": "number", "position": len(tokens)})
        elif t in '.!?,;:':
            tokens.append({"text": t, "type": "punct", "position": len(tokens)})
        elif t in PARTICLES:
            tokens.append({"text": t, "type": "particle", "position": len(tokens)})
        elif t in CHEMICALS:
            tokens.append({"text": t, "type": "chemical", "position": len(tokens)})
        elif t in BODY_PARTS:
            tokens.append({"text": t, "type": "body", "position": len(tokens)})
        elif t in SCIENCE_TERMS:
            tokens.append({"text": t, "type": "science", "position": len(tokens)})
        else:
            # 조사 분리 시도
            separated = False
            for p in sorted(PARTICLES, key=len, reverse=True):
                if t.endswith(p) and len(t) > len(p):
                    stem = t[:-len(p)]
                    stem_type = "noun"
                    if stem in CHEMICALS:
                        stem_type = "chemical"
                    elif stem in BODY_PARTS:
                        stem_type = "body"
                    elif stem in SCIENCE_TERMS:
                        stem_type = "science"
                    tokens.append({"text": stem, "type": stem_type, "position": len(tokens)})
                    tokens.append({"text": p, "type": "particle", "position": len(tokens)})
                    separated = True
                    break
            if not separated:
                # 동사/형용사 어미 분리
                if t.endswith(("다", "한다", "된다", "진다", "있다", "없다")):
                    tokens.append({"text": t, "type": "verb", "position": len(tokens)})
                else:
                    tokens.append({"text": t, "type": "noun", "position": len(tokens)})

    return tokens


# ============================================================
# Semantic Intensity 계산
# ============================================================
def compute_semantic_intensity(text, tokens, data_density):
    """
    문장의 의미 강도(0.05~1.0) 계산.
    verb_score×0.30 + emotion_score×0.30 + structure_score×0.20 + density_score×0.20
    """
    # 1. Verb score: 동사 토큰에서 어간 매칭, 최대값
    verb_score = 0.0
    for t in tokens:
        if t["type"] == "verb":
            word = t["text"]
            for stem, energy in VERB_ENERGY.items():
                if stem in word:
                    verb_score = max(verb_score, energy)

    # 2. Emotion score: 모든 토큰에서 감정어 매칭, 최대값
    emotion_score = 0.0
    for t in tokens:
        word = t["text"]
        if word in EMOTION_INTENSITY:
            emotion_score = max(emotion_score, EMOTION_INTENSITY[word])
        # 부분 매칭 (합성어 내부 감정어)
        for emo, val in EMOTION_INTENSITY.items():
            if emo in word and len(emo) >= 2:
                emotion_score = max(emotion_score, val * 0.8)

    # 3. Structure score: 문장 구조 요소
    structure_score = 0.0
    text_stripped = text.strip()
    char_count = len(text_stripped.replace(" ", ""))
    if char_count <= 15:
        structure_score += 0.3  # 짧은 문장 = 임팩트
    elif char_count <= 25:
        structure_score += 0.15
    if text_stripped.endswith("!"):
        structure_score += 0.15
    if text_stripped.endswith("?"):
        structure_score += 0.1
    # 다중 문장 (마침표 여러 개)
    sentence_count = text.count(".") + text.count("!") + text.count("?")
    if sentence_count >= 2:
        structure_score += 0.15
    structure_score = min(structure_score, 1.0)

    # 4. Density score: 데이터 밀도 + 과학/화학/신체 키워드 보너스
    density_score = data_density
    special_count = sum(1 for t in tokens if t["type"] in ("chemical", "body", "science"))
    density_score += special_count * 0.1
    density_score = min(density_score, 1.0)

    # 가중 합산
    intensity = (
        verb_score * 0.30
        + emotion_score * 0.30
        + structure_score * 0.20
        + density_score * 0.20
    )

    return round(max(0.05, min(1.0, intensity)), 3)


def compute_keyword_intensity(kw_text, kw_type):
    """키워드별 개별 intensity 계산"""
    base = KEYWORD_TYPE_INTENSITY.get(kw_type, 0.3)

    # 동사: VERB_ENERGY 룩업
    if kw_type == "verb":
        for stem, energy in VERB_ENERGY.items():
            if stem in kw_text:
                base = max(base, energy)
                break

    # 감정어 매칭
    if kw_text in EMOTION_INTENSITY:
        base = max(base, EMOTION_INTENSITY[kw_text])

    return round(min(1.0, base), 2)


# ============================================================
# 문장 분석
# ============================================================
def analyze_sentence(text):
    """문장 구조 분석"""
    tokens = tokenize_korean(text)
    numbers = [float(t["text"]) for t in tokens if t["type"] == "number"]

    # 문장 유형 판별
    text_stripped = text.strip()
    if text_stripped.endswith("?"):
        stype = "question"
    elif text_stripped.endswith("!"):
        stype = "exclamation"
    elif text_stripped.endswith("."):
        stype = "statement"
    else:
        stype = "fragment"

    # 핵심 단어 추출 (조사/문장부호 제외)
    keywords = [t for t in tokens if t["type"] not in ("particle", "punct")]

    # 데이터 밀도 계산 (semantic_intensity보다 먼저)
    data_elements = len(numbers) + len([t for t in tokens if t["type"] in ("chemical", "body", "science")])
    total_content = len([t for t in tokens if t["type"] not in ("particle", "punct")])
    data_density = min(1.0, data_elements / max(total_content, 1) + len(numbers) * 0.15)

    # 단어별 데이터 시그니처 + 키워드별 intensity
    word_data = []
    for kw in keywords:
        kw_intensity = compute_keyword_intensity(kw["text"], kw["type"])
        if kw["type"] == "number":
            word_data.append({
                "text": kw["text"],
                "type": "number",
                "intensity": kw_intensity,
                "number_data": number_to_data(kw["text"]),
                "word_data": word_to_data(kw["text"]),
            })
        else:
            word_data.append({
                "text": kw["text"],
                "type": kw["type"],
                "intensity": kw_intensity,
                "word_data": word_to_data(kw["text"]),
            })

    # Semantic intensity 계산
    semantic_intensity = compute_semantic_intensity(text, tokens, data_density)

    return {
        "tokens": tokens,
        "token_count": len(tokens),
        "numbers": numbers,
        "sentence_type": stype,
        "char_count": len(text.replace(" ", "")),
        "byte_count": len(text.encode("utf-8")),
        "data_density": round(data_density, 2),
        "semantic_intensity": semantic_intensity,
        "keywords": word_data,
    }


# ============================================================
# 단위 추출
# ============================================================
UNIT_PATTERNS = [
    (r'분당\s*(\d+)', 'BPM'),
    (r'(\d+\.?\d*)\s*초', 'sec'),
    (r'(\d+\.?\d*)\s*%', 'percent'),
    (r'(\d+\.?\d*)\s*Hz', 'Hz'),
    (r'(\d+\.?\d*)\s*dB', 'dB'),
]


def extract_units(text):
    """문맥 기반 단위 추출"""
    units = []
    for pattern, unit in UNIT_PATTERNS:
        matches = re.findall(pattern, text)
        for m in matches:
            units.append({"value": float(m), "unit": unit})
    return units


# ============================================================
# 메인: 전체 추출
# ============================================================
def extract_script_data(narration_timing_path):
    """narration_timing.json → script_data.json"""
    with open(narration_timing_path, 'r', encoding='utf-8') as f:
        timing = json.load(f)

    segments_out = []
    all_numbers = []
    all_chemicals = set()
    freq_map = {}

    for seg in timing.get("segments", []):
        text = seg["text"]
        analysis = analyze_sentence(text)
        units = extract_units(text)

        # 화학물질/신체 추출
        chemicals_found = []
        for kw in analysis["keywords"]:
            if kw["type"] == "chemical":
                chemicals_found.append(kw["text"])
                all_chemicals.add(kw["text"])

        # 숫자 수집
        for n in analysis["numbers"]:
            all_numbers.append(n)
            # freq_map: 숫자 → 주파수
            if n > 20:
                freq_map[str(n)] = round(n, 2)
            elif n > 0:
                freq_map[str(n)] = round(1.0 / n, 2)

        segment_data = {
            "index": seg["index"],
            "text": text,
            "start_sec": seg["start_sec"],
            "end_sec": seg["end_sec"],
            "duration_sec": seg["duration_sec"],
            "analysis": analysis,
            "units": units,
            "chemicals": chemicals_found,
        }
        segments_out.append(segment_data)

    # 글로벌 데이터
    global_data = {
        "all_numbers": sorted(set(all_numbers)),
        "all_chemicals": sorted(all_chemicals),
        "freq_map": freq_map,
        "total_segments": len(segments_out),
        "total_duration_sec": timing.get("total_duration_sec", 0),
    }

    return {
        "metadata": {
            "episode": os.path.basename(os.path.dirname(narration_timing_path)),
            "source": os.path.basename(narration_timing_path),
            "version": 1,
        },
        "segments": segments_out,
        "global": global_data,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: py scripts/script_data_extractor.py <narration_timing.json> [output.json]")
        sys.exit(1)

    input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    else:
        output_path = os.path.join(os.path.dirname(input_path), "script_data.json")

    print(f"=== ENOMETA Script Data Extractor ===")
    print(f"  Input: {input_path}")

    result = extract_script_data(input_path)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 요약 출력
    g = result["global"]
    print(f"  Segments: {g['total_segments']}")
    print(f"  Numbers found: {g['all_numbers']}")
    print(f"  Chemicals found: {g['all_chemicals']}")
    print(f"  Freq map: {g['freq_map']}")
    print(f"  Output: {output_path}")

    # 세그먼트별 데이터 밀도 + semantic intensity
    for seg in result["segments"]:
        density = seg["analysis"]["data_density"]
        si = seg["analysis"]["semantic_intensity"]
        kw_count = len(seg["analysis"]["keywords"])
        si_bar = "█" * int(si * 10) + "░" * (10 - int(si * 10))
        text_preview = seg['text'][:35]
        try:
            print(f"  [{seg['index']:02d}] {si_bar} si={si:.2f} d={density:.2f} kw={kw_count} | {text_preview}")
        except UnicodeEncodeError:
            print(f"  [{seg['index']:02d}] si={si:.2f} d={density:.2f} kw={kw_count}")


if __name__ == "__main__":
    main()

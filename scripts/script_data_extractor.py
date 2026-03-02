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
from pathlib import Path


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
             "엔도르핀", "옥시토신", "GABA", "글루타메이트",
             # v11.1 확장
             "멜라토닌", "테스토스테론", "에스트로겐", "인슐린", "글리코겐",
             "아세틸콜린", "히스타민", "프로락틴", "바소프레신", "ATP"}

BODY_PARTS = {"편도체", "전두엽", "해마", "시상하부", "뇌", "심장", "심박수",
              "호흡", "손바닥", "몸",
              # v11.1 확장
              "측두엽", "두정엽", "후두엽", "소뇌", "뇌간", "대뇌피질", "시냅스",
              "뉴런", "축삭", "수상돌기", "신경세포", "척수", "미주신경",
              "동공", "피부", "혈관", "근육", "폐", "위장", "간"}

SCIENCE_TERMS = {"화학식", "회로", "신호", "패턴", "수치", "실험", "데이터",
                 "반응", "분비", "급등", "상승", "하강",
                 # 컴퓨팅/시스템
                 "알고리즘", "네트워크", "최적화", "시뮬레이션", "변수", "함수",
                 "코드", "연산", "프로세스", "루프", "재귀", "캐시", "버퍼",
                 "대역폭", "지연시간", "처리량", "병렬", "직렬", "모듈", "인터페이스",
                 "컴파일", "런타임", "스택", "큐", "트리", "그래프", "해시",
                 # 데이터/수학
                 "확률", "통계", "평균", "분산", "표준편차", "상관", "회귀",
                 "분포", "정규분포", "빈도", "비율", "퍼센트", "편차", "중앙값",
                 # 뇌과학/생물
                 "가소성", "전위", "활성화", "억제", "흥분성", "수용체", "전달물질",
                 "리듬", "진동", "주파수", "진폭", "파장", "스펙트럼",
                 # 철학/인문학
                 "존재", "본질", "의식", "인식", "자아", "자유의지",
                 "구조", "메커니즘", "역학", "현상", "실체", "범주", "명제",
                 "귀납", "연역", "인과", "상관", "필연", "우연", "결정론"}

# ============================================================
# Semantic Intensity 룩업 테이블
# ============================================================
VERB_ENERGY = {
    # 최고 에너지 (0.85~0.9) — 파괴/폭발/극단
    "폭발": 0.9, "급등": 0.9, "폭주": 0.9, "붕괴": 0.9, "전멸": 0.9,
    "분비": 0.85, "터지": 0.85, "치솟": 0.85, "추락": 0.85, "압도": 0.85,
    "소멸": 0.85, "잠식": 0.85, "침식": 0.85,
    # 고에너지 (0.7~0.8) — 변혁/관통/초월
    "초월": 0.8, "관통": 0.8, "휩쓸": 0.8, "뒤흔들": 0.8, "쏟아지": 0.8, "돌진": 0.8,
    "전복": 0.8, "침투": 0.8, "뚫": 0.8, "격돌": 0.8,
    "해체": 0.75, "찢": 0.75, "질주": 0.75, "가속": 0.75, "각성": 0.75,
    "점령": 0.75, "지배": 0.75, "압축": 0.75, "증폭": 0.75, "삼키": 0.75,
    "깨우": 0.7, "오르": 0.7, "상승": 0.7, "올라가": 0.7, "재정의": 0.7, "발산": 0.7,
    "돌파": 0.7, "해방": 0.7, "분열": 0.7, "충돌": 0.7, "제거": 0.7, "소진": 0.7,
    # 중고 에너지 (0.5~0.65) — 변화/이동/작용
    "밀려오": 0.65, "수렴": 0.65, "흡수": 0.65, "확산": 0.65, "변환": 0.65,
    "작동": 0.6, "최적화": 0.6, "성장": 0.6, "진화": 0.6, "활성화": 0.6,
    "소모": 0.6, "축적": 0.6, "전환": 0.6, "이탈": 0.6,
    "연산": 0.55, "탐구": 0.55, "복제": 0.55, "변형": 0.55, "증가": 0.55,
    "순환": 0.5, "성찰": 0.5, "사유": 0.5, "움직이": 0.5, "반복": 0.5,
    "처리": 0.5, "저장": 0.5, "전달": 0.5, "생성": 0.5, "삭제": 0.5,
    # 중에너지 (0.3~0.45) — 정적 변화/관찰
    "응시": 0.45, "흐르": 0.45, "멈추": 0.45, "기다리": 0.45, "지나가": 0.45,
    "퍼지": 0.4, "감소": 0.4, "줄어들": 0.4, "식": 0.4, "가라앉": 0.4,
    "스며들": 0.3, "감싸": 0.3, "머무르": 0.3, "쉬": 0.3, "놓": 0.3,
    # 저에너지 (0.1~0.2) — 상태/존재
    "같": 0.2, "보이": 0.2, "느끼": 0.2, "알": 0.2, "모르": 0.2,
    "하": 0.15, "되": 0.15, "나": 0.15, "가": 0.15,
    "있": 0.1, "없": 0.1, "아니": 0.1,
}

EMOTION_INTENSITY = {
    # 최고 강도 (0.85~0.9) — 극단적 감정/위기/충격
    "공포": 0.9, "경악": 0.9, "절망": 0.9, "광기": 0.9,
    "두려움": 0.85, "혼돈": 0.85, "비탄": 0.85, "분노": 0.85, "격분": 0.85,
    "공황": 0.85, "파멸": 0.85, "소멸감": 0.85,
    # 고강도 (0.7~0.8) — 강렬한 감정/각성/전환
    "전율": 0.8, "경외": 0.8, "숭고": 0.8, "열광": 0.8, "환희": 0.8, "황홀": 0.8,
    "각성": 0.75, "해방": 0.75, "경이": 0.75, "비장": 0.75, "결연": 0.75, "격앙": 0.75,
    "흥분": 0.7, "자각": 0.7, "열망": 0.7, "갈망": 0.7, "초월감": 0.7, "통찰": 0.7,
    # 중고 강도 (0.55~0.65) — 뚜렷한 감정/긴장
    "쾌감": 0.65, "긴장": 0.65, "죄책감": 0.65, "수치심": 0.65, "질투": 0.65,
    "불안": 0.6, "초조": 0.6, "허무": 0.6, "고독": 0.6, "상실": 0.6, "그리움": 0.6,
    "아이러니": 0.55, "모순": 0.55, "혼란": 0.55, "의심": 0.55,
    # 중강도 (0.4~0.5) — 인지적/성찰적 감정
    "집중": 0.5, "몰입": 0.5, "연민": 0.5, "동경": 0.5, "경탄": 0.5,
    "기대": 0.45, "호기심": 0.45, "체념": 0.45, "무력감": 0.45,
    "회의": 0.4, "의문": 0.4, "향수": 0.4, "담담함": 0.4,
    # 저강도 (0.1~0.3) — 잔잔한/배경적 감정
    "위안": 0.3, "안도": 0.3, "수용": 0.3, "관조": 0.25,
    "안정": 0.2, "무관심": 0.2, "나른함": 0.15,
    "평온": 0.1, "고요": 0.1, "정적": 0.1,
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


# ============================================================
# Custom Dictionary 로딩 (사용자 추가 단어)
# ============================================================
CUSTOM_DICT_PATH = Path(__file__).parent / "custom_dictionary.json"


def load_custom_dictionary():
    """custom_dictionary.json 로드 → 기존 사전에 머지"""
    if not CUSTOM_DICT_PATH.exists():
        return
    try:
        with open(CUSTOM_DICT_PATH, 'r', encoding='utf-8') as f:
            custom = json.load(f)
    except (json.JSONDecodeError, IOError):
        return

    # VERB_ENERGY 머지
    for word, score in custom.get("verb_energy", {}).items():
        if word not in VERB_ENERGY:
            VERB_ENERGY[word] = score

    # EMOTION_INTENSITY 머지
    for word, score in custom.get("emotion_intensity", {}).items():
        if word not in EMOTION_INTENSITY:
            EMOTION_INTENSITY[word] = score

    # Set 사전들 머지
    for term in custom.get("science_terms", []):
        SCIENCE_TERMS.add(term)
    for term in custom.get("chemicals", []):
        CHEMICALS.add(term)
    for term in custom.get("body_parts", []):
        BODY_PARTS.add(term)


def save_to_custom_dictionary(updates):
    """미등록 단어를 custom_dictionary.json에 저장
    updates: {"verb_energy": {word: score}, "emotion_intensity": {word: score},
              "science_terms": [word], "chemicals": [word], "body_parts": [word]}
    """
    # 기존 파일 로드
    if CUSTOM_DICT_PATH.exists():
        try:
            with open(CUSTOM_DICT_PATH, 'r', encoding='utf-8') as f:
                custom = json.load(f)
        except (json.JSONDecodeError, IOError):
            custom = {}
    else:
        custom = {}

    # 머지
    custom.setdefault("_comment", "ENOMETA 사용자 커스텀 사전")
    custom.setdefault("_version", "1.0")
    for k in ("verb_energy", "emotion_intensity"):
        custom.setdefault(k, {})
        custom[k].update(updates.get(k, {}))
    for k in ("science_terms", "chemicals", "body_parts"):
        custom.setdefault(k, [])
        existing = set(custom[k])
        for item in updates.get(k, []):
            if item not in existing:
                custom[k].append(item)

    with open(CUSTOM_DICT_PATH, 'w', encoding='utf-8') as f:
        json.dump(custom, f, ensure_ascii=False, indent=2)


# ============================================================
# 미등록 단어 감지 (Unregistered Word Detection)
# ============================================================
# 미등록 단어 감지 제외 목록 (일반적인 비-키워드 단어)
_COMMON_SKIP = {
    "것", "수", "때", "중", "안", "속", "위", "뒤", "앞", "번", "개", "명",
    "년", "월", "일", "시", "분", "초", "곳", "등", "더", "덜", "가장",
    "매우", "아주", "정말", "진짜", "모두", "다시", "그", "이", "저",
    "어떤", "무엇", "왜", "어디", "누구", "언제", "아닌", "같은", "다른",
    "새로운", "오래된", "큰", "작은", "많은", "적은", "높은", "낮은",
    "좋은", "나쁜", "첫", "마지막", "하나", "둘", "셋",
}


def detect_unregistered_words(segments):
    """대본 세그먼트에서 미등록 단어 감지.
    Returns: {
        "unregistered_verbs": [{"word": str, "context": str, "suggested_score": float}],
        "unregistered_nouns": [{"word": str, "context": str, "frequency": int}],
    }
    """
    unregistered_verbs = {}  # word → {"contexts": [], "count": int}
    unregistered_nouns = {}  # word → {"contexts": [], "count": int}

    # 모든 등록된 단어 집합 (빠른 조회)
    all_registered = (
        set(VERB_ENERGY.keys())
        | set(EMOTION_INTENSITY.keys())
        | SCIENCE_TERMS | CHEMICALS | BODY_PARTS
        | PARTICLES | _COMMON_SKIP
    )

    for seg in segments:
        text = seg.get("text", "")
        tokens = tokenize_korean(text)

        for t in tokens:
            word = t["text"]
            wtype = t["type"]

            # 등록 여부 확인: 조사/구두점/숫자/이미 분류된 특수 타입은 스킵
            if wtype in ("particle", "punct", "number", "chemical", "body", "science"):
                continue

            # 이미 등록된 단어면 스킵
            if word in all_registered:
                continue

            # 동사 어간이 VERB_ENERGY에 부분 매칭되는지 체크
            if wtype == "verb":
                matched = False
                for stem in VERB_ENERGY:
                    if stem in word:
                        matched = True
                        break
                if matched:
                    continue
                # 미등록 동사 발견
                if word not in unregistered_verbs:
                    unregistered_verbs[word] = {"contexts": [], "count": 0}
                unregistered_verbs[word]["count"] += 1
                if len(unregistered_verbs[word]["contexts"]) < 3:
                    unregistered_verbs[word]["contexts"].append(text[:50])
            else:
                # 감정어/명사 중 미등록
                # 2글자 이상만 (1글자는 대부분 조사/접미사)
                if len(word) < 2:
                    continue
                if word not in unregistered_nouns:
                    unregistered_nouns[word] = {"contexts": [], "count": 0}
                unregistered_nouns[word]["count"] += 1
                if len(unregistered_nouns[word]["contexts"]) < 3:
                    unregistered_nouns[word]["contexts"].append(text[:50])

    # 결과 정리 (빈도 높은 순)
    result_verbs = []
    for word, info in sorted(unregistered_verbs.items(), key=lambda x: -x[1]["count"]):
        # 동사 점수 추정: 글자 수 + 어감 기반 (기본 0.5)
        suggested = 0.5
        result_verbs.append({
            "word": word,
            "frequency": info["count"],
            "contexts": info["contexts"],
            "suggested_score": suggested,
            "category": "verb_energy",
        })

    result_nouns = []
    for word, info in sorted(unregistered_nouns.items(), key=lambda x: -x[1]["count"]):
        # 감정어 후보인지 판별 (주관적 감정/상태를 나타내는 단어)
        result_nouns.append({
            "word": word,
            "frequency": info["count"],
            "contexts": info["contexts"],
            "category": "unknown",  # 사용자가 분류
        })

    return {
        "unregistered_verbs": result_verbs,
        "unregistered_nouns": result_nouns,
        "total_unregistered": len(result_verbs) + len(result_nouns),
    }


# 모듈 로드 시 커스텀 사전 자동 머지
load_custom_dictionary()


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


def print_unregistered_report(unregistered):
    """미등록 단어 리포트 출력"""
    if unregistered["total_unregistered"] == 0:
        print("\n  [DICT] All words registered - no unregistered words found.")
        return

    print(f"\n  ========== UNREGISTERED WORDS: {unregistered['total_unregistered']} ==========")

    if unregistered["unregistered_verbs"]:
        print(f"\n  [VERB] Unregistered verbs ({len(unregistered['unregistered_verbs'])}):")
        for v in unregistered["unregistered_verbs"]:
            ctx = v["contexts"][0] if v["contexts"] else ""
            print(f"    - \"{v['word']}\" (x{v['frequency']}) suggested={v['suggested_score']}")
            if ctx:
                try:
                    print(f"      context: \"{ctx}\"")
                except UnicodeEncodeError:
                    pass

    if unregistered["unregistered_nouns"]:
        print(f"\n  [NOUN/EMOTION] Unregistered nouns ({len(unregistered['unregistered_nouns'])}):")
        for n in unregistered["unregistered_nouns"][:20]:  # 상위 20개만
            ctx = n["contexts"][0] if n["contexts"] else ""
            print(f"    - \"{n['word']}\" (x{n['frequency']})")
            if ctx:
                try:
                    print(f"      context: \"{ctx}\"")
                except UnicodeEncodeError:
                    pass
        if len(unregistered["unregistered_nouns"]) > 20:
            print(f"    ... and {len(unregistered['unregistered_nouns']) - 20} more")

    print(f"\n  [TIP] Use --update-dict to interactively add words to custom_dictionary.json")
    print(f"  [TIP] Or manually edit: scripts/custom_dictionary.json")


def interactive_dict_update(unregistered):
    """미등록 단어를 대화형으로 custom_dictionary에 추가"""
    updates = {
        "verb_energy": {},
        "emotion_intensity": {},
        "science_terms": [],
        "chemicals": [],
        "body_parts": [],
    }
    added_count = 0

    # 동사 처리
    for v in unregistered["unregistered_verbs"]:
        print(f"\n  Verb: \"{v['word']}\" (used {v['frequency']}x)")
        if v["contexts"]:
            try:
                print(f"  Context: \"{v['contexts'][0]}\"")
            except UnicodeEncodeError:
                pass
        answer = input(f"  Add to VERB_ENERGY? [y/N/score(0.1~0.9)]: ").strip().lower()
        if answer == 'y':
            updates["verb_energy"][v["word"]] = v["suggested_score"]
            added_count += 1
            print(f"    -> Added with score {v['suggested_score']}")
        elif answer and answer != 'n':
            try:
                score = float(answer)
                score = max(0.1, min(0.9, score))
                updates["verb_energy"][v["word"]] = score
                added_count += 1
                print(f"    -> Added with score {score}")
            except ValueError:
                print(f"    -> Skipped")

    # 명사/감정어 처리 (상위 15개만)
    for n in unregistered["unregistered_nouns"][:15]:
        print(f"\n  Word: \"{n['word']}\" (used {n['frequency']}x)")
        if n["contexts"]:
            try:
                print(f"  Context: \"{n['contexts'][0]}\"")
            except UnicodeEncodeError:
                pass
        answer = input(f"  Category? [e=emotion/s=science/c=chemical/b=body/N=skip/score]: ").strip().lower()
        if answer == 'e' or answer.startswith('e'):
            score_str = input(f"  Emotion score (0.1~0.9, default 0.5): ").strip()
            score = 0.5
            if score_str:
                try:
                    score = max(0.1, min(0.9, float(score_str)))
                except ValueError:
                    pass
            updates["emotion_intensity"][n["word"]] = score
            added_count += 1
            print(f"    -> Added to EMOTION with score {score}")
        elif answer == 's':
            updates["science_terms"].append(n["word"])
            added_count += 1
            print(f"    -> Added to SCIENCE_TERMS")
        elif answer == 'c':
            updates["chemicals"].append(n["word"])
            added_count += 1
            print(f"    -> Added to CHEMICALS")
        elif answer == 'b':
            updates["body_parts"].append(n["word"])
            added_count += 1
            print(f"    -> Added to BODY_PARTS")

    if added_count > 0:
        save_to_custom_dictionary(updates)
        print(f"\n  [SAVED] {added_count} words added to {CUSTOM_DICT_PATH}")
        # 런타임에도 즉시 반영
        load_custom_dictionary()
    else:
        print(f"\n  No words added.")


def main():
    if len(sys.argv) < 2:
        print("Usage: py scripts/script_data_extractor.py <narration_timing.json> [output.json]")
        print("  Options:")
        print("    --update-dict   Interactive mode to add unregistered words to custom dictionary")
        print("    --report-only   Show unregistered word report without extraction")
        sys.exit(1)

    # 옵션 파싱
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    update_dict = '--update-dict' in sys.argv
    report_only = '--report-only' in sys.argv

    input_path = args[0]
    if len(args) > 1:
        output_path = args[1]
    else:
        output_path = os.path.join(os.path.dirname(input_path), "script_data.json")

    print(f"=== ENOMETA Script Data Extractor ===")
    print(f"  Input: {input_path}")
    print(f"  Dictionaries: VERB={len(VERB_ENERGY)} EMOTION={len(EMOTION_INTENSITY)} "
          f"SCIENCE={len(SCIENCE_TERMS)} CHEM={len(CHEMICALS)} BODY={len(BODY_PARTS)}")

    result = extract_script_data(input_path)

    if not report_only:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    # 요약 출력
    g = result["global"]
    print(f"  Segments: {g['total_segments']}")
    print(f"  Numbers found: {g['all_numbers']}")
    print(f"  Chemicals found: {g['all_chemicals']}")
    print(f"  Freq map: {g['freq_map']}")
    if not report_only:
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

    # 미등록 단어 감지
    unregistered = detect_unregistered_words(
        [{"text": seg["text"]} for seg in result["segments"]]
    )
    # 미등록 단어를 결과에 포함
    result["unregistered_words"] = unregistered

    if not report_only:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    # 리포트 출력
    print_unregistered_report(unregistered)

    # 대화형 사전 업데이트
    if update_dict and unregistered["total_unregistered"] > 0:
        interactive_dict_update(unregistered)


if __name__ == "__main__":
    main()

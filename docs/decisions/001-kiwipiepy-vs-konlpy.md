# 001. kiwipiepy 선택 — KoNLPy 대신

**날짜**: 2026-03-06
**상태**: 결정됨

## 컨텍스트

`script_data_extractor.py`의 `tokenize_korean()`이 정규식 기반으로 구현되어 있었다.
"저랬을까" 같은 활용형 동사가 명사로 잘못 분류되는 문제가 있었다.
형태소 분석기 도입이 필요했고, KoNLPy와 kiwipiepy가 후보였다.

## 결정

kiwipiepy 선택.

## 이유

- KoNLPy는 Java(JDK) 의존성 필요 → 로컬 환경 복잡도 증가
- kiwipiepy는 순수 C++ → `pip install kiwipiepy` 한 줄로 끝
- 사용자 사전 등록 기능: `kiwi.add_user_word("전전두엽", "NNG")`
- 성능: "저랬을까" → verb 정상 분류 확인

## 결과

`scripts/script_data_extractor.py`의 `tokenize_korean()`이 kiwipiepy 기반으로 교체됨.
전문용어(전전두엽, 대뇌피질 등) 사용자 사전 등록.

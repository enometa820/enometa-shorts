"""enometa_music — ENOMETA Generative Music Engine 패키지

enometa_music_engine.py 4,382줄 모놀리스를 모듈로 분리.
CLI 인터페이스는 기존 enometa_music_engine.py (thin wrapper)에서 유지.
"""
from .engine import EnometaMusicEngine
from .script_gen import generate_music_script
from .synthesis import SAMPLE_RATE

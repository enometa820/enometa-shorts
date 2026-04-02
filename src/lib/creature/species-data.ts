/**
 * 픽셀아트 크리처 종족 데이터
 * 16×16 PNG 스프라이트 기반 — public/creatures/{id}.png
 *
 * 감정 매핑: ASCII 표정 교체 → 색상 오버레이 (CreatureRenderer에서 처리)
 */

export type ExpressionId = 'default' | 'happy' | 'sad' | 'surprised' | 'angry';

export type SpeciesData = {
  id: string;
  name: string;
  colorHint: 'warm' | 'cool' | 'accent';
  idlePreference: 'breathe' | 'wobble' | 'twitch' | 'vibrate';
};

export const SPECIES_DATA: SpeciesData[] = [
  { id: 'cat',       name: '냥냥이',   colorHint: 'warm',   idlePreference: 'breathe' },
  { id: 'dog',       name: '멍멍이',   colorHint: 'warm',   idlePreference: 'wobble'  },
  { id: 'fox',       name: '여시',     colorHint: 'accent', idlePreference: 'twitch'  },
  { id: 'frog',      name: '개구리',   colorHint: 'cool',   idlePreference: 'wobble'  },
  { id: 'jellyfish', name: '해파리',   colorHint: 'cool',   idlePreference: 'breathe' },
  { id: 'mouse',     name: '쥐돌이',   colorHint: 'warm',   idlePreference: 'twitch'  },
  { id: 'duck',      name: '오리',     colorHint: 'warm',   idlePreference: 'wobble'  },
  { id: 'bird',      name: '새',       colorHint: 'cool',   idlePreference: 'vibrate' },
  { id: 'bee',       name: '꿀벌',     colorHint: 'accent', idlePreference: 'vibrate' },
  { id: 'squirrel',  name: '다람쥐',   colorHint: 'warm',   idlePreference: 'twitch'  },
  { id: 'dolphin',   name: '돌핀',     colorHint: 'cool',   idlePreference: 'wobble'  },
];

export const SPECIES_MAP = new Map(SPECIES_DATA.map(s => [s.id, s]));

// 감정 문자열 → ExpressionId (레거시 호환 유지)
export function mapEmotionToExpression(emotion: string): ExpressionId {
  if (emotion.startsWith('tension') || emotion.startsWith('angry')) return 'angry';
  if (emotion.startsWith('awakening') || emotion === 'hopeful')     return 'happy';
  if (emotion.startsWith('somber'))                                   return 'sad';
  return 'default';
}

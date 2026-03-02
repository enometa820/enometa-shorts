"""
visual_layers/particle_layer.py
numpy 벡터 연산으로 파티클 시뮬레이션.
오디오 에너지가 직접 파티클 물리에 작용.
"""

import numpy as np


class ParticleLayer:
    def __init__(self, width, height, palette, intensity=0.6,
                 blend="additive", max_particles=500):
        self.width = width
        self.height = height
        self.palette = palette
        self.intensity = intensity
        self.blend = blend
        self.max_particles = max_particles

        self.positions = np.random.rand(max_particles, 2) * [width, height]
        self.velocities = (np.random.rand(max_particles, 2) - 0.5) * 2
        self.lifetimes = np.random.rand(max_particles)
        self.sizes = np.random.rand(max_particles) * 3 + 1

    def render(self, ctx: dict) -> np.ndarray:
        canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        audio_chunk = ctx["audio_chunk"]
        rms = np.sqrt(np.mean(audio_chunk ** 2)) if len(audio_chunk) > 0 and np.any(audio_chunk) else 0
        energy = ctx.get("section_energy", rms)

        # 물리 업데이트 (벡터 연산)
        force = (np.random.rand(self.max_particles, 2) - 0.5) * energy * 10
        self.velocities += force * 0.1
        self.velocities *= 0.98
        self.positions += self.velocities * self.intensity

        self.lifetimes -= 0.01
        dead = self.lifetimes <= 0
        n_dead = dead.sum()
        if n_dead > 0:
            self.lifetimes[dead] = 1.0
            self.positions[dead] = np.random.rand(n_dead, 2) * [self.width, self.height]
            self.velocities[dead] = (np.random.rand(n_dead, 2) - 0.5) * energy * 5

        self.positions[:, 0] %= self.width
        self.positions[:, 1] %= self.height

        # 렌더링
        accent = np.array(self.palette["accent"], dtype=float)
        alive = self.lifetimes > 0
        for i in np.where(alive)[0]:
            x = int(self.positions[i, 0])
            y = int(self.positions[i, 1])
            size = max(1, int(self.sizes[i] * (1 + rms * 3)))
            alpha = self.lifetimes[i] * self.intensity
            color = (accent * alpha).astype(np.uint8)

            x0 = max(0, x - size)
            x1 = min(self.width, x + size)
            y0 = max(0, y - size)
            y1 = min(self.height, y + size)
            canvas[y0:y1, x0:x1] = np.maximum(canvas[y0:y1, x0:x1], color)

        return canvas

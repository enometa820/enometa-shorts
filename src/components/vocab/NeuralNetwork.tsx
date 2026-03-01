import React, { useRef, useEffect, useMemo } from "react";
import { VocabComponentProps } from "../../types";

/**
 * NeuralNetwork — 뇌/생각/연결 표현
 * 노드 + 엣지 + 신호 전파 애니메이션
 * scene_01 (뇌), scene_06 (생각) 용
 */

interface Node {
  x: number;
  y: number;
  radius: number;
  connections: number[]; // 연결된 노드 인덱스
  pulsePhase: number;
  layer: number; // 0=inner, 1=mid, 2=outer
}

export const NeuralNetwork: React.FC<VocabComponentProps> = ({
  count = 40,
  color = "#8B5CF6",
  audio,
  sceneProgress,
  width = 1080,
  height = 1080,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const nodes = useMemo(() => {
    const arr: Node[] = [];
    const cx = width / 2;
    const cy = height / 2;

    for (let i = 0; i < count; i++) {
      const layer = i < count * 0.2 ? 0 : i < count * 0.6 ? 1 : 2;
      const radiusRange = layer === 0 ? 120 : layer === 1 ? 280 : 420;
      const angle = Math.random() * Math.PI * 2;
      const dist = radiusRange * (0.3 + Math.random() * 0.7);

      arr.push({
        x: cx + Math.cos(angle) * dist,
        y: cy + Math.sin(angle) * dist,
        radius: 3 + Math.random() * 4,
        connections: [],
        pulsePhase: Math.random() * Math.PI * 2,
        layer,
      });
    }

    // 가까운 노드끼리 연결
    for (let i = 0; i < arr.length; i++) {
      for (let j = i + 1; j < arr.length; j++) {
        const dx = arr[i].x - arr[j].x;
        const dy = arr[i].y - arr[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 180 && arr[i].connections.length < 4) {
          arr[i].connections.push(j);
        }
      }
    }

    return arr;
  }, [count, width, height]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const time = sceneProgress * 10;
    const signalSpeed = 3 + audio.mid * 10;

    // 엣지 (연결선)
    for (const node of nodes) {
      for (const ci of node.connections) {
        const target = nodes[ci];
        const signalPos = ((time * signalSpeed + node.pulsePhase) % 1);

        ctx.beginPath();
        ctx.moveTo(node.x, node.y);
        ctx.lineTo(target.x, target.y);
        ctx.strokeStyle = `rgba(139, 92, 246, ${0.1 + audio.rms * 0.2})`;
        ctx.lineWidth = 0.8;
        ctx.stroke();

        // 신호 전파 (빛나는 점이 엣지를 따라 이동)
        const sx = node.x + (target.x - node.x) * signalPos;
        const sy = node.y + (target.y - node.y) * signalPos;

        ctx.beginPath();
        ctx.arc(sx, sy, 3 + audio.bass * 6, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 215, 0, ${0.4 + audio.rms * 0.6})`;
        ctx.fill();
      }
    }

    // 노드
    for (const node of nodes) {
      const pulse = Math.sin(time * 3 + node.pulsePhase) * 0.5 + 0.5;
      const r = node.radius * (1 + audio.bass * 1.2 + pulse * 0.5);

      // 글로우
      const gradient = ctx.createRadialGradient(
        node.x, node.y, 0,
        node.x, node.y, r * 3
      );
      gradient.addColorStop(0, `rgba(139, 92, 246, ${0.5 + audio.rms * 0.5})`);
      gradient.addColorStop(1, "rgba(139, 92, 246, 0)");
      ctx.beginPath();
      ctx.arc(node.x, node.y, r * 3, 0, Math.PI * 2);
      ctx.fillStyle = gradient;
      ctx.fill();

      // 코어
      ctx.beginPath();
      ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(200, 180, 255, ${0.6 + pulse * 0.4})`;
      ctx.fill();
    }
  });

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{ position: "absolute", top: 0, left: 0 }}
    />
  );
};

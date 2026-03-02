import React, { useRef, useEffect, useMemo } from "react";
import { VocabComponentProps } from "../../types";

/**
 * NeuralNetwork — 뇌/생각/연결 표현
 * variants: default (3층 신경망), tree_branch (나무 가지), constellation (별자리)
 */

interface Node {
  x: number;
  y: number;
  radius: number;
  connections: number[];
  pulsePhase: number;
  layer: number;
}

export const NeuralNetwork: React.FC<VocabComponentProps> = ({
  count = 40,
  color = "#8B5CF6",
  variant = "default",
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

    if (variant === "tree_branch") {
      // 하단 중앙에서 나무처럼 분기
      const rootX = cx;
      const rootY = height * 0.85;

      function addBranch(x: number, y: number, angle: number, depth: number, idx: number) {
        if (depth > 5 || arr.length >= count) return;
        arr.push({
          x, y, radius: 4 - depth * 0.5,
          connections: [], pulsePhase: Math.random() * Math.PI * 2, layer: depth,
        });
        const parentIdx = arr.length - 1;

        const branches = depth < 2 ? 3 : 2;
        for (let i = 0; i < branches; i++) {
          const spread = 0.6 + Math.random() * 0.4;
          const newAngle = angle + (i - (branches - 1) / 2) * spread;
          const len = 60 + Math.random() * 40 - depth * 8;
          const nx = x + Math.cos(newAngle) * len;
          const ny = y + Math.sin(newAngle) * len;
          if (ny < 50 || arr.length >= count) continue;
          const childIdx = arr.length;
          arr[parentIdx].connections.push(childIdx);
          addBranch(nx, ny, newAngle, depth + 1, childIdx);
        }
      }
      addBranch(rootX, rootY, -Math.PI / 2, 0, 0);

    } else if (variant === "constellation") {
      // 별자리: 넓게 분포된 별 + 가까운 별끼리 선 연결
      for (let i = 0; i < count; i++) {
        arr.push({
          x: 80 + Math.random() * (width - 160),
          y: 80 + Math.random() * (height - 160),
          radius: 2 + Math.random() * 3,
          connections: [],
          pulsePhase: Math.random() * Math.PI * 2,
          layer: 0,
        });
      }
      // 가까운 별 연결 (최대 2개)
      for (let i = 0; i < arr.length; i++) {
        const dists: { idx: number; d: number }[] = [];
        for (let j = 0; j < arr.length; j++) {
          if (i === j) continue;
          const dx = arr[i].x - arr[j].x;
          const dy = arr[i].y - arr[j].y;
          dists.push({ idx: j, d: Math.sqrt(dx * dx + dy * dy) });
        }
        dists.sort((a, b) => a.d - b.d);
        for (let k = 0; k < Math.min(2, dists.length); k++) {
          if (dists[k].d < 250) arr[i].connections.push(dists[k].idx);
        }
      }

    } else {
      // default: 3층 신경망
      for (let i = 0; i < count; i++) {
        const layer = i < count * 0.2 ? 0 : i < count * 0.6 ? 1 : 2;
        const radiusRange = layer === 0 ? 120 : layer === 1 ? 280 : 420;
        const angle = Math.random() * Math.PI * 2;
        const dist = radiusRange * (0.3 + Math.random() * 0.7);
        arr.push({
          x: cx + Math.cos(angle) * dist,
          y: cy + Math.sin(angle) * dist,
          radius: 3 + Math.random() * 4,
          connections: [], pulsePhase: Math.random() * Math.PI * 2, layer,
        });
      }
      for (let i = 0; i < arr.length; i++) {
        for (let j = i + 1; j < arr.length; j++) {
          const dx = arr[i].x - arr[j].x;
          const dy = arr[i].y - arr[j].y;
          if (Math.sqrt(dx * dx + dy * dy) < 180 && arr[i].connections.length < 4) {
            arr[i].connections.push(j);
          }
        }
      }
    }

    return arr;
  }, [count, width, height, variant]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const time = sceneProgress * 10;
    const signalSpeed = 3 + audio.mid * 10;

    // 엣지
    for (const node of nodes) {
      for (const ci of node.connections) {
        const target = nodes[ci];
        if (!target) continue;
        const signalPos = ((time * signalSpeed + node.pulsePhase) % 1);

        ctx.beginPath();
        ctx.moveTo(node.x, node.y);
        ctx.lineTo(target.x, target.y);
        ctx.strokeStyle = `rgba(139, 92, 246, ${0.1 + audio.rms * 0.2})`;
        ctx.lineWidth = variant === "constellation" ? 0.5 : 0.8;
        ctx.stroke();

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

      const gradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, r * 3);
      gradient.addColorStop(0, `rgba(139, 92, 246, ${0.5 + audio.rms * 0.5})`);
      gradient.addColorStop(1, "rgba(139, 92, 246, 0)");
      ctx.beginPath();
      ctx.arc(node.x, node.y, r * 3, 0, Math.PI * 2);
      ctx.fillStyle = gradient;
      ctx.fill();

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

import React, { useEffect, useRef } from 'react';

interface CircularAudioWaveformProps {
  isPaused: boolean;
  level?: number;
  size?: number;
  color?: string;
  onClick?: () => void;
}

export const CircularAudioWaveform = ({
  isPaused,
  level = 0,
  size = 256,
  color = "#353839", // onyx
  onClick
}: CircularAudioWaveformProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Handle high DPI
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    ctx.scale(dpr, dpr);

    const centerX = size / 2;
    const centerY = size / 2;
    const baseRadius = (size / 2) * 0.78;
    const barCount = 100;
    const innerRadius = baseRadius + 4;

    let animationFrameId = 0;
    let smoothedLevel = 0;
    let renderedLevel = 0;
    let rotationAngle = 0;
    let lastTimeMs = 0;

    const draw = (timeMs: number) => {
      const dt = Math.min(50, lastTimeMs ? timeMs - lastTimeMs : 16.67);
      lastTimeMs = timeMs;
      const targetLevel = isPaused ? 0 : Math.max(0, Math.min(1, level));
      // Asymmetric smoothing: quick enough to react, slower to decay.
      const rise = 1 - Math.exp(-dt / 220);
      const fall = 1 - Math.exp(-dt / 520);
      const smoothingFactor = targetLevel > smoothedLevel ? rise : fall;
      smoothedLevel += (targetLevel - smoothedLevel) * smoothingFactor;

      // Additional render smoothing to reduce visible jitter.
      renderedLevel += (smoothedLevel - renderedLevel) * (1 - Math.exp(-dt / 280));

      ctx.clearRect(0, 0, size, size);

      // Extremely slow "breathing" rotation
      rotationAngle += 0.0003;

      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(rotationAngle);

      for (let i = 0; i < barCount; i++) {
        const angle = (i / barCount) * Math.PI * 2;

        const barHeight = 5;

        ctx.save();
        ctx.rotate(angle);

        ctx.beginPath();
        ctx.fillStyle = color;
        const barWidth = 3.8;

        const x = -barWidth / 2;
        const y = innerRadius;

        // Radiating rounded bars
        ctx.roundRect(x, y, barWidth, Math.max(0.1, barHeight), barWidth / 2);
        ctx.fill();

        ctx.restore();
      }
      ctx.restore();

      // Core Circle - draws on top
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(centerX, centerY, baseRadius - 4, 0, Math.PI * 2);
      ctx.fill();

      animationFrameId = requestAnimationFrame(draw);
    };

    animationFrameId = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [isPaused, level, size, color]);

  return (
    <canvas
      ref={canvasRef}
      onClick={onClick}
      className="cursor-pointer"
    />
  );
};

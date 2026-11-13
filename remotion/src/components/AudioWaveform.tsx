import React from "react";
import { useCurrentFrame } from "remotion";

interface AudioWaveformProps {
  barCount?: number;
  height?: number;
  color?: string;
  secondaryColor?: string;
  styleType?: "neon" | "cinematic" | "kinetic" | "corporate";
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({
  barCount = 32,
  height = 64,
  color = "#00F0FF",
  secondaryColor = "#A3E635",
  styleType = "neon",
}) => {
  const frame = useCurrentFrame();

  const bars = Array.from({ length: barCount }, (_, i) => {
    // Generate realistic multi-harmonic frequency wave
    const normalizedIndex = i / barCount;
    const wave1 = Math.sin(frame * 0.18 + i * 0.42);
    const wave2 = Math.cos(frame * 0.12 - i * 0.28);
    const wave3 = Math.sin(frame * 0.26 + i * 0.15);
    
    // Envelope to taper sides (higher in center)
    const envelope = Math.sin(normalizedIndex * Math.PI);
    
    // Combine waves and clamp between 0.15 and 1.0
    const rawAmplitude = Math.abs(wave1 * 0.5 + wave2 * 0.35 + wave3 * 0.15);
    const amp = Math.max(0.12, Math.min(1.0, rawAmplitude * (0.4 + 0.6 * envelope)));
    const barHeight = Math.round(amp * height);

    return {
      id: i,
      height: barHeight,
      opacity: 0.5 + amp * 0.5,
    };
  });

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: styleType === "kinetic" ? "6px" : "4px",
        height: `${height}px`,
        width: "100%",
        padding: "0 16px",
      }}
    >
      {bars.map((bar) => {
        const isCenter = Math.abs(bar.id - barCount / 2) < barCount / 4;
        const barColor = isCenter && secondaryColor ? secondaryColor : color;

        return (
          <div
            key={bar.id}
            style={{
              width: styleType === "kinetic" ? "6px" : "4px",
              height: `${bar.height}px`,
              backgroundColor: barColor,
              borderRadius: styleType === "corporate" ? "2px" : "9999px",
              opacity: bar.opacity,
              boxShadow:
                styleType === "neon"
                  ? `0 0 10px ${barColor}, 0 0 20px ${barColor}88`
                  : styleType === "cinematic"
                  ? `0 0 8px rgba(245, 158, 11, 0.4)`
                  : "none",
              transition: "height 0.05s ease",
            }}
          />
        );
      })}
    </div>
  );
};

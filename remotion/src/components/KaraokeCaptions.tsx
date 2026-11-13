import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { WordTimestamp } from "../types";

interface KaraokeCaptionsProps {
  words: WordTimestamp[];
  styleType: "neon" | "cinematic" | "kinetic" | "corporate";
  aspectRatio: "9:16" | "16:9";
  accentColor?: string;
}

export const KaraokeCaptions: React.FC<KaraokeCaptionsProps> = ({
  words = [],
  styleType,
  aspectRatio,
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  if (!words || words.length === 0) {
    return null;
  }

  // Find index of current word
  let activeIndex = words.findIndex(
    (w) => currentTime >= w.start && currentTime <= w.end
  );

  // If between words, pick closest previous or 0
  if (activeIndex === -1) {
    if (currentTime < words[0].start) {
      activeIndex = 0;
    } else {
      // Find the last word that started before current time
      for (let i = words.length - 1; i >= 0; i--) {
        if (currentTime >= words[i].start) {
          activeIndex = i;
          break;
        }
      }
      if (activeIndex === -1) activeIndex = words.length - 1;
    }
  }

  // Chunking strategy:
  // For 9:16 (TikTok/Reels), chunk size 3-4 words for quick kinetic reading.
  // For 16:9 (Horizontal/YouTube), chunk size 6-8 words for horizontal cinematic readability.
  const chunkSize = aspectRatio === "9:16" ? (styleType === "kinetic" ? 3 : 4) : 7;
  const chunkIndex = Math.floor(activeIndex / chunkSize);
  const visibleWords = words.slice(
    chunkIndex * chunkSize,
    (chunkIndex + 1) * chunkSize
  );

  // Font size calculation
  let baseFontSize = aspectRatio === "9:16" ? 64 : 48;
  if (styleType === "kinetic") {
    baseFontSize = aspectRatio === "9:16" ? 76 : 56;
  } else if (styleType === "cinematic") {
    baseFontSize = aspectRatio === "9:16" ? 54 : 42;
  }

  return (
    <div
      dir="rtl"
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        alignItems: "center",
        gap: aspectRatio === "9:16" ? "14px 20px" : "18px 24px",
        width: "90%",
        maxWidth: aspectRatio === "9:16" ? "920px" : "1500px",
        margin: "0 auto",
        lineHeight: 1.5,
        textAlign: "center",
      }}
    >
      {visibleWords.map((item, idx) => {
        const globalIdx = chunkIndex * chunkSize + idx;
        const isActive = globalIdx === activeIndex;
        const isPast = globalIdx < activeIndex;

        // Spring animation for active word entry
        const wordStartFrame = Math.round(item.start * fps);
        const wordFrame = Math.max(0, frame - wordStartFrame);
        const scaleSpring = spring({
          frame: wordFrame,
          fps,
          config: {
            damping: 12,
            stiffness: 180,
            mass: 0.6,
          },
        });

        const activeScale = isActive
          ? interpolate(scaleSpring, [0, 1], [1.0, styleType === "kinetic" ? 1.22 : 1.12])
          : 1.0;

        // Color definitions per template
        let textColor = "#FFFFFF";
        let textShadow = "none";
        let bgBadge = "transparent";
        let borderBadge = "transparent";

        if (styleType === "neon") {
          const neonAccent = accentColor || "#00F0FF";
          if (isActive) {
            textColor = neonAccent;
            textShadow = `0 0 16px ${neonAccent}, 0 0 32px ${neonAccent}AA`;
            bgBadge = "rgba(0, 240, 255, 0.12)";
            borderBadge = `1px solid ${neonAccent}66`;
          } else if (isPast) {
            textColor = "#FFFFFF";
          } else {
            textColor = "#64748B";
          }
        } else if (styleType === "kinetic") {
          const kineticAccent = accentColor || "#A3E635";
          if (isActive) {
            textColor = "#09090B";
            bgBadge = kineticAccent;
            textShadow = "none";
          } else if (isPast) {
            textColor = "#FFFFFF";
          } else {
            textColor = "#71717A";
          }
        } else if (styleType === "cinematic") {
          const goldAccent = accentColor || "#F59E0B";
          if (isActive) {
            textColor = goldAccent;
            textShadow = "0 0 20px rgba(245, 158, 11, 0.5)";
          } else if (isPast) {
            textColor = "#F1F5F9";
          } else {
            textColor = "#64748B";
          }
        } else {
          // clean_corporate
          const blueAccent = accentColor || "#38BDF8";
          if (isActive) {
            textColor = blueAccent;
            bgBadge = "rgba(56, 189, 248, 0.15)";
            borderBadge = "1px solid rgba(56, 189, 248, 0.3)";
          } else if (isPast) {
            textColor = "#F8FAFC";
          } else {
            textColor = "#94A3B8";
          }
        }

        return (
          <span
            key={`${item.word}-${globalIdx}`}
            style={{
              display: "inline-block",
              fontSize: `${baseFontSize}px`,
              fontWeight: isActive ? 700 : (styleType === "kinetic" ? 700 : 500),
              color: textColor,
              textShadow,
              backgroundColor: bgBadge,
              border: borderBadge,
              borderRadius: styleType === "corporate" ? "8px" : "16px",
              padding: isActive && bgBadge !== "transparent" ? "4px 16px" : "0 4px",
              transform: `scale(${activeScale})`,
              transformOrigin: "center center",
              transition: "transform 0.08s ease, color 0.1s ease",
              fontFamily: '"IBM Plex Sans Arabic", sans-serif',
            }}
          >
            {item.word}
          </span>
        );
      })}
    </div>
  );
};

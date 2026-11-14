import React from "react";
import { OffthreadVideo, Img } from "remotion";

interface PictureInPictureProps {
  url?: string;
  position?: "top-right" | "top-left" | "bottom-right" | "bottom-left";
  scale?: number;
  muted?: boolean;
  aspectRatio?: "9:16" | "16:9";
  accentColor?: string;
}

export const PictureInPicture: React.FC<PictureInPictureProps> = ({
  url,
  position = "top-left",
  scale = 0.28,
  muted = true,
  aspectRatio = "9:16",
  accentColor = "#00F0FF",
}) => {
  if (!url || !url.trim()) {
    return null;
  }

  const cleanUrl = url.trim();
  const isVideo =
    cleanUrl.toLowerCase().endsWith(".mp4") ||
    cleanUrl.toLowerCase().endsWith(".webm") ||
    cleanUrl.toLowerCase().endsWith(".mov") ||
    cleanUrl.includes("/videos/");

  const isVertical = aspectRatio === "9:16";

  // Calculate coordinates based on position
  const posStyles: React.CSSProperties = {};
  const marginV = isVertical ? "160px" : "100px";
  const marginH = isVertical ? "40px" : "60px";

  if (position === "top-left") {
    posStyles.top = marginV;
    posStyles.left = marginH;
  } else if (position === "top-right") {
    posStyles.top = marginV;
    posStyles.right = marginH;
  } else if (position === "bottom-left") {
    posStyles.bottom = marginV;
    posStyles.left = marginH;
  } else {
    // bottom-right
    posStyles.bottom = marginV;
    posStyles.right = marginH;
  }

  const widthPercent = Math.max(18, Math.min(45, Math.round(scale * 100)));

  return (
    <div
      style={{
        position: "absolute",
        ...posStyles,
        width: `${widthPercent}%`,
        aspectRatio: isVertical ? "9 / 16" : "16 / 9",
        borderRadius: "18px",
        overflow: "hidden",
        border: `2px solid ${accentColor || "#00F0FF"}88`,
        boxShadow: `0 16px 40px rgba(0, 0, 0, 0.7), 0 0 20px ${accentColor || "#00F0FF"}33`,
        zIndex: 25,
        backgroundColor: "#08090D",
      }}
    >
      {isVideo ? (
        <OffthreadVideo
          src={cleanUrl}
          muted={muted}
          volume={muted ? 0 : 0.2}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      ) : (
        <Img
          src={cleanUrl}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
        />
      )}

      {/* Mini PiP B-Roll Badge */}
      <div
        style={{
          position: "absolute",
          top: "8px",
          right: "8px",
          backgroundColor: "rgba(0, 0, 0, 0.75)",
          border: `1px solid ${accentColor || "#00F0FF"}66`,
          borderRadius: "6px",
          padding: "2px 6px",
          fontSize: "10px",
          fontWeight: 700,
          color: accentColor || "#00F0FF",
          fontFamily: '"JetBrains Mono", monospace',
          display: "flex",
          alignItems: "center",
          gap: "4px",
        }}
      >
        <span
          style={{
            width: "6px",
            height: "6px",
            borderRadius: "50%",
            backgroundColor: "#EF4444",
            boxShadow: "0 0 6px #EF4444",
          }}
        />
        <span>B-ROLL</span>
      </div>
    </div>
  );
};

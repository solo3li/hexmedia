import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { BackgroundMotion } from "../components/BackgroundMotion";
import { KaraokeCaptions } from "../components/KaraokeCaptions";
import { AudioWaveform } from "../components/AudioWaveform";
import { MotionCompositionProps } from "../types";

export const TikTokKinetic: React.FC<MotionCompositionProps> = ({
  title = "TIKTOK / REELS KINETIC",
  subtitle = "VIRAL HOOK",
  speakerName = "HexMedia Shorts",
  words = [],
  backgroundUrl,
  backgroundType = "gradient",
  accentColor = "#A3E635",
  aspectRatio = "9:16",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const isVertical = aspectRatio === "9:16";
  const progressPercent = Math.min(100, Math.max(0, (frame / durationInFrames) * 100));

  return (
    <AbsoluteFill style={{ fontFamily: '"IBM Plex Sans Arabic", sans-serif', color: "#FFF" }}>
      {/* Dynamic Purple/Violet Mesh Background */}
      <BackgroundMotion
        type={backgroundType}
        src={backgroundUrl}
        templateId="tiktok_kinetic"
        overlayOpacity={0.65}
      />

      {/* Top Video Progress Bar */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: isVertical ? "8px" : "6px",
          backgroundColor: "rgba(255, 255, 255, 0.15)",
          zIndex: 30,
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progressPercent}%`,
            backgroundColor: accentColor,
            boxShadow: `0 0 10px ${accentColor}`,
            transition: "width 0.05s linear",
          }}
        />
      </div>

      {/* Main Layout */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          alignItems: "center",
          padding: isVertical ? "80px 40px 70px 40px" : "50px 70px 40px 70px",
          zIndex: 10,
        }}
      >
        {/* Top Header Pill */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            background: "rgba(15, 12, 27, 0.85)",
            backdropFilter: "blur(12px)",
            border: `2px solid ${accentColor}`,
            borderRadius: "9999px",
            padding: "8px 24px",
            boxShadow: `0 8px 24px rgba(163, 230, 53, 0.25)`,
          }}
        >
          <span style={{ fontSize: isVertical ? "22px" : "18px" }}>⚡</span>
          <span
            style={{
              fontSize: isVertical ? "20px" : "16px",
              fontWeight: 700,
              color: "#FFF",
              letterSpacing: "0.5px",
            }}
          >
            {speakerName}
          </span>
          <span
            style={{
              backgroundColor: accentColor,
              color: "#000",
              fontSize: isVertical ? "13px" : "11px",
              fontWeight: 800,
              padding: "2px 8px",
              borderRadius: "9999px",
              textTransform: "uppercase",
            }}
          >
            LIVE
          </span>
        </div>

        {/* Center: Punchy Kinetic Words */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            width: "100%",
            flex: 1,
            gap: "24px",
          }}
        >
          <KaraokeCaptions
            words={words}
            styleType="kinetic"
            aspectRatio={aspectRatio}
            accentColor={accentColor}
          />
        </div>

        {/* Bottom Waveform & Channel Tag */}
        <div
          style={{
            width: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "16px",
          }}
        >
          <AudioWaveform
            barCount={isVertical ? 24 : 40}
            height={isVertical ? 80 : 56}
            color={accentColor}
            secondaryColor="#C084FC"
            styleType="kinetic"
          />

          <div
            style={{
              fontSize: isVertical ? "16px" : "14px",
              fontWeight: 600,
              color: "rgba(255, 255, 255, 0.7)",
              fontFamily: '"JetBrains Mono", monospace',
            }}
          >
            #Reels #TikTok #ViralMotion 🚀
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

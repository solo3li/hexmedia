import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { BackgroundMotion } from "../components/BackgroundMotion";
import { KaraokeCaptions } from "../components/KaraokeCaptions";
import { AudioWaveform } from "../components/AudioWaveform";
import { MotionCompositionProps } from "../types";

export const CleanCorporate: React.FC<MotionCompositionProps> = ({
  title = "HEXMEDIA CORPORATE",
  subtitle = "Executive Briefing",
  speakerName = "المتحدث الرسمي",
  words = [],
  backgroundUrl,
  backgroundType = "gradient",
  accentColor = "#38BDF8",
  aspectRatio = "9:16",
  videoStartOffset = 0,
  videoMuted = false,
  videoVolume = 0.15,
  transitionEffect = "dissolve",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const isVertical = aspectRatio === "9:16";

  return (
    <AbsoluteFill style={{ fontFamily: '"IBM Plex Sans Arabic", sans-serif', color: "#FFF" }}>
      {/* Background with Deep Slate & Clean Gradient */}
      <BackgroundMotion
        type={backgroundType}
        src={backgroundUrl}
        templateId="clean_corporate"
        overlayOpacity={0.70}
        videoStartOffset={videoStartOffset}
        videoMuted={videoMuted}
        videoVolume={videoVolume}
        transitionEffect={transitionEffect}
      />

      {/* Main Layout */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          alignItems: "center",
          padding: isVertical ? "90px 48px 80px 48px" : "60px 90px 50px 90px",
          zIndex: 10,
        }}
      >
        {/* Header: Professional Glass Card */}
        <div
          style={{
            width: "100%",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            background: "rgba(15, 23, 42, 0.75)",
            backdropFilter: "blur(16px)",
            border: "1px solid rgba(255, 255, 255, 0.12)",
            borderRadius: "16px",
            padding: "16px 24px",
            boxShadow: "0 10px 30px rgba(0, 0, 0, 0.3)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "10px",
                backgroundColor: accentColor,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 700,
                color: "#0F172A",
                fontSize: "18px",
              }}
            >
              H
            </div>
            <div>
              <div style={{ fontSize: isVertical ? "18px" : "16px", fontWeight: 600, color: "#F8FAFC" }}>
                {speakerName}
              </div>
              <div style={{ fontSize: isVertical ? "14px" : "12px", color: "#94A3B8" }}>
                {subtitle}
              </div>
            </div>
          </div>

          <div
            style={{
              padding: "4px 12px",
              borderRadius: "8px",
              backgroundColor: "rgba(56, 189, 248, 0.12)",
              border: `1px solid ${accentColor}33`,
              color: accentColor,
              fontSize: isVertical ? "14px" : "12px",
              fontWeight: 500,
              fontFamily: '"JetBrains Mono", monospace',
            }}
          >
            REPORT
          </div>
        </div>

        {/* Center: Frosted Content Card with Karaoke */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            width: "100%",
            flex: 1,
            margin: "30px 0",
            background: "rgba(15, 23, 42, 0.6)",
            backdropFilter: "blur(12px)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "24px",
            padding: isVertical ? "40px 20px" : "30px 40px",
          }}
        >
          <KaraokeCaptions
            words={words}
            styleType="corporate"
            aspectRatio={aspectRatio}
            accentColor={accentColor}
            transitionEffect={transitionEffect}
          />
        </div>

        {/* Footer: Clean Audio Meter & Copyright */}
        <div
          style={{
            width: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "14px",
          }}
        >
          <AudioWaveform
            barCount={isVertical ? 32 : 52}
            height={isVertical ? 48 : 36}
            color={accentColor}
            secondaryColor="#38BDF8"
            styleType="corporate"
          />

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              width: "100%",
              fontSize: isVertical ? "14px" : "12px",
              color: "#64748B",
              fontFamily: '"JetBrains Mono", monospace',
            }}
          >
            <span>HexMedia Studio © 2026</span>
            <span>SECURE AI VERIFIED</span>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

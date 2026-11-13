import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { BackgroundMotion } from "../components/BackgroundMotion";
import { KaraokeCaptions } from "../components/KaraokeCaptions";
import { AudioWaveform } from "../components/AudioWaveform";
import { MotionCompositionProps } from "../types";

export const CinematicNarrative: React.FC<MotionCompositionProps> = ({
  title = "دراما سينمائية",
  subtitle = "سرد روائي أصيل",
  speakerName = "الراوي",
  words = [],
  backgroundUrl,
  backgroundType = "gradient",
  accentColor = "#F59E0B",
  aspectRatio = "9:16",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const isVertical = aspectRatio === "9:16";

  return (
    <AbsoluteFill style={{ fontFamily: '"IBM Plex Sans Arabic", sans-serif', color: "#FFF" }}>
      {/* Background with Cinematic Warm Tones & Ken Burns */}
      <BackgroundMotion
        type={backgroundType}
        src={backgroundUrl}
        templateId="cinematic_narrative"
        overlayOpacity={0.72}
      />

      {/* Cinematic Letterbox effect in 16:9 */}
      {!isVertical && (
        <>
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "44px",
              backgroundColor: "#000",
              zIndex: 20,
            }}
          />
          <div
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              width: "100%",
              height: "44px",
              backgroundColor: "#000",
              zIndex: 20,
            }}
          />
        </>
      )}

      {/* Main Content Layout */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          alignItems: "center",
          padding: isVertical ? "110px 54px 90px 54px" : "80px 100px 70px 100px",
          zIndex: 10,
        }}
      >
        {/* Cinematic Header */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
              color: accentColor,
              fontSize: isVertical ? "20px" : "16px",
              fontWeight: 600,
              letterSpacing: "2px",
              textTransform: "uppercase",
            }}
          >
            <span style={{ width: "24px", height: "1px", backgroundColor: accentColor }} />
            <span>{speakerName}</span>
            <span style={{ width: "24px", height: "1px", backgroundColor: accentColor }} />
          </div>

          <div
            style={{
              fontSize: isVertical ? "16px" : "13px",
              color: "#94A3B8",
              fontFamily: '"JetBrains Mono", monospace',
            }}
          >
            {subtitle}
          </div>
        </div>

        {/* Center: Storytelling Karaoke */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            width: "100%",
            flex: 1,
            gap: "30px",
          }}
        >
          <div
            style={{
              width: "48px",
              height: "2px",
              backgroundColor: "rgba(245, 158, 11, 0.4)",
            }}
          />

          <KaraokeCaptions
            words={words}
            styleType="cinematic"
            aspectRatio={aspectRatio}
            accentColor={accentColor}
          />

          <div
            style={{
              width: "48px",
              height: "2px",
              backgroundColor: "rgba(245, 158, 11, 0.4)",
            }}
          />
        </div>

        {/* Footer: Ambient Waveform */}
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
            barCount={isVertical ? 30 : 44}
            height={isVertical ? 50 : 40}
            color={accentColor}
            secondaryColor="#FDE68A"
            styleType="cinematic"
          />

          <div
            style={{
              fontSize: isVertical ? "15px" : "13px",
              color: "rgba(255, 255, 255, 0.4)",
              letterSpacing: "1px",
              fontFamily: '"JetBrains Mono", monospace',
            }}
          >
            CINEMATIC STORY ENGINE • HEXMEDIA
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

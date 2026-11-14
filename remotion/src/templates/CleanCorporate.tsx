import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, Audio } from "remotion";
import { BackgroundMotion } from "../components/BackgroundMotion";
import { KaraokeCaptions } from "../components/KaraokeCaptions";
import { AudioWaveform } from "../components/AudioWaveform";
import { SoundDesign } from "../components/SoundDesign";
import { BackgroundAudio } from "../components/BackgroundAudio";
import { PictureInPicture } from "../components/PictureInPicture";
import { MotionCompositionProps } from "../types";

export const CleanCorporate: React.FC<MotionCompositionProps> = (props) => {
  const {
    title = "HEXMEDIA CORPORATE",
    subtitle = "Executive Briefing",
    speakerName = "المتحدث الرسمي",
    words = [],
    audioUrl,
    backgroundUrl,
    backgroundType = "gradient",
    scenes,
    accentColor = "#38BDF8",
    aspectRatio = "9:16",
    videoStartOffset = 0,
    videoMuted = false,
    videoVolume = 0.15,
    transitionEffect = "dissolve",
    fontFamily = "IBM Plex Sans Arabic",
    entryAnimation = "pop",
    smartEmojisEnabled = true,
    wordGlowBox = true,
    sfxEnabled = true,
    sfxVolume = 0.25,
    bgmPreset = "lofi_chill",
    bgmUrl,
    bgmVolume = 0.25,
    smartDucking = true,
    dynamicZoom = true,
    captionPositionPercent = 50,
    pipUrl,
    pipPosition = "top-left",
    pipScale = 0.28,
    pipMuted = true,
  } = props;

  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const isVertical = aspectRatio === "9:16";

  const captionJustify =
    captionPositionPercent <= 35
      ? "flex-start"
      : captionPositionPercent >= 65
      ? "flex-end"
      : "center";
  const captionPadTop = captionPositionPercent <= 35 ? "40px" : undefined;
  const captionPadBottom = captionPositionPercent >= 65 ? "40px" : undefined;

  return (
    <AbsoluteFill
      style={{
        fontFamily: `"${fontFamily || "IBM Plex Sans Arabic"}", sans-serif`,
        color: "#FFF",
      }}
    >
      {/* Background with Deep Slate & Clean Gradient + Multi-Scene */}
      <BackgroundMotion
        type={backgroundType}
        src={backgroundUrl}
        scenes={scenes}
        templateId="clean_corporate"
        overlayOpacity={0.70}
        videoStartOffset={videoStartOffset}
        videoMuted={videoMuted}
        videoVolume={videoVolume}
        transitionEffect={transitionEffect}
      />

      {/* Picture-in-Picture B-Roll Overlay */}
      <PictureInPicture
        url={pipUrl}
        position={pipPosition}
        scale={pipScale}
        muted={pipMuted}
        aspectRatio={aspectRatio}
        accentColor={accentColor}
      />

      {/* Voice Audio Track */}
      {audioUrl && <Audio src={audioUrl} />}

      {/* Background Music with Smart Ducking */}
      <BackgroundAudio
        bgmPreset={bgmPreset}
        bgmUrl={bgmUrl}
        bgmVolume={bgmVolume}
        smartDucking={smartDucking}
        words={words}
      />

      {/* Auto Sound Design SFX cues */}
      <SoundDesign
        words={words}
        aspectRatio={aspectRatio}
        templateId="clean_corporate"
        sfxEnabled={sfxEnabled}
        sfxVolume={sfxVolume}
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
              <div
                style={{
                  fontSize: isVertical ? "18px" : "16px",
                  fontWeight: 600,
                  color: "#F8FAFC",
                }}
              >
                {speakerName}
              </div>
              <div
                style={{
                  fontSize: isVertical ? "14px" : "12px",
                  color: "#94A3B8",
                }}
              >
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
              fontWeight: 600,
              fontSize: isVertical ? "13px" : "11px",
              letterSpacing: "1px",
              textTransform: "uppercase",
            }}
          >
            REPORT // AI
          </div>
        </div>

        {/* Captions Stage (with dynamic vertical repositioning) */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: captionJustify,
            paddingTop: captionPadTop,
            paddingBottom: captionPadBottom,
            width: "100%",
            flex: 1,
            gap: "24px",
            margin: "30px 0",
          }}
        >
          <KaraokeCaptions
            words={words}
            styleType="corporate"
            aspectRatio={aspectRatio}
            accentColor={accentColor}
            transitionEffect={transitionEffect}
            fontFamily={fontFamily}
            entryAnimation={entryAnimation}
            smartEmojisEnabled={smartEmojisEnabled}
            wordGlowBox={wordGlowBox}
            dynamicZoom={dynamicZoom}
            captionPositionPercent={captionPositionPercent}
          />
        </div>

        {/* Footer: Clean Brand & Waveform */}
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
            barCount={isVertical ? 26 : 44}
            height={isVertical ? 48 : 36}
            color={accentColor}
            secondaryColor="#60A5FA"
            styleType="corporate"
          />

          <div
            style={{
              fontSize: isVertical ? "14px" : "12px",
              color: "#64748B",
              fontFamily: '"JetBrains Mono", monospace',
              letterSpacing: "1px",
            }}
          >
            {title}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

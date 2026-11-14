import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, Audio } from "remotion";
import { BackgroundMotion } from "../components/BackgroundMotion";
import { KaraokeCaptions } from "../components/KaraokeCaptions";
import { AudioWaveform } from "../components/AudioWaveform";
import { SoundDesign } from "../components/SoundDesign";
import { BackgroundAudio } from "../components/BackgroundAudio";
import { PictureInPicture } from "../components/PictureInPicture";
import { MotionCompositionProps } from "../types";

export const DarkNeon: React.FC<MotionCompositionProps> = (props) => {
  const {
    title = "HEXMEDIA // DARK NEON",
    subtitle = "AI MOTION STUDIO",
    speakerName = "الراوي الذكي",
    words = [],
    audioUrl,
    backgroundUrl,
    backgroundType = "gradient",
    scenes,
    accentColor = "#00F0FF",
    aspectRatio = "9:16",
    videoStartOffset = 0,
    videoMuted = false,
    videoVolume = 0.15,
    transitionEffect = "zoom_in",
    fontFamily = "IBM Plex Sans Arabic",
    entryAnimation = "pop",
    smartEmojisEnabled = true,
    wordGlowBox = true,
    sfxEnabled = true,
    sfxVolume = 0.25,
    bgmPreset = "cyber_ambient",
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
  const seconds = (frame / fps).toFixed(2);
  const totalSeconds = (durationInFrames / fps).toFixed(2);

  // Caption vertical alignment based on captionPositionPercent
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
      {/* Background with Neon Glows & Tech Grid + Multi-Scene support */}
      <BackgroundMotion
        type={backgroundType}
        src={backgroundUrl}
        scenes={scenes}
        templateId="dark_neon"
        overlayOpacity={0.65}
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
        templateId="dark_neon"
        sfxEnabled={sfxEnabled}
        sfxVolume={sfxVolume}
      />

      {/* Main Content Layout */}
      <AbsoluteFill
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          alignItems: "center",
          padding: isVertical ? "90px 48px 80px 48px" : "60px 80px 50px 80px",
          zIndex: 10,
        }}
      >
        {/* Header HUD */}
        <div
          style={{
            width: "100%",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: "1px solid rgba(0, 240, 255, 0.2)",
            paddingBottom: "16px",
          }}
        >
          {/* Tech Badge */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              background: "rgba(8, 9, 13, 0.8)",
              border: `1px solid ${accentColor}44`,
              borderRadius: "8px",
              padding: "6px 14px",
              fontSize: isVertical ? "18px" : "15px",
              fontFamily: '"JetBrains Mono", monospace',
              color: accentColor,
              boxShadow: `0 0 12px ${accentColor}22`,
            }}
          >
            <span
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: accentColor,
                boxShadow: `0 0 8px ${accentColor}`,
              }}
            />
            <span>{speakerName}</span>
          </div>

          {/* Timecode */}
          <div
            style={{
              fontFamily: '"JetBrains Mono", monospace',
              fontSize: isVertical ? "18px" : "15px",
              color: "#94A3B8",
              letterSpacing: "1px",
            }}
          >
            REC [{seconds}s / {totalSeconds}s]
          </div>
        </div>

        {/* Center: Title & Karaoke Captions (with dynamic vertical repositioning) */}
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
            gap: isVertical ? "40px" : "28px",
            margin: isVertical ? "40px 0" : "20px 0",
          }}
        >
          {/* Optional Category / Subtitle pill */}
          <div
            style={{
              textTransform: "uppercase",
              fontSize: isVertical ? "20px" : "16px",
              letterSpacing: "3px",
              color: "#FF007F",
              fontWeight: 600,
              fontFamily: '"JetBrains Mono", monospace',
              textShadow: "0 0 12px rgba(255, 0, 127, 0.6)",
            }}
          >
            {subtitle}
          </div>

          {/* Interactive Karaoke Captions */}
          <KaraokeCaptions
            words={words}
            styleType="neon"
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

        {/* Footer: Waveform Visualizer & Branding */}
        <div
          style={{
            width: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "18px",
          }}
        >
          <AudioWaveform
            barCount={isVertical ? 28 : 48}
            height={isVertical ? 72 : 54}
            color={accentColor}
            secondaryColor="#FF007F"
            styleType="neon"
          />

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              width: "100%",
              paddingTop: "12px",
              borderTop: "1px solid rgba(255, 255, 255, 0.08)",
              fontSize: isVertical ? "16px" : "14px",
              fontFamily: '"JetBrains Mono", monospace',
              color: "#64748B",
            }}
          >
            <span>HEXMEDIA NEON // 4K 60FPS</span>
            <span>AUDIO-SYNC AI</span>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

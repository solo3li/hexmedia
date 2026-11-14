import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, Audio } from "remotion";
import { BackgroundMotion } from "../components/BackgroundMotion";
import { KaraokeCaptions } from "../components/KaraokeCaptions";
import { AudioWaveform } from "../components/AudioWaveform";
import { SoundDesign } from "../components/SoundDesign";
import { BackgroundAudio } from "../components/BackgroundAudio";
import { PictureInPicture } from "../components/PictureInPicture";
import { MotionCompositionProps } from "../types";

export const TikTokKinetic: React.FC<MotionCompositionProps> = (props) => {
  const {
    title = "TIKTOK / REELS KINETIC",
    subtitle = "VIRAL HOOK",
    speakerName = "HexMedia Shorts",
    words = [],
    audioUrl,
    backgroundUrl,
    backgroundType = "gradient",
    scenes,
    accentColor = "#A3E635",
    aspectRatio = "9:16",
    videoStartOffset = 0,
    videoMuted = false,
    videoVolume = 0.15,
    transitionEffect = "whip_pan",
    fontFamily = "IBM Plex Sans Arabic",
    entryAnimation = "pop",
    smartEmojisEnabled = true,
    wordGlowBox = true,
    sfxEnabled = true,
    sfxVolume = 0.25,
    bgmPreset = "energetic_hook",
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
  const { durationInFrames } = useVideoConfig();

  const isVertical = aspectRatio === "9:16";
  const progressPercent = Math.min(100, Math.max(0, (frame / durationInFrames) * 100));

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
      {/* Dynamic Purple/Violet Mesh Background with Multi-Scene support */}
      <BackgroundMotion
        type={backgroundType}
        src={backgroundUrl}
        scenes={scenes}
        templateId="tiktok_kinetic"
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
        templateId="tiktok_kinetic"
        sfxEnabled={sfxEnabled}
        sfxVolume={sfxVolume}
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
        </div>

        {/* Center Captions Area (with dynamic vertical repositioning) */}
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
            gap: isVertical ? "30px" : "20px",
            margin: isVertical ? "30px 0" : "15px 0",
          }}
        >
          {/* Viral Subtitle Hook Tag */}
          <div
            style={{
              fontSize: isVertical ? "22px" : "18px",
              fontWeight: 800,
              backgroundColor: "rgba(255, 230, 0, 0.15)",
              color: "#FFE600",
              border: "1.5px solid #FFE600",
              borderRadius: "12px",
              padding: "4px 18px",
              textTransform: "uppercase",
              letterSpacing: "1px",
              boxShadow: "0 0 15px rgba(255, 230, 0, 0.3)",
            }}
          >
            {subtitle}
          </div>

          <KaraokeCaptions
            words={words}
            styleType="kinetic"
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

        {/* Bottom Bar: Mini Equalizer & Title */}
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
            barCount={isVertical ? 32 : 52}
            height={isVertical ? 64 : 48}
            color={accentColor}
            secondaryColor="#A855F7"
            styleType="kinetic"
          />

          <div
            style={{
              fontSize: isVertical ? "16px" : "14px",
              fontWeight: 600,
              color: "rgba(255, 255, 255, 0.8)",
              letterSpacing: "1px",
              textTransform: "uppercase",
            }}
          >
            {title}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

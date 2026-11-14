import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, Audio } from "remotion";
import { BackgroundMotion } from "../components/BackgroundMotion";
import { KaraokeCaptions } from "../components/KaraokeCaptions";
import { AudioWaveform } from "../components/AudioWaveform";
import { SoundDesign } from "../components/SoundDesign";
import { BackgroundAudio } from "../components/BackgroundAudio";
import { PictureInPicture } from "../components/PictureInPicture";
import { MotionCompositionProps } from "../types";

export const CinematicNarrative: React.FC<MotionCompositionProps> = (props) => {
  const {
    title = "دراما سينمائية",
    subtitle = "سرد روائي أصيل",
    speakerName = "الراوي",
    words = [],
    audioUrl,
    backgroundUrl,
    backgroundType = "gradient",
    scenes,
    accentColor = "#F59E0B",
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
    bgmPreset = "cinematic_warm",
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
      {/* Background with Cinematic Warm Tones & Ken Burns + Multi-Scene */}
      <BackgroundMotion
        type={backgroundType}
        src={backgroundUrl}
        scenes={scenes}
        templateId="cinematic_narrative"
        overlayOpacity={0.68}
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
        templateId="cinematic_narrative"
        sfxEnabled={sfxEnabled}
        sfxVolume={sfxVolume}
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
            <span>{speakerName}</span>
            <span>•</span>
            <span>{subtitle}</span>
          </div>

          <div
            style={{
              fontSize: isVertical ? "16px" : "14px",
              color: "#94A3B8",
              fontStyle: "italic",
            }}
          >
            {title}
          </div>
        </div>

        {/* Captions Stage (with dynamic vertical repositioning) */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: captionJustify,
            paddingTop: captionPadTop,
            paddingBottom: captionPadBottom,
            width: "100%",
            flex: 1,
            margin: "20px 0",
          }}
        >
          <KaraokeCaptions
            words={words}
            styleType="cinematic"
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

        {/* Footer: Subtle Audio Waveform */}
        <div
          style={{
            width: "100%",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
          }}
        >
          <AudioWaveform
            barCount={isVertical ? 24 : 40}
            height={isVertical ? 48 : 36}
            color={accentColor}
            secondaryColor="#D97706"
            styleType="cinematic"
          />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

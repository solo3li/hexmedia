import React from "react";
import { Composition, Folder } from "remotion";
import { MotionStudioComposition } from "./MotionStudioComposition";
import { DarkNeon } from "./templates/DarkNeon";
import { CinematicNarrative } from "./templates/CinematicNarrative";
import { TikTokKinetic } from "./templates/TikTokKinetic";
import { CleanCorporate } from "./templates/CleanCorporate";
import { AudioWaveform } from "./components/AudioWaveform";
import { KaraokeCaptions } from "./components/KaraokeCaptions";
import { defaultMotionProps } from "./types";

const AudioWaveformPreview: React.FC<typeof defaultMotionProps> = (props) => (
  <div
    style={{
      width: "100%",
      height: "100%",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      backgroundColor: "#08080a",
    }}
  >
    <AudioWaveform
      barCount={props.aspectRatio === "9:16" ? 28 : 48}
      height={props.aspectRatio === "9:16" ? 72 : 54}
      color={props.accentColor || "#00F0FF"}
      secondaryColor="#FF007F"
      styleType="neon"
    />
  </div>
);

const KaraokeCaptionsPreview: React.FC<typeof defaultMotionProps> = (props) => (
  <div
    style={{
      width: "100%",
      height: "100%",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      backgroundColor: "#08080a",
      padding: props.aspectRatio === "9:16" ? "60px 40px" : "40px 80px",
    }}
  >
    <KaraokeCaptions
      words={props.words || defaultMotionProps.words}
      styleType="neon"
      aspectRatio={props.aspectRatio || "9:16"}
      accentColor={props.accentColor || "#00F0FF"}
    />
  </div>
);

export const RemotionRoot: React.FC = () => {
  const fps = 30;
  const durationInFrames = 150; // default 5s preview

  const calculateDynamicMetadata = ({ props }: { props: typeof defaultMotionProps }) => {
    const customFps = props.fps || 30;
    const duration = props.durationInSeconds || 5.0;
    return {
      durationInFrames: Math.max(15, Math.round(duration * customFps)),
      fps: customFps,
    };
  };

  return (
    <>
      {/* Universal Dynamic Composition */}
      <Composition
        id="MotionStudio-Dynamic-9-16"
        component={MotionStudioComposition}
        durationInFrames={durationInFrames}
        fps={fps}
        width={1080}
        height={1920}
        defaultProps={{ ...defaultMotionProps, aspectRatio: "9:16" }}
        calculateMetadata={calculateDynamicMetadata}
      />
      <Composition
        id="MotionStudio-Dynamic-16-9"
        component={MotionStudioComposition}
        durationInFrames={durationInFrames}
        fps={fps}
        width={1920}
        height={1080}
        defaultProps={{ ...defaultMotionProps, aspectRatio: "16:9" }}
        calculateMetadata={calculateDynamicMetadata}
      />

      <Folder name="Vertical-9-16">
        <Composition
          id="DarkNeon-9-16"
          component={DarkNeon}
          durationInFrames={durationInFrames}
          fps={fps}
          width={1080}
          height={1920}
          defaultProps={{ ...defaultMotionProps, aspectRatio: "9:16", templateId: "dark_neon" }}
          calculateMetadata={calculateDynamicMetadata}
        />
        <Composition
          id="CinematicNarrative-9-16"
          component={CinematicNarrative}
          durationInFrames={durationInFrames}
          fps={fps}
          width={1080}
          height={1920}
          defaultProps={{ ...defaultMotionProps, aspectRatio: "9:16", templateId: "cinematic_narrative" }}
          calculateMetadata={calculateDynamicMetadata}
        />
        <Composition
          id="TikTokKinetic-9-16"
          component={TikTokKinetic}
          durationInFrames={durationInFrames}
          fps={fps}
          width={1080}
          height={1920}
          defaultProps={{ ...defaultMotionProps, aspectRatio: "9:16", templateId: "tiktok_kinetic" }}
          calculateMetadata={calculateDynamicMetadata}
        />
        <Composition
          id="CleanCorporate-9-16"
          component={CleanCorporate}
          durationInFrames={durationInFrames}
          fps={fps}
          width={1080}
          height={1920}
          defaultProps={{ ...defaultMotionProps, aspectRatio: "9:16", templateId: "clean_corporate" }}
          calculateMetadata={calculateDynamicMetadata}
        />
      </Folder>

      <Folder name="Horizontal-16-9">
        <Composition
          id="DarkNeon-16-9"
          component={DarkNeon}
          durationInFrames={durationInFrames}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{ ...defaultMotionProps, aspectRatio: "16:9", templateId: "dark_neon" }}
          calculateMetadata={calculateDynamicMetadata}
        />
        <Composition
          id="CinematicNarrative-16-9"
          component={CinematicNarrative}
          durationInFrames={durationInFrames}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{ ...defaultMotionProps, aspectRatio: "16:9", templateId: "cinematic_narrative" }}
          calculateMetadata={calculateDynamicMetadata}
        />
        <Composition
          id="TikTokKinetic-16-9"
          component={TikTokKinetic}
          durationInFrames={durationInFrames}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{ ...defaultMotionProps, aspectRatio: "16:9", templateId: "tiktok_kinetic" }}
          calculateMetadata={calculateDynamicMetadata}
        />
        <Composition
          id="CleanCorporate-16-9"
          component={CleanCorporate}
          durationInFrames={durationInFrames}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{ ...defaultMotionProps, aspectRatio: "16:9", templateId: "clean_corporate" }}
          calculateMetadata={calculateDynamicMetadata}
        />
      </Folder>

      <Folder name="Components-Preview">
        <Composition
          id="AudioWaveform-9-16"
          component={AudioWaveformPreview}
          durationInFrames={durationInFrames}
          fps={fps}
          width={1080}
          height={1920}
          defaultProps={{ ...defaultMotionProps, aspectRatio: "9:16" }}
          calculateMetadata={calculateDynamicMetadata}
        />
        <Composition
          id="AudioWaveform-16-9"
          component={AudioWaveformPreview}
          durationInFrames={durationInFrames}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{ ...defaultMotionProps, aspectRatio: "16:9" }}
          calculateMetadata={calculateDynamicMetadata}
        />
        <Composition
          id="KaraokeCaptions-9-16"
          component={KaraokeCaptionsPreview}
          durationInFrames={durationInFrames}
          fps={fps}
          width={1080}
          height={1920}
          defaultProps={{ ...defaultMotionProps, aspectRatio: "9:16" }}
          calculateMetadata={calculateDynamicMetadata}
        />
        <Composition
          id="KaraokeCaptions-16-9"
          component={KaraokeCaptionsPreview}
          durationInFrames={durationInFrames}
          fps={fps}
          width={1920}
          height={1080}
          defaultProps={{ ...defaultMotionProps, aspectRatio: "16:9" }}
          calculateMetadata={calculateDynamicMetadata}
        />
      </Folder>
    </>
  );
};

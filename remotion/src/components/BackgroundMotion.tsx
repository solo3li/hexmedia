import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, Img, OffthreadVideo, Sequence } from "remotion";
import { SceneClip } from "../types";

interface BackgroundMotionProps {
  type?: "color" | "gradient" | "image" | "video";
  src?: string;
  scenes?: SceneClip[];
  templateId: "dark_neon" | "cinematic_narrative" | "tiktok_kinetic" | "clean_corporate";
  overlayOpacity?: number;
  videoStartOffset?: number;
  videoMuted?: boolean;
  videoVolume?: number;
  transitionEffect?: "whip_pan" | "zoom_in" | "glitch" | "dissolve" | "none";
}

export const BackgroundMotion: React.FC<BackgroundMotionProps> = ({
  type = "gradient",
  src,
  scenes,
  templateId,
  overlayOpacity = 0.60,
  videoStartOffset = 0,
  videoMuted = false,
  videoVolume = 0.15,
  transitionEffect = "zoom_in",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const currentTime = frame / fps;
  const totalDuration = durationInFrames / fps;

  // Transition Camera Dynamics
  let zoomStart = 1.0;
  let zoomEnd = 1.12;
  if (transitionEffect === "zoom_in") {
    zoomStart = 1.0;
    zoomEnd = 1.20;
  }

  const zoom = interpolate(frame, [0, durationInFrames], [zoomStart, zoomEnd], {
    extrapolateRight: "clamp",
  });

  // Pan / Whip-Pan
  let panX = interpolate(frame, [0, durationInFrames], [0, -20], {
    extrapolateRight: "clamp",
  });
  if (transitionEffect === "whip_pan") {
    const whipIn = interpolate(frame, [0, 8], [60, 0], {
      extrapolateRight: "clamp",
    });
    panX += whipIn;
  }

  // Glitch Jitter
  let jitterX = 0;
  let jitterY = 0;
  let glitchRGB = 0;
  if (transitionEffect === "glitch") {
    const cycle = frame % 30;
    if (cycle < 4) {
      jitterX = (Math.sin(frame * 9) > 0 ? 1 : -1) * (cycle * 4);
      jitterY = (Math.cos(frame * 7) > 0 ? 1 : -1) * (cycle * 2);
      glitchRGB = cycle * 3;
    }
  }

  // Animated gradient shifts for procedural backgrounds
  const angle = Math.round((frame * 0.4) % 360);
  const orb1Y = Math.sin(frame * 0.03) * 60;
  const orb2X = Math.cos(frame * 0.025) * 80;

  let baseBackground = "#090A0F";
  let gradientOverlay = "";

  if (templateId === "dark_neon") {
    baseBackground = "#08090D";
    gradientOverlay = `
      radial-gradient(circle at ${40 + orb2X * 0.1}% ${30 + orb1Y * 0.1}%, rgba(0, 240, 255, 0.16) 0%, transparent 55%),
      radial-gradient(circle at 75% 80%, rgba(255, 0, 128, 0.12) 0%, transparent 50%),
      linear-gradient(${angle}deg, #08090D 0%, #0D111A 100%)
    `;
  } else if (templateId === "cinematic_narrative") {
    baseBackground = "#0B0C10";
    gradientOverlay = `
      radial-gradient(ellipse at 50% 40%, rgba(245, 158, 11, 0.10) 0%, transparent 60%),
      radial-gradient(circle at 20% 90%, rgba(30, 41, 59, 0.4) 0%, transparent 50%),
      linear-gradient(180deg, #07080B 0%, #10121A 100%)
    `;
  } else if (templateId === "tiktok_kinetic") {
    baseBackground = "#090514";
    gradientOverlay = `
      radial-gradient(circle at ${60 + orb2X * 0.1}% 40%, rgba(168, 85, 247, 0.22) 0%, transparent 60%),
      radial-gradient(circle at 30% ${70 + orb1Y * 0.1}%, rgba(163, 230, 53, 0.14) 0%, transparent 55%),
      linear-gradient(${angle}deg, #0C061F 0%, #05020A 100%)
    `;
  } else {
    // clean_corporate
    baseBackground = "#0B1120";
    gradientOverlay = `
      radial-gradient(circle at 50% 30%, rgba(56, 189, 248, 0.12) 0%, transparent 60%),
      linear-gradient(180deg, #0B1120 0%, #020617 100%)
    `;
  }

  // Multi-Scene Timeline or Single Background
  if (scenes && scenes.length > 0) {
    const defaultDurationPerScene = totalDuration / scenes.length;
    let accumulatedFrames = 0;

    return (
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          overflow: "hidden",
          backgroundColor: baseBackground,
          zIndex: 0,
          transform: `translate(${jitterX}px, ${jitterY}px)`,
        }}
      >
        {scenes.map((sc, idx) => {
          const sceneDur = sc.duration && sc.duration > 0 ? sc.duration : defaultDurationPerScene;
          const sceneFrames = Math.max(1, Math.round(sceneDur * fps));
          const fromFrame = accumulatedFrames;
          accumulatedFrames += sceneFrames;

          const isVid =
            sc.type === "video" ||
            (!sc.type &&
              (sc.url.toLowerCase().endsWith(".mp4") ||
                sc.url.toLowerCase().endsWith(".webm") ||
                sc.url.toLowerCase().endsWith(".mov") ||
                sc.url.includes("/videos/")));

          const startOffsetFrames = Math.max(0, Math.round((sc.startOffset || 0) * fps));

          return (
            <Sequence key={sc.id || idx} from={fromFrame} durationInFrames={sceneFrames}>
              {isVid ? (
                <OffthreadVideo
                  src={sc.url}
                  startFrom={startOffsetFrames}
                  muted={videoMuted}
                  volume={videoMuted ? 0 : videoVolume}
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                    transform: `scale(${zoom}) translate(${panX}px, 0px)`,
                    filter:
                      glitchRGB > 0
                        ? `drop-shadow(${glitchRGB}px 0 rgba(0,240,255,0.7)) drop-shadow(-${glitchRGB}px 0 rgba(255,0,128,0.7))`
                        : undefined,
                  }}
                />
              ) : (
                <Img
                  src={sc.url}
                  style={{
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                    transform: `scale(${zoom}) translate(${panX}px, 0px)`,
                  }}
                />
              )}
            </Sequence>
          );
        })}

        {/* Readability & Tint Overlay */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            backgroundColor: `rgba(9, 10, 15, ${overlayOpacity})`,
            background: gradientOverlay,
            mixBlendMode: "multiply",
          }}
        />
      </div>
    );
  }

  // Single Background Mode
  let resolvedType = type;
  if (!resolvedType && src) {
    const lower = src.toLowerCase();
    resolvedType =
      lower.endsWith(".mp4") || lower.endsWith(".webm") || lower.endsWith(".mov") || lower.includes("/videos/")
        ? "video"
        : "image";
  }
  const startFrame = Math.max(0, Math.round(videoStartOffset * fps));

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        overflow: "hidden",
        backgroundColor: baseBackground,
        zIndex: 0,
        transform: `translate(${jitterX}px, ${jitterY}px)`,
      }}
    >
      {src && resolvedType === "video" ? (
        <>
          <OffthreadVideo
            src={src}
            startFrom={startFrame}
            muted={videoMuted}
            volume={videoMuted ? 0 : videoVolume}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${zoom}) translate(${panX}px, 0px)`,
              filter:
                glitchRGB > 0
                  ? `drop-shadow(${glitchRGB}px 0 rgba(0,240,255,0.7)) drop-shadow(-${glitchRGB}px 0 rgba(255,0,128,0.7))`
                  : undefined,
            }}
          />
          {/* Readability & Tint Overlay */}
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              backgroundColor: `rgba(9, 10, 15, ${overlayOpacity})`,
              background: gradientOverlay,
              mixBlendMode: "multiply",
            }}
          />
        </>
      ) : src && resolvedType === "image" ? (
        <>
          <Img
            src={src}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${zoom}) translate(${panX}px, 0px)`,
            }}
          />
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              backgroundColor: `rgba(9, 10, 15, ${overlayOpacity})`,
              background: gradientOverlay,
            }}
          />
        </>
      ) : (
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            background: gradientOverlay,
          }}
        />
      )}
    </div>
  );
};

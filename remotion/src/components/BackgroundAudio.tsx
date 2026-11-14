import React, { useMemo } from "react";
import { Audio, useVideoConfig } from "remotion";
import { WordTimestamp } from "../types";
import { getBgmDataUri } from "../audio/soundPresets";

interface BackgroundAudioProps {
  bgmPreset?: "cinematic_warm" | "cyber_ambient" | "lofi_chill" | "energetic_hook" | "none";
  bgmUrl?: string;
  bgmVolume?: number;
  smartDucking?: boolean;
  words?: WordTimestamp[];
}

export const BackgroundAudio: React.FC<BackgroundAudioProps> = ({
  bgmPreset = "cyber_ambient",
  bgmUrl,
  bgmVolume = 0.25,
  smartDucking = true,
  words = [],
}) => {
  const { fps } = useVideoConfig();

  const resolvedSrc = useMemo(() => {
    if (bgmPreset === "none" && !bgmUrl) return null;
    if (bgmUrl && bgmUrl.trim()) return bgmUrl.trim();
    if (bgmPreset && bgmPreset !== "none") {
      return getBgmDataUri(bgmPreset);
    }
    return null;
  }, [bgmPreset, bgmUrl]);

  if (!resolvedSrc) {
    return null;
  }

  // Automated ducking volume function: 12% during dialogue, 40% in silence
  const duckingVolumeCalculator = (frame: number): number => {
    const t = frame / fps;
    const baseVol = bgmVolume ?? 0.25;

    if (!smartDucking || !words || words.length === 0) {
      return baseVol;
    }

    // Check if current time is within speech range (with 0.08s lead/trail margins)
    const isSpeaking = words.some(
      (w) => t >= Math.max(0, w.start - 0.08) && t <= (w.end + 0.12)
    );

    // Ducking rules: 12% during speech, 40% in silence / breaks
    const duckFactor = isSpeaking ? 0.12 : 0.40;
    return baseVol * duckFactor;
  };

  return (
    <Audio
      src={resolvedSrc}
      loop
      volume={duckingVolumeCalculator}
    />
  );
};

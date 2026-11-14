import React, { useMemo } from "react";
import { Audio, Sequence, useVideoConfig } from "remotion";
import { WordTimestamp } from "../types";
import { getWhooshSfxDataUri, getPopSfxDataUri } from "../audio/soundPresets";

interface SoundDesignProps {
  words?: WordTimestamp[];
  aspectRatio?: "9:16" | "16:9";
  templateId?: string;
  sfxEnabled?: boolean;
  sfxVolume?: number;
}

export const SoundDesign: React.FC<SoundDesignProps> = ({
  words = [],
  aspectRatio = "9:16",
  templateId = "dark_neon",
  sfxEnabled = true,
  sfxVolume = 0.25,
}) => {
  const { fps } = useVideoConfig();

  const whooshUri = useMemo(() => getWhooshSfxDataUri(), []);
  const popUri = useMemo(() => getPopSfxDataUri(), []);

  if (!sfxEnabled || words.length === 0) {
    return null;
  }

  // Calculate chunk boundaries
  const chunkSize = aspectRatio === "9:16" ? (templateId === "tiktok_kinetic" ? 3 : 4) : 7;
  const chunkCount = Math.ceil(words.length / chunkSize);

  const transitionFrames: number[] = [];
  for (let c = 0; c < chunkCount; c++) {
    const chunkWord = words[c * chunkSize];
    if (chunkWord) {
      const frameStart = Math.max(0, Math.round(chunkWord.start * fps));
      transitionFrames.push(frameStart);
    }
  }

  return (
    <>
      {/* Whoosh sound on chunk transitions */}
      {transitionFrames.map((f, idx) => (
        <Sequence
          key={`whoosh-${idx}-${f}`}
          from={f}
          durationInFrames={Math.round(fps * 0.35)}
        >
          <Audio src={whooshUri} volume={sfxVolume} />
        </Sequence>
      ))}

      {/* Subtle pop sound on key word emphasis (first word of each chunk and middle punch words) */}
      {words.map((w, idx) => {
        // Only trigger pop on chunk starts or every 4th word to avoid clutter
        if (idx % chunkSize !== 0 && idx % 3 !== 0) return null;
        const popFrame = Math.max(0, Math.round(w.start * fps));
        return (
          <Sequence
            key={`pop-${idx}-${popFrame}`}
            from={popFrame}
            durationInFrames={Math.round(fps * 0.12)}
          >
            <Audio src={popUri} volume={sfxVolume * 0.65} />
          </Sequence>
        );
      })}
    </>
  );
};

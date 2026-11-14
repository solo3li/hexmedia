import React, { useMemo } from "react";
import { Audio, Sequence, useVideoConfig } from "remotion";
import { WordTimestamp } from "../types";
import { getWhooshSfxDataUri, getPopSfxDataUri, getClickSfxDataUri } from "../audio/soundPresets";

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
  const clickUri = useMemo(() => getClickSfxDataUri(), []);

  if (!sfxEnabled || words.length === 0) {
    return null;
  }

  // Calculate chunk boundaries
  const chunkSize = aspectRatio === "9:16" ? (templateId === "tiktok_kinetic" ? 3 : 4) : 7;
  const chunkCount = Math.ceil(words.length / chunkSize);

  // Transition frames strictly between chunk changes (cuts)
  const transitionFrames: number[] = [];
  for (let c = 1; c < chunkCount; c++) {
    const chunkWord = words[c * chunkSize];
    if (chunkWord) {
      const frameStart = Math.max(0, Math.round(chunkWord.start * fps));
      transitionFrames.push(frameStart);
    }
  }

  return (
    <>
      {/* Whoosh sound on phrase cuts & chunk transitions (A3) */}
      {transitionFrames.map((f, idx) => (
        <Sequence
          key={`whoosh-${idx}-${f}`}
          from={f}
          durationInFrames={Math.round(fps * 0.35)}
        >
          <Audio src={whooshUri} volume={sfxVolume} />
        </Sequence>
      ))}

      {/* Pop sound on chunk opening key word emphasis */}
      {words.map((w, idx) => {
        if (idx % chunkSize !== 0) return null;
        const popFrame = Math.max(0, Math.round(w.start * fps));
        return (
          <Sequence
            key={`pop-${idx}-${popFrame}`}
            from={popFrame}
            durationInFrames={Math.round(fps * 0.12)}
          >
            <Audio src={popUri} volume={sfxVolume * 0.7} />
          </Sequence>
        );
      })}

      {/* Crisp click SFX on rhythmic subtitle step words */}
      {words.map((w, idx) => {
        if (idx % chunkSize === 0 || idx % 2 !== 0) return null;
        const clickFrame = Math.max(0, Math.round(w.start * fps));
        return (
          <Sequence
            key={`click-${idx}-${clickFrame}`}
            from={clickFrame}
            durationInFrames={Math.round(fps * 0.08)}
          >
            <Audio src={clickUri} volume={sfxVolume * 0.5} />
          </Sequence>
        );
      })}
    </>
  );
};

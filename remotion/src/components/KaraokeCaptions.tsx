import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { WordTimestamp } from "../types";

interface KaraokeCaptionsProps {
  words: WordTimestamp[];
  styleType: "neon" | "cinematic" | "kinetic" | "corporate";
  aspectRatio: "9:16" | "16:9";
  accentColor?: string;
  transitionEffect?: "whip_pan" | "zoom_in" | "glitch" | "dissolve" | "none";
  fontFamily?: string;
  entryAnimation?: "pop" | "bounce" | "wave" | "fade";
  smartEmojisEnabled?: boolean;
  wordGlowBox?: boolean;
  dynamicZoom?: boolean;
  captionPositionPercent?: number;
}

// Keyword-to-Emoji dictionary for viral kinetic video hooks
const SMART_EMOJI_KEYWORDS: [RegExp, string][] = [
  [/صاروخ|انطلاق|صاروخي|rocket|launch/i, "🚀"],
  [/نار|حريق|شعلة|ولع|fire|flame|lit/i, "🔥"],
  [/فكرة|إبداع|خاطرة|ابتكار|idea|think/i, "💡"],
  [/سرعة|برق|خاطف|صدمة|سريع|speed|flash|lightning/i, "⚡"],
  [/مال|فلوس|أرباح|ثروة|دولار|غنيمة|كاش|money|cash|profit/i, "💰"],
  [/ذكاء|روبوت|تقنية|برمج|كود|خوارزم|ai|robot|tech|code/i, "🤖"],
  [/نسر|صقر|طيران|شاهين|تحليق|eagle/i, "🦅"],
  [/قلب|حب|عشق|غرام|love|heart/i, "❤️"],
  [/هدف|تركيز|دقة|إصابة|target|goal|focus/i, "🎯"],
  [/سر|لغز|مفتاح|حل|key|secret/i, "🔑"],
  [/نجاح|فوز|كأس|بطولة|انتصار|win|trophy/i, "🏆"],
  [/قنبلة|انفجار|زلزال|صدم|boom|bomb/i, "💣"],
  [/تحذير|خطر|انتباه|تنبيه|warning|danger/i, "⚠️"],
  [/ساعة|وقت|زمن|دقيقة|ميعاد|time|clock/i, "⏰"],
  [/عين|نظرة|شوف|شاهد|راقب|eye|watch|look/i, "👁️"],
  [/سحر|خيال|إعجاز|مبهر|magic|sparkles/i, "✨"],
  [/نجم|قمة|أفضل|أول|star/i, "⭐"],
  [/درع|حماية|أمان|حصن|shield|security/i, "🛡️"],
];

function getWordEmoji(rawWord: string): string | null {
  if (!rawWord) return null;
  const clean = rawWord.replace(/[^\w\u0600-\u06FF]/g, "").trim();
  for (const [pattern, emoji] of SMART_EMOJI_KEYWORDS) {
    if (pattern.test(clean)) {
      return emoji;
    }
  }
  return null;
}

export const KaraokeCaptions: React.FC<KaraokeCaptionsProps> = ({
  words = [],
  styleType,
  aspectRatio,
  accentColor,
  transitionEffect = "zoom_in",
  fontFamily = "IBM Plex Sans Arabic",
  entryAnimation = "pop",
  smartEmojisEnabled = true,
  wordGlowBox = true,
  dynamicZoom = true,
  captionPositionPercent,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  if (!words || words.length === 0) {
    return null;
  }

  // Find index of current word
  let activeIndex = words.findIndex(
    (w) => currentTime >= w.start && currentTime <= w.end
  );

  // If between words, pick closest previous or 0
  if (activeIndex === -1) {
    if (currentTime < words[0].start) {
      activeIndex = 0;
    } else {
      for (let i = words.length - 1; i >= 0; i--) {
        if (currentTime >= words[i].start) {
          activeIndex = i;
          break;
        }
      }
      if (activeIndex === -1) activeIndex = words.length - 1;
    }
  }

  // Chunking strategy:
  // 9:16 (TikTok/Reels): chunk size 3-4 words for quick kinetic reading.
  // 16:9 (Horizontal/YouTube): chunk size 6-7 words for horizontal cinematic readability.
  const chunkSize = aspectRatio === "9:16" ? (styleType === "kinetic" ? 3 : 4) : 7;
  const chunkIndex = Math.floor(activeIndex / chunkSize);
  const visibleWords = words.slice(
    chunkIndex * chunkSize,
    (chunkIndex + 1) * chunkSize
  );

  // Chunk transition dynamics
  const chunkStartSec = visibleWords[0]?.start ?? 0;
  const chunkStartFrame = Math.round(chunkStartSec * fps);
  const chunkAge = Math.max(0, frame - chunkStartFrame);

  let chunkTranslateX = 0;
  let chunkScale = 1.0;
  let chunkOpacity = 1.0;
  let chunkFilter = "none";

  if (transitionEffect === "whip_pan") {
    chunkTranslateX = interpolate(chunkAge, [0, 6], [45, 0], {
      extrapolateRight: "clamp",
    });
    chunkOpacity = interpolate(chunkAge, [0, 4], [0.3, 1.0], {
      extrapolateRight: "clamp",
    });
  } else if (transitionEffect === "zoom_in") {
    const chunkSpring = spring({
      frame: chunkAge,
      fps,
      config: { damping: 14, stiffness: 170, mass: 0.5 },
    });
    chunkScale = interpolate(chunkSpring, [0, 1], [0.88, 1.0]);
    chunkOpacity = interpolate(chunkAge, [0, 3], [0.2, 1.0], {
      extrapolateRight: "clamp",
    });
  } else if (transitionEffect === "glitch") {
    if (chunkAge < 6) {
      const gOffset = (chunkAge % 2 === 0 ? 1 : -1) * (6 - chunkAge) * 3;
      chunkTranslateX = gOffset;
      chunkFilter = `drop-shadow(3px 0 #00F0FF) drop-shadow(-3px 0 #FF007F)`;
    }
  } else if (transitionEffect === "dissolve") {
    chunkOpacity = interpolate(chunkAge, [0, 8], [0, 1.0], {
      extrapolateRight: "clamp",
    });
  }

  // Auto Jump Cuts & Dynamic Zoom: alternating 1.0x -> 1.14x between speech chunks
  let jumpCutScale = 1.0;
  if (dynamicZoom) {
    const isOddChunk = chunkIndex % 2 === 1;
    const targetScale = isOddChunk ? 1.14 : 1.0;
    const jumpCutSpring = spring({
      frame: chunkAge,
      fps,
      config: { damping: 14, stiffness: 220, mass: 0.5 },
    });
    jumpCutScale = interpolate(
      jumpCutSpring,
      [0, 1],
      [isOddChunk ? 1.0 : 1.14, targetScale]
    );
  }

  // Font size calculation
  let baseFontSize = aspectRatio === "9:16" ? 64 : 48;
  if (styleType === "kinetic") {
    baseFontSize = aspectRatio === "9:16" ? 76 : 56;
  } else if (styleType === "cinematic") {
    baseFontSize = aspectRatio === "9:16" ? 54 : 42;
  }

  const effectiveFontFamily = fontFamily ? `"${fontFamily}", sans-serif` : '"IBM Plex Sans Arabic", sans-serif';

  return (
    <div
      dir="rtl"
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        alignItems: "center",
        gap: aspectRatio === "9:16" ? "14px 20px" : "18px 24px",
        width: "92%",
        maxWidth: aspectRatio === "9:16" ? "920px" : "1500px",
        margin: "0 auto",
        lineHeight: 1.5,
        textAlign: "center",
        transform: `scale(${chunkScale * jumpCutScale}) translateX(${chunkTranslateX}px)`,
        opacity: chunkOpacity,
        filter: chunkFilter,
        transition: "transform 0.05s ease-out, opacity 0.05s ease-out",
        fontFamily: effectiveFontFamily,
      }}
    >
      {visibleWords.map((item, idx) => {
        const globalIdx = chunkIndex * chunkSize + idx;
        const isActive = globalIdx === activeIndex;
        const isPast = globalIdx < activeIndex;

        // Active word entry spring
        const wordStartFrame = Math.round(item.start * fps);
        const wordFrame = Math.max(0, frame - wordStartFrame);
        const scaleSpring = spring({
          frame: wordFrame,
          fps,
          config: {
            damping: 12,
            stiffness: 180,
            mass: 0.6,
          },
        });

        // Entry animation variants: pop, bounce, wave, fade
        let wordTranslateY = 0;
        let wordCustomScale = 1.0;
        let wordCustomOpacity = 1.0;

        if (entryAnimation === "bounce") {
          const bounceOffset = interpolate(scaleSpring, [0, 0.6, 1], [0, -16, 0]);
          wordTranslateY = isActive ? bounceOffset : 0;
          wordCustomScale = isActive ? interpolate(scaleSpring, [0, 1], [0.92, 1.20]) : 1.0;
        } else if (entryAnimation === "wave") {
          const wavePhase = Math.sin((frame + globalIdx * 3.5) * 0.16) * 7;
          wordTranslateY = wavePhase;
          wordCustomScale = isActive ? interpolate(scaleSpring, [0, 1], [1.0, 1.15]) : 1.0;
        } else if (entryAnimation === "fade") {
          wordCustomOpacity = interpolate(wordFrame, [0, 4], [0.3, 1.0], {
            extrapolateRight: "clamp",
          });
          wordCustomScale = isActive ? 1.12 : 1.0;
        } else {
          // pop (default)
          wordCustomScale = isActive
            ? interpolate(scaleSpring, [0, 1], [1.0, styleType === "kinetic" ? 1.24 : 1.14])
            : 1.0;
        }

        // Color & Badge definitions per template
        let textColor = "#FFFFFF";
        let textShadow = "none";
        let bgBadge = "transparent";
        let borderBadge = "transparent";
        let glowShadow = "none";

        if (styleType === "neon") {
          const neonAccent = accentColor || "#00F0FF";
          if (isActive) {
            textColor = neonAccent;
            textShadow = `0 0 16px ${neonAccent}, 0 0 32px ${neonAccent}AA`;
            if (wordGlowBox) {
              bgBadge = "rgba(0, 240, 255, 0.16)";
              borderBadge = `1.5px solid ${neonAccent}`;
              glowShadow = `0 0 24px rgba(0, 240, 255, 0.4), inset 0 0 14px rgba(0, 240, 255, 0.2)`;
            }
          } else if (isPast) {
            textColor = "#FFFFFF";
          } else {
            textColor = "#64748B";
          }
        } else if (styleType === "kinetic") {
          const kineticAccent = accentColor || "#A3E635";
          if (isActive) {
            textColor = "#09090B";
            bgBadge = kineticAccent;
            textShadow = "none";
            if (wordGlowBox) {
              glowShadow = `0 0 30px rgba(163, 230, 53, 0.65), 0 8px 20px rgba(0,0,0,0.4)`;
              borderBadge = `2px solid #FFFFFF`;
            }
          } else if (isPast) {
            textColor = "#FFFFFF";
          } else {
            textColor = "#71717A";
          }
        } else if (styleType === "cinematic") {
          const goldAccent = accentColor || "#F59E0B";
          if (isActive) {
            textColor = goldAccent;
            textShadow = "0 0 20px rgba(245, 158, 11, 0.6)";
            if (wordGlowBox) {
              bgBadge = "rgba(245, 158, 11, 0.15)";
              borderBadge = `1px solid rgba(245, 158, 11, 0.5)`;
              glowShadow = "0 0 22px rgba(245, 158, 11, 0.35)";
            }
          } else if (isPast) {
            textColor = "#F1F5F9";
          } else {
            textColor = "#64748B";
          }
        } else {
          // clean_corporate
          const blueAccent = accentColor || "#38BDF8";
          if (isActive) {
            textColor = blueAccent;
            if (wordGlowBox) {
              bgBadge = "rgba(56, 189, 248, 0.18)";
              borderBadge = "1.5px solid rgba(56, 189, 248, 0.5)";
              glowShadow = "0 0 20px rgba(56, 189, 248, 0.3)";
            }
          } else if (isPast) {
            textColor = "#F8FAFC";
          } else {
            textColor = "#94A3B8";
          }
        }

        // Smart Emoji Auto-attachment
        const emoji = smartEmojisEnabled ? getWordEmoji(item.word) : null;

        return (
          <span
            key={`${item.word}-${globalIdx}`}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              fontSize: `${baseFontSize}px`,
              fontWeight: isActive ? 700 : styleType === "kinetic" ? 700 : 500,
              color: textColor,
              textShadow,
              backgroundColor: bgBadge,
              border: borderBadge,
              borderRadius: styleType === "corporate" ? "10px" : "18px",
              boxShadow: glowShadow,
              padding: isActive && bgBadge !== "transparent" ? "4px 18px" : "0 4px",
              transform: `scale(${wordCustomScale}) translateY(${wordTranslateY}px)`,
              transformOrigin: "center center",
              opacity: wordCustomOpacity,
              transition: "transform 0.08s ease, color 0.1s ease, box-shadow 0.1s ease",
            }}
          >
            <span>{item.word}</span>
            {emoji && (
              <span
                style={{
                  fontSize: `${Math.round(baseFontSize * 0.85)}px`,
                  display: "inline-block",
                  transform: isActive ? "scale(1.15) rotate(-6deg)" : "scale(1.0)",
                  transition: "transform 0.1s ease",
                }}
              >
                {emoji}
              </span>
            )}
          </span>
        );
      })}
    </div>
  );
};

export interface WordTimestamp {
  word: string;
  start: number; // in seconds
  end: number;   // in seconds
}

export interface SceneClip {
  id?: string;
  url: string;
  type?: 'video' | 'image' | 'gradient';
  duration?: number; // in seconds
  startOffset?: number; // in seconds
}

export interface MotionCompositionProps {
  title?: string;
  subtitle?: string;
  speakerName?: string;
  words?: WordTimestamp[];
  audioUrl?: string;
  backgroundUrl?: string;
  backgroundType?: 'color' | 'gradient' | 'image' | 'video';
  backgroundColor?: string;
  accentColor?: string;
  aspectRatio?: '9:16' | '16:9';
  templateId?: 'dark_neon' | 'cinematic_narrative' | 'tiktok_kinetic' | 'clean_corporate';
  durationInSeconds?: number;
  fps?: number;
  videoStartOffset?: number;
  videoMuted?: boolean;
  videoVolume?: number;
  transitionEffect?: 'whip_pan' | 'zoom_in' | 'glitch' | 'dissolve' | 'none';

  // Kinetic Typography Enhancements (A2)
  fontFamily?: 'IBM Plex Sans Arabic' | 'Tajawal' | 'Cairo' | 'Amiri' | string;
  entryAnimation?: 'pop' | 'bounce' | 'wave' | 'fade';
  smartEmojisEnabled?: boolean;
  wordGlowBox?: boolean;

  // Sound FX & Sound Design (A3)
  sfxEnabled?: boolean;
  sfxVolume?: number;

  // Background Music (BGM) & Smart Ducking (A4)
  bgmPreset?: 'cinematic_warm' | 'cyber_ambient' | 'lofi_chill' | 'energetic_hook' | 'none';
  bgmUrl?: string;
  bgmVolume?: number;
  smartDucking?: boolean;

  // Multi-Scene Timeline & B-Roll / Picture-in-Picture (A5 & A8)
  scenes?: SceneClip[];
  pipUrl?: string;
  pipPosition?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  pipScale?: number;
  pipMuted?: boolean;

  // Auto Jump Cuts & Dynamic Zoom (A6)
  dynamicZoom?: boolean;

  // Canvas Drag & Repositioning (A9)
  captionPositionPercent?: number; // 25: Top, 50: Center, 75: Bottom

  // High Frame-rate & GIF Export (A10)
  exportFormat?: 'mp4' | 'gif';
}

export const sampleArabicWords: WordTimestamp[] = [
  { word: "أهلاً", start: 0.1, end: 0.6 },
  { word: "بكم", start: 0.6, end: 1.0 },
  { word: "في", start: 1.0, end: 1.3 },
  { word: "أستوديو", start: 1.3, end: 1.9 },
  { word: "HexMedia", start: 1.9, end: 2.7 },
  { word: "للموشن", start: 2.7, end: 3.3 },
  { word: "جرافيكس", start: 3.3, end: 4.0 },
  { word: "البرمجي", start: 4.0, end: 4.8 },
];

export const defaultMotionProps: MotionCompositionProps = {
  title: "HexMedia Motion Studio",
  subtitle: "Code-to-Video Engine",
  speakerName: "الراوي الذكي",
  words: sampleArabicWords,
  aspectRatio: "9:16",
  templateId: "dark_neon",
  durationInSeconds: 5.0,
  fps: 30,
  fontFamily: "IBM Plex Sans Arabic",
  entryAnimation: "pop",
  smartEmojisEnabled: true,
  wordGlowBox: true,
  sfxEnabled: true,
  sfxVolume: 0.25,
  bgmPreset: "cyber_ambient",
  bgmVolume: 0.25,
  smartDucking: true,
  dynamicZoom: true,
  captionPositionPercent: 50,
  exportFormat: "mp4",
};

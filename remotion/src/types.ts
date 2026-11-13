export interface WordTimestamp {
  word: string;
  start: number; // in seconds
  end: number;   // in seconds
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
};

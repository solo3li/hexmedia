import React from "react";
import { DarkNeon } from "./templates/DarkNeon";
import { CinematicNarrative } from "./templates/CinematicNarrative";
import { TikTokKinetic } from "./templates/TikTokKinetic";
import { CleanCorporate } from "./templates/CleanCorporate";
import { MotionCompositionProps } from "./types";

export const MotionStudioComposition: React.FC<MotionCompositionProps> = (props) => {
  const { templateId = "dark_neon" } = props;

  switch (templateId) {
    case "cinematic_narrative":
      return <CinematicNarrative {...props} />;
    case "tiktok_kinetic":
      return <TikTokKinetic {...props} />;
    case "clean_corporate":
      return <CleanCorporate {...props} />;
    case "dark_neon":
    default:
      return <DarkNeon {...props} />;
  }
};

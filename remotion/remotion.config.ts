import { Config } from "@remotion/cli/config";

Config.setChromiumFlags({
  "no-sandbox": true,
  "disable-setuid-sandbox": true,
  "disable-dev-shm-usage": true,
  "disable-gpu": true,
});
Config.setChromiumOpenGlRenderer("swangle");
Config.setOverwriteOutput(true);
Config.setChromiumDisableWebSecurity(true);

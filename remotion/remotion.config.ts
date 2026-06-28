import { Config } from "@remotion/cli/config";

// ===== 图像与质量配置 =====
Config.setVideoImageFormat("jpeg"); // jpeg 比 png 快 2-3 倍
Config.setJpegQuality(85);
Config.setCrf(18); // H.264 质量因子 (0-51, 越低质量越高)

// ===== 渲染性能配置 =====
Config.setConcurrency(6); // 根据 CPU 核心数调整

// ===== 输出配置 =====
Config.setCodec("h264");
Config.setOverwriteOutput(true);

// ===== 浏览器配置 =====
// Config.setChromiumOpenGlRenderer("angle");
Config.setChromiumDisableWebSecurity(true); // 本地渲染需要

// ===== 日志配置 =====
Config.setLogLevel("info");

// ===== 开发环境优化 =====
if (process.env.NODE_ENV === "development") {
  Config.setConcurrency(4);
  Config.setJpegQuality(70);
}

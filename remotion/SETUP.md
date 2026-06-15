# Remotion 环境配置指南

## 前置条件

1. **Node.js** ≥ 18（已安装，版本 v24.15.0）
2. **Chrome/Chromium**（用于 Remotion 渲染）

## 快速开始

```bash
# 1. 安装依赖（已完成）
cd remotion
npm install

# 2. 测试渲染
npm run render
```

## Chrome 浏览器配置

Remotion 需要 Chrome 或 Chromium 来渲染视频。有三种方式：

### 方式一：自动下载（推荐）

```bash
# Remotion 会在首次渲染时自动下载 Chrome Headless Shell
npx remotion render src/Root.tsx CAPVideo out/test.mp4 --props=./input.json
```

如果下载慢，可以配置环境变量使用镜像：
```bash
# 使用中国镜像（如腾讯云、阿里云等）
REMOTION_BROWSER_EXECUTABLE="C:\Program Files\Google\Chrome\Application\chrome.exe"
```

### 方式二：使用系统已安装的 Chrome

如果已安装 Chrome，Remotion 会自动检测。也可以手动指定：
```bash
npx remotion render src/Root.tsx CAPVideo out/test.mp4 ^
  --props=./input.json ^
  --browser-executable="C:\Program Files\Google\Chrome\Application\chrome.exe"
```

### 方式三：使用 Playwright 的 Chromium

本项目已依赖 Playwright，可以安装其 Chromium 供 Remotion 使用：

```bash
# 安装 Playwright Chromium
python -m playwright install chromium

# 使用 Playwright 的 Chromium 路径
npx remotion render src/Root.tsx CAPVideo out/test.mp4 ^
  --props=./input.json ^
  --browser-executable="C:\Users\$(whoami)\AppData\Local\ms-playwright\chromium-*\chrome-win64\chrome.exe"
```

## 中国用户加速方案

如果下载 Chrome 慢，可以：

1. **手动下载 Chrome for Testing**：
   - 访问 https://googlechromelabs.github.io/chrome-for-testing/
   - 下载对应平台（Win64）的 chrome-headless-shell
   - 解压后指定路径

2. **使用 VPN/代理** 加速 Google Storage 下载

3. **使用系统 Chrome**（需 Chrome ≥ 115）：
   ```bash
   set CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe
   ```

## 验证安装

```bash
# 检查能否列出合成组件
npx remotion compositions src/Root.tsx

# 渲染一帧测试
npx remotion still src/Root.tsx CAPVideo out/test.png --props=./input.json
```

## 常见问题

- **"Failed to launch the browser process"**: Chrome 未安装或路径不对
- **下载超时**: 网络问题，使用 `--browser-executable` 指定已有 Chrome
- **"registerRoot" 错误**: 入口文件必须是调用 `registerRoot()` 的文件

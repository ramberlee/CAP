/**
 * 单场景快速渲染脚本
 * 使用方法: npm run render:scene -- [sceneIndex] [quality]
 * 示例: npm run render:scene -- 0 preview
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const sceneIndex = parseInt(args[0]) || 0;
const quality = args[1] || 'preview';

const qualityPresets = {
  preview: { scale: 0.5, quality: 60, concurrency: 8 },
  normal: { scale: 1, quality: 80, concurrency: 6 },
  high: { scale: 1, quality: 90, concurrency: 4 },
};

const preset = qualityPresets[quality] || qualityPresets.preview;

// 读取并修改 input.json，只保留指定场景
const inputPath = path.join(__dirname, '..', 'input-v3-demo.json');
const outputPath = path.join(__dirname, '..', `out/scene-${sceneIndex}-${quality}.mp4`);

if (!fs.existsSync(inputPath)) {
  console.error('请先创建 input-v3-demo.json');
  process.exit(1);
}

const plan = JSON.parse(fs.readFileSync(inputPath, 'utf-8'));

if (sceneIndex >= plan.scenes.length) {
  console.error(`场景索引 ${sceneIndex} 超出范围 (总共 ${plan.scenes.length} 个场景)`);
  process.exit(1);
}

// 创建单场景计划
const singleScenePlan = {
  ...plan,
  scenes: [plan.scenes[sceneIndex]],
};

const tempPath = path.join(__dirname, '..', '.temp-single-scene.json');
fs.writeFileSync(tempPath, JSON.stringify(singleScenePlan, null, 2));

console.log(`🎬 渲染场景 #${sceneIndex}: ${singleScenePlan.scenes[0].layout || singleScenePlan.scenes[0].type}`);
console.log(`📐 缩放: ${preset.scale}x | 质量: ${preset.quality} | 并发: ${preset.concurrency}`);
console.log();

const command = `npx remotion render src/Root.tsx CAPVideo "${outputPath}" --props="${tempPath}" --scale=${preset.scale} --quality=${preset.quality} --concurrency=${preset.concurrency}`;

try {
  execSync(command, { stdio: 'inherit' });
  console.log();
  console.log(`✅ 渲染完成! 输出: ${outputPath}`);
} catch (e) {
  console.error('❌ 渲染失败');
  process.exit(1);
} finally {
  // 清理临时文件
  if (fs.existsSync(tempPath)) {
    fs.unlinkSync(tempPath);
  }
}

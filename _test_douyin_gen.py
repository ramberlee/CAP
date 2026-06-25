"""Test douyin multi-step generation directly."""
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from modules.config import load_config
from modules.database import Database
from modules.generator import ContentGenerator

config = load_config()
db = Database(config.database.path)

# Add a test topic
topic_id = db.add_topic(
    source="manual",
    title="Claude Code vs Cursor：AI编程工具终极对决",
    category="shu",
)

g = ContentGenerator.from_config(db, config)

# Generate only for douyin
result = g._generate_for_platform(
    topic="Claude Code vs Cursor：AI编程工具终极对决",
    platform="douyin",
    category="shu",
)

if result:
    print("\n" + "="*60)
    print("✅ 抖音内容生成成功!")
    print("="*60)
    print(f"\n📌 标题: {result.get('title', 'N/A')}")
    print(f"📝 描述: {result.get('description', 'N/A')}")
    print(f"🏷️ 标签: {result.get('tags', [])}")
    print(f"\n📄 脚本 ({len(result.get('script',''))}字):")
    print("-"*40)
    print(result.get('script', 'N/A'))
    print("-"*40)
else:
    print("❌ 生成失败")

# Cleanup test topic
with db._connect() as conn:
    conn.execute("DELETE FROM topics WHERE id = ?", (topic_id,))

import os
os.remove("_test_douyin_gen.py")

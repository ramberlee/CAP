"""
Video Planner 缓存与校验增强模块

提供:
1. LLM 响应缓存 - 避免重复请求
2. JSON Schema 校验 - 确保输出格式正确
3. 计划校验增强 - v3 布局完整支持
"""

import hashlib
import json
import logging
import re as _re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)

# ===== JSON Schema 定义 =====

SCENE_SCHEMA = {
    "type": "object",
    "properties": {
        "layout": {"type": "string"},
        "type": {"type": "string"},
        "duration": {"type": "number", "minimum": 0.5, "maximum": 30},
        "animation": {"type": "string"},
        "englishLabel": {"type": "string"},
        "sceneSubtitle": {"type": "string"},
        # v3 布局
        "techMultiPanel": {"type": "object"},
        "connectedCards": {"type": "object"},
        "architectureFlow": {"type": "object"},
        "stackHighlight": {"type": "object"},
        # v2 布局
        "titleCard": {"type": "object"},
        "cardGrid": {"type": "object"},
        "numberedCards": {"type": "object"},
        "splitCompare": {"type": "object"},
        "flowDiagram": {"type": "object"},
        "fanOut": {"type": "object"},
        "docTree": {"type": "object"},
        # 通用字段
        "title": {"type": "string"},
        "subtitle": {"type": "string"},
        "items": {"type": "array"},
    },
}

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "theme": {"type": "string"},
        "scenes": {"type": "array", "items": SCENE_SCHEMA},
        "audioPath": {"type": ["string", "null"]},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["scenes"],
}

# ===== 简单 JSON 校验器 =====


class SimpleSchemaValidator:
    """简单的 JSON Schema 校验器"""

    @staticmethod
    def _validate_type(value: Any, expected_type: str) -> bool:
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        elif expected_type == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        elif expected_type == "null":
            return value is None
        return False

    @classmethod
    def validate(cls, instance: Any, schema: dict) -> tuple[bool, list[str]]:
        """验证 instance 是否符合 schema"""
        errors = []

        # 类型校验
        if "type" in schema:
            types = schema["type"]
            if isinstance(types, list):
                if not any(cls._validate_type(instance, t) for t in types):
                    errors.append(f"类型错误: 期望 {types}, 实际 {type(instance).__name__}")
            else:
                if not cls._validate_type(instance, types):
                    errors.append(f"类型错误: 期望 {types}, 实际 {type(instance).__name__}")
                    return False, errors

        # 对象属性校验
        if isinstance(instance, dict) and "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                if prop_name in instance:
                    is_valid, prop_errors = cls.validate(instance[prop_name], prop_schema)
                    if not is_valid:
                        for err in prop_errors:
                            errors.append(f"属性 {prop_name}: {err}")

        # 必填字段校验
        if "required" in schema and isinstance(instance, dict):
            for field in schema["required"]:
                if field not in instance or instance[field] in (None, "", [], {}):
                    errors.append(f"缺失必填字段: {field}")

        # 范围校验
        if isinstance(instance, (int, float)):
            if "minimum" in schema and instance < schema["minimum"]:
                errors.append(f"值过小: {instance} < {schema['minimum']}")
            if "maximum" in schema and instance > schema["maximum"]:
                errors.append(f"值过大: {instance} > {schema['maximum']}")

        # 数组项校验
        if isinstance(instance, list) and "items" in schema:
            for i, item in enumerate(instance):
                is_valid, item_errors = cls.validate(item, schema["items"])
                if not is_valid:
                    for err in item_errors:
                        errors.append(f"项目 [{i}]: {err}")

        return len(errors) == 0, errors


# ===== 缓存管理器 =====


class PlanCacheManager:
    """视频计划缓存管理器

    根据输入内容的哈希值缓存 LLM 生成结果，
    避免相同内容重复请求 LLM。
    """

    def __init__(self, cache_dir: Optional[Union[str, Path]] = None):
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "cap_video_planner"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.enabled = True

    def _compute_key(
        self,
        script: str,
        title: str = "",
        tags: Optional[list[str]] = None,
        model: str = "",
    ) -> str:
        """计算缓存键"""
        content = f"{script}:{title}:{json.dumps(tags or [], ensure_ascii=False)}:{model}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def get(self, script: str, title: str = "", tags: Optional[list[str]] = None, model: str = "") -> Optional[dict]:
        """从缓存获取计划"""
        if not self.enabled:
            return None

        key = self._compute_key(script, title, tags, model)
        cache_file = self.cache_dir / f"{key}.json"

        try:
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                # 检查过期时间（默认 7 天）
                cached_at = cached.get("_cached_at", 0)
                now = datetime.now().timestamp()
                if now - cached_at < 7 * 24 * 3600:
                    logger.info(f"使用缓存的视频计划 (key={key[:8]}...)")
                    return cached.get("plan")
                else:
                    cache_file.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")

        return None

    def put(
        self,
        plan: dict,
        script: str,
        title: str = "",
        tags: Optional[list[str]] = None,
        model: str = "",
    ) -> None:
        """保存计划到缓存"""
        if not self.enabled:
            return

        key = self._compute_key(script, title, tags, model)
        cache_file = self.cache_dir / f"{key}.json"

        try:
            cache_data = {
                "_cached_at": datetime.now().timestamp(),
                "_script_preview": script[:100],
                "plan": plan,
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"已缓存视频计划 (key={key[:8]}...)")
        except Exception as e:
            logger.warning(f"写入缓存失败: {e}")

    def clear(self, older_than_days: Optional[int] = None) -> int:
        """清理缓存

        Args:
            older_than_days: 只清理超过指定天数的缓存，None 则清理全部
        """
        count = 0
        try:
            now = datetime.now().timestamp()
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    if older_than_days is not None:
                        with open(cache_file, "r", encoding="utf-8") as f:
                            cached = json.load(f)
                        cached_at = cached.get("_cached_at", 0)
                        if now - cached_at < older_than_days * 24 * 3600:
                            continue
                    cache_file.unlink()
                    count += 1
                except Exception:
                    pass
            logger.info(f"已清理 {count} 个缓存文件")
        except Exception as e:
            logger.warning(f"清理缓存失败: {e}")
        return count

    def stats(self) -> dict:
        """获取缓存统计信息"""
        try:
            files = list(self.cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in files)
            return {
                "count": len(files),
                "size_bytes": total_size,
                "size_mb": round(total_size / (1024 * 1024), 2),
                "cache_dir": str(self.cache_dir),
            }
        except Exception as e:
            logger.warning(f"获取缓存统计失败: {e}")
            return {"count": 0, "size_bytes": 0, "size_mb": 0}


# ===== v3 布局增强校验器 =====


class V3PlanValidator:
    """v3 布局增强校验器"""

    VALID_LAYOUTS = {
        # v3
        "tech_multi_panel",
        "connected_cards",
        "architecture_flow",
        "stack_highlight",
        # v2
        "title_card",
        "card_grid",
        "numbered_cards",
        "split_compare",
        "flow_diagram",
        "fan_out",
        "doc_tree",
        "block_tree",
    }

    VALID_THEMES = {
        "dark_tech_v3",
        "dark_glass",
        "dark_tech",
        "light_clean",
        "vibrant",
        "minimal",
        "news",
    }

    LAYOUT_REQUIRED_FIELDS = {
        # v3 layouts
        "tech_multi_panel": ["techMultiPanel.leftPanel.items", "techMultiPanel.centerPanel.body"],
        "connected_cards": ["connectedCards.cards"],
        "architecture_flow": ["architectureFlow.nodes"],
        "stack_highlight": ["stackHighlight.leftItems", "stackHighlight.rightCard.title"],
        # v2 layouts
        "title_card": ["titleCard.title"],
        "card_grid": ["cardGrid.cards"],
        "numbered_cards": ["numberedCards.cards"],
        "split_compare": ["splitCompare.leftItems", "splitCompare.rightHeader"],
        "flow_diagram": ["flowDiagram.llmLabel"],
        "fan_out": ["fanOut.leftItems", "fanOut.rightCardTitle"],
        "doc_tree": ["docTree.toc"],
        "block_tree": ["blocks"],
    }

    @classmethod
    def validate_plan(cls, plan: dict) -> tuple[bool, list[str]]:
        """校验完整视频计划"""
        errors = []

        # 基础结构校验
        if not isinstance(plan, dict):
            return False, ["计划必须是字典类型"]

        if "scenes" not in plan or not isinstance(plan["scenes"], list):
            return False, ["缺少 scenes 数组"]

        # 主题校验
        theme = plan.get("theme", "")
        if theme and theme not in cls.VALID_THEMES:
            errors.append(f"未知主题: {theme}，将使用默认值")

        # 场景数量校验
        scenes = plan["scenes"]
        if len(scenes) < 2:
            errors.append(f"场景数量过少 ({len(scenes)} 个)，建议至少 2 个场景")

        # 逐个场景校验
        layout_counts = {}
        for i, scene in enumerate(scenes):
            scene_valid, scene_errors = cls.validate_scene(scene, index=i)
            if not scene_valid:
                errors.extend([f"场景 [{i}]: {e}" for e in scene_errors])

            # 统计布局类型
            layout = scene.get("layout") or scene.get("type") or "unknown"
            layout_counts[layout] = layout_counts.get(layout, 0) + 1

        # v3 布局使用统计
        v3_count = sum(count for layout, count in layout_counts.items() if layout in cls.VALID_LAYOUTS)
        if v3_count == 0 and len(scenes) > 0:
            errors.append("警告: 未使用任何 v3 科技风布局，建议优先使用 v3 布局以获得更佳视觉效果")

        # 校验布局多样性
        if len(scenes) > 4:
            for layout, count in layout_counts.items():
                max_allowed = max(2, int(len(scenes) * 0.4))
                if count > max_allowed and layout not in ("title_card", "ending"):
                    errors.append(f"布局 '{layout}' 使用过于频繁 ({count}/{len(scenes)})，建议增加布局多样性")

        return len(errors) == 0 or all("警告" in e for e in errors), errors

    @classmethod
    def validate_scene(cls, scene: dict, index: int = -1) -> tuple[bool, list[str]]:
        """校验单个场景"""
        errors = []

        if not isinstance(scene, dict):
            return False, ["场景必须是字典类型"]

        # 校验布局类型
        layout = scene.get("layout")
        scene_type = scene.get("type")

        if layout and layout not in cls.VALID_LAYOUTS:
            errors.append(f"未知布局类型: {layout}")

        # 校验必填字段
        if layout in cls.LAYOUT_REQUIRED_FIELDS:
            for field_path in cls.LAYOUT_REQUIRED_FIELDS[layout]:
                obj = scene
                parts = field_path.split(".")
                valid = True
                for part in parts:
                    if not isinstance(obj, dict) or part not in obj or obj[part] in (None, "", [], {}):
                        valid = False
                        break
                    obj = obj[part]
                if not valid:
                    errors.append(f"缺少必填字段: {field_path}")

        # 校验时长
        duration = scene.get("duration")
        if duration is None or not isinstance(duration, (int, float)) or duration <= 0:
            errors.append(f"无效的时长: {duration}，将使用默认值 3.0")
        elif duration > 15:
            errors.append(f"时长过长: {duration}s，建议单场景不超过 15s")

        # 校验字幕长度
        subtitle = scene.get("sceneSubtitle", "")
        if isinstance(subtitle, str) and len(subtitle) > 30:
            errors.append(f"底部字幕过长 ({len(subtitle)} 字符)，建议控制在 30 字符以内")

        return len(errors) == 0 or all("建议" in e or "将使用" in e for e in errors), errors

    @staticmethod
    def fix_plan(plan: dict) -> dict:
        """自动修复计划中的常见问题"""
        plan = json.loads(json.dumps(plan))  # 深拷贝

        # 确保有 title
        if "title" not in plan or not plan.get("title"):
            plan["title"] = "AI 资讯"
        plan["title"] = _re.sub(r"\[VIDEO:.*?]", "", plan["title"]).strip() or "AI 资讯"

        # 确保有主题
        if "theme" not in plan or plan.get("theme") not in V3PlanValidator.VALID_THEMES:
            plan["theme"] = "dark_tech_v3"

        # 确保有场景
        if "scenes" not in plan or not plan["scenes"]:
            plan["scenes"] = [
                {"layout": "title_card", "titleCard": {"title": plan["title"]}, "duration": 3, "animation": "scaleIn"},
                {"layout": "title_card", "titleCard": {"title": "感谢观看"}, "duration": 2, "animation": "fade"},
            ]

        # 修复每个场景
        for i, scene in enumerate(plan["scenes"]):
            V3PlanValidator._fix_scene(scene, i, plan.get("title", ""))

        return plan

    @staticmethod
    def _fix_scene(scene: dict, index: int, plan_title: str) -> None:
        """修复单个场景"""
        # 确保有布局或类型
        layout = scene.get("layout")
        if not layout and not scene.get("type"):
            scene["layout"] = "title_card"

        # 确保有时长
        if "duration" not in scene or not isinstance(scene["duration"], (int, float)) or scene["duration"] <= 0:
            scene["duration"] = 3.0

        # 确保有动画
        if "animation" not in scene or not scene["animation"]:
            scene["animation"] = "fade"

        # 第一个场景强制为封面
        if index == 0:
            if scene.get("layout") not in ("title_card", "title", "tech_multi_panel") and scene.get("type") != "title":
                V3PlanValidator._coerce_to_title_card(scene, plan_title)

        # 清理括号内容
        V3PlanValidator._scrub_brackets_in_place(scene)

    @staticmethod
    def _coerce_to_title_card(scene: dict, title_hint: str) -> None:
        """强制转换为 title_card 场景"""
        title = (
            scene.get("title")
            or (scene.get("titleCard") or {}).get("title")
            or (scene.get("cardGrid") or {}).get("title")
            or title_hint
            or "亮点"
        )
        scene.clear()
        scene.update({
            "layout": "title_card",
            "englishLabel": scene.get("englishLabel", "TITLE"),
            "sceneSubtitle": scene.get("sceneSubtitle", ""),
            "duration": scene.get("duration", 3.0),
            "animation": "scaleIn",
            "titleCard": {"title": title, "sceneSubtitle": scene.get("sceneSubtitle")},
        })

    @staticmethod
    def _scrub_brackets_in_place(obj: dict) -> None:
        """递归移除字符串中的 [VIDEO:...] 标记"""
        for k, v in list(obj.items()):
            if isinstance(v, str):
                obj[k] = _re.sub(r"\[VIDEO:.*?]", "", v).strip()
            elif isinstance(v, list):
                obj[k] = [
                    _re.sub(r"\[VIDEO:.*?]", "", t).strip() if isinstance(t, str) else t
                    for t in v
                ]
            elif isinstance(v, dict):
                V3PlanValidator._scrub_brackets_in_place(v)


# 向后兼容别名
PlanValidator = V3PlanValidator


# ===== 便捷函数 =====

_default_cache_manager: Optional[PlanCacheManager] = None


def get_cache_manager() -> PlanCacheManager:
    """获取默认缓存管理器实例"""
    global _default_cache_manager
    if _default_cache_manager is None:
        _default_cache_manager = PlanCacheManager()
    return _default_cache_manager


def validate_plan(plan: dict) -> tuple[bool, list[str]]:
    """校验视频计划"""
    return V3PlanValidator.validate_plan(plan)


def fix_plan(plan: dict) -> dict:
    """修复视频计划中的常见问题"""
    return V3PlanValidator.fix_plan(plan)

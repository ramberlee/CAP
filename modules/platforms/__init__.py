"""Platform modules registry."""

from modules.platforms import wechat, douyin, xiaohongshu

_MODULES = {
    "wechat": wechat,
    "douyin": douyin,
    "xiaohongshu": xiaohongshu,
}


def get_validator(platform: str):
    """Return the validate_content function for a platform, or None."""
    mod = _MODULES.get(platform)
    return getattr(mod, "validate_content", None)


def get_repairer(platform: str):
    """Return the repair_content function for a platform, or None."""
    mod = _MODULES.get(platform)
    return getattr(mod, "repair_content", None)


def get_processor(platform: str):
    """Return the process_content function for a platform, or None."""
    mod = _MODULES.get(platform)
    return getattr(mod, "process_content", None)

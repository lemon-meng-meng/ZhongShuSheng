"""中书省国际化模块。"""
from __future__ import annotations

import gettext as gettext_module
import locale
import os
from typing import Optional

LOCALE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "locale")
LOCALE_DIR = os.path.normpath(LOCALE_DIR)

_current_lang: Optional[str] = None
_current_font_weight: str = "normal"  # "normal" or "bold"
_translation = gettext_module.translation("zhongshu", LOCALE_DIR, languages=[locale.getdefaultlocale()[0] or "en"], fallback=True)


def _get_translation() -> gettext_module.GNUTranslations:
    """获取当前翻译对象（内部使用）。"""
    global _translation
    return _translation


def gettext(text: str) -> str:
    """动态获取翻译：始终使用当前语言的翻译对象。"""
    return _get_translation().gettext(text)


# 别名，兼容 _() 用法
_ = gettext


def set_language(lang: str) -> None:
    """切换运行时语言。"""
    global _translation, _current_lang
    if lang == "en":
        _translation = gettext_module.translation("zhongshu", LOCALE_DIR, languages=["en"])
    elif lang == "zh_CN":
        _translation = gettext_module.translation("zhongshu", LOCALE_DIR, languages=["zh_CN"], fallback=True)
    else:
        _translation = gettext_module.translation("zhongshu", LOCALE_DIR, languages=[locale.getdefaultlocale()[0] or "en"], fallback=True)
    _translation.install()
    _current_lang = lang


def get_current_language() -> str:
    """获取当前语言代码。"""
    return _current_lang or locale.getdefaultlocale()[0] or "en"


def get_available_languages() -> list:
    """获取可用语言列表。"""
    return [
        ("zh_CN", "中文"),
        ("en", "English"),
    ]


# 字体粗细相关
def set_font_weight(weight: str) -> None:
    """设置字体粗细：'normal' 或 'bold'。"""
    global _current_font_weight
    if weight in ("normal", "bold"):
        _current_font_weight = weight


def get_font_weight() -> str:
    """获取当前字体粗细。"""
    return _current_font_weight


def get_available_font_weights() -> list:
    """获取可用字体粗细列表。"""
    return [
        ("normal", "常规"),
        ("bold", "加粗"),
    ]


def apply_font_weight_css() -> str:
    """生成应用字体粗细的 CSS。"""
    if _current_font_weight == "bold":
        return """
* {
    font-weight: 700 !important;
}
"""
    else:
        return """
* {
    font-weight: 400 !important;
}
"""
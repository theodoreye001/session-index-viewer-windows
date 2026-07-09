"""Text cleaning helpers shared by all parsers."""

import re

from .config import CLIP_LEN, SKIP_USER_PREFIXES


def clean_inline(text):
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"  +", " ", text)
    return text.strip()


def clean_multiline(text):
    text = text.replace("\r", "")
    text = re.sub(r"\t+", " ", text)
    text = re.sub(r" +\n", "\n", text)
    text = re.sub(r"\n +", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip("\n")


def clip(text, limit=CLIP_LEN):
    return text[:limit] + "..." if len(text) > limit else text


def usable_user_text(text):
    text = text.strip()
    return bool(text) and not text.startswith(SKIP_USER_PREFIXES)


def blocks_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""

"""Счётчик имён вложений в формате SIR_PERFORMER_NN.jpg."""
import re
from collections.abc import Iterable

ATTACHMENT_PATTERN = re.compile(r"attachment:([^\s]+)", re.IGNORECASE)


def attachment_counter_key(sir: str, performer: str) -> tuple[str, str]:
    return sir.strip().casefold(), performer.strip().casefold()


def iter_attachment_values(text_blocks: Iterable[str]):
    for block in text_blocks:
        for line in block.splitlines():
            for match in ATTACHMENT_PATTERN.finditer(line):
                yield match.group(1).strip()


def find_max_attachment_index(sir: str, performer: str, text_blocks: Iterable[str]) -> int:
    if not sir or not performer:
        return 0
    pattern = re.compile(rf"^{re.escape(sir)}_{re.escape(performer)}_(\d+)\.jpg$", re.IGNORECASE)
    max_index = 0
    for value in iter_attachment_values(text_blocks):
        match = pattern.fullmatch(value)
        if match:
            max_index = max(max_index, int(match.group(1)))
    return max_index


def format_attachment_name(sir: str, performer: str, index: int) -> str:
    if not sir:
        return "attachment:"
    if not performer:
        return f"attachment:{sir}"
    return f"attachment:{sir}_{performer}_{index:02d}.jpg"

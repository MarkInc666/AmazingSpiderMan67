from dataclasses import dataclass
from typing import Optional


@dataclass
class Shot:
    name: str
    x: int
    y: int
    event: str
    group: str = ""
    is_lit: bool = False
    is_clue: bool = False
    is_jackpot: bool = False
    disabled: bool = False
    hint: Optional[str] = None
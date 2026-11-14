from types import SimpleNamespace

from src.parser import _extract_page_text


class FakePage:
    rect = SimpleNamespace(width=1000)

    def __init__(self, blocks):
        self.blocks = blocks

    def get_text(self, mode, sort=False):
        if mode == "blocks":
            return self.blocks
        if mode == "text":
            return "fallback reading order"


def block(x0, y0, x1, y1, text):
    return (x0, y0, x1, y1, text, 0, 0)


def test_two_column_extraction_does_not_duplicate_center_gutter_blocks():
    page = FakePage([
        block(50, 100, 200, 120, "left one"),
        block(50, 200, 200, 220, "left two"),
        block(490, 150, 510, 170, "center gutter"),
        block(550, 100, 700, 120, "right one"),
        block(550, 200, 700, 220, "right two"),
    ])

    extracted = _extract_page_text(page)

    assert extracted.splitlines().count("center gutter") == 1
    assert extracted.splitlines().count("left one") == 1
    assert extracted.splitlines().count("left two") == 1
    assert extracted.splitlines().count("right one") == 1
    assert extracted.splitlines().count("right two") == 1
    assert extracted.index("left one") < extracted.index("left two")
    assert extracted.index("right one") < extracted.index("right two")

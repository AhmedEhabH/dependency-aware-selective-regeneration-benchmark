from __future__ import annotations

import pytest

from benchmark.execution.exact_patch import (
    ExactPatchBlock,
    ExactPatchError,
    apply_exact_patches,
    parse_exact_patch,
)


class TestParseExactPatch:
    def test_single_block_round_trip(self) -> None:
        text = "<<<<<<< SEARCH\nold line\n=======\nnew line\n>>>>>>> REPLACE\n"
        blocks = parse_exact_patch(text)
        assert blocks == [ExactPatchBlock(search="old line\n", replace="new line\n")]

    def test_multiple_blocks_preserve_order(self) -> None:
        text = (
            "<<<<<<< SEARCH\nfirst\n=======\nfirst_new\n>>>>>>> REPLACE\n"
            "<<<<<<< SEARCH\nsecond\n=======\nsecond_new\n>>>>>>> REPLACE\n"
        )
        blocks = parse_exact_patch(text)
        assert blocks == [
            ExactPatchBlock(search="first\n", replace="first_new\n"),
            ExactPatchBlock(search="second\n", replace="second_new\n"),
        ]

    def test_search_without_trailing_newline(self) -> None:
        text = "<<<<<<< SEARCH\nabc\n=======\ndef\n>>>>>>> REPLACE\n"
        blocks = parse_exact_patch(text)
        assert blocks == [ExactPatchBlock(search="abc\n", replace="def\n")]

    def test_empty_payload_rejected(self) -> None:
        with pytest.raises(ExactPatchError):
            parse_exact_patch("   \n  ")

    def test_garbage_before_first_marker_rejected(self) -> None:
        with pytest.raises(ExactPatchError):
            parse_exact_patch("prose\n<<<<<<< SEARCH\nx\n=======\ny\n>>>>>>> REPLACE\n")

    def test_unterminated_search_rejected(self) -> None:
        with pytest.raises(ExactPatchError):
            parse_exact_patch("<<<<<<< SEARCH\nabc\n")

    def test_unterminated_replace_rejected(self) -> None:
        with pytest.raises(ExactPatchError):
            parse_exact_patch("<<<<<<< SEARCH\nabc\n=======\ndef\n")

    def test_empty_search_block_rejected(self) -> None:
        with pytest.raises(ExactPatchError):
            parse_exact_patch("<<<<<<< SEARCH\n=======\ndef\n>>>>>>> REPLACE\n")

    def test_missing_divider_rejected(self) -> None:
        with pytest.raises(ExactPatchError):
            parse_exact_patch("<<<<<<< SEARCH\nabc\n>>>>>>> REPLACE\n")

    def test_nested_marker_rejected(self) -> None:
        with pytest.raises(ExactPatchError):
            parse_exact_patch(
                "<<<<<<< SEARCH\n<<<<<<< SEARCH\nx\n=======\n=======\ny\n>>>>>>> REPLACE\n>>>>>>> REPLACE\n"
            )


class TestApplyExactPatches:
    def test_applies_single_replace(self) -> None:
        result = apply_exact_patches(
            "line1\nline2\nline3\n",
            [ExactPatchBlock(search="line2\n", replace="MIDDLE\n")],
        )
        assert result == "line1\nMIDDLE\nline3\n"

    def test_applies_multiple_blocks_in_order(self) -> None:
        result = apply_exact_patches(
            "a\nb\nc\n",
            [
                ExactPatchBlock(search="a\n", replace="A\n"),
                ExactPatchBlock(search="c\n", replace="C\n"),
            ],
        )
        assert result == "A\nb\nC\n"

    def test_multiple_applications_overlapping_matches_fail_closed(self) -> None:
        with pytest.raises(ExactPatchError, match="ambiguous"):
            apply_exact_patches("x = 1\nx = 1\n", [ExactPatchBlock(search="x = 1\n", replace="y\n")])

    def test_search_not_found_fails_closed(self) -> None:
        with pytest.raises(ExactPatchError, match="not found"):
            apply_exact_patches(
                "hello\n", [ExactPatchBlock(search="missing\n", replace="x\n")]
            )

    def test_no_fuzzy_whitespace_matching(self) -> None:
        with pytest.raises(ExactPatchError, match="not found"):
            apply_exact_patches(
                "def f():\n    return 1\n",
                [ExactPatchBlock(search="def f():\n    return 2\n", replace="x\n")],
            )


class TestExactPatchBoundaryRecovery:
    """FAST-RESULTS-01: bounded delimiter-boundary newline recovery (D048).

    One extra trailing newline in SEARCH (emitted right before the divider) is
    recovered ONLY when removing exactly one newline yields a unique literal
    match. No other whitespace/fuzzy normalization exists.
    """

    def test_extra_boundary_newline_recovered_when_unique(self) -> None:
        content = "rename_me = 0\n\ndef increment():\n    return rename_me + 1\n"
        patch = ExactPatchBlock(
            search="rename_me = 0\n\n",
            replace="counter_new = 0\n\n",
        )
        result = apply_exact_patches(content, [patch])
        assert result == (
            "counter_new = 0\n\ndef increment():\n    return rename_me + 1\n"
        )

    def test_ambiguous_trimmed_candidate_fails_closed(self) -> None:
        content = "x = 1\nx = 1\n"
        patch = ExactPatchBlock(
            search="x = 1\n\n",
            replace="y\n\n",
        )
        with pytest.raises(ExactPatchError, match="not found"):
            apply_exact_patches(content, [patch])
        assert content.count("x = 1\n") != 1

    def test_non_boundary_whitespace_difference_still_rejected(self) -> None:
        with pytest.raises(ExactPatchError, match="not found"):
            apply_exact_patches(
                "def f():\n    return 1\n",
                [ExactPatchBlock(search="def f():\n    return  1\n", replace="x\n")],
            )


class TestExactPatchProductionScale:
    """D13r1 F4/F1: production-shape large-file patch.

    The real pilot-canary's ``djangocms-cross-007`` failure was caused by
    complete-file regeneration of a ~56 000-char djangoCMS source file: the
    O(file) rewrite consumed ~1154 s for only 1839 completion tokens and was
    deadline-censored. Exact-patch mode must edit such files with a SHORT
    SEARCH/REPLACE patch at every scale — the model emits a tiny patch, not the
    whole file. These tests exercise ~60k and ~85k char files with short,
    exactly-once-matching patches (production shape, no fuzzy/partial matching).
    """

    def _big_content(self, target_bytes: int) -> str:
        lines: list[str] = []
        total = 0
        index = 0
        while total < target_bytes:
            line = (
                f"    def method_{index:05d}(self):\n"
                "        return self.template.render({})\n"
            )
            lines.append(line)
            total += len(line)
            index += 1
        return "".join(lines)

    def test_short_patch_applies_to_60k_file(self) -> None:
        content = self._big_content(60_000)
        assert len(content.encode("utf-8")) >= 60_000
        patch = ExactPatchBlock(
            search="    def method_00000(self):\n",
            replace="    def method_00000(self, ctx=None):\n",
        )
        result = apply_exact_patches(content, [patch])
        assert len(result) == len(content) + (
            len("    def method_00000(self, ctx=None):\n")
            - len("    def method_00000(self):\n")
        )
        assert result.count("def method_00000(self, ctx=None):") == 1
        # The rest of the file is byte-identical (short, surgical patch).
        assert "        return self.template.render({})\n" in result

    def test_short_patch_applies_to_85k_file(self) -> None:
        content = self._big_content(85_000)
        assert len(content.encode("utf-8")) >= 85_000
        patch = ExactPatchBlock(
            search="    def method_00420(self):\n",
            replace="    def method_00420(self, ctx=None):\n",
        )
        result = apply_exact_patches(content, [patch])
        assert result.count("def method_00420(self, ctx=None):") == 1
        assert result != content

    def test_multi_block_short_patch_on_85k_file(self) -> None:
        content = self._big_content(85_000)
        blocks = [
            ExactPatchBlock(
                search="    def method_00001(self):\n",
                replace="    def method_00001(self, ctx=None):\n",
            ),
            ExactPatchBlock(
                search="    def method_00002(self):\n",
                replace="    def method_00002(self, ctx=None):\n",
            ),
        ]
        result = apply_exact_patches(content, blocks)
        assert result.count("def method_00001(self, ctx=None):") == 1
        assert result.count("def method_00002(self, ctx=None):") == 1
        assert len(result) == len(content) + 2 * (
            len("(self, ctx=None)") - len("(self)")
        )

    def test_failed_search_on_85k_file_fails_closed_fast(self) -> None:
        content = self._big_content(85_000)
        with pytest.raises(ExactPatchError, match="not found"):
            apply_exact_patches(
                content,
                [ExactPatchBlock(search="    def absent(self):\n", replace="x\n")],
            )
        assert content.count("def absent(self):") == 0

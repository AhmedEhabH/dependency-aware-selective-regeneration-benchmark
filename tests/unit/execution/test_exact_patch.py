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

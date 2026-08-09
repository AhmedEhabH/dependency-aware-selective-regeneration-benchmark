from benchmark.llm.output_normalization import normalize_single_payload, parse_single_json_object


class TestNormalizeSinglePayload:
    def test_raw_payload(self) -> None:
        body, reason = normalize_single_payload("print('hello')")
        assert body == "print('hello')"
        assert reason == "raw"

    def test_raw_payload_preserves_leading_and_trailing_whitespace(self) -> None:
        text = "  \nprint('hello')\n  "
        body, reason = normalize_single_payload(text)
        assert body == text
        assert reason == "raw"

    def test_raw_payload_preserves_final_newline(self) -> None:
        text = "first line\nsecond line\n"
        body, reason = normalize_single_payload(text)
        assert body == text
        assert reason == "raw"

    def test_raw_baseline_source_remains_byte_identical(self) -> None:
        text = "from django.db import models\n\n\nclass Task(models.Model):\n    pass\n"
        body, reason = normalize_single_payload(text)
        assert body == text
        assert body.encode("utf-8") == text.encode("utf-8")
        assert reason == "raw"

    def test_fenced_python_payload(self) -> None:
        body, reason = normalize_single_payload("```python\nprint('hello')\n```")
        assert body == "print('hello')"
        assert reason == "single_fence_stripped"

    def test_fenced_py_and_json_tokens(self) -> None:
        body, reason = normalize_single_payload("```py\nx = 1\n```")
        assert body == "x = 1"
        assert reason == "single_fence_stripped"
        body, reason = normalize_single_payload("```json\n{\"a\": 1}\n```")
        assert body == "{\"a\": 1}"
        assert reason == "single_fence_stripped"

    def test_fenced_crlf_normalized(self) -> None:
        body, reason = normalize_single_payload("```python\r\nprint('hello')\r\n```\r\n")
        assert body == "print('hello')"
        assert reason == "single_fence_stripped"

    def test_unsupported_language_token_breaks_fence(self) -> None:
        body, reason = normalize_single_payload("```sql\nSELECT 1\n```")
        assert body is None
        assert reason == "unbalanced_fence"

    def test_mixed_prose_before_fence(self) -> None:
        body, reason = normalize_single_payload("here is the code:\n```\nx = 1\n```")
        assert body is None
        assert reason == "mixed_prose"

    def test_mixed_prose_after_fence(self) -> None:
        body, reason = normalize_single_payload("```\nx = 1\n```\ndone")
        assert body is None
        assert reason == "mixed_prose"

    def test_multiple_fences(self) -> None:
        body, reason = normalize_single_payload("```\na\n```\n```\nb\n```")
        assert body is None
        assert reason == "multiple_fences"

    def test_unbalanced_fence(self) -> None:
        body, reason = normalize_single_payload("```\ncontent without closing")
        assert body is None
        assert reason == "unbalanced_fence"

    def test_inline_fenced_payload_is_rejected(self) -> None:
        body, reason = normalize_single_payload("```bad output```")
        assert body is None
        assert reason == "unbalanced_fence"

    def test_backticks_inside_ordinary_source_do_not_form_a_fence_only_when_below_three(self) -> None:
        text = "x = '``tick``'"
        body, reason = normalize_single_payload(text)
        assert body == text
        assert reason == "raw"

    def test_outer_fence_lengths_must_match(self) -> None:
        body, reason = normalize_single_payload("```python\nx = 1\n````")
        assert body is None
        assert reason == "unbalanced_fence"

    def test_empty_payload(self) -> None:
        body, reason = normalize_single_payload("   \n  ")
        assert body is None
        assert reason == "empty"

    def test_empty_block(self) -> None:
        body, reason = normalize_single_payload("```\n\n```")
        assert body is None
        assert reason == "empty"

    def test_multiline_body_preserved(self) -> None:
        body, reason = normalize_single_payload("```python\nimport os\n\nx = os.getcwd()\n```")
        assert body == "import os\n\nx = os.getcwd()"
        assert reason == "single_fence_stripped"


class TestParseSingleJsonObject:
    def test_bare_json_object(self) -> None:
        data, reason = parse_single_json_object('{"action": "final", "selected_paths": ["a.py"]}')
        assert data == {"action": "final", "selected_paths": ["a.py"]}
        assert reason == "raw"

    def test_fenced_json_object(self) -> None:
        data, reason = parse_single_json_object(
            '```json\n{"action": "final", "selected_paths": ["a.py"]}\n```'
        )
        assert data == {"action": "final", "selected_paths": ["a.py"]}
        assert reason == "single_fence_stripped"

    def test_json_array_rejected(self) -> None:
        data, reason = parse_single_json_object("[1, 2, 3]")
        assert data is None
        assert reason == "not_object"

    def test_invalid_json_rejected(self) -> None:
        data, reason = parse_single_json_object("{not valid")
        assert data is None
        assert reason == "invalid_json"

    def test_mixed_prose_rejected(self) -> None:
        data, reason = parse_single_json_object("the answer is\n{\"action\": \"final\"}")
        assert data is None
        assert reason == "invalid_json"

    def test_empty_rejected(self) -> None:
        data, reason = parse_single_json_object("")
        assert data is None
        assert reason == "empty"

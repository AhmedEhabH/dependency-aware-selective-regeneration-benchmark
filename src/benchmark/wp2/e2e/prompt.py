"""WP-2 Mission-11 E2E Smoke - prompt builder + leakage guard (B6).

Appendix P1 (generator prompt) and P2 (repair prompt) are built verbatim.
``leakage_scan`` checks the editable-files section against protected strings
(F2P/P2P ids, changed test paths, target-only added lines); the description
section is reported as INFO hits only.
"""
from __future__ import annotations

import hashlib

SYSTEM_PROMPT = """You are a senior Python/Django engineer working on the Saleor e-commerce repository at a historical commit.
You receive a developer change description and the complete current contents of the files you are allowed to edit.
Implement the described change by editing ONLY those files.

Output ONLY edit blocks in this exact format and nothing else:

FILE: <path exactly as given>
<<<<<<< SEARCH
<exact lines copied from the current file>
=======
<replacement lines>
>>>>>>> REPLACE

Rules:
1. Put a FILE line before every block. Several blocks may target the same file; they are applied in order.
2. The SEARCH text must match exactly one contiguous region of the current file, character for character, including indentation and blank lines. Include enough lines to make it unique.
3. To add code, SEARCH for an existing anchor line and REPLACE it with the anchor line plus the new lines.
4. Do not edit any file that is not listed. Do not create files. Do not delete files. Do not edit tests.
5. Keep the code valid for the stated Python version.
6. No explanations. No markdown code fences."""

# I04 (Interface v2): rule 6 replaced with the formatting-only instruction.
SYSTEM_PROMPT_V2 = SYSTEM_PROMPT.replace(
    "6. No explanations. No markdown code fences.",
    "6. Begin your output directly with the first FILE line. No explanations. No markdown code fences.",
)

REPAIR_TEMPLATE = """Your previous output could not be applied. Problems:
{problems}

Return the COMPLETE corrected set of edit blocks for the whole change (not only the fixes), in the same format. Output only edit blocks."""

# I05 (Interface v2): one extra line appended when SEARCH_ELLIPSIS or SEARCH_ERROR occurred.
REPAIR_HINT_ELLIPSIS = ('Copy SEARCH lines exactly from the file shown above; '
                        'never abbreviate with "...".')


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_user_prompt(rendered_description: str, python_requirement: str,
                      editable: list[str], parent_texts: dict[str, str],
                      excluded: dict[str, list[str]]) -> str:
    parts = ["DEVELOPER CHANGE DESCRIPTION", rendered_description,
             "", "PYTHON VERSION REQUIREMENT", python_requirement,
             "", f"EDITABLE FILES ({len(editable)})"]
    for path in editable:
        text = parent_texts.get(path, "")
        n_lines = text.count("\n") + 1
        parts.append(f"===== FILE: {path} ({n_lines} lines) =====")
        parts.append(text)
        parts.append(f"===== END FILE: {path} =====")
    ex = []
    ex += excluded.get("LARGE_FILE_EXCLUDED", [])
    ex += excluded.get("CONTEXT_BUDGET_EXCLUDED", [])
    if ex:
        parts.append("")
        parts.append("NOT EDITABLE IN THIS TASK (too large or over the context budget): "
                     + ", ".join(ex))
    return "\n".join(parts)


def build_prompt(task_input, editable: list[str], parent_texts: dict[str, str],
                 excluded: dict[str, list[str]]) -> tuple[str, str, str]:
    user = build_user_prompt(task_input.developer_change_description_rendered,
                             task_input.python_requirement, editable,
                             parent_texts, excluded)
    return SYSTEM_PROMPT, user, _sha(user)


def build_repair_prompt(_previous_output: str, errors: list[str]) -> str:
    problems = "\n".join(f"- {e}" for e in errors)
    return REPAIR_TEMPLATE.format(problems=problems)


def build_repair_user_message(errors: list[str], hint_ellipsis: bool = False) -> str:
    """Repair instruction (user role). I05: append the ellipsis hint when the
    previous output triggered SEARCH_ELLIPSIS or SEARCH_ERROR."""
    msg = REPAIR_TEMPLATE.format(problems="\n".join(f"- {e}" for e in errors))
    if hint_ellipsis:
        msg += "\n" + REPAIR_HINT_ELLIPSIS
    return msg


def build_repair_messages(system_prompt: str, original_user: str,
                          previous_output: str, errors: list[str],
                          hint_ellipsis: bool = False) -> list[dict[str, str]]:
    """Exact four-message repair request (Mission-11 Appendix P2 / Mission-12 D2):

    1. system
    2. original user
    3. previous assistant output
    4. repair instruction
    """
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": original_user},
        {"role": "assistant", "content": previous_output},
        {"role": "user", "content": build_repair_user_message(errors, hint_ellipsis)},
    ]


def split_sections(user_prompt: str) -> tuple[str, str]:
    """Return (description_section, editable_files_section)."""
    idx = user_prompt.find("===== FILE:")
    if idx == -1:
        return user_prompt, ""
    return user_prompt[:idx], user_prompt[idx:]


def leakage_scan(user_prompt: str, protected: dict[str, list[str]]) -> dict:
    """Scan the editable-files section for protected strings.

    protected = {"f2p_ids": [...], "p2ps_ids": [...], "p2pu_ids": [...],
                 "changed_test_paths": [...], "target_added_lines": [...]}
    Returns {"blocking": [hit...], "info": [hit...]}.
    """
    desc, files_sec = split_sections(user_prompt)
    hits: list[str] = []
    for key in ("f2p_ids", "p2ps_ids", "p2pu_ids", "changed_test_paths", "target_added_lines"):
        for token in protected.get(key, []):
            if token and token in files_sec:
                hits.append(f"{key}:{token[:80]}")
    # description section = INFO hits
    info: list[str] = []
    for key in ("f2p_ids", "p2ps_ids", "p2pu_ids", "changed_test_paths"):
        for token in protected.get(key, []):
            if token and token in desc:
                info.append(f"{key}:{token[:80]}")
    return {"blocking": hits, "info": info}

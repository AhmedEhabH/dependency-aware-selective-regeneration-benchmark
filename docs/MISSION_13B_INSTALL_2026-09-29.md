# MISSION 13B — INSTALL ONLY (OpenCode)

ROLE: installer operator. BUILD ONLY. Do not design, repair, interpret, or improvise.

## Rules
- R1. Run only the commands below, in order, exactly as written.
- R2. Make zero OpenRouter/model/API calls and run zero Docker/WSL commands. Do not run `scripts/wp2_ctl_v223.py run`.
- R3. Do not create, edit, move, or delete any file yourself. The installer writes everything.
- R4. If any output differs from its EXPECT, stop at once. Print the STOP block and do nothing else.
- R5. Write in English only. Never print or persist the API key.

## Input
The human has placed `WP2_M13B_INSTALL_2026-09-29.py` in the repository root.

## Steps
**S1** Verify the installer hash:

    python -c "import hashlib;print(hashlib.sha256(open('WP2_M13B_INSTALL_2026-09-29.py','rb').read()).hexdigest())"

EXPECT: the value given in the human's message. Otherwise, TOKEN=INSTALLER_HASH_MISMATCH.

**S2** Run the installer:

    python WP2_M13B_INSTALL_2026-09-29.py

EXPECT: the block starts with `M13B_KIT_INSTALL_COMPLETE`. If it prints `M13B_INSTALL_STOP`, then TOKEN=M13B_INSTALL_STOP. The installer has already rolled itself back.

**S3** Print the installer's final block exactly as it appeared, then STOP. The human runs the controller.

## STOP block

    ================================================================
    MISSION_13B_STOPPED
    STEP=<S#>
    TOKEN=<token>
    OUTPUT=<the complete installer output, verbatim>
    CHANGES_MADE_BY_OPENCODE=none
    ================================================================

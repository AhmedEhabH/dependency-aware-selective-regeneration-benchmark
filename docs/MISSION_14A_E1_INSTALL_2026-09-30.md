# MISSION 14A-E1: INSTALL ONLY (OpenCode)

ROLE: installer operator. BUILD ONLY.

## Rules

- R1. Run only the two commands below, exactly as written.
- R2. Make zero model/API calls and run zero Docker/WSL commands. Do not run `scripts/wp2_ctl_v224.py run`.
- R3. Do not create, edit or delete any file. The installer writes everything, and it rolls back on failure.
- R4. On any deviation, print the STOP block, including the complete output, and do nothing else.

**S1** Verify the installer hash. EXPECT: the value given in the human's message.

    python -c "import hashlib;print(hashlib.sha256(open('WP2_M14A_E1_INSTALL_2026-09-30.py','rb').read()).hexdigest())"

**S2** Run the installer. EXPECT: the output starts with `M14A_E1_INSTALL_COMPLETE`.

    python WP2_M14A_E1_INSTALL_2026-09-30.py

**S3** Print the final block verbatim, then STOP.

## STOP block

    MISSION_14A_E1_STOPPED / STEP=<S#> / OUTPUT=<verbatim> / CHANGES_MADE_BY_OPENCODE=none

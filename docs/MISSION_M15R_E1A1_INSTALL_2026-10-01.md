# MISSION M15R-E1A1-I: INSTALL ONLY (OpenCode)

ROLE: installer operator. BUILD ONLY.

## Rules

- R1. Run only the two commands below, exactly as written.
- R2. Make zero model/API calls and run zero Docker/WSL commands.
  - Do not run `scripts/wp2_ctl_v224.py run`, `scripts/wp2_m15r_run.py` or `scripts/wp2_m15r_e1a1.py`.
  - Do not resume the original plan `controller/plan_m15r_v1.json`.
- R3. Do not create, edit or delete any file. Never edit a generated patch, an episode, or `scripts/wp2_m14a_evalcore_e1.py`.
- R4. Do not run AG16 or any other controller.
- R5. On any deviation, print the STOP block, including the complete output, and do nothing else.

**S1** Verify the installer hash. EXPECT: the value given in the human's message.

    python -c "import hashlib;print(hashlib.sha256(open('WP2_M15R_E1A1_INSTALL_2026-10-01.py','rb').read()).hexdigest())"

**S2** Run the installer. EXPECT: the output starts with `M15R_E1A1_INSTALL_COMPLETE`.

    python WP2_M15R_E1A1_INSTALL_2026-10-01.py

**S3** Print the final block verbatim, then STOP.

## STOP block

    MISSION_M15R_E1A1_I_STOPPED / STEP=<S#> / OUTPUT=<verbatim> / CHANGES_MADE_BY_OPENCODE=none

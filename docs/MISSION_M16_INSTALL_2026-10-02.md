# MISSION M16-I: INSTALL ONLY (OpenCode)

ROLE: installer operator. BUILD ONLY.

## Rules

- **R1.** Run only the two commands below, exactly as written.
- **R2.** Zero model/API calls and zero Docker/WSL commands. Do not run:
  - `scripts/wp2_ctl_v224.py run`
  - `scripts/wp2_m16_run.py`
  - `scripts/wp2_m16_maint.py`
  - any plan
- **R3.** Do not create, edit or delete any file yourself. The installer writes the kit and appends one DECISIONS.md entry.
- **R4.** Do not run AG16 or any other controller.
- **R5.** On any deviation, print the STOP block with the complete output and do nothing else.

## Steps

**S1. Verify the installer hash.** Expected: the value given in the human's message.

    python -c "import hashlib;print(hashlib.sha256(open('WP2_M16_INSTALL_2026-10-02.py','rb').read()).hexdigest())"

**S2. Run the installer.** Expected: the output starts with `M16_INSTALL_COMPLETE`.

    python WP2_M16_INSTALL_2026-10-02.py

**S3.** Print the final block verbatim, then STOP. Do not start the dry-run; the human does that.

## STOP block

    MISSION_M16_I_STOPPED / STEP=<S#> / OUTPUT=<verbatim> / CHANGES_MADE_BY_OPENCODE=none

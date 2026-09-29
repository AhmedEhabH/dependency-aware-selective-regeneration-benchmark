# MISSION-12D: install the v2.2 reliability kit and deterministic controller

Executor: OpenCode. Authoring: brain. Date: 2026-09-29.

Mission-12C, the prose version, is superseded. Its ideas (INFRA_PENDING, circuit breaker,
Retry-After, LIGHT export) already exist as tested code in this kit. The executor
implements nothing.

## 0. Rules (absolute)

- R1. Do not create, edit, reformat or delete any kit file. The controller verifies their
  hashes and refuses to run if one was touched (`KIT_TAMPERED`).
- R2. Make zero OpenRouter/API calls, run zero docker/WSL commands, and do not run
  `scripts/wp2_ctl.py run`. The human runs the controller.
- R3. Run only the commands in section 2, in order, exactly as written.
- R4. If any output differs from its EXPECT line, stop immediately. Print the STOP block
  (section 3) with the step's token, then do nothing else. Do not attempt a fix.
- R5. Write in English only. Never print or persist the API key.

## 1. Input

The human has placed `wp2_v22_kit_2026-09-29.zip` in the parent folder of the repository,
next to the repository folder. Its sha256 is given in the human's message.

## 2. Steps

**S1** Confirm you are at the repository root and on branch main.

    git rev-parse --abbrev-ref HEAD

- EXPECT: `main`
- Otherwise: token `BRANCH_MISMATCH`.

**S2** Verify the zip hash.

    python -c "import hashlib;print(hashlib.sha256(open('../wp2_v22_kit_2026-09-29.zip','rb').read()).hexdigest())"

- EXPECT: equal to the sha256 in the human's message.
- Otherwise: token `KIT_ZIP_HASH_MISMATCH`.

**S3** List conflicts. No kit file may already exist with different content.

    python -c "import zipfile,pathlib,hashlib;z=zipfile.ZipFile('../wp2_v22_kit_2026-09-29.zip');bad=[n for n in z.namelist() if not n.endswith('/') and pathlib.Path(n).exists() and pathlib.Path(n).read_bytes().replace(b'\r\n',b'\n')!=z.read(n).replace(b'\r\n',b'\n')];print('CONFLICTS',bad)"

- EXPECT: `CONFLICTS []`
- Otherwise: token `KIT_CONFLICT`.

**S4** Extract the kit into the repository root.

    python -c "import zipfile;zipfile.ZipFile('../wp2_v22_kit_2026-09-29.zip').extractall('.');print('EXTRACTED')"

- EXPECT: `EXTRACTED`

**S5** Verify the kit hashes.

    python scripts/wp2_ctl.py verify-kit

- EXPECT: `KIT_OK`
- Otherwise: token `KIT_TAMPERED`.

**S6** Run the kit self-tests. They need no network and no Docker.

    python -c "import os,sys,subprocess;os.environ['PYTHONPATH']=os.pathsep.join(['src','.']);sys.exit(subprocess.call([sys.executable,'-m','pytest','-q','-p','no:cacheprovider','tests/unit/wp2/e2e_v22']))"

- EXPECT: the last line reads `70 passed` with zero failed and zero errors.
- Otherwise: token `KIT_SELFTEST_FAIL`. Include the last 60 lines of output.

**S7** Commit and push the kit. Stage only the kit paths.

    python -c "import json,subprocess;f=sorted(json.load(open('controller/KIT_MANIFEST.json'))['files'])+['controller/KIT_MANIFEST.json'];subprocess.run(['git','add','--']+f,check=True);print('STAGED',len(f))"
    git commit -m "feat(wp2): v2.2 reliability kit + deterministic controller (brain-authored, hash-verified)"
    git push origin main

- EXPECT: `STAGED <n>`, then the commit succeeds and the push succeeds.
- If the push fails: retry twice, 20 seconds apart. If it still fails: token `PUSH_FAILED`.

**S8** Dry-run and status.

    python scripts/wp2_ctl.py dry-run
    python scripts/wp2_ctl.py status --plan controller/plan_smoke_v22.json

- EXPECT: 13 phases, P00_KIT_SELFTEST to P12_CLOSE, all PENDING.

**S9** Print the exact command the human will run.

    python -c "import sys;print('RUN_COMMAND=' + sys.executable + ' scripts/wp2_ctl.py run')"

**S10** Print the final block below and stop.

    ================================================================
    MISSION_12D_COMPLETE
    KIT_COMMIT=<git rev-parse HEAD>
    KIT_OK=YES
    SELFTEST=70 passed
    RUN_COMMAND=<from S9>
    NEXT=HUMAN_RUNS_CONTROLLER
    ================================================================

## 3. STOP block (use on any deviation)

    ================================================================
    MISSION_12D_STOPPED
    STEP=<S#>
    TOKEN=<token>
    OUTPUT_TAIL=<last 60 lines of the failing command>
    CHANGES_MADE=<none | list>
    ================================================================

# POST-RUN STORAGE AUDIT (2026-09-28) — READ-ONLY

Mission-11 is fully closed (E2E_SMOKE_FLOOR_EFFECT). This is a STORAGE AUDIT
ONLY: **no file, container, image, volume, or VHDX was deleted or moved.**
No scientific/experimental work was performed.

## 1. Drive space
| Drive | Total | Used | Free |
|---|---|---|---|
| C: | 476.02 GiB | 439.06 GiB | **36.96 GiB** |
| D: | 1863.0 GiB | 1393.39 GiB | **469.61 GiB** |

## 2. docker system df -v (persisted below in JSON)
- Images: 12 total, 3.196 GB; reclaimable 758.3 MB (23%)
- Containers: 4 total, 63.12 MB; reclaimable 63.12 MB (100%)
- Local Volumes: 75 total, 35.31 GB; reclaimable 34.06 GB (96%)
- Build Cache: 0 B

## 3. Docker resource inventory + classification
| Resource | Size | Class |
|---|---|---|
| wp2-era-py38 / py39 / py312 images | 949/877/825 MB | **PROTECTED_EVIDENCE** (referenced by all V3 evidence) |
| python:3.8/3.9/3.12-slim (era parents) | 191/185/179 MB | **PROTECTED_EVIDENCE** (parents of era images) |
| postgres:15-alpine (wp2-pg image) | 417 MB | **PROTECTED_EVIDENCE** (wp2-pg depends on it) |
| redis:7-alpine | 57.8 MB | PROTECTED_EVIDENCE (kept; referenced by some checks) |
| a333fddb / 3c7eb2df / 6c64f632 (anonymous, scratch containers) | 183/189/177 MB | REBUILDABLE_CACHE (dangling, ~135 MB unique) |
| hello-world:latest | 25.9 kB | SAFE_DELETE (disposable) |
| wp2-pg container (4dfa7057) | 16.4 kB + data | **PROTECTED_EVIDENCE** |
| kind_ptolemy / mystifying_panini / silly_hugle (exited scratch) | ~63 MB | SAFE_DELETE (reproducible scratch; images reusable) |
| wp2-uv-cache volume | 21 GB | **PROTECTED_EVIDENCE** (required for reproducibility; referenced by evidence) |
| 74 anonymous hash-named volumes | ~34 GB | REBUILDABLE_CACHE (docker system df: 96% reclaimable) |
| Build cache | 0 B | — |

## 4. Parent top-level sizes (master-2026-07-21-2355)
| Path | GiB | Class |
|---|---|---|
| `_workspace` | 26.94 | MIXED (see breakdown) |
| — `_workspace/wp2_oracle_confirmation/envs` | 23.95 | REBUILDABLE_CACHE / UNKNOWN_REVIEW_REQUIRED (per-task venvs; recreatable by uv, some may be referenced) |
| — `_workspace/cache` | 2.06 | REBUILDABLE_CACHE (venvs, repositories, external_repos) |
| — `_workspace/active` | 0.28 | PROTECTED_EVIDENCE (mission files) |
| `project` | 5.63 | PROTECTED (research evidence) |
| parent zips (12 project/LIGHT exports + 1 bundle) | ~1.16 | COLD_MOVE_TO_D_HDD (superseded exports; latest 1015 kept HOT) |
| `inputs`, `logs`, `_historical_archive`, others | <0.1 | — |

## 5. Project top-level (>0.2 GiB)
| Path | GiB | Class |
|---|---|---|
| `dist/locagent-venv` | 1.25 | REBUILDABLE_CACHE |
| `dist/pilot-repo-cache` | 0.29 | **PROTECTED_EVIDENCE** (Saleor git cache) |
| `.uv-task-cache` | 1.69 | REBUILDABLE_CACHE |
| `research/wp2` | 0.64 | **PROTECTED_EVIDENCE** |
| `benchmark_data` | 0.46 | PROTECTED (input dataset) |
| `.venv` | 0.39 | REBUILDABLE_CACHE |
| `.mypy_cache/.pytest_cache/.ruff_cache` | <0.01 | REBUILDABLE_CACHE (trivial) |

## 6. WSL storage
- Ubuntu-24.04 distro root `/dev/sdf`: 1007 GB logical, 50 GB used, 907 GB free (6%).
- ext4.vhdx physical: `C:\Users\Ahmed\AppData\Local\WSL\{0c13781c-f355-4fad-95f7-ad01df935d7c}\ext4.vhdx` = **63.12 GiB**.
- Breakdown inside: `/var/lib/docker` 36 GB (volumes 36 GB: wp2-uv-cache 21 GB + ~15 GB anonymous), `/root/p5` 2.4 GB, `/opt` 1.1 GB.
- **Estimated reclaimable VHDX space WITHOUT compacting:** ~34 GB of dead anonymous-volume data inside the 63 GB VHDX (docker system df reclaimable 34.06 GB). A compaction could shrink the VHDX to roughly 63 − 34 ≈ **~30 GiB** (post-cleanup). Not executed.

## 7. Docker Desktop Windows-side
- `C:\Users\Ahmed\AppData\Local\Docker\wsl\disk\docker_data.vhdx` = 4.55 GiB
- `C:\Users\Ahmed\AppData\Local\Docker\wsl\main\ext4.vhdx` = 0.10 GiB
- The Ubuntu-24.04 distro VHDX (where docker actually stores data) is item 6 above.

## 8–9. Cold data suitable to move to D: + proposals
| Current path | GiB | Why safe | Reproducible | Git/evidence referenced | Destination | C: gained |
|---|---|---|---|---|---|---|
| `_workspace/wp2_oracle_confirmation/envs` (23.95) | 23.95 | per-task uv venvs; recreatable from lockfiles | yes | some may be referenced → UNKNOWN_REVIEW_REQUIRED | D:\wp2_envs_archive | 23.95 |
| `_workspace/cache` (2.06) | 2.06 | venv/repo caches | yes | no | D:\wp2_cache_archive | 2.06 |
| superseded parent zips (11 files, ~1.16) | 1.16 | old exports; latest 1015 kept on C: | yes (regenerable) | exports only | D:\archives\exports | 1.16 |
| `dist/locagent-venv` (1.25) | 1.25 | venv | yes | no | D:\venv_archive | 1.25 |
| `.uv-task-cache` (1.69) | 1.69 | uv cache | yes | no | D:\uv_cache | 1.69 |
| `.venv` (0.39) | 0.39 | venv | yes | no | D:\venv_archive | 0.39 |
| WSL `/root/p5` (2.4) | 2.4 | unknown content | — | UNKNOWN_REVIEW_REQUIRED | D:\wsl_root_p5 | 2.4 |

## 10. Three plans
- **SAFE_ONLY** (no evidence loss, unquestionably disposable caches): remove the 3 exited scratch containers by name, `docker builder prune -f`, `docker image prune -f` (dangling only), delete hello-world. Reclaim ≈ **0.8 GiB** on C: (0.76 GB images + 0.06 GB containers). Resulting C: free ≈ **37.8 GiB**. Downside: none. Rebuild: n/a.
- **SAFE_PLUS_MOVE_TO_D**: SAFE_ONLY + move superseded parent zips and the `_workspace/cache` + `dist/locagent-venv` + `.venv` + `.uv-task-cache` to D:. Reclaim ≈ **5.6 GiB** (moving) + 0.8 GiB (SAFE_ONLY) ≈ **6.4 GiB** on C:. Resulting C: free ≈ **43.3 GiB**. Downside: D: HDD access latency if paths change (set env/PYTHONPATH accordingly). Rebuild: re-create venvs/caches (~0.5–2 h).
- **AGGRESSIVE_BUT_REPRODUCIBLE**: SAFE_PLUS_MOVE + remove the 74 anonymous docker volumes (~34 GiB, REBUILDABLE_CACHE) + move `_workspace/wp2_oracle_confirmation/envs` to D: (23.95 GiB, after UNKNOWN-review) + WSL `/root/p5` (2.4 GiB). Reclaim ≈ **60 GiB** on C:/WSL. Resulting C: free ≈ **97 GiB** (and the WSL VHDX can shrink ~30 GiB after compaction — NOT executed). Downside: `docker volume prune`/compaction are on the FORBIDDEN list for this audit and would be user-side maintenance; the envs move needs verification that no committed evidence references the hash dirs. Rebuild: docker anonymous volumes repopulate on next run; envs recreated by uv.

## 11. Worthwhileness of the standard commands (NOT executed)
- `docker builder prune -f`: LOW (build cache = 0 B).
- `docker container prune -f`: **NOT RECOMMENDED as-is** — it would also remove the stopped wp2-pg. Use a name-filtered `docker rm` of the 3 scratch containers instead.
- `docker image prune -f`: MODEST (≈0.76 GB dangling images) — worthwhile.
- Anonymous docker volume removal: HIGH (≈34 GB) but `docker volume prune` is FORBIDDEN for this audit; user-side.
- WSL VHDX compaction: **HIGHEST** — after the volume cleanup the 63 GB VHDX holds ~30 GB of reclaimable data; compaction alone could restore ~30 GiB. Requires `wsl --shutdown` + `compactvhd`/Disk Management (user-side, not executed).
- WSL sparse VHD setting: prevents regrowth after compaction; configure via `.wslconfig [wsl2] sparseVhd=true`.

## 12. Not executed (per instructions)
No deletion, no move, no `docker system prune -a`, no `docker volume prune`,
no `wsl --shutdown`, no VHDX compaction, no Docker/WSL storage-location change,
no modification to the research project.

See POST_RUN_STORAGE_AUDIT.json for the machine-readable records.
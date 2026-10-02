# MISSION M16-S3: conditional storage maintenance (human run, ONLY if the gate said S3_REQUIRED)

Run this only after the brain confirms an `M16_S3_REQUIRED` STOP.

Before starting:

- All controllers must be stopped. Nothing may be running in Docker.
- Use PowerShell from the repository root with the project Python. Admin rights are needed only where step 5 says so.

## Never do any of these

- `docker volume prune`, `docker system prune`, or any other prune.
- Delete `wp2-uv-cache`, `wp2-pg` or any volume the script does not list.
- Move the WSL distro, or anything on D:.

## Steps

1. **Probe (read-only).** It writes `maintenance/capability_probe.json` and `maintenance/COMPACTION_INSTRUCTIONS.md` for THIS machine.

        python scripts/wp2_m16_maint.py probe

2. **Inventory (read-only, frozen).** It prints `sha=<64 hex>` and writes `maintenance/volume_inventory.json`.

        python scripts/wp2_m16_maint.py inventory

   The allow-list contains ONLY volumes with an anonymous 64-hex name, referenced by no container, and not protected. Send the inventory to the brain and wait for OK.

3. **Measure before.**

        python scripts/wp2_m16_maint.py measure --label pre_delete

4. **Delete the frozen allow-list.** Each volume is re-checked right before `docker volume rm <name>`, one at a time.

        python scripts/wp2_m16_maint.py delete --inventory-sha <sha from step 2>

5. **Compact.** Follow `research/wp2/m16_v1/maintenance/COMPACTION_INSTRUCTIONS.md` exactly: `wsl --shutdown`, then the compaction command the probe found (Optimize-VHD or diskpart) in an admin PowerShell, then start WSL. The instructions include `measure --label pre_compaction` and `measure --label post_compaction`.

6. **Health check.** It checks Docker, `wp2-pg` ready, era images present, `wp2-uv-cache` present, historical evidence unchanged, and the kit unchanged. It must print `M16_S3_POST_CHECK PASS`.

        python scripts/wp2_m16_maint.py post-check

7. **Commit the maintenance evidence.**

        git add research/wp2/m16_v1/maintenance
        git commit -m "evidence(wp2): M16 S3 maintenance"
        git push origin main

8. **Re-run the dry-run plan.** Its R05 gate recomputes the projection with the new free space.

        python scripts/wp2_ctl_v224.py run --plan controller/plan_m16_v1_dryrun.json

   - If it passes, the plan completes. Send the LIGHT.
   - If it still says S3_REQUIRED, STOP and send everything to the brain. Do not repeat S3 on your own.

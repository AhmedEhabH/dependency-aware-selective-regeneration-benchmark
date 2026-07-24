import json

with open(r'C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\notebooks\seven_arm_benchmark.ipynb', 'r') as f:
    nb = json.load(f)

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'markdown':
        content = ''.join(cell['source'])
        if 'Notes' in content[:20]:
            print(f'Found at index {i}: {cell["id"]}')
            break

# Insert new cell before exec-cell (which is at index 3)
new_cell = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## Auto-Resume Behavior\n\nThis cell runs the benchmark with `--auto-resume-hf` which:\n\n1. **Searches** Hugging Face for compatible incomplete experiments under the canonical prefix:\n   `experiments/{profile}/{protocol_version}/{source_commit}/`\n\n2. **Discovers candidates** by downloading each experiment's `checkpoint.json` and `run_records.jsonl`\n\n3. **Validates compatibility** against current run:\n   - Profile (smoke/pilot/research)\n   - Protocol version\n   - Source commit (tag/commit)\n   - Config hash\n   - Model identity\n   - Scenario IDs\n   - Strategy names\n\n4. **Selects action**:\n   - **RESUME** if exactly one compatible *incomplete* experiment found → skips completed runs, continues from next\n   - **ALREADY_COMPLETE** if one compatible *complete* experiment found → exits\n   - **START_NEW** if no compatible experiment found → creates new experiment\n   - **ERROR** if multiple compatible *incomplete* experiments found → requires `--experiment-id`\n\n5. **Every candidate and rejection reason is logged at INFO level** with full diagnostic details\n\n**Key points**:\n- `START_NEW` is acceptable only when no compatible candidate exists\n- If an existing experiment is rejected unexpectedly, STOP execution and investigate\n- All rejection reasons are logged at INFO level with full diagnostic detail\n- The canonical Run ID flows unchanged through all artifacts (checkpoint, records, summaries)"
    ]
}

# Find the exec-cell index and insert before it
for i, cell in enumerate(nb['cells']):
    if cell.get('id') == 'exec-cell':
        nb['cells'].insert(i, new_cell)
        break

with open(r'C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\notebooks\seven_arm_benchmark.ipynb', 'w') as f:
    json.dump(nb, f, indent=1)
print("Done")
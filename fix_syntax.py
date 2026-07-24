with open(r'C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\src\benchmark\checkpoint\hf_sync.py', 'rb') as f:
    content = f.read()

old = b'''                    continue
try:
                cp_data = json.loads(cp_local.read_text(encoding="utf-8"))'''

new = b'''                    continue

                cp_data = json.loads(cp_local.read_text(encoding="utf-8"))'''

content = content.replace(old, new)

with open(r'C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\src\benchmark\checkpoint\hf_sync.py', 'wb') as f:
    f.write(content)
print('Fixed')
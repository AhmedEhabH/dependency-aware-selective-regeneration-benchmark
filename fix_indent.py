with open(r'C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\src\benchmark\checkpoint\hf_sync.py', 'rb') as f:
    content = f.read()

old = b'                remote_protocol = cp_data.get("protocol_version", "")'
new = b'            try:\r\n                remote_protocol = cp_data.get("protocol_version", "")'
content = content.replace(old, new)

with open(r'C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\src\benchmark\checkpoint\hf_sync.py', 'wb') as f:
    f.write(content)
print('Fixed')
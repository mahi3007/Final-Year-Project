with open('scratch/reconstructed_stdout.txt', 'r', encoding='utf-8') as f:
    text = f.read()

matches = []
for line in text.splitlines():
    l_lower = line.lower()
    if any(k in l_lower for k in ['saving', 'saved', 'checkpoint', 'stage5m_', 'csv', 'report']):
        if not 'progress' in l_lower and not 'b/s' in l_lower:
            matches.append(line)

with open('scratch/saved_search.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(matches))

print(f"Total matching lines found: {len(matches)}")
for m in matches[:30]:
    print(m[:100])

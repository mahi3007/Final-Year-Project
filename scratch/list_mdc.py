import datacollective

print("=== Query: 'Common Voice' with locale='en' ===")
res = datacollective.list_datasets(query="Common Voice", locale="en", results_per_page=50)
print(f"Total matching: {res.total}")
for d in res.items:
    mb = (d.sizeBytes or 0) / (1024 * 1024)
    print(f"- {d.name} | ID: {d.id} | Size: {mb:.1f} MB | URL: {d.datasetUrl}")

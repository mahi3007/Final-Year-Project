import json

runs = []
with open("scratch/kaggle_kernel_session.log", "r", encoding="utf-8", errors="replace") as f:
    text = f.read()

# The log appears to be a list of json objects or json lines: [{"stream_name":..., "data":...}, ...]
try:
    data = json.loads(text)
except Exception:
    # Maybe lines
    data = []
    for line in text.splitlines():
        line = line.strip().lstrip(",")
        if line.startswith("{") and line.endswith("}"):
            try:
                data.append(json.loads(line))
            except:
                pass

full_stdout = ""
for item in data:
    if item.get("stream_name") == "stdout":
        full_stdout += item.get("data", "")

print(f"Total reconstructed stdout characters: {len(full_stdout)}")
with open("scratch/reconstructed_stdout.txt", "w", encoding="utf-8") as f:
    f.write(full_stdout)

print("\n--- Key sections from reconstructed stdout ---")
for line in full_stdout.splitlines():
    if "--- Model:" in line or "LOADING CTC MODEL" in line or "STAGE 5M" in line or "STEP" in line or "Overall WER" in line or "DISPARITY" in line or "ACCEPTED" in line or "REJECTED" in line:
        print(line[:120])

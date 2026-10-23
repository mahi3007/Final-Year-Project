import csv
import json

tsv_path = r"datasets/external/common_voice_27/validated.tsv"
targets = {
    "f3ea04475e301f84785710b9": "f3ea04475e301f84785710b9...",
    "fc22fd45334612a489c45562": "fc22fd45334612a489c45562..."
}

found = {k: [] for k in targets}

with open(tsv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        client_id = row.get('client_id', '')
        for t in targets:
            if client_id.startswith(t):
                sentence = row.get('sentence', '')
                words = len(sentence.strip().split())
                found[t].append({
                    "path": row.get("path"),
                    "locale": row.get("locale"),
                    "up_votes": int(row.get("up_votes", 0)),
                    "down_votes": int(row.get("down_votes", 0)),
                    "words": words,
                    "sentence": sentence,
                    "accents": row.get("accents", row.get("accent", "")),
                    "client_id": client_id
                })

for t, clips in found.items():
    print(f"\n=================== Target: {t} (Total TSV Rows: {len(clips)}) ===================")
    for idx, c in enumerate(clips, 1):
        b0 = (c["words"] >= 2) and (c["client_id"] != "") and (c["path"] != "")
        strict_v = (c["locale"] == "en") and (c["up_votes"] >= 2) and (c["down_votes"] < 2)
        both = b0 and strict_v
        reasons = []
        if c["words"] < 2:
            reasons.append(f"words < 2 ({c['words']})")
        if c["up_votes"] < 2:
            reasons.append(f"up_votes < 2 ({c['up_votes']})")
        if c["down_votes"] >= 2:
            reasons.append(f"down_votes >= 2 ({c['down_votes']})")
        if c["locale"] != "en":
            reasons.append(f"locale != 'en' ({c['locale']})")
        reason_str = ", ".join(reasons) if reasons else "PASSES_STRICT"
        print(f"[{idx:02d}] {c['path']} | words={c['words']:2d} | up={c['up_votes']} | down={c['down_votes']} | B0={b0} | V={strict_v} | StrictElig={both} | {reason_str}")
        print(f"     Sentence: '{c['sentence']}'")

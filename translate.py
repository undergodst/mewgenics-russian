#!/usr/bin/env python3
"""
Mewgenics Translator (Google Translate, free)

pip install deep-translator

Usage:
    python translate.py                  # translate all CSVs
    python translate.py --file items.csv # translate one file
    python translate.py --resume         # continue after interrupt
    python translate.py --cost           # count strings, estimate time
"""

import csv, os, sys, json, time, io, re, argparse

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("pip install deep-translator")
    sys.exit(1)

INPUT_DIR = 'text_output/data/text'
OUTPUT_DIR = 'override/data/text'
PROGRESS_FILE = 'translation_progress.json'
BATCH_SIZE = 20
SEPARATOR = '\n||\n'

PLACEHOLDER_RE = re.compile(
    r'\{[^}]+\}|\[img:[^\]]+\]|\[b\]|\[/b\]|\[i\]|\[/i\]'
    r'|\[s:[^\]]*\]|\[/s\]|\[color[^\]]*\]|\[/color\]|\[n\]'
)


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_progress(progress):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def read_csv_file(filepath):
    with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
        content = f.read()
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return None, None, None, None
    header = rows[0]
    try:
        en_idx = header.index('en')
    except ValueError:
        return header, rows, None, None
    key_idx = header.index('KEY') if 'KEY' in header else 0
    return header, rows, en_idx, key_idx


def protect_placeholders(text):
    mapping = {}
    counter = [0]
    def replacer(m):
        marker = f'__PH{counter[0]}__'
        mapping[marker] = m.group(0)
        counter[0] += 1
        return marker
    cleaned = PLACEHOLDER_RE.sub(replacer, text)
    return cleaned, mapping


def restore_placeholders(text, mapping):
    for marker, original in mapping.items():
        text = text.replace(marker, original)
    return text


def translate_batch(translator, texts):
    protected = []
    mappings = []
    for t in texts:
        cleaned, mapping = protect_placeholders(t)
        protected.append(cleaned)
        mappings.append(mapping)

    joined = SEPARATOR.join(protected)

    try:
        translated = translator.translate(joined)
    except Exception as e:
        print(f" ERROR: {e}")
        return texts

    parts = translated.split('||')
    parts = [p.strip() for p in parts]

    if len(parts) != len(texts):
        print(f" split mismatch ({len(parts)} vs {len(texts)}), 1-by-1...", end="", flush=True)
        results = []
        for i, t in enumerate(protected):
            try:
                tr = translator.translate(t)
                results.append(restore_placeholders(tr, mappings[i]))
                time.sleep(0.5)
            except:
                results.append(texts[i])
        return results

    return [restore_placeholders(p, mappings[i]) for i, p in enumerate(parts)]


def write_translated_csv(filename, header, rows, en_idx, key_idx, translations):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outpath = os.path.join(OUTPUT_DIR, filename)
    output = io.StringIO()
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(header)
    for row in rows[1:]:
        new_row = list(row)
        if key_idx < len(row) and row[key_idx] in translations:
            new_row[en_idx] = translations[row[key_idx]]
        writer.writerow(new_row)
    with open(outpath, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(output.getvalue())


def translate_file(translator, filename, progress):
    filepath = os.path.join(INPUT_DIR, filename)
    header, rows, en_idx, key_idx = read_csv_file(filepath)
    if en_idx is None:
        print(f"  Skip {filename} (no 'en' column)")
        return

    if filename not in progress:
        progress[filename] = {}
    file_tr = progress[filename]

    to_keys = []
    to_texts = []
    for row in rows[1:]:
        if key_idx < len(row) and en_idx < len(row):
            key = row[key_idx]
            en = row[en_idx].strip()
            if en and key not in file_tr:
                to_keys.append(key)
                to_texts.append(en)

    total = len(to_keys) + len(file_tr)
    if not to_keys:
        print(f"  {filename}: {total} strings [done]")
        write_translated_csv(filename, header, rows, en_idx, key_idx, file_tr)
        return

    total_batches = (len(to_keys) - 1) // BATCH_SIZE + 1
    print(f"  {filename}: {len(to_keys)} to translate ({len(file_tr)} cached), {total_batches} batches")

    for i in range(0, len(to_keys), BATCH_SIZE):
        bk = to_keys[i:i+BATCH_SIZE]
        bt = to_texts[i:i+BATCH_SIZE]
        bn = i // BATCH_SIZE + 1

        t0 = time.time()
        translated = translate_batch(translator, bt)
        elapsed = time.time() - t0

        for k, t in zip(bk, translated):
            file_tr[k] = t

        # Save progress after EVERY batch
        save_progress(progress)

        done = len(file_tr)
        print(f"    [{bn}/{total_batches}] +{len(bk)} -> {done}/{total} ({elapsed:.1f}s)")

        if i + BATCH_SIZE < len(to_keys):
            time.sleep(1)

    write_translated_csv(filename, header, rows, en_idx, key_idx, file_tr)
    print(f"  -> {filename} saved to {OUTPUT_DIR}/")


def cmd_cost():
    csv_files = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith('.csv'))
    total_s = 0
    for fn in csv_files:
        _, rows, en_idx, _ = read_csv_file(os.path.join(INPUT_DIR, fn))
        if en_idx is None: continue
        c = sum(1 for r in rows[1:] if en_idx < len(r) and r[en_idx].strip())
        total_s += c
        print(f"  {fn}: {c} strings")
    batches = total_s // BATCH_SIZE + 1
    print(f"\nTotal: {total_s} strings, {batches} batches")
    print(f"Time: ~{batches * 2 // 60}m {batches * 2 % 60}s")
    print(f"Cost: FREE")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--file', help='Translate one file')
    p.add_argument('--resume', action='store_true', help='Resume from progress')
    p.add_argument('--cost', action='store_true', help='Estimate only')
    args = p.parse_args()

    if not os.path.isdir(INPUT_DIR):
        print(f"ERROR: '{INPUT_DIR}' not found. Run: python gpak_tool.py extract-text")
        sys.exit(1)

    if args.cost:
        cmd_cost()
        return

    translator = GoogleTranslator(source='en', target='ru')
    progress = load_progress() if args.resume else {}

    csv_files = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith('.csv'))
    if args.file:
        if args.file not in csv_files:
            print(f"Not found: {args.file}\nAvailable: {', '.join(csv_files)}")
            sys.exit(1)
        csv_files = [args.file]

    print(f"Files: {len(csv_files)} | Batch: {BATCH_SIZE} | Progress: {'resume' if args.resume else 'fresh'}\n")

    t0 = time.time()
    for fn in csv_files:
        translate_file(translator, fn, progress)

    print(f"\nDone in {time.time()-t0:.0f}s!")
    print(f"Files in: {OUTPUT_DIR}/")
    print(f"Next: python gpak_tool.py patch")


if __name__ == '__main__':
    main()

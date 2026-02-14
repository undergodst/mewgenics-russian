#!/usr/bin/env python3
"""
Mewgenics Russian Translator — Claude Haiku 4.5
Переводит CSV-файлы из text_output/ → override/data/text/

Использование:
  python translate_haiku.py --cost          # Оценить стоимость
  python translate_haiku.py                 # Перевести всё
  python translate_haiku.py --resume        # Продолжить после обрыва
  python translate_haiku.py --file npc.csv  # Перевести один файл
"""

import os, sys, json, csv, io, time, argparse
try:
    import anthropic
except ImportError:
    print("Установи SDK: pip install anthropic")
    sys.exit(1)

# --- Настройки ---
INPUT_DIR = os.path.join("data", "text_output")
OUTPUT_DIR = os.path.join("data", "text")
PROGRESS_FILE = "translation_progress_haiku.json"
BATCH_SIZE = 30  # строк за один запрос
MODEL = "claude-haiku-4-5-20251001"

SKIP_FILES = {"credits.csv", "fonts.csv", "languages.csv"}

SYSTEM_PROMPT = """You are a professional game localizer (English → Russian) for Mewgenics — a cat breeding/adventure roguelike by Edmund McMillen (creator of The Binding of Isaac).

The game has dark humor, absurd situations, and cat-themed wordplay. Tone: quirky, slightly edgy, playful.

CRITICAL RULES:
- Keep ALL {placeholders} unchanged: {he}, {she}, {name}, {amount}, {0}, {1}, {target}, etc.
- Keep ALL markup tags unchanged: [b], [i], [color], [shake], [wave], etc.
- Keep \\n line breaks unchanged
- If string is a number, symbol, empty, or a single word that looks like a code/key — return unchanged
- Strings starting with // are comments — return unchanged

TRANSLATION STYLE:
- Natural Russian gamer language, not formal/literary
- Keep ability and item names short and punchy (1-3 words ideal)
- Dark humor and puns: adapt creatively, don't translate literally
- Cat terminology: Кот/Кошка, Котёнок, Мурлыка — use naturally
- UI text must be concise

GLOSSARY:
Cat=Кот/Кошка, Kitten=Котёнок, Collar=Ошейник, House=Дом, Gene=Ген, Mutation=Мутация, Breed=Разведение, Adventure=Приключение, Trait=Черта, Passive=Пассивка, Litter=Помёт, Feral=Дикий, Stray=Бездомный, Shelter=Приют, Purrsonality=Мурчность

Output ONLY valid JSON. No markdown, no explanations."""


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_progress(progress):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def read_csv(filepath):
    with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
        return list(csv.reader(f))


def translate_batch(client, batch: dict, retries=0) -> dict:
    """Отправить батч строк на перевод. batch = {key: english_text}"""
    MAX_RETRIES = 5
    prompt = (
        "Translate these game strings from English to Russian.\n"
        "Input: JSON object {key: english}.\n"
        "Output: JSON object {key: russian}. Same keys, translated values.\n\n"
        + json.dumps(batch, ensure_ascii=False, indent=2)
    )

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        # Очистить от возможных markdown-обёрток
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)

        # Проверить что все ключи на месте
        for k in batch:
            if k not in result:
                result[k] = batch[k]  # оставить оригинал если пропущено
        return result

    except (json.JSONDecodeError, anthropic.RateLimitError, anthropic.APIError) as e:
        if retries < MAX_RETRIES:
            wait = 2 ** (retries + 1)
            print(f"\n    Retry ({e.__class__.__name__}), waiting {wait}s...")
            time.sleep(wait)
            return translate_batch(client, batch, retries + 1)
        print(f"\n    FAILED after {MAX_RETRIES} retries: {e}")
        return batch  # вернуть оригинал при неудаче


def translate_file(client, filename, progress):
    filepath = os.path.join(INPUT_DIR, filename)
    rows = read_csv(filepath)
    if not rows:
        return

    header = rows[0]
    en_idx = header.index("en") if "en" in header else 1
    key_idx = header.index("KEY") if "KEY" in header else 0

    # Уже переведённые строки
    done = progress.get(filename, {})

    # Собрать строки для перевода
    todo = {}
    for row in rows[1:]:
        if len(row) <= max(en_idx, key_idx):
            continue
        key = row[key_idx]
        text = row[en_idx].strip()
        if text and key not in done and not row[0].startswith("//"):
            todo[key] = text

    total = len(todo) + len(done)
    if not todo:
        print(f"  {filename}: {total} strings ✓ (all done)")
        write_csv(filename, rows, header, en_idx, key_idx, done)
        return

    print(f"  {filename}: {len(todo)} to translate ({len(done)} cached)")

    keys = list(todo.keys())
    num_batches = (len(keys) - 1) // BATCH_SIZE + 1

    for i in range(0, len(keys), BATCH_SIZE):
        batch_keys = keys[i : i + BATCH_SIZE]
        batch = {k: todo[k] for k in batch_keys}
        batch_num = i // BATCH_SIZE + 1

        sys.stdout.write(f"\r    [{batch_num}/{num_batches}] ...")
        sys.stdout.flush()

        result = translate_batch(client, batch)

        for k in batch_keys:
            done[k] = result.get(k, todo[k])

        # Сохранить прогресс после каждого батча
        progress[filename] = done
        save_progress(progress)

        if i + BATCH_SIZE < len(keys):
            time.sleep(0.3)

    print(f"\r    Translated {len(todo)} strings.              ")
    write_csv(filename, rows, header, en_idx, key_idx, done)


def write_csv(filename, rows, header, en_idx, key_idx, translations):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(header)
    for row in rows[1:]:
        new_row = list(row)
        if key_idx < len(row) and row[key_idx] in translations:
            new_row[en_idx] = translations[row[key_idx]]
        writer.writerow(new_row)
    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8-sig", newline="") as f:
        f.write(out.getvalue())


def estimate_cost():
    csv_files = sorted(
        f for f in os.listdir(INPUT_DIR) if f.endswith(".csv") and f not in SKIP_FILES
    )
    total_strings = 0
    total_chars = 0

    for fn in csv_files:
        rows = read_csv(os.path.join(INPUT_DIR, fn))
        if not rows:
            continue
        en_idx = rows[0].index("en") if "en" in rows[0] else 1
        for row in rows[1:]:
            if len(row) > en_idx and row[en_idx].strip() and not row[0].startswith("//"):
                total_strings += 1
                total_chars += len(row[en_idx])

    tokens_in = int(total_chars / 3 * 2.5)  # с учётом промпта
    tokens_out = int(total_chars / 3 * 1.4)  # русский длиннее

    cost_in = tokens_in / 1e6 * 0.80
    cost_out = tokens_out / 1e6 * 4.00
    cost_total = cost_in + cost_out

    print(f"Files: {len(csv_files)}")
    print(f"Strings: {total_strings:,}")
    print(f"Characters: {total_chars:,}")
    print(f"Estimated tokens: ~{tokens_in + tokens_out:,}")
    print(f"Estimated cost (Haiku 4.5): ~${cost_total:.2f}")
    print(f"  Input:  ~${cost_in:.2f}")
    print(f"  Output: ~${cost_out:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Mewgenics Translator (Claude Haiku)")
    parser.add_argument("--cost", action="store_true", help="Estimate cost only")
    parser.add_argument("--resume", action="store_true", help="Resume from progress")
    parser.add_argument("--file", help="Translate one specific CSV file")
    args = parser.parse_args()

    if not os.path.isdir(INPUT_DIR):
        print(f"ERROR: папка '{INPUT_DIR}' не найдена.")
        print("Сначала извлеки текст: python gpak_tool.py extract-text")
        sys.exit(1)

    if args.cost:
        estimate_cost()
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Задай API ключ:")
        print("  Windows:  set ANTHROPIC_API_KEY=sk-ant-...")
        print("  Linux:    export ANTHROPIC_API_KEY=sk-ant-...")
        print()
        print("Ключ берёшь тут: https://console.anthropic.com/settings/keys")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    progress = load_progress() if args.resume else {}

    csv_files = sorted(
        f for f in os.listdir(INPUT_DIR) if f.endswith(".csv") and f not in SKIP_FILES
    )

    if args.file:
        if args.file not in csv_files:
            print(f"Не найден: {args.file}")
            print(f"Доступные: {', '.join(csv_files)}")
            sys.exit(1)
        csv_files = [args.file]

    print(f"Model: {MODEL}")
    print(f"Files: {len(csv_files)}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Progress: {'resume' if args.resume else 'fresh start'}")
    print()

    t0 = time.time()
    for fn in csv_files:
        translate_file(client, fn, progress)

    elapsed = time.time() - t0
    print(f"\nГотово за {elapsed:.0f}s!")
    print(f"Переведённые файлы: {OUTPUT_DIR}/")
    print(f"\nСледующий шаг: python gpak_tool.py patch")


if __name__ == "__main__":
    main()

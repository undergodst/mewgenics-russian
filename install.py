#!/usr/bin/env python3
"""Mewgenics Russian Translation — Installer"""

import os, sys, struct, shutil, time, winreg

if getattr(sys, 'frozen', False):
    OVERRIDE_DIR = os.path.join(os.path.dirname(sys.executable), 'data')
else:
    OVERRIDE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

GPAK = 'resources.gpak'
TEXT_EXT = {'.csv', '.gon'}


def find_game_path():
    """Auto-detect Mewgenics install path via Steam registry + library folders."""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
        steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
        winreg.CloseKey(key)
    except (OSError, FileNotFoundError):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam")
            steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
            winreg.CloseKey(key)
        except (OSError, FileNotFoundError):
            return None

    # Check default library
    candidates = [os.path.join(steam_path, "steamapps", "common", "Mewgenics")]

    # Parse libraryfolders.vdf for additional libraries
    vdf = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    if os.path.exists(vdf):
        with open(vdf, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip().strip('"')
                if 'path' in line.lower():
                    parts = line.split('"')
                    for p in parts:
                        p = p.strip()
                        if p and os.path.isdir(p):
                            candidates.append(os.path.join(p, "steamapps", "common", "Mewgenics"))

    for c in candidates:
        if os.path.isfile(os.path.join(c, GPAK)):
            return c
    return None


def read_directory(path):
    entries = []
    with open(path, 'rb') as f:
        n = struct.unpack('<I', f.read(4))[0]
        for _ in range(n):
            nl = struct.unpack('<H', f.read(2))[0]
            name = f.read(nl).decode('utf-8', 'replace')
            size = struct.unpack('<I', f.read(4))[0]
            entries.append((name, size))
        data_start = f.tell()
    return entries, data_start


def stream_copy(src, dst, size):
    rem = size
    while rem > 0:
        buf = src.read(min(rem, 8 * 1024 * 1024))
        if not buf:
            break
        dst.write(buf)
        rem -= len(buf)


def patch(game_dir):
    gpak = os.path.join(game_dir, GPAK)
    bak = gpak + '.bak'

    # Collect override files
    overrides = {}
    for root, _, files in os.walk(OVERRIDE_DIR):
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, OVERRIDE_DIR).replace(os.sep, '/')
            rel = 'data/' + rel
            overrides[rel] = full

    if not overrides:
        print("[!] No translation files found in data/ folder.")
        return False

    # Backup
    if not os.path.exists(bak):
        print(f"[*] Creating backup: {os.path.basename(bak)}")
        shutil.copy2(gpak, bak)
    else:
        print("[*] Backup already exists, using it as source.")
    source = bak

    entries, data_start = read_directory(source)

    matched = {}
    for i, (name, _) in enumerate(entries):
        if name in overrides:
            matched[i] = overrides[name]

    if not matched:
        print("[!] No matching files found in archive.")
        return False

    print(f"[*] Patching {len(matched)} file(s)...")

    new_entries = [(name, os.path.getsize(matched[i]) if i in matched else size)
                   for i, (name, size) in enumerate(entries)]

    tmp = gpak + '.tmp'
    t0 = time.time()

    with open(tmp, 'wb') as out:
        out.write(struct.pack('<I', len(new_entries)))
        for name, size in new_entries:
            nb = name.encode('utf-8')
            out.write(struct.pack('<H', len(nb)))
            out.write(nb)
            out.write(struct.pack('<I', size))

        with open(source, 'rb') as src:
            offset = data_start
            total = len(entries)
            for i, (name, orig_size) in enumerate(entries):
                if i in matched:
                    with open(matched[i], 'rb') as ov:
                        stream_copy(ov, out, new_entries[i][1])
                else:
                    src.seek(offset)
                    stream_copy(src, out, orig_size)
                offset += orig_size
                pct = (i + 1) / total
                if (i + 1) % 2000 == 0 or i == total - 1:
                    print(f"    {pct:.0%}...", end='\r')

    os.replace(tmp, gpak)
    print(f"\n[+] Done in {time.time() - t0:.1f}s!")
    return True


def main():
    print("=" * 50)
    print("  Mewgenics — Русский перевод (установка)")
    print("  Google Translate | Community Edition")
    print("=" * 50)
    print()

    # Check data folder exists
    if not os.path.isdir(OVERRIDE_DIR):
        print("[!] Папка data/ не найдена рядом со скриптом.")
        input("\nНажмите Enter для выхода...")
        return

    csv_count = sum(1 for f in os.listdir(os.path.join(OVERRIDE_DIR, 'text'))
                    if f.endswith('.csv'))
    print(f"[*] Найдено файлов перевода: {csv_count}")

    # Find game
    print("[*] Поиск Mewgenics...")
    game_dir = find_game_path()

    if game_dir:
        print(f"[+] Найдено: {game_dir}")
    else:
        print("[!] Автоматически найти не удалось.")
        game_dir = input("    Введите путь к папке Mewgenics: ").strip().strip('"')

    if not os.path.isfile(os.path.join(game_dir, GPAK)):
        print(f"[!] {GPAK} не найден в {game_dir}")
        input("\nНажмите Enter для выхода...")
        return

    print()
    ok = patch(game_dir)

    if ok:
        print()
        print("[+] Перевод установлен!")
        print("    Запустите игру через Steam.")
        print()
        print("    Для удаления запустите uninstall.bat")

    input("\nНажмите Enter для выхода...")


if __name__ == '__main__':
    main()

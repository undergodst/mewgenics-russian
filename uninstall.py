#!/usr/bin/env python3
"""Mewgenics Russian Translation — Uninstaller"""

import os, sys, shutil, winreg

GPAK = 'resources.gpak'


def find_game_path():
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

    candidates = [os.path.join(steam_path, "steamapps", "common", "Mewgenics")]

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


def main():
    print("=" * 50)
    print("  Mewgenics — Русский перевод (удаление)")
    print("=" * 50)
    print()

    game_dir = find_game_path()

    if game_dir:
        print(f"[+] Найдено: {game_dir}")
    else:
        print("[!] Автоматически найти не удалось.")
        game_dir = input("    Введите путь к папке Mewgenics: ").strip().strip('"')

    gpak = os.path.join(game_dir, GPAK)
    bak = gpak + '.bak'

    if not os.path.exists(bak):
        print("[!] Бэкап не найден. Перевод не был установлен или уже удалён.")
        print("    Можно проверить целостность файлов через Steam.")
        input("\nНажмите Enter для выхода...")
        return

    print("[*] Восстановление оригинала из бэкапа...")
    shutil.copy2(bak, gpak)
    os.remove(bak)
    print("[+] Готово! Оригинальные файлы восстановлены.")

    input("\nНажмите Enter для выхода...")


if __name__ == '__main__':
    main()

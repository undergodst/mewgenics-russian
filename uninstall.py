#!/usr/bin/env python3

import os
import sys
import shutil
import winreg

FOLDERS_TO_REMOVE = ["data", "swfs"]
GPAK = "resources.gpak"
EXE_NAME = "Mewgenics.exe"


def find_game_path():
    steam_path = None
    for reg_path in [
        r"SOFTWARE\WOW6432Node\Valve\Steam",
        r"SOFTWARE\Valve\Steam",
    ]:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
            steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
            winreg.CloseKey(key)
            break
        except (OSError, FileNotFoundError):
            continue

    if not steam_path:
        return None

    candidates = [os.path.join(steam_path, "steamapps", "common", "Mewgenics")]

    vdf = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    if os.path.exists(vdf):
        with open(vdf, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"path"' in line.lower():
                    parts = line.split('"')
                    for p in parts:
                        p = p.strip()
                        if p and os.path.isdir(p):
                            candidates.append(
                                os.path.join(p, "steamapps", "common", "Mewgenics")
                            )

    for c in candidates:
        if os.path.isfile(os.path.join(c, EXE_NAME)) or os.path.isfile(
            os.path.join(c, GPAK)
        ):
            return c
    return None


def main():
    print("=" * 50)
    print("  Mewgenics — Русский перевод (удаление)")
    print("=" * 50)
    print()

    print("[*] Поиск Mewgenics...")
    game_dir = find_game_path()

    if game_dir:
        print(f"[+] Найдено: {game_dir}")
    else:
        print("[!] Автоматически найти не удалось.")
        game_dir = input("    Введите путь к папке Mewgenics: ").strip().strip('"')

    if not os.path.isdir(game_dir):
        print(f"[!] Папка не существует: {game_dir}")
        input("\nНажмите Enter для выхода...")
        return

    removed = 0
    for folder in FOLDERS_TO_REMOVE:
        folder_path = os.path.join(game_dir, folder)
        if os.path.exists(folder_path):
            print(f"[*] Удаление {folder}/...")
            shutil.rmtree(folder_path)
            print(f"[+] {folder}/ удалена")
            removed += 1

    if removed > 0:
        print()
        print("[+] Перевод удалён!")
        print("    Игра использует оригинальные файлы из resources.gpak")
    else:
        print("[!] Папки data/ и swfs/ не найдены. Перевод не установлен или уже удалён.")

    input("\nНажмите Enter для выхода...")


if __name__ == "__main__":
    main()

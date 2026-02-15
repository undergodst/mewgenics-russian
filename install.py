#!/usr/bin/env python3

import os
import sys
import shutil
import winreg

FOLDERS_TO_INSTALL = ["data", "swfs"]
GPAK = "resources.gpak"
EXE_NAME = "Mewgenics.exe"


def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


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


def install_folder(folder_name, base_dir, game_dir):
    src = os.path.join(base_dir, folder_name)
    dst = os.path.join(game_dir, folder_name)

    if not os.path.isdir(src):
        return False

    file_count = sum(len(files) for _, _, files in os.walk(src))
    if file_count == 0:
        return False

    if os.path.exists(dst):
        print(f"[*] Удаление старой папки {folder_name}/...")
        shutil.rmtree(dst)

    print(f"[*] Копирование {folder_name}/ ({file_count} файлов)...")
    shutil.copytree(src, dst)
    print(f"[+] {folder_name}/ скопирована")
    return True


def main():
    print("=" * 50)
    print("  Mewgenics — Русский перевод (установка)")
    print("=" * 50)
    print()

    base_dir = get_base_dir()

    if not os.path.isdir(os.path.join(base_dir, "data")):
        print("[!] Папка data/ не найдена рядом с установщиком.")
        input("\nНажмите Enter для выхода...")
        return

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

    if not (
        os.path.isfile(os.path.join(game_dir, EXE_NAME))
        or os.path.isfile(os.path.join(game_dir, GPAK))
    ):
        print(f"[!] {EXE_NAME} или {GPAK} не найден в {game_dir}")
        input("\nНажмите Enter для выхода...")
        return

    print()
    installed = 0
    for folder in FOLDERS_TO_INSTALL:
        if install_folder(folder, base_dir, game_dir):
            installed += 1

    if installed > 0:
        print()
        print("[+] Перевод установлен!")
        print("    Запустите игру через Steam.")
        print("    Для удаления запустите uninstall_ru.exe")
    else:
        print("[!] Нечего устанавливать — папки data/ и swfs/ пусты или отсутствуют.")

    input("\nНажмите Enter для выхода...")


if __name__ == "__main__":
    main()

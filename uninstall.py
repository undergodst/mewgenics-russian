#!/usr/bin/env python3

import os
import sys
import shutil
import traceback

FOLDERS_TO_REMOVE = ["data", "swfs"]
GPAK = "resources.gpak"
EXE_NAME = "Mewgenics.exe"


def find_game_path():
    steam_path = None

    if sys.platform == "win32":
        try:
            import winreg
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
        except ImportError:
            pass

    # Если в реестре пусто, проверяем стандартные места
    if not steam_path:
        common_paths = [
            os.path.expandvars(r"%ProgramFiles(x86)%\Steam"),
            os.path.expandvars(r"%ProgramFiles%\Steam"),
            r"C:\Steam",
            r"D:\Steam",
            r"D:\SteamLibrary",
            r"E:\SteamLibrary",
        ]
        for p in common_paths:
            if os.path.isdir(p):
                steam_path = p
                break

    if not steam_path:
        return None

    candidates = [os.path.join(steam_path, "steamapps", "common", "Mewgenics")]

    vdf = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    if os.path.exists(vdf):
        try:
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
        except Exception:
            pass

    for c in candidates:
        if os.path.isfile(os.path.join(c, EXE_NAME)) or os.path.isfile(
            os.path.join(c, GPAK)
        ):
            return os.path.normpath(c)
    return None


def main():
    print("=" * 50)
    print("  Mewgenics — Удаление русского перевода")
    print("=" * 50)
    print()

    print("[*] Поиск Mewgenics...")
    game_dir = find_game_path()

    if game_dir:
        print(f"[+] Найдено: {game_dir}")
    else:
        print("[!] Автоматически найти не удалось.")
        game_dir = input("    Введите путь к папке Mewgenics вручную: ").strip().strip('"')

    if not game_dir or not os.path.isdir(game_dir):
        print(f"[!] Путь не найден: {game_dir}")
        input("\nНажмите Enter для выхода...")
        return

    removed = 0
    for folder in FOLDERS_TO_REMOVE:
        folder_path = os.path.normpath(os.path.join(game_dir, folder))
        if os.path.exists(folder_path):
            print(f"[*] Удаление {folder}/...")
            try:
                shutil.rmtree(folder_path)
                print(f"[+] {folder}/ удалена")
                removed += 1
            except PermissionError:
                print(f"[!] Нет прав на удаление в {folder_path}")
                print(f"    Закройте игру и попробуйте запустить от администратора.")
            except Exception as e:
                print(f"[!] Ошибка при удалении {folder}: {e}")

    if removed > 0:
        print()
        print("[+] Перевод успешно удалён!")
        print("    Игра будет использовать оригинальные файлы.")
    else:
        print("\n[!] Папки перевода не найдены (возможно, они уже удалены).")

    input("\nНажмите Enter для выхода...")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[!] Произошла критическая ошибка: {e}")
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")

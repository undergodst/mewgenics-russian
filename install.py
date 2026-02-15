#!/usr/bin/env python3

import os
import sys
import shutil
import traceback

FOLDERS_TO_INSTALL = ["data", "swfs"]
GPAK = "resources.gpak"
EXE_NAME = "Mewgenics.exe"


def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


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

    if not steam_path:
        common_paths = [
            os.path.expandvars(r"%ProgramFiles(x86)%\Steam"),
            os.path.expandvars(r"%ProgramFiles%\Steam"),
            r"C:\Steam",
            r"D:\Steam",
            r"E:\Steam",
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


def install_folder(folder_name, base_dir, game_dir):
    # Используем normpath для предотвращения проблем с длинными путями и двойными слешами
    src = os.path.normpath(os.path.join(base_dir, folder_name))
    dst = os.path.normpath(os.path.join(game_dir, folder_name))

    if not os.path.isdir(src):
        print(f"[!] Папка {folder_name}/ не найдена в {base_dir}")
        return False

    file_count = sum(len(files) for _, _, files in os.walk(src))
    if file_count == 0:
        print(f"[!] Папка {folder_name}/ пуста")
        return False

    print(f"[*] Копирование {folder_name}/ ({file_count} файлов)...")
    try:
        # dirs_exist_ok=True позволяет копировать файлы поверх существующих
        # Это стабильнее в Windows, чем rmtree + copytree
        shutil.copytree(src, dst, dirs_exist_ok=True)
    except PermissionError:
        print(f"[!] Ошибка доступа к {dst}")
        print(f"    Закройте игру и запустите установщик от имени администратора.")
        return False
    except Exception as e:
        print(f"[!] Не удалось скопировать {folder_name}: {e}")
        return False

    print(f"[+] {folder_name}/ установлена")
    return True


def main():
    print("=" * 50)
    print("  Mewgenics — Русский перевод v2.1 (установка)")
    print("=" * 50)
    print()

    base_dir = get_base_dir()
    print(f"[*] Рабочая папка: {base_dir}")

    has_data = os.path.isdir(os.path.join(base_dir, "data"))
    has_swfs = os.path.isdir(os.path.join(base_dir, "swfs"))

    if not has_data and not has_swfs:
        print("[!] Папки перевода не найдены.")
        print(f"    Убедитесь, что архив полностью распакован в одну папку.")
        print(f"    Содержимое текущей директории:")
        try:
            for item in os.listdir(base_dir):
                print(f"      {item}")
        except Exception:
            pass
        input("\nНажмите Enter для выхода...")
        return

    print("[*] Поиск папки с игрой...")
    game_dir = find_game_path()

    if game_dir:
        print(f"[+] Найдено: {game_dir}")
    else:
        print("[!] Игра не найдена автоматически.")
        game_dir = input("    Введите путь к Mewgenics вручную: ").strip().strip('"')

    if not game_dir or not os.path.isdir(game_dir):
        print(f"[!] Указанный путь не существует: {game_dir}")
        input("\nНажмите Enter для выхода...")
        return

    # Проверка на наличие важных файлов игры
    if not (
        os.path.isfile(os.path.join(game_dir, EXE_NAME))
        or os.path.isfile(os.path.join(game_dir, GPAK))
    ):
        print(f"[!] В папке {game_dir} не найден {EXE_NAME} или {GPAK}")
        print(f"    Проверьте правильность пути.")
        input("\nНажмите Enter для выхода...")
        return

    print()
    installed = 0
    for folder in FOLDERS_TO_INSTALL:
        if install_folder(folder, base_dir, game_dir):
            installed += 1

    if installed > 0:
        print()
        print("[+] Установка завершена успешно!")
        print("    Запускайте игру через Steam.")
    else:
        print("[!] Ошибки при установке. Файлы не были скопированы.")

    input("\nНажмите Enter для завершения...")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print()
        print(f"[!!!] КРИТИЧЕСКАЯ ОШИБКА: {e}")
        print("-" * 50)
        traceback.print_exc()
        print("-" * 50)
        input("\nНажмите Enter для закрытия (сделайте скриншот ошибки)...")

#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FOLDERS_TO_INSTALL=("data" "swfs")

echo "=================================================="
echo "  Mewgenics — Русский перевод v3.2.1 (установка)"
echo "  Steam Deck / Linux"
echo "=================================================="
echo

# --- Диагностика: содержимое папки скрипта ---
echo "[*] Рабочая папка: $SCRIPT_DIR"
echo "[*] Содержимое:"
ls -la "$SCRIPT_DIR" 2>/dev/null | head -20
echo

if [ ! -d "$SCRIPT_DIR/data" ]; then
    echo "[!] Папка data/ не найдена рядом со скриптом."
    echo "    Убедитесь, что архив полностью распакован в одну папку."
    echo
    echo "[?] Диагностика:"
    echo "    Скрипт запущен из: $SCRIPT_DIR"
    echo "    pwd: $(pwd)"
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

echo "[*] Поиск Mewgenics..."

GAME_DIR=""

# Собираем все возможные пути к игре
STEAM_DIRS=(
    "$HOME/.steam/steam/steamapps/common/Mewgenics"
    "$HOME/.local/share/Steam/steamapps/common/Mewgenics"
    "/home/deck/.steam/steam/steamapps/common/Mewgenics"
    "/home/deck/.local/share/Steam/steamapps/common/Mewgenics"
)

# SD-карта (частый кейс на Steam Deck)
for sdcard in /run/media/mmcblk* /run/media/deck/mmcblk*; do
    if [ -d "$sdcard" ]; then
        STEAM_DIRS+=("$sdcard/steamapps/common/Mewgenics")
    fi
done

# Парсинг libraryfolders.vdf для дополнительных библиотек Steam
for vdf in "$HOME/.steam/steam/steamapps/libraryfolders.vdf" \
           "$HOME/.local/share/Steam/steamapps/libraryfolders.vdf"; do
    if [ -f "$vdf" ]; then
        while IFS= read -r line; do
            if [[ $line =~ \"path\"[[:space:]]*\"([^\"]+)\" ]]; then
                lib_path="${BASH_REMATCH[1]}"
                lib_path="${lib_path//\\\\/\/}"
                STEAM_DIRS+=("$lib_path/steamapps/common/Mewgenics")
            fi
        done < "$vdf"
    fi
done

# Ищем игру — проверяем и .exe (Proton) и .x86_64 (нативный)
for dir in "${STEAM_DIRS[@]}"; do
    if [ -f "$dir/Mewgenics.exe" ] || [ -f "$dir/Mewgenics.x86_64" ] || [ -f "$dir/resources.gpak" ]; then
        GAME_DIR="$dir"
        break
    fi
done

if [ -z "$GAME_DIR" ]; then
    echo "[!] Автоматически найти не удалось."
    echo
    echo "[?] Диагностика — проверенные пути:"
    for dir in "${STEAM_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            echo "    [существует, но без игры] $dir"
            ls "$dir" 2>/dev/null | head -5
        else
            echo "    [не найден] $dir"
        fi
    done
    echo
    read -p "    Введите путь к папке Mewgenics: " GAME_DIR
    GAME_DIR="${GAME_DIR//\~/$HOME}"
    GAME_DIR="${GAME_DIR%\"}"
    GAME_DIR="${GAME_DIR#\"}"
fi

if [ ! -d "$GAME_DIR" ]; then
    echo "[!] Папка не существует: $GAME_DIR"
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

# Проверяем наличие файлов игры (Proton .exe или нативный .x86_64)
if [ ! -f "$GAME_DIR/Mewgenics.exe" ] && [ ! -f "$GAME_DIR/Mewgenics.x86_64" ] && [ ! -f "$GAME_DIR/resources.gpak" ]; then
    echo "[!] Файлы игры не найдены в $GAME_DIR"
    echo "    Ожидается: Mewgenics.exe, Mewgenics.x86_64 или resources.gpak"
    echo
    echo "[?] Содержимое папки:"
    ls -la "$GAME_DIR" 2>/dev/null | head -20
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

# Определяем тип запуска
if [ -f "$GAME_DIR/Mewgenics.exe" ]; then
    echo "[+] Найдено (Proton): $GAME_DIR"
elif [ -f "$GAME_DIR/Mewgenics.x86_64" ]; then
    echo "[+] Найдено (Native Linux): $GAME_DIR"
else
    echo "[+] Найдено: $GAME_DIR"
fi

echo "[*] Содержимое папки игры:"
ls "$GAME_DIR" 2>/dev/null
echo

INSTALLED=0
for folder in "${FOLDERS_TO_INSTALL[@]}"; do
    SRC="$SCRIPT_DIR/$folder"
    DST="$GAME_DIR/$folder"

    if [ ! -d "$SRC" ]; then
        continue
    fi

    FILE_COUNT=$(find "$SRC" -type f | wc -l)
    if [ "$FILE_COUNT" -eq 0 ]; then
        continue
    fi

    echo "[*] Копирование $folder/ ($FILE_COUNT файлов)..."
    # Используем cp с merge (не удаляем старую папку, перезаписываем поверх)
    cp -rf "$SRC" "$GAME_DIR/"
    echo "[+] $folder/ скопирована"
    INSTALLED=$((INSTALLED + 1))
done

if [ "$INSTALLED" -gt 0 ]; then
    echo
    echo "[+] Перевод установлен!"
    echo "    Запустите игру через Steam."
    echo "    Для удаления запустите ./uninstall_steamdeck.sh"
    echo
    echo "[*] Проверка — файлы в папке игры:"
    for folder in "${FOLDERS_TO_INSTALL[@]}"; do
        if [ -d "$GAME_DIR/$folder" ]; then
            count=$(find "$GAME_DIR/$folder" -type f | wc -l)
            echo "    $folder/ — $count файлов"
        fi
    done
else
    echo "[!] Нечего устанавливать — папки data/ и swfs/ пусты или отсутствуют."
fi

echo
read -p "Нажмите Enter для выхода..."

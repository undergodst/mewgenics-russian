#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FOLDERS_TO_INSTALL=("data" "swfs")
EXE_NAME="Mewgenics.x86_64"

echo "=================================================="
echo "  Mewgenics — Русский перевод (установка)"
echo "  Steam Deck / Linux"
echo "=================================================="
echo

if [ ! -d "$SCRIPT_DIR/data" ]; then
    echo "[!] Папка data/ не найдена рядом со скриптом."
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

echo "[*] Поиск Mewgenics..."

GAME_DIR=""

STEAM_DIRS=(
    "$HOME/.steam/steam/steamapps/common/Mewgenics"
    "$HOME/.local/share/Steam/steamapps/common/Mewgenics"
    "/home/deck/.steam/steam/steamapps/common/Mewgenics"
    "/home/deck/.local/share/Steam/steamapps/common/Mewgenics"
)

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

for dir in "${STEAM_DIRS[@]}"; do
    if [ -f "$dir/$EXE_NAME" ] || [ -f "$dir/resources.gpak" ]; then
        GAME_DIR="$dir"
        break
    fi
done

if [ -z "$GAME_DIR" ]; then
    echo "[!] Автоматически найти не удалось."
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

if [ ! -f "$GAME_DIR/$EXE_NAME" ] && [ ! -f "$GAME_DIR/resources.gpak" ]; then
    echo "[!] $EXE_NAME или resources.gpak не найден в $GAME_DIR"
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

echo "[+] Найдено: $GAME_DIR"
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

    if [ -d "$DST" ]; then
        echo "[*] Удаление старой папки $folder/..."
        rm -rf "$DST"
    fi

    echo "[*] Копирование $folder/ ($FILE_COUNT файлов)..."
    cp -r "$SRC" "$DST"
    echo "[+] $folder/ скопирована"
    INSTALLED=$((INSTALLED + 1))
done

if [ "$INSTALLED" -gt 0 ]; then
    echo
    echo "[+] Перевод установлен!"
    echo "    Запустите игру через Steam."
    echo "    Для удаления запустите ./uninstall_steamdeck.sh"
else
    echo "[!] Нечего устанавливать — папки data/ и swfs/ пусты или отсутствуют."
fi

echo
read -p "Нажмите Enter для выхода..."

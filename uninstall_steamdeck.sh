#!/bin/bash

set -e

FOLDERS_TO_REMOVE=("data" "swfs")
EXE_NAME="Mewgenics.x86_64"

echo "=================================================="
echo "  Mewgenics — Русский перевод (удаление)"
echo "  Steam Deck / Linux"
echo "=================================================="
echo

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

echo "[+] Найдено: $GAME_DIR"
echo

REMOVED=0
for folder in "${FOLDERS_TO_REMOVE[@]}"; do
    FOLDER_PATH="$GAME_DIR/$folder"
    if [ -d "$FOLDER_PATH" ]; then
        echo "[*] Удаление $folder/..."
        rm -rf "$FOLDER_PATH"
        echo "[+] $folder/ удалена"
        REMOVED=$((REMOVED + 1))
    fi
done

if [ "$REMOVED" -gt 0 ]; then
    echo
    echo "[+] Перевод удалён!"
    echo "    Игра использует оригинальные файлы из resources.gpak"
else
    echo "[!] Папки data/ и swfs/ не найдены. Перевод не установлен или уже удалён."
fi

echo
read -p "Нажмите Enter для выхода..."

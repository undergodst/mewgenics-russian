# Mewgenics — Русский перевод

Неофициальный русский перевод для [Mewgenics](https://store.steampowered.com/app/686060/Mewgenics/).

## Установка

### Windows

1. Скачайте [последний релиз](https://github.com/undergodst/mewgenics-russian/releases/latest)
2. Распакуйте архив
3. Запустите `install_ru.exe`
4. Установщик найдёт игру автоматически и скопирует `data/` и `swfs/`

### Steam Deck / Linux

1. Скачайте релиз и распакуйте
2. Откройте терминал в папке с файлами
3. Запустите:
   ```bash
   chmod +x install_steamdeck.sh
   ./install_steamdeck.sh
   ```

## Удаление

### Windows
Запустите `uninstall_ru.exe`

### Steam Deck / Linux
```bash
chmod +x uninstall_steamdeck.sh
./uninstall_steamdeck.sh
```

Или удалите папки `data/` и `swfs/` из папки с игрой вручную, или проверьте целостность файлов через Steam.

## После обновления игры

Steam может перезаписать файлы. Запустите установщик заново.

## Как это работает

Установщик копирует папки `data/` и `swfs/` в папку с игрой. Движок Glaiel Engine автоматически использует файлы из этих папок вместо оригинальных из `resources.gpak`.

## Сборка из исходников

См. [BUILD.md](BUILD.md)

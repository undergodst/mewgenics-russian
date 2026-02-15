# Сборка EXE через PyInstaller

## Требования

- Python 3.7+
- PyInstaller

## Установка PyInstaller

```bash
pip install pyinstaller
```

## Сборка

Откройте терминал в папке `mewgenics-russian/` и выполните:

```bash
# Установщик (включает папки data/ и swfs/ внутрь exe)
pyinstaller install.spec

# Деинсталлятор
pyinstaller uninstall.spec
```

Готовые файлы будут в `dist/`:
- `dist/install_ru.exe`
- `dist/uninstall_ru.exe`

## Альтернативный способ (без spec файла)

```bash
# Установщик
pyinstaller --onefile --console --name install_ru --add-data "data;data" --add-data "swfs;swfs" install.py

# Деинсталлятор
pyinstaller --onefile --console --name uninstall_ru uninstall.py
```

> На Windows разделитель в `--add-data` это `;`, на Linux — `:`.

## Структура релиза

```
mewgenics-ru/
├── install_ru.exe
├── uninstall_ru.exe
├── install_steamdeck.sh
├── uninstall_steamdeck.sh
├── data/
│   └── text/
│       └── [CSV файлы перевода]
├── swfs/
│   └── [SWF файлы]
└── README.md
```

> Папки `data/` и `swfs/` нужны рядом с exe только если собирать без spec файла.
> При сборке через spec файл они вшиваются внутрь exe.

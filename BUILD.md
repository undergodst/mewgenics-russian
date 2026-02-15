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
pyinstaller --onefile --console --uac-admin --name install_ru install.py

# Деинсталлятор
pyinstaller --onefile --console --uac-admin --name uninstall_ru uninstall.py
```

Разбор флагов:
`--onefile:` Собирает всё в один EXE-файл.

`--console:` Оставляет окно консоли для отображения процесса и ошибок.

`--uac-admin:` Добавляет запрос прав администратора (необходимо для работы с папками Steam).

> Примечание: Мы сознательно не вшиваем папки data/ и >swfs/ внутрь EXE, чтобы пользователь мог видеть >содержимое перевода и легко его обновлять.
> Папки `data/` и `swfs/` нужны рядом с exe для установки.

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

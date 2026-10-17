# depgraph

Инструмент визуализации графа зависимостей npm-пакетов. Зависимости получаются напрямую из репозитория, без менеджеров пакетов и сторонних библиотек.

Практическая работа 2, вариант 31. Реализован этап 1: CLI с настройкой параметров и проверкой ошибок.

## Параметры

Все параметры задаются опциями командной строки.

- --package - имя анализируемого пакета (обязательный)
- --repo - URL репозитория или путь к файлу тестового репозитория (обязательный)
- --test-mode - режим работы с тестовым репозиторием, --repo тогда путь к файлу
- --version - версия пакета в формате semver, например 4.18.2 (обязательный)

При запуске параметры выводятся в формате ключ-значение.

## Проверки и ошибки

При ошибке в stderr выводится сообщение вида "Ошибка: ..." и программа завершается с кодом 1.

- имя пакета: непустое, не длиннее 214 символов, корректное имя npm; в тестовом режиме только большие латинские буквы
- репозиторий: в обычном режиме URL со схемой http или https и хостом; в тестовом режиме существующий читаемый файл
- версия: формат X.Y.Z, допускаются суффиксы -prerelease и +build
- отсутствие обязательной или неизвестная опция: ошибка argparse с кодом 2

## Запуск

    make run ARGS="--package express --repo https://registry.npmjs.org --version 4.18.2"

## Тесты

    make test

## Примеры

    $ make run ARGS="--package express --repo https://registry.npmjs.org --version 4.18.2"
    package: express
    repo: https://registry.npmjs.org
    test_mode: False
    version: 4.18.2

    $ make run ARGS="--package A --repo tests/data/repo.txt --test-mode --version 1.0.0"
    package: A
    repo: tests/data/repo.txt
    test_mode: True
    version: 1.0.0

    $ make run ARGS="--package express --repo ftp://x.com --version 1.0.0"
    Ошибка: некорректный URL репозитория: ftp://x.com

    $ make run ARGS="--package express --repo https://registry.npmjs.org --version 1.0"
    Ошибка: некорректная версия пакета: 1.0

    $ make run ARGS="--package a --repo tests/data/repo.txt --test-mode --version 1.0.0"
    Ошибка: в тестовом режиме имя пакета - большие латинские буквы

    $ make run ARGS="--package A --repo nofile.txt --test-mode --version 1.0.0"
    Ошибка: файл тестового репозитория не найден: nofile.txt

# Асинхронный API для кинотеатра (2ая часть сервиса Admin Panel).

_Этот сервис будет точкой входа для всех клиентов. В первой итерации в сервисе будут только анонимные пользователи._

## Стек:

- FastAPI
- Elasticsearch
- Redis

## Styleguide:

- isort
- flake8
- flake8-blind-except
- flake8-bugbear
- flake8-builtins
- flake8-class-attributes-order
- flake8-cognitive-complexity
- flake8-commas
- flake8-comprehensions
- flake8-debugger
- flake8-functions
- flake8-isort
- flake8-mutable
- flake8-print
- flake8-pytest
- flake8-pytest-style
- flake8-quotes
- flake8-string-format
- flake8-variables-names

## Пакетный менеджер:

- Poetry

## Установка

Перед началом установки убедитесь, что у вас установлен Python 3.11 и Poetry (пакетный менеджер для Python).

1. Склонируйте репозиторий:

`git clone https://github.com/192117/AsyncApiProject.git`

2. Перейдите в директорию:

`cd AsyncApiProject`

## Запуск приложения c использованием Docker Compose (после пункта "Установка")

1. Создайте переменные окружения:

_Создайте файл .env.docker (в src/core) на основе .env.example для запуска с Docker. Файл содержит 
переменные окружения, которые требуются для настройки приложения._

2. Данный сервис запускается после [admin_panel](https://github.com/192117/admin_panel) и объединяется в одну сеть 
с admin_panel.

3. Запустите сборку docker-compose:

`docker compose up -d --build`

4. Доступ к документации: 

[Документация Swagger](http://127.0.0.1:8888/api/openapi/)


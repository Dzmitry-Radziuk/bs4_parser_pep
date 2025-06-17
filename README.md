# 🐍 Python Documentation Parser

Парсер официальной документации Python с возможностью анализа PEP, получения новостей о версиях и загрузки PDF-документации.

---

## 🚀 Быстрый старт

### Клонируйте репозиторий:
```sh
git clone https://github.com/Dzmitry-Radziuk/bs4_parser_pep.git
cd bs4_parser_pep
```

### Создайте и активируйте виртуальное окружение:
```sh
# Linux/macOS
python3 -m venv venv
source venv/bin/activate
# Windows (PowerShell)
python -m venv venv
source venv\Scripts\Activate
```

### Установите зависимости:
```sh
pip install -r requirements.txt
```

## 🛠 Использование:
Запуск основного скрипта с выбором режима
```sh
python main.py --mode <mode> [--clear-cache]
```

## Доступные режимы:

| Режим             | Описание                                   |
| ----------------- | ------------------------------------------ |
| `pep`             | Парсинг PEP и подсчет статусов             |
| `whats-new`       | Получение новостей из раздела "What's New" |
| `latest-versions` | Список последних версий Python             |
| `download`        | Загрузка PDF архива документации           |

## Пример запуска:
```sh
python main.py --mode pep
```

## Очистка кэша (опционально):
```sh
python main.py --mode pep --clear-cache
```

### ⚙️ Конфигурация и логирование:

* Логирование настраивается автоматически при запуске.
* HTTP-сессии с ретраями и кэшированием для устойчивой работы.
* Все результаты выводятся или сохраняются согласно аргументам.

## 📦 Зависимости:

* Python 3.8+
* requests
* requests-cache
* beautifulsoup4
* tqdm
* lxml

Установить все сразу:
```sh
pip install -r requirements.txt
```

## 📞 Обратная связь:

Автор: Дмитрий Радюк
Email: mitia.radiuk@yandex.ru

## 📜 Лицензия:

MIT License
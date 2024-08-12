# Бот-асситент.

## Описание:
Бот-асситент для отслеживания статуса сданных на проверку работ в Яндекс Практикум. Бот раз в 10 минут опрашивает API сервиса Практикум.Домашка и проверяет статус отправленной на ревью домашней работы. При обновлении статуса анализирует ответ API и отправляет соответствующее уведомление в Telegram. В боте настроено логгирование работы и основных ошибок.

## Использованные технологии:
Python 3.9.  
python-telegram-bot==13.7

## Как запустить проект:

1. Клонировать репозиторий и перейти в него в командной строке.
```
git clone https://github.com/Emphori-a/bot_assistant
```
```
cd bot_assistant
```

2. Cоздать и активировать виртуальное окружение.
- Если у вас Linux/macOS:
```
python3 -m venv venv
```
```
source venv/bin/activate
```
- Если у вас Windows:
```
python -m venv venv
```
```
source venv/Scripts/activate
```

3. Установить зависимости.
```
python -m pip install --upgrade pip  # обновляем установщик пакетов pip
```
```
pip install -r requirements.txt
```

4. Создать файл ".env" наполнить его данными. Для примера в корне проекта есть файл .env.example.

5. Запуск бота.
```
python homework.py
```

## Автор проекта, контактная информация.
Мартынова Валерия
- https://github.com/Emphori-a
- e-mail: v.e.martynova@yandex.ru
- Telegram: @Emphori
# KOD OS 1.5

KOD OS 1.5 — это веб-приложение в стиле ретро-терминала, построенное на Django, которое объединяет файловый менеджер с множеством дополнительных функций. Проект имитирует работу старых терминалов и включает в себя следующие возможности:

- **Файловый менеджер**: Просмотр, создание, редактирование, удаление и перемещение файлов и папок(реализовано только создание папок) с использованием дерева файлов.
- **Ограничения доступа**: Настраиваемые права доступа и ограничения на редактирование, удаление и перемещение файлов через конфигурационный файл.
- **Просмотр файлов**: Динамическая анимация "печатной машинки" для вывода содержимого файлов, с поддержкой рендеринга изображений, если в тексте присутствуют URL.
- **Интегрированные мини-игры**: Встроенные игры (Snake, Pong) запускаются при открытии файлов с определёнными именами.
- **ASCII-анимация**: Отображение ASCII-анимации в правом верхнем углу, создающее атмосферу старых компьютеров. (Может работать некорректно, добавляется через ascii_animation.json)
- **Логирование событий**: Все операции (открытие, создание, редактирование, удаление, перемещение) логируются с учетом настроек времени и корректировок.
- **Перемещение файлов без перезагрузки**: Файлы можно перемещать по дереву через AJAX-запросы, без необходимости вводить полный путь вручную.

## Функциональные возможности

- **Аутентификация пользователей**: Вход в систему осуществляется через форму логина с учётными данными, заданными в конфигурационном файле.
- **Файловый менеджер**: Древовидное представление файлов и папок, с поддержкой раскрытия/сворачивания узлов.
- **Редактирование файлов**: Возможность редактировать файлы через встроенный редактор с терминальным оформлением.
- **Обработка изображений**: В тексте файла ссылки на изображения преобразуются в теги `<img>` и корректно отображаются.
- **Ограничения**: Функционал редактирования, удаления и перемещения файлов зависит от настроек, указанных в `config.ini` (например, список `restricted_files`).
- **Мини-игры**: Запуск мини-игр (Snake, Pong, Hacking) при открытии соответствующих файлов.
- **Звуковые эффекты и анимации**: Звуки при выборе элементов, а также эффекты печатной машинки и ASCII-анимация для создания уникальной атмосферы.

## Требования

- **Python 3.x**
- **Django 2.2+**

## Пример конфиг файла

```
[credentials]
login1 = password
login2 = password

[access_levels]
admin = 3
user = 1

[restrictions]
restricted_files = logs.txt, pong, pong.txt, snake, snake.txt, div, div.txt
restricted_folders = C:, D:, External Drive:, Logs

[folder_visibility]
superadmin = your_superadmin_login
```

## Структура проекта
```
kodod/
├── config.ini
├── manage.py
├── requirements.txt
├── hidden_folders.json
├── KOD OS 1.5/
│   ├── ... (файлы и папки для рп процесса - что будут видеть игроки)
├── main/
│   ├── views.py
│   ├── urls.py
│   └── templates/
│       └── main/
│           ├── base.html
│           ├── file_manager.html
│           ├── file_tree.html
│           ├── file_view.html
│           ├── edit_file.html
│           ├── snake.html
│           ├── pong.html
│           └── hacking.html
└── static/
    ├── images/
    │   ├── file_add.png
    │   ├── folder_add.png
    │   ├── file_delete.png
    │   ├── folder_delete.png
    │   ├── move_file.png
    │   └── move_dest.png
    ├── js/
    │   ├── move_file.js
    │   └── ascii.js
    └── json/
        ├── minigame_settings.json
        ├── hacking_words.json
        └── ascii_animation.json
```

## Важные замечания

В коде реализованы 3 мини игры для создания ощущуения настоящего компьютера
- snake
- pong
- div
Для запуска данных приложений - достаточно в рп папке компьютера создать файл с соответствующим названием. Наполнять его каким-либо текстом не требуется.
### Уточнение
- div - является РП разработкой и требует вложения игроков для отображения 

import os
import json
import configparser
import datetime
import random
import codecs
import re
import html
from urllib.parse import urlencode, unquote
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .decorators import rate_limit

# Базовая директория проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Папка с файлами (например, "KOD OS 1.5")
FILES_FOLDER = os.path.join(BASE_DIR, "KOD OS 1.5")
# Папка для логов (согласно вашим настройкам)
LOG_DIR = os.path.join(BASE_DIR, "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Файл для хранения скрытых папок (относительных путей относительно FILES_FOLDER)
HIDDEN_FOLDERS_FILE = os.path.join(BASE_DIR, "hidden_folders.json")
if not os.path.exists(HIDDEN_FOLDERS_FILE):
    with open(HIDDEN_FOLDERS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

# ---------------------- Чтение конфигураций ----------------------

def read_credentials():
    config = configparser.ConfigParser()
    config_path = os.path.join(BASE_DIR, "config.ini")
    config.read(config_path)
    if config.has_section("accounts"):
        return dict(config.items("accounts"))
    else:
        login_value = config.get("credentials", "login", fallback="admin")
        password_value = config.get("credentials", "password", fallback="secret")
        return {login_value: password_value}

def read_access_levels():
    config = configparser.ConfigParser()
    config_path = os.path.join(BASE_DIR, "config.ini")
    config.read(config_path)
    levels = {}
    if config.has_section("access_levels"):
        for user, level in config.items("access_levels"):
            try:
                levels[user.strip()] = int(level.strip())
            except ValueError:
                levels[user.strip()] = 1
    return levels

def read_restrictions():
    config = configparser.ConfigParser()
    config_path = os.path.join(BASE_DIR, "config.ini")
    config.read(config_path)
    restricted_files = set()
    restricted_folders = set()
    if config.has_section("restrictions"):
        if config.has_option("restrictions", "restricted_files"):
            files_str = config.get("restrictions", "restricted_files")
            restricted_files = set(x.strip().lower() for x in files_str.split(",") if x.strip())
        if config.has_option("restrictions", "restricted_folders"):
            folders_str = config.get("restrictions", "restricted_folders")
            restricted_folders = set(x.strip().upper() for x in folders_str.split(",") if x.strip())
    return restricted_files, restricted_folders

def read_folder_visibility_config():
    """Возвращает логин суперадмина из секции [folder_visibility]."""
    config = configparser.ConfigParser()
    config_path = os.path.join(BASE_DIR, "config.ini")
    config.read(config_path)
    superadmin = None
    if config.has_section("folder_visibility") and config.has_option("folder_visibility", "superadmin"):
        superadmin = config.get("folder_visibility", "superadmin").strip()
    return superadmin

def read_hidden_folders():
    try:
        with open(HIDDEN_FOLDERS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()

def write_hidden_folders(hidden_set):
    try:
        with open(HIDDEN_FOLDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(hidden_set), f)
    except Exception as e:
        print("Error writing hidden folders:", e)

def get_adjusted_time():
    now = datetime.datetime.now()
    try:
        adjusted = now.replace(year=now.year - 12)
    except ValueError:
        adjusted = now - datetime.timedelta(days=365 * 12)
    return adjusted.strftime("%Y-%m-%d %H:%M:%S")

def log_event(event_type, message):
    log_file = os.path.join(LOG_DIR, "logs.txt")
    timestamp = get_adjusted_time()
    log_message = f"[{timestamp}] {event_type}: {message}\n"
    try:
        decoded = codecs.decode(log_message, 'unicode_escape')
    except Exception:
        decoded = log_message
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(decoded)
    except Exception as e:
        print("Log write error:", e)

def get_user_groups(user):
    """
    Возвращает список групп, в которые входит пользователь.
    Читает секцию [groups] из config.ini.
    Например, если пользователь test встречается в группах science и mercs,
    возвращается список ["science", "mercs"].
    """
    config = configparser.ConfigParser()
    config_path = os.path.join(BASE_DIR, "config.ini")
    config.read(config_path)
    groups = []
    if config.has_section("groups"):
        for group in config.options("groups"):
            users_str = config.get("groups", group)
            users = [u.strip() for u in users_str.split(",") if u.strip()]
            if user in users:
                groups.append(group)
    return groups

def get_group_folders(user_group):
    """
    Для заданной группы возвращает список разрешённых корневых папок,
    указанных в секции [group_folders] конфигурационного файла.
    Если группа не задана или не найдена, возвращается пустой список.
    Например, для группы clear_sky может вернуться ["Clear_sky", "Science"].
    """
    config = configparser.ConfigParser()
    config_path = os.path.join(BASE_DIR, "config.ini")
    config.read(config_path)
    if user_group and config.has_section("group_folders") and config.has_option("group_folders", user_group):
        folders_str = config.get("group_folders", user_group)
        return [f.strip() for f in folders_str.split(",") if f.strip()]
    return []

# ---------------------- Представления ----------------------

@rate_limit('login', max_attempts=5, timeout=300)  # 5 attempts per 5 minutes
def login_view(request):
    credentials = read_credentials()
    if request.method == "POST":
        login_input = request.POST.get("login", "")
        password_input = request.POST.get("password", "")
        
        # First check credentials without setting session
        if login_input in credentials and password_input == credentials[login_input]:
            # Only set session after successful authentication
            request.session['logged_in'] = True
            request.session['login'] = login_input
            # Now save the list of groups for the user
            groups = get_user_groups(login_input)
            request.session['login_groups'] = groups if groups else ["default"]
            log_event("SUCCESS", f"login='{login_input}'")
            return redirect("file_manager")
        else:
            log_event("FAILED", f"login='{login_input}'")
            return render(request, "main/login.html", {"error": "Неверные учетные данные"})
    return render(request, "main/login.html")

def build_file_tree(path, current_user=None):
    """
    Рекурсивно строит дерево файлов и папок из указанного пути.
    Сортирует элементы: сначала папки, затем файлы, оба списка по алфавиту.
    Если текущий пользователь не является суперадмином, скрытые папки (из hidden_folders.json) исключаются.
    Если текущий пользователь – суперадмин, то каждому узлу-папке добавляется флаг "is_hidden"
    для изменения цвета отображения.
    """
    hidden = read_hidden_folders()  # набор скрытых папок (относительные пути)
    superadmin = read_folder_visibility_config()  # логин суперадмина
    tree = []
    try:
        items = os.listdir(path)
        items.sort(key=lambda x: (0 if os.path.isdir(os.path.join(path, x)) else 1, x.lower()))
        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                rel_path = os.path.relpath(full_path, FILES_FOLDER)
                if current_user != superadmin and rel_path in hidden:
                    continue  # обычные пользователи не видят скрытые папки
                node = {
                    "name": item,
                    "type": "dir",
                    "full_path": full_path,
                    "children": build_file_tree(full_path, current_user)
                }
                if current_user == superadmin:
                    node["is_hidden"] = rel_path in hidden
                tree.append(node)
            else:
                tree.append({
                    "name": item,
                    "type": "file",
                    "path": full_path
                })
    except Exception as e:
        print("Ошибка при построении дерева:", e)
    return tree

def file_manager(request):
    if not request.session.get("logged_in"):
        return redirect("login")
    current_user = request.session.get("login", "unknown")
    superadmin = read_folder_visibility_config()  # Например, "admin"
    # Если пользователь является суперадмином, показываем все файлы.
    if current_user == superadmin:
        folder_path = FILES_FOLDER
        tree = build_file_tree(folder_path, current_user)
    else:
        # Получаем список групп, к которым принадлежит пользователь.
        user_groups = get_user_groups(current_user)
        if not user_groups:
            error = "Вам не назначена группа доступа — файлы не отображаются."
            return render(request, "main/file_manager.html", {
                "tree": [],
                "error": error,
                "current_user": current_user,
                "superadmin": superadmin,
                "access_level": read_access_levels().get(current_user, 1),
            })
        # Для каждой группы получаем список разрешённых папок и объединяем их
        allowed_folders = []
        for group in user_groups:
            allowed_folders.extend(get_group_folders(group))
        # Если есть хотя бы одна разрешённая папка, строим дерево файлов для каждой из них и объединяем
        if allowed_folders:
            tree = []
            for folder_name in allowed_folders:
                folder_path_candidate = os.path.join(FILES_FOLDER, folder_name)
                tree.extend(build_file_tree(folder_path_candidate, current_user))
            # При необходимости можно отсортировать объединённое дерево:
            tree.sort(key=lambda node: node["name"].lower())
        else:
            tree = build_file_tree(FILES_FOLDER, current_user)
    # Определяем фон: используем фон для первой группы пользователя (вы можете изменить логику выбора)
    user_groups = get_user_groups(current_user)
    if user_groups:
        background = "images/background_" + user_groups[0] + ".gif"
    else:
        background = "images/background_default.gif"
    error = request.GET.get("error", "")
    access_levels = read_access_levels()
    user_level = access_levels.get(current_user, 1)
    return render(request, "main/file_manager.html", {
        "tree": tree,
        "error": error,
        "current_user": current_user,
        "superadmin": superadmin,
        "access_level": user_level,
        "background_path": background,
    })

def file_view(request):
    if not request.session.get("logged_in"):
        return redirect("login")
    file_path = request.GET.get("file")
    if not file_path:
        return HttpResponse("Файл не указан")

    abs_file_path = os.path.abspath(file_path)
    abs_files_folder = os.path.abspath(FILES_FOLDER)
    if not abs_file_path.startswith(abs_files_folder):
        return HttpResponse("Доступ запрещён")

    filename = os.path.basename(file_path)
    current_user = request.session.get("login", "unknown")
    superadmin = read_folder_visibility_config()  # Значение из [folder_visibility], например, "admin"
    # Получаем список групп пользователя
    user_groups = get_user_groups(current_user)
    user_group = user_groups[0] if user_groups else None

    # Если пользователь не суперадмин, применяем групповые ограничения
    if current_user != superadmin:
        if user_group is None:
            return HttpResponse("Доступ запрещён")
        allowed_folders = get_group_folders(user_group)  # возвращает список, например, ["Clear_sky", "Science"]
        if allowed_folders:
            allowed = False
            for folder_name in allowed_folders:
                allowed_folder = os.path.join(FILES_FOLDER, folder_name)
                abs_allowed_folder = os.path.abspath(allowed_folder)
                if abs_file_path.startswith(abs_allowed_folder):
                    allowed = True
                    break
            if not allowed:
                return HttpResponse("Доступ запрещён")
    if user_group:
        background = "images/background_" + user_group + ".gif"
    else:
        background = "images/background_default.gif"

    # Обработка разных мини-игр по имени файла
    lower_filename = filename.lower()
    if lower_filename in ("snake", "snake.txt"):
        return render(request, "main/snake.html", {"background_path": background})
    elif lower_filename in ("pong", "pong.txt"):
        return render(request, "main/pong.html", {"background_path": background})
    elif lower_filename in ("div", "div.txt"):
        return render(request, "main/hacking.html", {"background_path": background})
    elif lower_filename in ("blackjack", "blackjack.txt"):
        return render(request, "main/blackjack.html", {"background_path": background})

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        content = "Ошибка при открытии файла: " + str(e)

    if not content.strip():
        error_code = random.randint(1000, 9999)
        content = f"Ошибка {error_code}: Файл пустой или поврежден."

    log_event("OPENED", f"user='{current_user}', file='{filename}'")
    return render(request, "main/file_view.html", {
        "content": content,
        "file": file_path,
        "filename": filename,
        "background_path": background,
        "access_level": read_access_levels().get(current_user, 1),
    })

def process_file_content(content):
    pattern = r'(https?://[^\s]+\.(?:jpg|jpeg|png|gif)(?:\?[^\s]+)?)(?=$|\s|[\'"<>])'
    def repl(match):
        url = match.group(1)
        safe_url = url.replace("&", "&amp;")
        return f'<img src="{safe_url}" alt="Image" style="max-width:100%; margin:5px 0;">'
    processed = re.sub(pattern, repl, content, flags=re.IGNORECASE)
    return mark_safe(processed)

def create_file(request):
    if not request.session.get("logged_in"):
        return redirect("login")
    folder = request.GET.get("folder")
    if not folder:
        return HttpResponseBadRequest("Папка не указана")
    abs_folder = os.path.abspath(folder)
    if not abs_folder.startswith(os.path.abspath(FILES_FOLDER)) or not os.path.isdir(abs_folder):
        return HttpResponse("Доступ запрещён или папка не найдена")
    access = read_access_levels()
    user = request.session.get("login", "unknown")
    if access.get(user, 1) < 2:
        return redirect(f"/file-manager/?{urlencode({'error':'Нет прав на создание файлов.'})}")
    _, restricted = read_restrictions()
    folder_name = os.path.basename(abs_folder).strip().upper()
    if folder_name in restricted:
        return redirect(f"/file-manager/?{urlencode({'error':'Нельзя создавать файлы в корневой папке этого диска.'})}")
    if request.method == "POST":
        filename = request.POST.get("filename", "").strip()
        content = request.POST.get("content", "")
        if not filename:
            return redirect(f"/file-manager/?{urlencode({'error':'Укажите название файла.'})}")
        if not filename.lower().endswith(".txt"):
            filename += ".txt"
        file_path = os.path.join(folder, filename)
        if os.path.exists(file_path):
            return redirect(f"/file-manager/?{urlencode({'error':'Файл уже существует.'})}")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            log_event("CREATED", f"user='{user}', file='{filename}'")
            return redirect(f"/file-view/?file={file_path}")
        except Exception as e:
            return redirect(f"/file-manager/?{urlencode({'error':'Ошибка создания файла: ' + str(e)})}")
    return render(request, "main/create_file.html", {"folder": folder})

def edit_file(request):
    if not request.session.get("logged_in"):
        return redirect("login")
    file_path = request.GET.get("file")
    if not file_path:
        return HttpResponseBadRequest("Файл не указан")
    abs_fp = os.path.abspath(file_path)
    if not abs_fp.startswith(os.path.abspath(FILES_FOLDER)):
        return HttpResponse("Доступ запрещён")
    filename = os.path.basename(file_path).strip().lower()
    restricted_files, _ = read_restrictions()
    if filename in restricted_files:
        return HttpResponse("Редактирование этого файла запрещено.")
    current_user = request.session.get("login", "unknown")
    user_group = get_user_groups(current_user)[0] if get_user_groups(current_user) else None
    if user_group:
        background = "images/background_"+user_group+".gif"
    else:
        background = "images/background_default.gif"
    if request.method == "POST":
        new_content = request.POST.get("content", "").rstrip()  # Remove trailing whitespace
        try:
            with open(file_path, "w", encoding="utf-8", newline='') as f:  # Use newline='' to prevent extra line endings
                f.write(new_content)
            log_event("EDITED", f"user='{request.session.get('login', 'unknown')}', file='{filename}'")
            return redirect(f"/file-view/?file={file_path}")
        except Exception as e:
            return HttpResponse("Ошибка сохранения файла: " + str(e))
    else:
        try:
            with open(file_path, "r", encoding="utf-8", newline='') as f:  # Use newline='' when reading too
                content = f.read().rstrip()  # Remove trailing whitespace when reading
        except Exception as e:
            content = "Ошибка открытия файла: " + str(e)
        return render(request, "main/edit_file.html", {
            "file": file_path,
            "filename": filename,
            "content": content,
            "background_path": background,
        })

def create_folder(request):
    if not request.session.get("logged_in"):
        return redirect("login")
    folder = request.GET.get("folder")
    if not folder:
        return HttpResponseBadRequest("Папка не указана")
    abs_folder = os.path.abspath(folder)
    if not abs_folder.startswith(os.path.abspath(FILES_FOLDER)) or not os.path.isdir(abs_folder):
        return HttpResponse("Доступ запрещён или папка не найдена")
    access = read_access_levels()
    user = request.session.get("login", "unknown")
    if access.get(user, 1) < 2:
        return redirect(f"/file-manager/?{urlencode({'error':'Нет прав на создание папок.'})}")
    if request.method == "POST":
        folder_name = request.POST.get("folder_name", "").strip()
        if not folder_name:
            return render(request, "main/create_folder.html", {"error": "Укажите название папки.", "folder": folder})
        new_folder_path = os.path.join(folder, folder_name)
        if os.path.exists(new_folder_path):
            return render(request, "main/create_folder.html", {"error": "Папка с таким названием уже существует.", "folder": folder})
        try:
            os.makedirs(new_folder_path)
            log_event("CREATED_FOLDER", f"user='{user}', folder='{folder_name}'")
            return redirect("file_manager")
        except Exception as e:
            return render(request, "main/create_folder.html", {"error": "Ошибка создания папки: " + str(e), "folder": folder})
    return render(request, "main/create_folder.html", {"folder": folder})

def toggle_folder_visibility(request):
    if not request.session.get("logged_in"):
        return redirect("login")
    folder = request.GET.get("folder")
    if not folder:
        return HttpResponseBadRequest("Папка не указана")
    abs_folder = os.path.abspath(folder)
    abs_files_folder = os.path.abspath(FILES_FOLDER)
    if not abs_folder.startswith(abs_files_folder) or not os.path.isdir(abs_folder):
        return HttpResponse("Доступ запрещён или папка не найдена")
    superadmin = read_folder_visibility_config()
    user = request.session.get("login", "unknown")
    if user != superadmin:
        return HttpResponse("Нет прав для изменения видимости папок.")
    rel_path = os.path.relpath(abs_folder, FILES_FOLDER)
    hidden = read_hidden_folders()
    if rel_path in hidden:
        hidden.remove(rel_path)
    else:
        hidden.add(rel_path)
    write_hidden_folders(hidden)
    return redirect("file_manager")

def delete_file(request):
    if not request.session.get("logged_in"):
        return redirect("login")
    file_path = request.GET.get("file")
    if not file_path:
        return HttpResponseBadRequest("Файл не указан")
    abs_fp = os.path.abspath(file_path)
    if not abs_fp.startswith(os.path.abspath(FILES_FOLDER)):
        return HttpResponse("Доступ запрещён")
    if not os.path.exists(file_path) or os.path.isdir(file_path):
        return HttpResponse("Файл не найден или это папка")
    filename = os.path.basename(file_path).strip().lower()
    restricted_files, _ = read_restrictions()
    if filename in restricted_files:
        error_message = "Удаление этого файла запрещено."
        tree = build_file_tree(FILES_FOLDER, request.session.get("login", "unknown"))
        return render(request, "main/file_manager.html", {"tree": tree, "error": error_message})
    access = read_access_levels()
    user = request.session.get("login", "unknown")
    if access.get(user, 1) < 3:
        error_message = "У вас нет прав на удаление файлов."
        tree = build_file_tree(FILES_FOLDER, user)
        return render(request, "main/file_manager.html", {"tree": tree, "error": error_message})
    try:
        os.remove(file_path)
        log_event("DELETED", f"user='{user}', file='{os.path.basename(file_path)}'")
    except Exception as e:
        error_message = "Ошибка удаления файла: " + str(e)
        tree = build_file_tree(FILES_FOLDER, user)
        return render(request, "main/file_manager.html", {"tree": tree, "error": error_message})
    return redirect("file_manager")

def move_file(request):
    if not request.session.get("logged_in"):
        return redirect("login")
    access_levels = read_access_levels()
    user = request.session.get("login", "unknown")
    if access_levels.get(user, 1) < 2:
        error_msg = "У вас нет прав на перемещение файлов."
        return redirect(f"/file-manager/?{urlencode({'error': error_msg})}")
    source_file = request.GET.get("file")
    if not source_file:
        return HttpResponseBadRequest("Исходный файл не указан")
    abs_source = os.path.abspath(source_file)
    if not abs_source.startswith(os.path.abspath(FILES_FOLDER)):
        return HttpResponse("Доступ запрещён")
    if not os.path.exists(source_file) or os.path.isdir(source_file):
        return HttpResponse("Исходный файл не найден или это папка")
    if request.method == "GET":
        return render(request, "main/move_file.html", {"file": source_file})
    elif request.method == "POST":
        destination = request.POST.get("destination", "").strip()
        if not destination:
            error_msg = "Укажите целевую папку."
            return render(request, "main/move_file.html", {"error": error_msg, "file": source_file})
        abs_destination = os.path.abspath(destination)
        if not abs_destination.startswith(os.path.abspath(FILES_FOLDER)) or not os.path.isdir(abs_destination):
            error_msg = "Целевая папка не найдена или доступ запрещён."
            return render(request, "main/move_file.html", {"error": error_msg, "file": source_file})
        filename = os.path.basename(source_file)
        target_file = os.path.join(destination, filename)
        if os.path.exists(target_file):
            error_msg = "В целевой папке уже существует файл с таким названием."
            return render(request, "main/move_file.html", {"error": error_msg, "file": source_file})
        try:
            os.rename(source_file, target_file)
            log_event("MOVED", f"user='{user}', file='{filename}', from='{source_file}', to='{target_file}'")
            return redirect("file_manager")
        except Exception as e:
            error_msg = "Ошибка перемещения файла: " + str(e)
            return render(request, "main/move_file.html", {"error": error_msg, "file": source_file})
@csrf_exempt
def move_file_ajax(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            file_path = unquote(data.get("file"))
            dest_folder = unquote(data.get("folder"))
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ALLOWED_FOLDER = os.path.join(BASE_DIR, "KOD OS 1.5")
            abs_file_path = os.path.abspath(file_path)
            abs_dest_folder = os.path.abspath(dest_folder)
            if not abs_file_path.startswith(ALLOWED_FOLDER) or not abs_dest_folder.startswith(ALLOWED_FOLDER):
                return JsonResponse({"success": False, "error": "Доступ запрещён."})
            restricted_files, _ = read_restrictions()
            filename = os.path.basename(file_path).strip().lower()
            if filename in restricted_files:
                return JsonResponse({"success": False, "error": "Перемещение этого файла запрещено."})
            target_path = os.path.join(dest_folder, filename)
            if not os.path.exists(abs_file_path):
                return JsonResponse({"success": True})
            os.rename(file_path, target_path)
            log_event("MOVED", f"user='{request.session.get('login', 'unknown')}', file='{filename}', from='{file_path}', to='{target_path}'")
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Неверный метод запроса."})

def delete_folder(request):
    if not request.session.get("logged_in"):
        return redirect("login")
    folder = request.GET.get("folder")
    if not folder:
        return HttpResponseBadRequest("Папка не указана")
    abs_folder = os.path.abspath(folder)
    abs_files_folder = os.path.abspath(FILES_FOLDER)
    if not abs_folder.startswith(abs_files_folder):
        return HttpResponse("Доступ запрещён")
    if not os.path.exists(folder) or not os.path.isdir(folder):
        return HttpResponse("Папка не найдена")
    _, restricted_folders = read_restrictions()
    folder_name = os.path.basename(abs_folder).strip().upper()
    if folder_name in restricted_folders:
        return HttpResponse("Удаление этой папки запрещено.")
    access = read_access_levels()
    user = request.session.get("login", "unknown")
    if access.get(user, 1) < 3:
        error_message = "У вас нет прав на удаление папок."
        tree = build_file_tree(FILES_FOLDER, user)
        return render(request, "main/file_manager.html", {"tree": tree, "error": error_message})
    if os.listdir(folder):
        return HttpResponse("Папка не пустая, удаление запрещено.")
    try:
        os.rmdir(folder)
        log_event("DELETED_FOLDER", f"user='{user}', folder='{os.path.basename(folder)}'")
        return redirect("file_manager")
    except Exception as e:
        error_message = "Ошибка удаления папки: " + str(e)
        tree = build_file_tree(FILES_FOLDER, user)
        return render(request, "main/file_manager.html", {"tree": tree, "error": error_message})

def snake_game(request):
    if not request.session.get("logged_in"):
        return redirect("login")
    return render(request, "main/snake.html")

def pong_game(request):
    if not request.session.get("logged_in"):
        return redirect("login")
    return render(request, "main/pong.html")

def hacking_game(request):
    if not request.session.get("logged_in"):
        return redirect("login")
    return render(request, "main/hacking.html")

def blackjack_game(request):
    if not request.session.get("logged_in"):
        return redirect("login")
    return render(request, "main/blackjack.html")

def get_glitch_state(request):
    """
    Возвращает состояние глич-эффекта из файла glitch_state.json.
    Если файл не найден или возникла ошибка, возвращает {"glitch_toggle": false}.
    """
    glitch_state_file = os.path.join(BASE_DIR, "glitch_state.json")
    try:
        with open(glitch_state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception:
        state = {"glitch_toggle": False}
    return JsonResponse(state)

@csrf_exempt
def update_glitch_state(request):
    """
    Обновляет состояние глич-эффекта.
    Ожидает POST-запрос с JSON: {"glitch_toggle": true/false}
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            glitch_state_file = os.path.join(BASE_DIR, "glitch_state.json")
            with open(glitch_state_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Неверный метод запроса."})

def custom_404(request, exception):
    return render(request, "main/404.html", status=404)
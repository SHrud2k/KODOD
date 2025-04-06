import os
import django
import json
from django.test.utils import override_settings
from main import views
from main.views import get_group_folder, BASE_DIR
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch

# Настройка переменной окружения и загрузка настроек Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
django.setup()

# Отключаем проверки админки, которые не используются в проекте.
SILENCED_CHECKS = ["admin.E402", "admin.E404", "admin.E408", "admin.E409"]


@override_settings(SILENCED_SYSTEM_CHECKS=SILENCED_CHECKS)
class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Тестовые учетные данные, возвращаемые функцией read_credentials
        self.test_credentials = {"testuser": "testpass"}

    @patch("main.views.log_event")
    @patch("main.views.get_user_group")
    @patch("main.views.read_credentials")
    def test_login_success(self, mock_read_credentials, mock_get_user_group, mock_log_event):
        # Подменяем функции, чтобы вернуть тестовые данные
        mock_read_credentials.return_value = self.test_credentials
        mock_get_user_group.return_value = "group1"

        # Отправляем POST-запрос с корректными данными
        data = {"login": "testuser", "password": "testpass"}
        response = self.client.post(reverse("login"), data)

        # Проверяем, что произошёл редирект на файловый менеджер
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("file_manager"))

        # Проверяем, что в сессии установлены нужные переменные
        session = self.client.session
        self.assertTrue(session.get("logged_in"))
        self.assertEqual(session.get("login"), "testuser")
        self.assertEqual(session.get("login_group"), "group1")

        # Проверяем, что log_event вызвана с успехом
        mock_log_event.assert_called_with("SUCCESS", "login='testuser'")

    @patch("main.views.log_event")
    @patch("main.views.read_credentials")
    def test_login_failure(self, mock_read_credentials, mock_log_event):
        mock_read_credentials.return_value = self.test_credentials

        # Отправляем POST-запрос с неверными данными
        data = {"login": "wronguser", "password": "wrongpass"}
        response = self.client.post(reverse("login"), data)

        # Ожидаем, что страница логина рендерится снова с сообщением об ошибке (код 200)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Неверные учетные данные", response.content.decode())

        # Сессия не должна содержать переменной logged_in
        session = self.client.session
        self.assertFalse(session.get("logged_in", False))

        # Проверяем, что log_event вызвана с ошибкой
        mock_log_event.assert_called_with("FAILED", "login='wronguser'")


@override_settings(SILENCED_SYSTEM_CHECKS=SILENCED_CHECKS)
class BasicPagesTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Если страницы мини-игр требуют авторизации, эмулируем её установкой сессионных переменных.
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "testuser"
        session["login_group"] = "group1"
        session.save()

    def test_homepage_loads(self):
        """
        Проверяем загрузку главной страницы.
        Ожидаем статус 200 и наличие ключевого слова "KOD OS".
        """
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("KOD OS", response.content.decode())

    def test_blackjack_page_loads(self):
        """
        Проверяем загрузку страницы игры блэкджек.
        """
        response = self.client.get(reverse("blackjack_game"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Blackjack Game", response.content.decode())

    def test_pong_page_loads(self):
        response = self.client.get(reverse("pong_game"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Pong", response.content.decode())

    def test_snake_page_loads(self):
        response = self.client.get(reverse("snake_game"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Snake", response.content.decode())

    def test_hacking_page_loads(self):
        response = self.client.get(reverse("hacking_game"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Hacking", response.content.decode())


@override_settings(SILENCED_SYSTEM_CHECKS=SILENCED_CHECKS)
class FileManagerTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Эмулируем авторизованного пользователя через установку сессионных переменных.
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "testuser"
        session["login_group"] = "group1"
        session.save()

    def test_file_manager_access(self):
        """
        Проверяем, что авторизованный пользователь получает доступ к файловому менеджеру.
        """
        response = self.client.get(reverse("file_manager"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Файловый менеджер", response.content.decode())


class DeleteFolderTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Эмулируем авторизованного пользователя
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "testuser"
        session["login_group"] = "group1"
        session.save()
        # Тестовый путь папки и FILES_FOLDER
        self.test_folder = "/allowed/test_folder"
        self.files_folder = "/allowed"
        views.FILES_FOLDER = self.files_folder

    def test_not_logged_in(self):
        """Если пользователь не залогинен, должно быть перенаправление на login."""
        session = self.client.session
        session.pop("logged_in", None)
        session.save()
        response = self.client.get(reverse("delete_folder") + "?folder=" + self.test_folder)
        # Проверяем, что редирект происходит на URL, заданный для логина
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))

    def test_folder_not_specified(self):
        """Если параметр folder отсутствует, возвращается BadRequest."""
        response = self.client.get(reverse("delete_folder"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("Папка не указана", response.content.decode())

    @patch("main.views.os.path.abspath")
    def test_folder_outside_files_folder(self, mock_abspath):
        """
        Если abs_folder не начинается с abs(FILES_FOLDER), возвращается сообщение "Доступ запрещён".
        """
        mock_abspath.side_effect = lambda path: "/not_allowed/folder" if path == self.test_folder else self.files_folder
        response = self.client.get(reverse("delete_folder") + "?folder=" + self.test_folder)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Доступ запрещён", response.content.decode())

    @patch("main.views.os.path.exists")
    @patch("main.views.os.path.isdir")
    def test_folder_not_found(self, mock_isdir, mock_exists):
        """Если папка не существует или не является директорией, возвращается сообщение "Папка не найдена"."""
        mock_exists.return_value = False
        response = self.client.get(reverse("delete_folder") + "?folder=" + self.test_folder)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Папка не найдена", response.content.decode())
        mock_exists.return_value = True
        mock_isdir.return_value = False
        response = self.client.get(reverse("delete_folder") + "?folder=" + self.test_folder)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Папка не найдена", response.content.decode())

    @patch("main.views.read_restrictions")
    @patch("main.views.os.path.exists")
    @patch("main.views.os.path.isdir")
    def test_folder_restricted(self, mock_isdir, mock_exists, mock_read_restrictions):
        """
        Если имя папки входит в restricted_folders, возвращается сообщение об ограничении.
        """
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_read_restrictions.return_value = (None, ["TEST_FOLDER"])
        response = self.client.get(reverse("delete_folder") + "?folder=" + self.test_folder)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Удаление этой папки запрещено", response.content.decode())

    @patch("main.views.read_access_levels")
    @patch("main.views.build_file_tree")
    @patch("main.views.os.path.exists")
    @patch("main.views.os.path.isdir")
    @patch("main.views.read_restrictions")
    def test_insufficient_access(self, mock_read_restrictions, mock_isdir, mock_exists, mock_build_file_tree, mock_read_access_levels):
        """
        Если уровень доступа пользователя меньше 3, должно отображаться сообщение об отсутствии прав.
        """
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_read_restrictions.return_value = (None, [])
        mock_read_access_levels.return_value = {"testuser": 2}
        mock_build_file_tree.return_value = "fake_tree"
        response = self.client.get(reverse("delete_folder") + "?folder=" + self.test_folder)
        self.assertEqual(response.status_code, 200)
        self.assertIn("У вас нет прав на удаление папок.", response.content.decode())
        # Проверка наличия дерева файлов может быть адаптирована под реальный шаблон
        # Здесь достаточно убедиться, что ошибка отображается.

    @patch("main.views.os.listdir")
    @patch("main.views.os.path.exists")
    @patch("main.views.os.path.isdir")
    @patch("main.views.read_restrictions")
    @patch("main.views.read_access_levels")
    def test_folder_not_empty(self, mock_read_access_levels, mock_read_restrictions, mock_isdir, mock_exists, mock_listdir):
        """
        Если папка не пуста, возвращается сообщение "Папка не пустая, удаление запрещено."
        """
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.return_value = ["file.txt"]
        mock_read_restrictions.return_value = (None, [])
        mock_read_access_levels.return_value = {"testuser": 3}
        response = self.client.get(reverse("delete_folder") + "?folder=" + self.test_folder)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Папка не пустая, удаление запрещено", response.content.decode())

    @patch("main.views.os.rmdir")
    @patch("main.views.os.listdir")
    @patch("main.views.os.path.exists")
    @patch("main.views.os.path.isdir")
    @patch("main.views.read_restrictions")
    @patch("main.views.read_access_levels")
    @patch("main.views.log_event")
    def test_successful_deletion(self, mock_log_event, mock_read_access_levels, mock_read_restrictions,
                                 mock_isdir, mock_exists, mock_listdir, mock_rmdir):
        """
        При успешном удалении папки происходит вызов os.rmdir, логирование и редирект на file_manager.
        """
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.return_value = []  # папка пуста
        mock_read_restrictions.return_value = (None, [])
        mock_read_access_levels.return_value = {"testuser": 3}
        response = self.client.get(reverse("delete_folder") + "?folder=" + self.test_folder)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("file_manager"))
        mock_rmdir.assert_called_with(self.test_folder)
        mock_log_event.assert_called_with("DELETED_FOLDER", f"user='testuser', folder='{os.path.basename(self.test_folder)}'")

    @patch("main.views.os.rmdir", side_effect=Exception("Deletion error"))
    @patch("main.views.build_file_tree")
    @patch("main.views.os.listdir")
    @patch("main.views.os.path.exists")
    @patch("main.views.os.path.isdir")
    @patch("main.views.read_restrictions")
    @patch("main.views.read_access_levels")
    def test_deletion_exception(self, mock_read_access_levels, mock_read_restrictions,
                                  mock_isdir, mock_exists, mock_listdir, mock_build_file_tree, mock_rmdir):
        """
        Если os.rmdir вызывает исключение, отображается страница file_manager с сообщением об ошибке.
        """
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.return_value = []  # папка пуста
        mock_read_restrictions.return_value = (None, [])
        mock_read_access_levels.return_value = {"testuser": 3}
        mock_build_file_tree.return_value = "fake_tree"
        response = self.client.get(reverse("delete_folder") + "?folder=" + self.test_folder)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Ошибка удаления папки", response.content.decode())
        # Проверяем, что сообщение об ошибке содержит информацию об исключении
        self.assertIn("Deletion error", response.content.decode())


class FileManagerViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Для тестов зададим фиктивное значение для FILES_FOLDER
        self.fake_files_folder = "/fake/files_folder"
        # Патчим FILES_FOLDER в модуле views
        patcher = patch.object(views, "FILES_FOLDER", self.fake_files_folder)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_not_logged_in_redirects_to_login(self):
        """
        Если пользователь не залогинен, происходит редирект на login.
        В вашем проекте reverse("login") может возвращать "/" – поэтому проверяем именно это.
        """
        # Удаляем сессионную переменную "logged_in"
        session = self.client.session
        session.pop("logged_in", None)
        session.save()
        response = self.client.get(reverse("file_manager"))
        self.assertEqual(response.status_code, 302)
        # Если reverse("login") возвращает "/", то:
        self.assertEqual(response.url, reverse("login"))

    @patch("main.views.build_file_tree")
    @patch("main.views.read_folder_visibility_config")
    @patch("main.views.read_access_levels")
    def test_superadmin_sees_all_files(self, mock_read_access_levels, mock_read_folder_visibility_config, mock_build_file_tree):
        """
        Если пользователь является суперадмином (его логин совпадает с read_folder_visibility_config),
        используется корневая папка FILES_FOLDER для построения дерева файлов.
        """
        mock_read_folder_visibility_config.return_value = "admin"
        mock_read_access_levels.return_value = {"admin": 5}
        mock_build_file_tree.return_value = "superadmin_tree"
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "admin"
        session.save()

        response = self.client.get(reverse("file_manager"))
        self.assertEqual(response.status_code, 200)
        # Проверяем, что в контексте шаблона передано дерево файлов
        self.assertEqual(response.context.get("tree"), "superadmin_tree")
        # Проверяем, что переданы current_user, superadmin и access_level
        self.assertEqual(response.context.get("current_user"), "admin")
        self.assertEqual(response.context.get("superadmin"), "admin")
        self.assertEqual(response.context.get("access_level"), 5)

    @patch("main.views.get_user_group")
    @patch("main.views.read_access_levels")
    def test_user_without_group_shows_error(self, mock_read_access_levels, mock_get_user_group):
        """
        Если get_user_group возвращает None, возвращается шаблон file_manager с сообщением об ошибке и пустым деревом.
        """
        mock_get_user_group.return_value = None
        mock_read_access_levels.return_value = {"user1": 1}
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "user1"
        session.save()

        response = self.client.get(reverse("file_manager"))
        self.assertEqual(response.status_code, 200)
        # В шаблоне должна быть ошибка об отсутствии группы
        self.assertIn("Вам не назначена группа доступа", response.content.decode())
        # Можно проверить, что tree пустое или равно [] (в зависимости от реализации)
        self.assertEqual(response.context.get("tree"), [])

    @patch("main.views.build_file_tree")
    @patch("main.views.get_group_folder")
    @patch("main.views.get_user_group")
    @patch("main.views.read_access_levels")
    @patch("main.views.read_folder_visibility_config")
    def test_user_with_group_sees_allowed_folder(self, mock_read_folder_visibility_config, mock_read_access_levels,
                                                 mock_get_user_group, mock_get_group_folder, mock_build_file_tree):
        """
        Если пользователь не суперадмин и имеет группу, вычисляется разрешённая папка и вызывается build_file_tree с ней.
        """
        mock_read_folder_visibility_config.return_value = "admin"
        mock_get_user_group.return_value = "group1"
        mock_get_group_folder.return_value = "group_folder"
        mock_read_access_levels.return_value = {"user2": 3}
        mock_build_file_tree.return_value = "group_tree"
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "user2"
        session.save()
        # Ожидаемая папка:
        expected_folder = (self.fake_files_folder + "/group_folder").replace("\\", "/")
        response = self.client.get(reverse("file_manager") + "?error=TestError")
        self.assertEqual(response.status_code, 200)
        # Извлекаем фактические аргументы вызова build_file_tree
        args, kwargs = mock_build_file_tree.call_args
        actual_folder = args[0].replace("\\", "/")
        self.assertEqual(actual_folder, expected_folder)
        self.assertEqual(args[1], "user2")
        # Проверяем контекст шаблона
        self.assertEqual(response.context.get("tree"), "group_tree")
        self.assertEqual(response.context.get("current_user"), "user2")
        self.assertEqual(response.context.get("access_level"), 3)
        self.assertEqual(response.context.get("error"), "TestError")


class GetGroupFolderTests(TestCase):
    @patch("main.views.configparser.ConfigParser")
    def test_valid_group(self, mock_config_parser):
        # Эмулируем конфигурацию с секцией "group_folders" и опцией "group1"
        fake_config = mock_config_parser.return_value
        fake_config.has_section.return_value = True
        fake_config.has_option.return_value = True
        fake_config.get.return_value = " folder1 "

        result = get_group_folder("group1")
        # Ожидается, что функция вернет обрезанное значение
        self.assertEqual(result, "folder1")
        expected_config_path = os.path.join(BASE_DIR, "config.ini")
        fake_config.read.assert_called_once_with(expected_config_path)

    @patch("main.views.configparser.ConfigParser")
    def test_no_group(self, mock_config_parser):
        # Если user_group не задан, функция должна вернуть None
        result = get_group_folder(None)
        self.assertIsNone(result)

    @patch("main.views.configparser.ConfigParser")
    def test_missing_section(self, mock_config_parser):
        fake_config = mock_config_parser.return_value
        fake_config.has_section.return_value = False  # Секция отсутствует

        result = get_group_folder("group1")
        self.assertIsNone(result)

    @patch("main.views.configparser.ConfigParser")
    def test_missing_option(self, mock_config_parser):
        fake_config = mock_config_parser.return_value
        fake_config.has_section.return_value = True
        fake_config.has_option.return_value = False  # Опция отсутствует

        result = get_group_folder("group1")
        self.assertIsNone(result)


class ToggleFolderVisibilityTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Устанавливаем фиктивное значение для FILES_FOLDER в представлении.
        self.fake_files_folder = "/fake/files"
        patcher = patch.object(views, "FILES_FOLDER", self.fake_files_folder)
        patcher.start()
        self.addCleanup(patcher.stop)
        # Фиктивный путь для тестовой папки (должен начинаться с fake_files_folder)
        self.test_folder = os.path.join(self.fake_files_folder, "test_folder")

    def test_not_logged_in_redirects_to_login(self):
        """Если пользователь не залогинен, происходит редирект на login."""
        session = self.client.session
        session.pop("logged_in", None)
        session.save()
        response = self.client.get(reverse("toggle_folder_visibility") + f"?folder={self.test_folder}")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))

    def test_no_folder_param_returns_bad_request(self):
        """Если параметр folder не указан, возвращается HTTP 400 с сообщением 'Папка не указана'."""
        session = self.client.session
        session["logged_in"] = True
        session.save()
        response = self.client.get(reverse("toggle_folder_visibility"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("Папка не указана", response.content.decode())

    @patch("main.views.os.path.isdir")
    @patch("main.views.os.path.abspath")
    def test_folder_not_in_allowed_or_not_directory(self, mock_abspath, mock_isdir):
        """
        Если переданный путь не начинается с FILES_FOLDER или не является директорией,
        возвращается сообщение "Доступ запрещён или папка не найдена".
        """
        # Пусть os.path.abspath возвращает путь без изменений
        mock_abspath.side_effect = lambda path: path
        # Эмулируем, что путь является директорией
        mock_isdir.return_value = False
        session = self.client.session
        session["logged_in"] = True
        session.save()
        response = self.client.get(reverse("toggle_folder_visibility") + f"?folder={self.test_folder}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Доступ запрещён или папка не найдена", response.content.decode())

        # Теперь эмулируем, что путь не начинается с FILES_FOLDER
        def fake_abspath(path):
            if path == self.test_folder:
                return "/not_allowed/test_folder"
            return path
        mock_abspath.side_effect = fake_abspath
        mock_isdir.return_value = True
        response = self.client.get(reverse("toggle_folder_visibility") + f"?folder={self.test_folder}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Доступ запрещён или папка не найдена", response.content.decode())

    @patch("main.views.read_folder_visibility_config")
    @patch("main.views.os.path.abspath")
    @patch("main.views.os.path.isdir")
    def test_non_superadmin_no_rights(self, mock_isdir, mock_abspath, mock_read_visibility):
        """
        Если пользователь не является суперадмином, возвращается сообщение "Нет прав для изменения видимости папок."
        """
        # Эмулируем, что test_folder корректно определяется
        mock_abspath.side_effect = lambda path: path
        mock_isdir.return_value = True
        # Пусть read_folder_visibility_config возвращает "admin"
        mock_read_visibility.return_value = "admin"
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "user1"
        session.save()
        response = self.client.get(reverse("toggle_folder_visibility") + f"?folder={self.test_folder}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Нет прав для изменения видимости папок.", response.content.decode())

    @patch("main.views.write_hidden_folders")
    @patch("main.views.read_hidden_folders")
    @patch("main.views.read_folder_visibility_config")
    @patch("main.views.os.path.abspath")
    @patch("main.views.os.path.isdir")
    def test_toggle_visibility_adds_folder(self, mock_isdir, mock_abspath, mock_read_visibility, mock_read_hidden, mock_write_hidden):
        """
        Если пользователь-суперадмин и папка не скрыта, она добавляется в hidden,
        затем вызывается write_hidden_folders и происходит редирект на file_manager.
        """
        # Эмулируем корректное определение пути
        mock_abspath.side_effect = lambda path: path
        mock_isdir.return_value = True
        # Пусть суперадмин – "admin"
        mock_read_visibility.return_value = "admin"
        # Пусть скрытых папок пока нет (возвращаем пустое множество)
        mock_read_hidden.return_value = set()
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "admin"
        session.save()
        response = self.client.get(reverse("toggle_folder_visibility") + f"?folder={self.test_folder}")
        # Ожидаем редирект на file_manager
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("file_manager"))
        # Ожидаем, что write_hidden_folders вызвана с множеством, содержащим относительный путь.
        rel_path = os.path.relpath(self.test_folder, self.fake_files_folder)
        mock_write_hidden.assert_called_with({rel_path})

    @patch("main.views.write_hidden_folders")
    @patch("main.views.read_hidden_folders")
    @patch("main.views.read_folder_visibility_config")
    @patch("main.views.os.path.abspath")
    @patch("main.views.os.path.isdir")
    def test_toggle_visibility_removes_folder(self, mock_isdir, mock_abspath, mock_read_visibility, mock_read_hidden, mock_write_hidden):
        """
        Если пользователь-суперадмин и папка уже скрыта, она удаляется из hidden,
        затем вызывается write_hidden_folders и происходит редирект на file_manager.
        """
        mock_abspath.side_effect = lambda path: path
        mock_isdir.return_value = True
        mock_read_visibility.return_value = "admin"
        # Пусть скрытых папок уже содержит относительный путь
        rel_path = os.path.relpath(self.test_folder, self.fake_files_folder)
        hidden_set = {rel_path}
        mock_read_hidden.return_value = hidden_set.copy()
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "admin"
        session.save()
        response = self.client.get(reverse("toggle_folder_visibility") + f"?folder={self.test_folder}")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("file_manager"))
        # После удаления, write_hidden_folders должна быть вызвана с множеством без rel_path.
        mock_write_hidden.assert_called_with(set())

if __name__ == "__main__":
    import unittest

    unittest.main()
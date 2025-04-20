import os
import django
import json
import configparser
from django.test.utils import override_settings
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from main import views
from main.views import BASE_DIR, get_group_folders  # get_group_folders теперь возвращает список

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
django.setup()

SILENCED_CHECKS = ["admin.E402", "admin.E404", "admin.E408", "admin.E409"]

#####################
# LoginViewTests
#####################
@override_settings(SILENCED_SYSTEM_CHECKS=SILENCED_CHECKS)
class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_credentials = {"testuser": "testpass"}

    # Теперь патчим get_user_groups, возвращая список групп
    @patch("main.views.log_event")
    @patch("main.views.get_user_groups")
    @patch("main.views.read_credentials")
    def test_login_success(self, mock_read_credentials, mock_get_user_groups, mock_log_event):
        mock_read_credentials.return_value = self.test_credentials
        mock_get_user_groups.return_value = ["group1"]
        data = {"login": "testuser", "password": "testpass"}
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("file_manager"))
        session = self.client.session
        self.assertTrue(session.get("logged_in"))
        self.assertEqual(session.get("login"), "testuser")
        # Ожидаем, что в сессии теперь сохранён список групп
        self.assertEqual(session.get("login_groups"), ["group1"])
        mock_log_event.assert_called_with("SUCCESS", "login='testuser'")

    @patch("main.views.log_event")
    @patch("main.views.read_credentials")
    def test_login_failure(self, mock_read_credentials, mock_log_event):
        mock_read_credentials.return_value = self.test_credentials
        data = {"login": "wronguser", "password": "wrongpass"}
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Неверные учетные данные", response.content.decode())
        session = self.client.session
        self.assertFalse(session.get("logged_in", False))
        mock_log_event.assert_called_with("FAILED", "login='wronguser'")


#####################
# BasicPagesTests
#####################
@override_settings(SILENCED_SYSTEM_CHECKS=SILENCED_CHECKS)
class BasicPagesTests(TestCase):
    def setUp(self):
        self.client = Client()
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "testuser"
        session["login_groups"] = ["group1"]
        session.save()

    def test_homepage_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("KOD OS", response.content.decode())

    def test_blackjack_page_loads(self):
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


#####################
# FileManagerTests
#####################
@override_settings(SILENCED_SYSTEM_CHECKS=SILENCED_CHECKS)
class FileManagerTests(TestCase):
    def setUp(self):
        self.client = Client()
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "testuser"
        session["login_groups"] = ["group1"]
        session.save()

    def test_file_manager_access(self):
        response = self.client.get(reverse("file_manager"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Файловый менеджер", response.content.decode())


#####################
# DeleteFolderTests
#####################
class DeleteFolderTests(TestCase):
    def setUp(self):
        self.client = Client()
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "testuser"
        session["login_groups"] = ["group1"]
        session.save()
        self.test_folder = "/allowed/test_folder"
        self.files_folder = "/allowed"
        views.FILES_FOLDER = self.files_folder

    def test_not_logged_in(self):
        session = self.client.session
        session.pop("logged_in", None)
        session.save()
        response = self.client.get(reverse("delete_folder") + "?folder=" + self.test_folder)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))

    def test_folder_not_specified(self):
        response = self.client.get(reverse("delete_folder"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("Папка не указана", response.content.decode())

    @patch("main.views.os.path.abspath")
    def test_folder_outside_files_folder(self, mock_abspath):
        mock_abspath.side_effect = lambda path: "/not_allowed/folder" if path == self.test_folder else self.files_folder
        response = self.client.get(reverse("delete_folder") + "?folder=" + self.test_folder)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Доступ запрещён", response.content.decode())

    @patch("main.views.os.path.exists")
    @patch("main.views.os.path.isdir")
    def test_folder_not_found(self, mock_isdir, mock_exists):
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
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_read_restrictions.return_value = (None, [])
        mock_read_access_levels.return_value = {"testuser": 2}
        mock_build_file_tree.return_value = "fake_tree"
        response = self.client.get(reverse("delete_folder") + "?folder=" + self.test_folder)
        self.assertEqual(response.status_code, 200)
        self.assertIn("У вас нет прав на удаление папок.", response.content.decode())

    @patch("main.views.os.listdir")
    @patch("main.views.os.path.exists")
    @patch("main.views.os.path.isdir")
    @patch("main.views.read_restrictions")
    @patch("main.views.read_access_levels")
    def test_folder_not_empty(self, mock_read_access_levels, mock_read_restrictions, mock_isdir, mock_exists, mock_listdir):
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
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.return_value = []
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
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.return_value = []
        mock_read_restrictions.return_value = (None, [])
        mock_read_access_levels.return_value = {"testuser": 3}
        mock_build_file_tree.return_value = "fake_tree"
        response = self.client.get(reverse("delete_folder") + "?folder=" + self.test_folder)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Ошибка удаления папки", response.content.decode())
        self.assertIn("Deletion error", response.content.decode())


#####################
# FileManagerViewTests (для file_manager)
#####################
class FileManagerViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.fake_files_folder = "/fake/files_folder"
        patcher = patch.object(views, "FILES_FOLDER", self.fake_files_folder)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_not_logged_in_redirects_to_login(self):
        session = self.client.session
        session.pop("logged_in", None)
        session.save()
        response = self.client.get(reverse("file_manager"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))

    @patch("main.views.build_file_tree")
    @patch("main.views.read_folder_visibility_config")
    @patch("main.views.read_access_levels")
    def test_superadmin_sees_all_files(self, mock_read_access_levels, mock_read_folder_visibility_config, mock_build_file_tree):
        mock_read_folder_visibility_config.return_value = "admin"
        mock_read_access_levels.return_value = {"admin": 5}
        mock_build_file_tree.return_value = "superadmin_tree"
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "admin"
        session["login_groups"] = ["clear_sky"]
        session.save()
        response = self.client.get(reverse("file_manager"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context.get("tree"), "superadmin_tree")
        self.assertEqual(response.context.get("current_user"), "admin")
        self.assertEqual(response.context.get("superadmin"), "admin")
        self.assertEqual(response.context.get("access_level"), 5)

    @patch("main.views.get_user_groups")
    @patch("main.views.read_access_levels")
    def test_user_without_group_shows_error(self, mock_read_access_levels, mock_get_user_groups):
        mock_get_user_groups.return_value = []
        mock_read_access_levels.return_value = {"user1": 1}
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "user1"
        session["login_groups"] = []
        session.save()
        response = self.client.get(reverse("file_manager"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Вам не назначена группа доступа", response.content.decode())
        self.assertEqual(response.context.get("tree"), [])

    @patch("main.views.build_file_tree")
    @patch("main.views.get_group_folders")
    @patch("main.views.get_user_groups")
    @patch("main.views.read_access_levels")
    @patch("main.views.read_folder_visibility_config")
    def test_user_with_group_sees_allowed_folder(self, mock_read_folder_visibility_config, mock_read_access_levels,
                                                 mock_get_user_groups, mock_get_group_folders, mock_build_file_tree):
        mock_read_folder_visibility_config.return_value = "admin"
        mock_get_user_groups.return_value = ["group1"]
        mock_get_group_folders.return_value = ["group_folder"]
        mock_read_access_levels.return_value = {"user2": 3}
        # Возвращаем список объектов, а не строку:
        mock_build_file_tree.return_value = [{"name": "group_tree"}]
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "user2"
        session["login_groups"] = ["group1"]
        session.save()
        expected_folder = (self.fake_files_folder + "/group_folder").replace("\\", "/")
        response = self.client.get(reverse("file_manager") + "?error=TestError")
        self.assertEqual(response.status_code, 200)
        args, kwargs = mock_build_file_tree.call_args
        actual_folder = args[0].replace("\\", "/")
        self.assertEqual(actual_folder, expected_folder)
        self.assertEqual(args[1], "user2")
        # Проверяем контекст шаблона – он теперь должен содержать список с объектом:
        self.assertEqual(response.context.get("tree"), [{"name": "group_tree"}])
        self.assertEqual(response.context.get("current_user"), "user2")
        self.assertEqual(response.context.get("access_level"), 3)
        self.assertEqual(response.context.get("error"), "TestError")


#####################
# GetGroupFolderTests
#####################
class GetGroupFolderTests(TestCase):
    @patch("main.views.configparser.ConfigParser")
    def test_valid_group(self, mock_config_parser):
        fake_config = mock_config_parser.return_value
        fake_config.has_section.return_value = True
        fake_config.has_option.return_value = True
        fake_config.get.return_value = " folder1 "
        result = get_group_folders("group1")
        self.assertEqual(result, ["folder1"])
        expected_config_path = os.path.join(BASE_DIR, "config.ini")
        fake_config.read.assert_called_once_with(expected_config_path)

    @patch("main.views.configparser.ConfigParser")
    def test_no_group(self, mock_config_parser):
        result = get_group_folders(None)
        self.assertEqual(result, [])

    @patch("main.views.configparser.ConfigParser")
    def test_missing_section(self, mock_config_parser):
        fake_config = mock_config_parser.return_value
        fake_config.has_section.return_value = False
        result = get_group_folders("group1")
        self.assertEqual(result, [])

    @patch("main.views.configparser.ConfigParser")
    def test_missing_option(self, mock_config_parser):
        fake_config = mock_config_parser.return_value
        fake_config.has_section.return_value = True
        fake_config.has_option.return_value = False
        result = get_group_folders("group1")
        self.assertEqual(result, [])


#####################
# ToggleFolderVisibilityTests
#####################
class ToggleFolderVisibilityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.fake_files_folder = "/fake/files"
        patcher = patch.object(views, "FILES_FOLDER", self.fake_files_folder)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.test_folder = os.path.join(self.fake_files_folder, "test_folder")

    def test_not_logged_in_redirects_to_login(self):
        session = self.client.session
        session.pop("logged_in", None)
        session.save()
        response = self.client.get(reverse("toggle_folder_visibility") + f"?folder={self.test_folder}")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))

    def test_no_folder_param_returns_bad_request(self):
        session = self.client.session
        session["logged_in"] = True
        session.save()
        response = self.client.get(reverse("toggle_folder_visibility"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("Папка не указана", response.content.decode())

    @patch("main.views.os.path.isdir")
    @patch("main.views.os.path.abspath")
    def test_folder_not_in_allowed_or_not_directory(self, mock_abspath, mock_isdir):
        mock_abspath.side_effect = lambda path: path
        mock_isdir.return_value = False
        session = self.client.session
        session["logged_in"] = True
        session.save()
        response = self.client.get(reverse("toggle_folder_visibility") + f"?folder={self.test_folder}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Доступ запрещён или папка не найдена", response.content.decode())
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
        mock_abspath.side_effect = lambda path: path
        mock_isdir.return_value = True
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
        mock_abspath.side_effect = lambda path: path
        mock_isdir.return_value = True
        mock_read_visibility.return_value = "admin"
        mock_read_hidden.return_value = set()
        session = self.client.session
        session["logged_in"] = True
        session["login"] = "admin"
        session.save()
        response = self.client.get(reverse("toggle_folder_visibility") + f"?folder={self.test_folder}")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("file_manager"))
        rel_path = os.path.relpath(self.test_folder, self.fake_files_folder)
        mock_write_hidden.assert_called_with({rel_path})

    @patch("main.views.write_hidden_folders")
    @patch("main.views.read_hidden_folders")
    @patch("main.views.read_folder_visibility_config")
    @patch("main.views.os.path.abspath")
    @patch("main.views.os.path.isdir")
    def test_toggle_visibility_removes_folder(self, mock_isdir, mock_abspath, mock_read_visibility, mock_read_hidden, mock_write_hidden):
        mock_abspath.side_effect = lambda path: path
        mock_isdir.return_value = True
        mock_read_visibility.return_value = "admin"
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
        mock_write_hidden.assert_called_with(set())


if __name__ == "__main__":
    import unittest
    unittest.main()

// Если обработчики уже инициализированы, выходим.
if (window.moveFileHandlersInitialized) {
    console.log("moveFileHandlers already initialized");
} else {
    window.moveFileHandlersInitialized = true;

    var fileToMove = null;

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++){
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function handleMoveFileClick(e) {
        e.preventDefault();
        e.stopPropagation();
        // Если уже выбран файл, игнорируем повторное нажатие
        if (fileToMove) return;
        fileToMove = this.getAttribute('data-file-path');
        console.log("Файл для перемещения выбран:", fileToMove);
        // Показываем все кнопки-приёмники у папок
        var destButtons = document.querySelectorAll('.move-dest-btn');
        for (var i = 0; i < destButtons.length; i++){
            destButtons[i].style.display = 'inline-block';
        }
        // Выделяем выбранный файл визуально (делаем имя жирным)
        var fileEntry = this.closest("li").querySelector(".file-name");
        if (fileEntry) {
            fileEntry.style.fontWeight = 'bold';
        }
    }

    function handleMoveDestClick(e) {
        e.preventDefault();
        e.stopPropagation();
        var destFolder = this.getAttribute('data-folder-path');
        if (!fileToMove) {
            alert("Сначала выберите файл для перемещения!");
            return;
        }
        console.log("Перемещение файла", fileToMove, "в папку", destFolder);
        fetch("/move-file-ajax/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify({ file: fileToMove, folder: destFolder })
        })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                alert("Файл успешно перемещён.");
                location.reload();
            } else {
                alert("Ошибка перемещения: " + data.error);
            }
        })
        .catch(function(error) {
            console.error("Ошибка при перемещении файла:", error);
            alert("Ошибка при перемещении файла.");
        });
    }

    function initMoveFileHandlers() {
        // Используем делегирование по контейнеру дерева с id "file-tree"
        var fileTree = document.getElementById("file-tree");
        if (!fileTree) {
            console.error("Элемент с id 'file-tree' не найден.");
            return;
        }
        fileTree.addEventListener("click", function(e) {
            var moveFileBtn = e.target.closest(".move-file-btn");
            if (moveFileBtn) {
                handleMoveFileClick.call(moveFileBtn, e);
                return;
            }
            var moveDestBtn = e.target.closest(".move-dest-btn");
            if (moveDestBtn) {
                handleMoveDestClick.call(moveDestBtn, e);
                return;
            }
        });
    }

    document.addEventListener("DOMContentLoaded", function() {
        console.log("Инициализация обработчиков перемещения файлов (делегирование)");
        initMoveFileHandlers();
    });
}
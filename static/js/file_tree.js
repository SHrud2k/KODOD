// Функция для переключения раскрытия/сворачивания папок
function toggleFolder(element) {
    var headerDiv = element.parentElement;
    var next = headerDiv.nextElementSibling;
    if (next && next.classList.contains('children')) {
        if (next.style.display === "none" || next.style.display === "") {
            next.style.display = "block";
            element.classList.add('open');
            localStorage.setItem("folder_" + element.getAttribute("data-folder"), "expanded");
        } else {
            next.style.display = "none";
            element.classList.remove('open');
            localStorage.setItem("folder_" + element.getAttribute("data-folder"), "collapsed");
        }
    }
}

// Функция воспроизведения звука при выборе (использует кешированное воспроизведение)
// SELECT_SOUND_URL должна быть определена глобально (например, в base.html)
function playSelectionSound() {
    if (typeof getCachedSound === "function" && typeof SELECT_SOUND_URL !== "undefined") {
        var sound = getCachedSound(SELECT_SOUND_URL);
        var clone = sound.cloneNode();
        clone.play();
    } else {
        console.warn("Cached sound function or SELECT_SOUND_URL not defined.");
    }
}

// Восстанавливаем состояние раскрытых папок при загрузке страницы
document.addEventListener("DOMContentLoaded", function() {
    var folders = document.querySelectorAll(".folder");
    folders.forEach(function(folder) {
        var folderId = folder.getAttribute("data-folder");
        var state = localStorage.getItem("folder_" + folderId);
        if (state === "expanded") {
            var headerDiv = folder.parentElement;
            var next = headerDiv.nextElementSibling;
            if (next && next.classList.contains('children')) {
                next.style.display = "block";
                folder.classList.add('open');
            }
        }
    });
});
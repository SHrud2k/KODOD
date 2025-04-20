document.addEventListener("DOMContentLoaded", function(){
    var soundToggleBtn = document.getElementById("sound-toggle");
    if (!soundToggleBtn) {
        console.warn("Элемент sound-toggle не найден");
        return;
    }

    // Если значение ещё не установлено, ставим его по умолчанию в "true"
    if (localStorage.getItem("soundEnabled") === null) {
        localStorage.setItem("soundEnabled", "true");
    }

    function updateSoundButton() {
        // При отсутствии значения считаем, что звук включён
        var soundEnabled = localStorage.getItem("soundEnabled") || "true";
        if (soundEnabled === "true") {
            soundToggleBtn.textContent = "Отключить звук";
        } else {
            soundToggleBtn.textContent = "Включить звук";
        }
    }

    updateSoundButton();

    soundToggleBtn.addEventListener("click", function(){
        var soundEnabled = localStorage.getItem("soundEnabled") || "true";
        // Переключаем состояние
        if (soundEnabled === "true") {
            localStorage.setItem("soundEnabled", "false");
        } else {
            localStorage.setItem("soundEnabled", "true");
        }
        updateSoundButton();
        console.log("Состояние звука: ", localStorage.getItem("soundEnabled"));
    });
});
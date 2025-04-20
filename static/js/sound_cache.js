// sound_cache.js
var soundCache = {};

/**
 * Возвращает клонированный объект Audio из кэша.
 * Если звук ещё не загружен, создаёт его, устанавливает preload и сохраняет в кэше.
 * @param {string} url - путь к звуковому файлу.
 * @return {Audio} - клонированный объект Audio.
 */
function getCachedSound(url) {
    if (!soundCache[url]) {
        var audio = new Audio(url);
        audio.preload = "auto";  // Предварительная загрузка звука
        soundCache[url] = audio;
    }
    return soundCache[url].cloneNode();
}
function playSelectionSound() {
    var soundEnabled = localStorage.getItem("soundEnabled");
    // Если значение не установлено, по умолчанию считаем, что звук включён
    if (soundEnabled === null) {
        soundEnabled = "true";
        localStorage.setItem("soundEnabled", "true");
    }
    if (soundEnabled !== "true") {
        return; // Звук отключен — ничего не делаем
    }
    var audio = new Audio(SELECT_SOUND_URL);
    audio.play();
}
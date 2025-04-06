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
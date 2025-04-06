document.addEventListener("DOMContentLoaded", function(){
    // Считываем исходный текст из скрытого элемента
    var rawText = document.getElementById("fileContent").textContent;

    // Функция для декодирования Unicode-escape последовательностей
    function decodeUnicode(str) {
        return str.replace(/\\u([\d\w]{4})/gi, function(match, grp) {
            return String.fromCharCode(parseInt(grp, 16));
        });
    }
    var decodedText = decodeUnicode(rawText);
    // Заменяем остаточные "\n" на реальные переносы строк
    decodedText = decodedText.replace(/\\n/g, "\n");

    // Обработка ссылок на изображения: ищем URL, заканчивающиеся на jpg, jpeg, png или gif (с необязательными параметрами)
    var processedText = decodedText.replace(/(https?:\/\/\S+\.(?:jpg|jpeg|png|gif)(?:\?\S+)?)(?=[\s'"<>]|$)/gi, function(match) {
        // Заменяем амперсанды на &amp; для корректного HTML
        var safeUrl = match.replace(/&/g, "&amp;");
        return '<img src="' + safeUrl + '" alt="Image" style="max-width:100%; margin:5px 0;">';
    });
    decodedText = processedText;

    var contentDiv = document.getElementById("content");
    var index = 0;
    // Используем кешированное воспроизведение звука (функция getCachedSound должна быть определена в sound_cache.js)
    var typingSoundUrl = TYPING_SOUND_URL;

    // Функция, которая "печатает" содержимое с поддержкой HTML-тегов:
    // Если встречается символ '<', ищем закрывающую '>' и выводим тег целиком.
    function typeLetter() {
        if (index < decodedText.length) {
            if (decodedText[index] === '<') {
                var closeIndex = decodedText.indexOf('>', index);
                if (closeIndex === -1) {
                    contentDiv.innerHTML += decodedText.substring(index);
                    index = decodedText.length;
                } else {
                    var tag = decodedText.substring(index, closeIndex + 1);
                    contentDiv.innerHTML += tag;
                    index = closeIndex + 1;
                }
            } else {
                contentDiv.innerHTML += decodedText.charAt(index);
                index++;
            }
            if (index % 3 === 0) {
                var clone = getCachedSound(typingSoundUrl);
                clone.play();
            }
            setTimeout(typeLetter, 25);
        } else {
            contentDiv.innerHTML += '<span class="blinking-cursor"></span>';
        }
    }
    typeLetter();
});
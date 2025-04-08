document.addEventListener("DOMContentLoaded", function(){
    console.log("Hacking game script loaded");

    // Функция для получения JSON через fetch
    function fetchJSON(url) {
        return fetch(url).then(function(response){
            return response.json();
        });
    }

    // Функция выбора кандидатов: возвращает случайное количество слов от minCount до maxCount
    function chooseCandidates(words, minCount, maxCount) {
        var candidateCount = Math.floor(Math.random() * (maxCount - minCount + 1)) + minCount;
        var selected = [];
        var used = {};
        while(selected.length < candidateCount && selected.length < words.length) {
            var idx = Math.floor(Math.random() * words.length);
            if (!used[idx]) {
                used[idx] = true;
                selected.push(words[idx]);
            }
        }
        return selected;
    }

    // Функция генерации случайного шума: от 4 до 20 символов
    function generateNoise(){
        var chars = '!@#$%^&*()-_=+[]{};:\'",.<>/?|';
        var noise = "";
        var count = Math.floor(Math.random() * 17) + 4; // от 4 до 20
        for (var i = 0; i < count; i++){
            noise += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return noise;
    }

    // Функция вычисления совпадений символов по позициям (без учета шума)
    function computeScore(selected, target){
        var score = 0;
        for (var i = 0; i < selected.length; i++){
            if (selected[i] === target[i]) {
                score++;
            }
        }
        return score;
    }

    // Отключает клики по вариантам (делает их неактивными)
    function disableWords(){
        var spans = document.getElementById("word-list").getElementsByTagName("span");
        for (var i = 0; i < spans.length; i++){
            spans[i].style.pointerEvents = "none";
            spans[i].style.opacity = "0.5";
        }
    }

    // Функция, возвращающая варианты к исходному виду (разблокировка кнопок)
    function enableWords(){
        var spans = document.getElementById("word-list").getElementsByTagName("span");
        for (var i = 0; i < spans.length; i++){
            spans[i].style.pointerEvents = "auto";
            spans[i].style.opacity = "1";
        }
    }

    // Функция запуска persistent countdown.
    // Если в localStorage уже сохранён конечный момент (в мс), обновляет отсчёт и блокирует выбор слов.
    function startPersistentCountdown(restartTimeout) {
        var resultEl = document.getElementById("result");
        var restartBtn = document.getElementById("restart");
        var storedEndTime = localStorage.getItem("hackingCountdown");
        var now = Date.now();
        if (!storedEndTime || now >= Number(storedEndTime)) {
            return;
        }
        // Блокируем выбор вариантов, но не перекрываем весь экран
        disableWords();
        var countdown = Math.ceil((Number(storedEndTime) - now) / 1000);
        resultEl.textContent = "Failed! Attempt limit reached. Try again after " + countdown + " seconds.";
        var countdownInterval = setInterval(function(){
            var remaining = Math.ceil((Number(storedEndTime) - Date.now()) / 1000);
            if (remaining > 0) {
                resultEl.textContent = "Failed! Attempt limit reached. Try again after " + remaining + " seconds.";
            } else {
                clearInterval(countdownInterval);
                localStorage.removeItem("hackingCountdown");
                restartBtn.style.display = "inline-block";
                resultEl.textContent = "";
                enableWords();
            }
        }, 1000);
    }

    // Проверяет наличие активного таймера в localStorage.
    // Если есть и время не истекло, запускает persistent countdown и возвращает true.
    function checkPersistentCountdown(restartTimeout) {
        var storedEndTime = localStorage.getItem("hackingCountdown");
        if (storedEndTime && Date.now() < Number(storedEndTime)) {
            startPersistentCountdown(restartTimeout);
            return true;
        }
        return false;
    }

    // Основная функция инициализации мини-игры
    function initHackingGame(words, correctWord, allowedAttempts, restartTimeout) {
        var wordListEl = document.getElementById("word-list");
        var resultEl = document.getElementById("result");
        var restartBtn = document.getElementById("restart");
        var historyEl = document.getElementById("history");
        var attemptCounter = 0;

        // Функция добавления записи в историю
        function addHistoryEntry(selectedWord, score) {
            var entry = document.createElement("div");
            entry.textContent = "[" + selectedWord + "] - [" + score + "] - Attempt: [" + attemptCounter + "/" + allowedAttempts + "]";
            historyEl.appendChild(entry);
        }

        // Рендер вариантов слов
        function renderWords() {
            wordListEl.innerHTML = "";
            words.forEach(function(word){
                var prefixNoise = generateNoise();
                var suffixNoise = generateNoise();
                var noisyWord = prefixNoise + word + suffixNoise;
                var span = document.createElement("span");
                span.textContent = noisyWord;
                span.style.cursor = "pointer";
                span.style.display = "inline-block";
                span.style.padding = "0";
                span.style.margin = "0";
                span.addEventListener("click", function(){
                    // Если таймер активен (выключенные варианты), ничего не делаем
                    if (resultEl.textContent.indexOf("Try again after") !== -1) return;
                    if (this.style.color === "gray") return;
                    attemptCounter++;
                    var score = computeScore(word, correctWord);
                    resultEl.textContent = "Matches: " + score + " из " + correctWord.length;
                    addHistoryEntry(word, score);
                    if (word === correctWord) {
                        resultEl.textContent += " - Access granted!";
                        disableWords();
                        restartBtn.style.display = "inline-block";
                    } else {
                        if (attemptCounter >= allowedAttempts) {
                            // Если попытки закончились и таймер еще не установлен, сохраняем таймер в localStorage
                            if (!localStorage.getItem("hackingCountdown")) {
                                localStorage.setItem("hackingCountdown", Date.now() + restartTimeout * 1000);
                            }
                            // Запускаем persistent countdown, который блокирует выбор вариантов и отображает таймер
                            startPersistentCountdown(restartTimeout);
                        }
                    }
                    if (word !== correctWord) {
                        this.style.color = "gray";
                    }
                });
                wordListEl.appendChild(span);
            });
        }

        // При клике на кнопку рестарта перезагружаем страницу
        restartBtn.addEventListener("click", function(){
            location.reload();
        });

        renderWords();
    }

    // Загрузка настроек игры и слов, затем инициализация игры
    fetchJSON("/static/json/minigame_settings.json")
      .then(function(settingsData) {
          var allowedAttempts = settingsData.allowed_attempts;
          var restartTimeout = settingsData.restart_timeout;
          console.log("Settings:", allowedAttempts, restartTimeout);
          // Если таймер уже активен, блокировка выбора уже запустится
          if (checkPersistentCountdown(restartTimeout)) {
              console.log("Timer active – game is locked");
          }
          return fetchJSON("/static/json/hacking_words.json")
            .then(function(wordsData) {
                var availableWords = wordsData;
                if (!availableWords || availableWords.length === 0) {
                    availableWords = [
                        "PASSWORD", "ACCESS  ", "SECURITY", "PROTECT ", "CREDENTIAL", "HACKER  ",
                        "NETWORK ", "TERMINAL", "DATABASE", "OVERRIDE", "PROTOCOL", "FIREWALL",
                        "BACKUP  ", "SOFTWARE", "HARDWARE", "ENCRYPT ", "DECRYPT ", "OVERRULE",
                        "SYSTEM  ", "CONTROL "
                    ];
                }
                var selected = chooseCandidates(availableWords, 16, 26);
                var correctWord = selected[Math.floor(Math.random() * selected.length)];
                console.log("Selected candidates:", selected);
                console.log("Correct word:", correctWord);
                initHackingGame(selected, correctWord, allowedAttempts, restartTimeout);
            });
      })
      .catch(function(error) {
          console.error("Failed to load settings:", error);
      });
});
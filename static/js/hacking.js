document.addEventListener("DOMContentLoaded", function(){
    console.log("Hacking game script loaded");

    // Вспомогательная функция для fetch JSON
    function fetchJSON(url) {
        return fetch(url).then(function(response) {
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

    // Функция генерации случайного шума: от 4 до 20 символов, без лишнего экранирования
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

    // Отключает клики по вариантам
    function disableWords(){
        var spans = document.getElementById("word-list").getElementsByTagName("span");
        for (var i = 0; i < spans.length; i++){
            spans[i].style.pointerEvents = "none";
            spans[i].style.opacity = "0.5";
        }
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
                            disableWords();
                            var countdown = restartTimeout;
                            resultEl.textContent = "Failed! Attemp limit reached. Try again after " + countdown + " seconds.";
                            var countdownInterval = setInterval(function(){
                                countdown--;
                                if (countdown > 0) {
                                    resultEl.textContent = "Failed! Attemp limit reached. Try again after " + countdown + " seconds.";
                                } else {
                                    clearInterval(countdownInterval);
                                }
                            }, 1000);
                            setTimeout(function(){
                                restartBtn.style.display = "inline-block";
                            }, restartTimeout * 1000);
                        }
                    }
                    if (word !== correctWord) {
                        this.style.color = "gray";
                    }
                });
                wordListEl.appendChild(span);
            });
        }
    
        restartBtn.addEventListener("click", function(){
            location.reload();
        });
    
        renderWords();
    }
    
    // Цепочка загрузки: сначала настройки, затем слова
    fetchJSON("/static/json/minigame_settings.json")
      .then(function(settingsData) {
          var allowedAttempts = settingsData.allowed_attempts;
          var restartTimeout = settingsData.restart_timeout;
          console.log("Settings:", allowedAttempts, restartTimeout);
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
    
    // Определение fetchJSON, чтобы не дублировать код
    function fetchJSON(url) {
        return fetch(url).then(function(response) {
            return response.json();
        });
    }
});
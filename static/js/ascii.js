document.addEventListener("DOMContentLoaded", function() {
    var asciiDiv = document.getElementById("asciiAnimation");
    if (!asciiDiv) return;

    // Функция для обновления анимации с заданными кадрами
    function startAnimation(frames) {
        var currentFrame = 0;
        setInterval(function() {
            asciiDiv.textContent = frames[currentFrame];
            currentFrame = (currentFrame + 1) % frames.length;
        }, 500);
    }

    // Пытаемся загрузить кадры анимации из JSON-файла
    fetch("/static/json/ascii_animation.json")
      .then(function(response) {
          return response.json();
      })
      .then(function(frames) {
          if (frames && frames.length) {
              startAnimation(frames);
          } else {
              console.error("ASCII animation: пустой массив кадров.");
          }
      })
      .catch(function(error) {
          console.error("Ошибка загрузки ASCII анимации:", error);
          // Если JSON не загрузился, используем запасной набор кадров
          var fallbackFrames = [
              "   __\n  /  \\\n |    |\n  \\__/",
              "   __\n  /--\\\n |    |\n  \\__/"
          ];
          startAnimation(fallbackFrames);
      });
});
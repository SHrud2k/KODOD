document.addEventListener("DOMContentLoaded", function(){
    // Функция для получения состояния глича с сервера
    fetch("/glitch_state/")
      .then(response => response.json())
      .then(state => {
          if (state.glitch_toggle === true) {
              document.body.classList.add("glitch-effect");
          } else {
              document.body.classList.remove("glitch-effect");
          }
      })
      .catch(error => {
          console.error("Ошибка загрузки состояния глича:", error);
      });

    // Если существует кнопка переключения (видна только суперадмину)
    var glitchBtn = document.getElementById("glitch-toggle");
    if (glitchBtn) {
        glitchBtn.addEventListener("click", function(){
            // Определяем новое состояние: переключаем текущее состояние эффекта
            var newState = !document.body.classList.contains("glitch-effect");
            fetch("/update_glitch_state/", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ "glitch_toggle": newState })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (newState) {
                        document.body.classList.add("glitch-effect");
                    } else {
                        document.body.classList.remove("glitch-effect");
                    }
                } else {
                    console.error("Ошибка обновления состояния глича:", data.error);
                }
            })
            .catch(error => {
                console.error("Ошибка при отправке запроса:", error);
            });
        });
    }
});
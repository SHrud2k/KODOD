(function(){
    const canvas = document.getElementById("snakeCanvas");
    const ctx = canvas.getContext("2d");
    const grid = 20;
    let count = 0;
    let snake = { x: 160, y: 160, cells: [], maxCells: 4 };
    let apple = { x: 320, y: 320 };
    let dx = grid;
    let dy = 0;
    let score = 0;

    function getRandomInt(min, max) {
      return Math.floor(Math.random() * (max - min)) + min;
    }

    function gameLoop() {
      requestAnimationFrame(gameLoop);
      // Обновляем игру каждые 16 кадров (в два раза медленнее)
      if (++count < 16) {
        return;
      }
      count = 0;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      snake.x += dx;
      snake.y += dy;

      // Оборачивание змейки по краям
      if (snake.x < 0) {
        snake.x = canvas.width - grid;
      } else if (snake.x >= canvas.width) {
        snake.x = 0;
      }
      if (snake.y < 0) {
        snake.y = canvas.height - grid;
      } else if (snake.y >= canvas.height) {
        snake.y = 0;
      }

      snake.cells.unshift({x: snake.x, y: snake.y});
      if (snake.cells.length > snake.maxCells) {
        snake.cells.pop();
      }

      // Рисуем яблоко
      ctx.fillStyle = "#F00";
      ctx.fillRect(apple.x, apple.y, grid-1, grid-1);

      ctx.fillStyle = "#0F0";
      snake.cells.forEach(function(cell, index) {
          ctx.fillRect(cell.x, cell.y, grid-1, grid-1);

          // Если змейка съела яблоко
          if (cell.x === apple.x && cell.y === apple.y) {
            snake.maxCells++;
            score = snake.maxCells - 4;
            document.getElementById("snakeScore").innerText = "Score: " + score;
            apple.x = getRandomInt(0, canvas.width / grid) * grid;
            apple.y = getRandomInt(0, canvas.height / grid) * grid;
          }

          // Проверка столкновений с телом змейки
          for (let i = index + 1; i < snake.cells.length; i++) {
              if (cell.x === snake.cells[i].x && cell.y === snake.cells[i].y) {
                  // Сброс игры
                  snake.x = 160;
                  snake.y = 160;
                  snake.cells = [];
                  snake.maxCells = 4;
                  dx = grid;
                  dy = 0;
                  score = 0;
                  document.getElementById("snakeScore").innerText = "Score: " + score;
                  apple.x = getRandomInt(0, canvas.width / grid) * grid;
                  apple.y = getRandomInt(0, canvas.height / grid) * grid;
              }
          }
      });

      // Рисуем счет на холсте (опционально)
      ctx.fillStyle = "#0F0";
      ctx.font = "16px Courier New";
      ctx.fillText("Score: " + score, 10, 20);
    }

    document.addEventListener("keydown", function(e) {
        if (e.which === 37 && dx === 0) {
            dx = -grid;
            dy = 0;
        } else if (e.which === 38 && dy === 0) {
            dy = -grid;
            dx = 0;
        } else if (e.which === 39 && dx === 0) {
            dx = grid;
            dy = 0;
        } else if (e.which === 40 && dy === 0) {
            dy = grid;
            dx = 0;
        }
    });

    requestAnimationFrame(gameLoop);
})();
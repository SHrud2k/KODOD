(function(){
    const canvas = document.getElementById("pongCanvas");
    const ctx = canvas.getContext("2d");

    let paddleWidth = 10, paddleHeight = 80;
    let playerX = 10, playerY = (canvas.height - paddleHeight) / 2;
    let aiX = canvas.width - paddleWidth - 10, aiY = (canvas.height - paddleHeight) / 2;
    let ballRadius = 8;
    let ballX = canvas.width / 2, ballY = canvas.height / 2;
    // Уменьшаем скорость мяча в три раза: 2 → ~0.67
    let ballSpeedX = 0.67, ballSpeedY = 0.67;
    let playerScore = 0, aiScore = 0;

    function drawRect(x, y, w, h, color) {
        ctx.fillStyle = color;
        ctx.fillRect(x, y, w, h);
    }

    function drawCircle(x, y, r, color) {
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI*2);
        ctx.closePath();
        ctx.fill();
    }

    function drawNet() {
        for(let i = 0; i < canvas.height; i += 15){
            drawRect(canvas.width/2 - 1, i, 2, 10, "#0F0");
        }
    }

    function moveAI() {
        let centerY = aiY + paddleHeight/2;
        if(centerY < ballY - 10) {
            aiY += 1;  // немного медленнее
        } else if(centerY > ballY + 10) {
            aiY -= 1;
        }
    }

    function update() {
        ballX += ballSpeedX;
        ballY += ballSpeedY;

        if(ballY - ballRadius < 0 || ballY + ballRadius > canvas.height) {
            ballSpeedY = -ballSpeedY;
        }

        // Если мяч выходит за границы по X, обновляем счет и сбрасываем мяч
        if(ballX - ballRadius < 0) {
            aiScore++;
            updateScore();
            resetBall();
        } else if(ballX + ballRadius > canvas.width) {
            playerScore++;
            updateScore();
            resetBall();
        }

        // Столкновение с левой ракеткой
        if(ballX - ballRadius < playerX + paddleWidth && ballY > playerY && ballY < playerY + paddleHeight) {
            ballSpeedX = -ballSpeedX;
            let deltaY = ballY - (playerY + paddleHeight/2);
            ballSpeedY = deltaY * 0.35;
        }
        // Столкновение с правой ракеткой
        if(ballX + ballRadius > aiX && ballY > aiY && ballY < aiY + paddleHeight) {
            ballSpeedX = -ballSpeedX;
            let deltaY = ballY - (aiY + paddleHeight/2);
            ballSpeedY = deltaY * 0.35;
        }

        moveAI();
    }

    function resetBall() {
        ballX = canvas.width / 2;
        ballY = canvas.height / 2;
        // Перезадаем скорость мяча с уменьшенными значениями
        ballSpeedX = (ballSpeedX > 0 ? 0.67 : -0.67);
        ballSpeedY = 0.67;
    }

    function updateScore() {
        document.getElementById("pongScore").innerText = "Player: " + playerScore + " | AI: " + aiScore;
    }

    function render() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawNet();
        drawRect(playerX, playerY, paddleWidth, paddleHeight, "#0F0");
        drawRect(aiX, aiY, paddleWidth, paddleHeight, "#0F0");
        drawCircle(ballX, ballY, ballRadius, "#0F0");
        // Рисуем счет на холсте (опционально)
        ctx.fillStyle = "#0F0";
        ctx.font = "20px Courier New";
        ctx.fillText("Player: " + playerScore, 50, 30);
        ctx.fillText("AI: " + aiScore, canvas.width - 150, 30);
    }

    function gameLoop() {
        update();
        render();
        requestAnimationFrame(gameLoop);
    }

    document.addEventListener("keydown", function(e) {
        if(e.key === "ArrowUp") {
            playerY -= 20;
            if(playerY < 0) playerY = 0;
        } else if(e.key === "ArrowDown") {
            playerY += 20;
            if(playerY + paddleHeight > canvas.height) playerY = canvas.height - paddleHeight;
        }
    });

    requestAnimationFrame(gameLoop);
})();
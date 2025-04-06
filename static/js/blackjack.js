document.addEventListener("DOMContentLoaded", function() {
    // Настраиваемые тайминги анимаций (в мс)
    const CARD_DRAW_DELAY = 800;         // задержка между добором карт дилера
    const DECK_SHAKE_DURATION = 500;       // длительность анимации колоды
    const CARD_ANIMATION_DURATION = 500;   // длительность анимации перемещения карты (fadeIn)

    const statusDiv = document.getElementById("game-status");
    const playerCardsDiv = document.getElementById("player-cards");
    const dealerCardsDiv = document.getElementById("dealer-cards");
    const scoreDiv = document.getElementById("score");
    const messageDiv = document.getElementById("message");
    const hitBtn = document.getElementById("hitBtn");
    const standBtn = document.getElementById("standBtn");
    const restartBtn = document.getElementById("restartBtn");
    const deckDiv = document.getElementById("deck");

    let deck = [];
    let playerHand = [];
    let dealerHand = [];
    let gameOver = false;
    let lastPlayerCount = 0;
    let lastDealerCount = 0;

    function createDeck() {
        deck = [];
        const suits = ["♠", "♥", "♦", "♣"];
        const values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"];
        for (let suit of suits) {
            for (let value of values) {
                deck.push({ suit: suit, value: value });
            }
        }
        deck.sort(() => Math.random() - 0.5);
    }

    function cardValue(card) {
        if (card.value === "A") return 11;
        if (["K", "Q", "J"].includes(card.value)) return 10;
        return parseInt(card.value);
    }

    function handScore(hand) {
        let score = hand.reduce((sum, card) => sum + cardValue(card), 0);
        let aces = hand.filter(card => card.value === "A").length;
        while (score > 21 && aces > 0) {
            score -= 10;
            aces--;
        }
        return score;
    }

    function displayHand(hand) {
        return hand.map(card => card.value + card.suit).join(" ");
    }

    // Функция рендеринга руки. Если isDealer=true и игра не окончена, показываем только первую карту дилера.
    function renderHand(container, hand, isDealer = false) {
        if (isDealer && !gameOver) {
            container.innerText = "Карты дилера: " + dealerHand[0].value + dealerHand[0].suit + " ?";
            return;
        }
        container.innerHTML = (isDealer ? "Карты дилера: " : "Ваши карты: ");
        hand.forEach((card, index) => {
            let span = document.createElement("span");
            span.innerText = card.value + card.suit + " ";
            // Если это новая карта, добавляем класс для анимации (CSS класс fade-in-card)
            if ((isDealer && index >= lastDealerCount) || (!isDealer && index >= lastPlayerCount)) {
                span.classList.add("fade-in-card");
            }
            container.appendChild(span);
        });
        if (!isDealer) {
            container.innerHTML += " (Счет: " + handScore(hand) + ")";
            lastPlayerCount = hand.length;
        } else {
            container.innerHTML += " (Счет: " + handScore(hand) + ")";
            lastDealerCount = hand.length;
        }
    }

    function updateDisplay() {
        renderHand(playerCardsDiv, playerHand, false);
        renderHand(dealerCardsDiv, dealerHand, true);
        scoreDiv.innerText = "";
    }

    // Анимация колоды: добавляем класс "shake" к элементу колоды на заданное время
    function animateDeck() {
        if (deckDiv) {
            deckDiv.classList.add("shake");
            setTimeout(() => {
                deckDiv.classList.remove("shake");
            }, DECK_SHAKE_DURATION);
        }
    }

    // Анимация перемещения карты дилера: принимает объект card и callback.
    function animateDealerCard(card, callback) {
        let tempCard = document.createElement("div");
        tempCard.innerText = card.value + card.suit;
        // Стилизация временного элемента карты
        tempCard.style.position = "absolute";
        tempCard.style.background = "#0F0";
        tempCard.style.color = "#000";
        tempCard.style.padding = "5px 8px";
        tempCard.style.border = "1px solid #000";
        tempCard.style.borderRadius = "4px";
        tempCard.style.fontFamily = "Courier New, monospace";
        // Позиционируем временную карту в позиции колоды
        let deckRect = deckDiv.getBoundingClientRect();
        tempCard.style.left = deckRect.left + "px";
        tempCard.style.top = deckRect.top + "px";
        tempCard.style.transition = `all ${CARD_ANIMATION_DURATION}ms ease-out`;
        document.body.appendChild(tempCard);

        // Определяем целевую позицию: центр области дилера (dealerCardsDiv)
        let dealerRect = dealerCardsDiv.getBoundingClientRect();
        let targetX = dealerRect.left + dealerRect.width/2 - 20; // отрегулируйте по необходимости
        let targetY = dealerRect.top + dealerRect.height/2 - 20;

        setTimeout(() => {
            tempCard.style.left = targetX + "px";
            tempCard.style.top = targetY + "px";
        }, 50);

        setTimeout(() => {
            document.body.removeChild(tempCard);
            callback();
        }, CARD_ANIMATION_DURATION + 100);
    }

    // Функция добора карт дилера с анимацией: если счет дилера меньше 17, анимированно добираем карту.
    function dealerDraw(callback) {
        if (handScore(dealerHand) < 17) {
            if (deck.length === 0) {
                callback();
                return;
            }
            let card = deck.pop();
            animateDealerCard(card, function(){
                dealerHand.push(card);
                updateDisplay();
                setTimeout(function(){
                    dealerDraw(callback);
                }, CARD_DRAW_DELAY);
            });
        } else {
            callback();
        }
    }

    function startGame() {
        createDeck();
        playerHand = [];
        dealerHand = [];
        gameOver = false;
        lastPlayerCount = 0;
        lastDealerCount = 0;
        statusDiv.innerText = "Ваш ход";
        messageDiv.innerText = "";
        hitBtn.disabled = false;
        standBtn.disabled = false;
        restartBtn.style.display = "none";
        // Раздаем по 2 карты игроку и дилеру
        playerHand.push(deck.pop(), deck.pop());
        dealerHand.push(deck.pop(), deck.pop());
        updateDisplay();
    }

    function playerHit() {
        animateDeck();
        playerHand.push(deck.pop());
        updateDisplay();
        if (handScore(playerHand) > 21) {
            endGame("Вы проиграли! Перебор.");
        }
    }

    function playerStand() {
        dealerDraw(function() {
            let playerScore = handScore(playerHand);
            let dealerScore = handScore(dealerHand);
            if (dealerScore > 21) {
                endGame("Вы выиграли! Дилер перебор.");
            } else if (playerScore === dealerScore) {
                endGame("Ничья.");
            } else if (playerScore > dealerScore) {
                endGame("Вы выиграли!");
            } else {
                endGame("Вы проиграли.");
            }
        });
    }

    function endGame(result) {
        gameOver = true;
        statusDiv.innerText = "Игра окончена";
        messageDiv.innerText = result;
        hitBtn.disabled = true;
        standBtn.disabled = true;
        restartBtn.style.display = "inline-block";
        updateDisplay();
    }

    hitBtn.addEventListener("click", playerHit);
    standBtn.addEventListener("click", playerStand);
    restartBtn.addEventListener("click", startGame);

    startGame();
});
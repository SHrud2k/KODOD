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
    // Флаг, показывающий, что скрытая карта дилера раскрыта
    let dealerTurn = false;
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

    // Функция рендеринга руки.
    // До раскрытия скрытой карты (dealerTurn==false) для дилера показывается первая карта и placeholder.
    // Когда dealerTurn==true или игра окончена, отображаются все карты дилера.
    function renderHand(container, hand, isDealer = false) {
        container.innerHTML = (isDealer ? "Карты дилера: " : "Ваши карты: ");
        if (isDealer && !dealerTurn && !gameOver) {
            // До раскрытия скрытой карты показываем только первую карту
            if (hand.length > 0) {
                let span = document.createElement("span");
                span.innerText = hand[0].value + hand[0].suit + " ";
                span.style.display = "inline-block";
                span.style.marginRight = "5px";
                if (lastDealerCount === 0) {
                    span.classList.add("fade-in-card");
                }
                container.appendChild(span);
            }
            // Добавляем placeholder для скрытой карты
            let placeholder = document.createElement("span");
            placeholder.innerText = " ? ";
            placeholder.style.display = "inline-block";
            placeholder.style.marginRight = "5px";
            container.appendChild(placeholder);
            container.innerHTML += " (Счет: ?)";
            lastDealerCount = hand.length;
        } else {
            // Отображаем все карты
            hand.forEach((card, index) => {
                let span = document.createElement("span");
                span.innerText = card.value + card.suit + " ";
                span.style.display = "inline-block";
                span.style.marginRight = "5px";
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
    }

    function updateDisplay() {
        renderHand(playerCardsDiv, playerHand, false);
        renderHand(dealerCardsDiv, dealerHand, true);
        scoreDiv.innerText = "";
    }

    // Анимация колоды: добавляем класс "shake" к элементу колоды на заданное время.
    function animateDeck() {
        if (deckDiv) {
            deckDiv.classList.add("shake");
            setTimeout(() => {
                deckDiv.classList.remove("shake");
            }, DECK_SHAKE_DURATION);
        }
    }

    // Анимация перемещения карты дилера: карта перемещается из позиции колоды в область дилера.
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
        let targetX = dealerRect.left + dealerRect.width / 2 - 20;
        let targetY = dealerRect.top + dealerRect.height / 2 - 20;

        setTimeout(() => {
            tempCard.style.left = targetX + "px";
            tempCard.style.top = targetY + "px";
        }, 50);

        setTimeout(() => {
            document.body.removeChild(tempCard);
            callback();
        }, CARD_ANIMATION_DURATION + 100);
    }

    // Функция добора карт дилера с анимацией.
    // Для каждого вытягиваемого элемента запускается анимация колоды и перемещения карты.
    function dealerDraw(callback) {
        if (handScore(dealerHand) < 17) {
            if (deck.length === 0) {
                callback();
                return;
            }
            let card = deck.pop();
            animateDeck();
            animateDealerCard(card, function() {
                dealerHand.push(card);
                updateDisplay();
                setTimeout(function() {
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
        dealerTurn = false;
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

    // При нажатии кнопки Hit добавляется карта игрока без анимации тряски колоды.
    function playerHit() {
        playerHand.push(deck.pop());
        updateDisplay();
        if (handScore(playerHand) > 21) {
            endGame("Вы проиграли! Перебор.");
        }
    }

    // При нажатии на Stand сначала раскрывается скрытая карта дилера,
    // затем запускается анимация добора оставшихся карт дилером.
    function playerStand() {
        dealerTurn = true;  // раскрываем скрытую карту дилера
        updateDisplay();    // обновляем отображение, чтобы скрытая карта стала видна
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
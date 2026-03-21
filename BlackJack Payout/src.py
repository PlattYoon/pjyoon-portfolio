import os
import cv2
import cmu_graphics
from cmu_graphics import *
from cmu_graphics import Image
import random

#https://www.geeksforgeeks.org/pyqt5-how-to-change-font-and-size-of-label-text/
#chat gpt for general instructions on importing videos into python
#from https://www.youtube.com/watch?v=lGtjVW-P1E4 and chatgpt for importing video
#Vegas montage https://www.youtube.com/watch?v=9uZ8CCa0t4Y&t=509s
#buttons https://www.geeksforgeeks.org/python-creating-a-button-in-tkinter/
#https://www.geeksforgeeks.org/multithreading-python-set-1/ for thereading
#https://www.youtube.com/watch?v=hN2Yrf4tqTY for threading algorithms
#chatgpt for general syntax for threading and understanding threading
#https://sdlccorp.com/post/what-is-a-rummy-in-blackjack/
#difficulty of blackjack was derived by code in https://www.geeksforgeeks.org/blackjack-console-game-using-python/
#Chatgpt for conversion from pyqt5 to cmu graphics
#blackjack https://www.youtube.com/watch?v=PljDuynF-j0 reasoning
#https://www.youtube.com/watch?v=BWFrkpq1Kg8 early payout blackjack reference
#https://www.youtube.com/watch?v=mpL0Y01v6tY blackjack logic
#https://www.youtube.com/watch?v=Au6FPjkgbUE popup window in python
# integrating images in python :https://www.geeksforgeeks.org/working-images-python/ and chatgpt
#how to run simulations in python : https://discovery.cs.illinois.edu/learn/Simulation-and-Distributions/Simple-Simulations-in-Python/
#simulation modeling in python: https://www.geeksforgeeks.org/introduction-to-simulation-modeling-in-python/
# simulation modules in python: https://medium.com/@sumit.tripathi/create-your-first-animated-simulation-model-on-python-in-4-steps-2ae18a4f340f
# image generation: chatgpt and https://deepai.org/machine-learning-model/retro-game-generator
#chatgpt for random.shuffle and timer
#chatgpt for general ideas of integration of blackjacktable class and blackjackgame class
#how to reference one class to another: https://stackoverflow.com/questions/17671242/composition-reference-to-another-class-in-python
#pokerchip images : chatgpt
#card images: https://www.istockphoto.com/search/2/image-film?phrase=blackjack+cards
#blackjack overall module inspiration : https://www.247blackjack.com/
#debugging for early payout module : chatgpt and https://www.onlinegdb.com/online_python_debugger
#checking tuples :https://www.geeksforgeeks.org/python-check-if-variable-is-tuple/
#trips : https://www.888poker.com/magazine/poker-terms/trips#:~:text=Trips%20is%20a%20common%20colloquial,pocket%20pair%20in%20Hold'em.
#class within a class: https://docs.python.org/3/tutorial/classes.html
#referencing different classes : https://softwareengineering.stackexchange.com/questions/448562/why-access-the-attributes-of-a-python-class-by-reference
class CourseOfAction:
    def __init__(self, deck, playerId, table):
        self.deck = deck
        self.playerId = playerId
        self.table = table

    def split(self):s
        hand = self.deck.hands[self.playerId]
        if len(hand) == 2 and hand[0][0] == hand[1][0]:
            newHandId = max(self.deck.hands.keys()) + 1
            self.deck.hands[newHandId] = [hand.pop()]
            self.deck.dealCard(self.playerId)
            self.deck.dealCard(newHandId)
            return "Hand split!"
        return "Cannot split, cards do not match."

    def doubleDown(self):
        if len(self.deck.hands[self.playerId]) == 2:
            self.deck.dealCard(self.playerId)
            playerValue = self.deck.calculateHandValue(self.deck.hands[self.playerId])
            dealerValue = self.deck.calculateHandValue(self.deck.dealerHand)
            if playerValue > 21:
                return "You lose!"
            elif playerValue > dealerValue or dealerValue > 21:
                return "You win!"
            else:
                return "You lose!"
        return "Cannot double down, not at the start of the round."

    def stand(self):
        playerValue = self.deck.calculateHandValue(self.deck.hands[self.playerId])
        dealerValue = self.deck.calculateHandValue(self.deck.dealerHand)
        while dealerValue < 17:
            self.deck.dealCard(toDealer=True)
            dealerValue = self.deck.calculateHandValue(self.deck.dealerHand)
        self.table.update_hand_values()
        return self.check_winner(playerValue, dealerValue)

    def hit(self):
        self.deck.dealCard(self.playerId)
        playerValue = self.deck.calculateHandValue(self.deck.hands[self.playerId])
        self.table.update_hand_values()

        if playerValue > 21:
            return "You bust! Game over."
        return "You took a hit!"

    def check_winner(self, playerValue, dealerValue):
        if playerValue > 21:
            print("Player busts! You lose.")
            self.table.update_balance(self.table.balance - self.table.bet)
            return "Player busts!"
        elif dealerValue > 21:
            print("Dealer busts! You win.")
            self.table.update_balance(self.table.balance + self.table.bet)
            return "Dealer busts!"
        elif playerValue > dealerValue:
            print("You win!")
            self.table.update_balance(self.table.balance + self.table.bet)
            return "You win!"
        elif playerValue < dealerValue:
            print("Dealer wins! You lose.")
            self.table.update_balance(self.table.balance - self.table.bet)
            return "Dealer wins!"
        else:
            print("It's a tie!")
            return "Tie"

    def simulate(self, playerValue, dealerValue, deck, isDealerTurn):
        print(
            f"Simulating: Player Value = {playerValue}, Dealer Value = {dealerValue}, Is Dealer Turn = {isDealerTurn}, Deck Size = {len(deck)}")
        if playerValue > 21:
            print("Player busts!")
            return False
        if dealerValue > 21:
            print("Dealer busts!")
            return True
        if isDealerTurn and dealerValue >= 17:
            print(f"Dealer stands. Dealer Value = {dealerValue}, Player Value = {playerValue}")
            if dealerValue > playerValue:
                return False
            elif dealerValue < playerValue:
                return True
            else:
                return None

        outcomes = []
        for i, card in enumerate(deck):
            nextCardValue = self.cardValue(card[0])
            newDeck = deck[:i] + deck[i + 1:]

            print(f"Card drawn: {card[0]} of {card[1]}. New deck size: {len(newDeck)}")

            if isDealerTurn:
                result = self.simulate(playerValue, dealerValue + nextCardValue, newDeck, True)
            else:
                result = self.simulate(playerValue + nextCardValue, dealerValue, newDeck, not isDealerTurn)

            outcomes.append(result)

        wins = outcomes.count(True)
        losses = outcomes.count(False)

        if wins > losses:
            return True
        elif losses > wins:
            return False
        else:
            return None

    def cardValue(self, card):
        if card in ['J', 'Q', 'K']:
            return 10
        elif card == 'A':
            return 11
        else:
            return int(card)

    def earlyPayout(self):
        playerHand = self.player_hand
        dealerUpcard = self.dealer_hand[0]
        remainingDeck = self.deck

        winProbability = self.simulateOutcomes(playerHand, dealerUpcard, remainingDeck)
        print(f"Debug: Win Probability = {winProbability:.2f}")

        betAmount = self.mainBetAmount
        payoutRatio = winProbability
        earlyPayoutOffer = max(0, betAmount * payoutRatio * 0.8)

        if earlyPayoutOffer < betAmount:
            return f"Early Payout Offer: ${earlyPayoutOffer:.2f}"
        else:
            return "Early payout not favorable. Continue playing."

    def simulateOutcomes(self, playerHand, dealerUpcard, remainingDeck):

        playerValue = self.deck.calculateHandValue(playerHand)
        dealerValue = self.deck.calculateHandValue([dealerUpcard])
        totalSimulations = 0
        playerWins = 0


        for i, card in enumerate(remainingDeck):
            cardValue = self.calculateCardValue(card)
            newDeck = remainingDeck[:i] + remainingDeck[i + 1:]
            if self.simulate(playerValue, dealerValue + cardValue, newDeck, isDealerTurn=True):
                playerWins += 1
            totalSimulations += 1

        return playerWins / totalSimulations if totalSimulations > 0 else 0

    def simulate(self, playerValue, dealerValue, remainingDeck, isDealerTurn):
        print(
            f"Simulating: Player Value = {playerValue}, Dealer Value = {dealerValue}, "
            f"Is Dealer Turn = {isDealerTurn}, Deck Size = {len(remainingDeck)}"
        )

        if playerValue > 21:
            print("Player busts!")
            return False
        if dealerValue > 21:
            print("Dealer busts!")
            return True
        if isDealerTurn and dealerValue >= 17:
            print(f"Dealer stands. Dealer Value = {dealerValue}, Player Value = {playerValue}")
            if dealerValue > playerValue:
                return False
            elif dealerValue < playerValue:
                return True
            else:
                return None

        outcomes = []
        for i, card in enumerate(remainingDeck):
            cardValue = calculateCardValue(card)
            newDeck = remainingDeck[:i] + remainingDeck[i + 1:]

            print(f"Card drawn: {card[0]} of {card[1]}. New deck size: {len(newDeck)}")

            if isDealerTurn:
                result = self.simulate(playerValue, dealerValue + cardValue, newDeck, True)
            else:
                result = self.simulate(playerValue + cardValue, dealerValue, newDeck, not isDealerTurn)

            outcomes.append(result)

        wins = outcomes.count(True)
        losses = outcomes.count(False)

        if wins > losses:
            return True
        elif losses > wins:
            return False
        else:
            return None

    def calculateCardValue(card):
        value, suit = card
        if value in ['J', 'Q', 'K']:
            return 10
        elif value == 'A':
            return 11
        else:
            return int(value)


# https://sdlccorp.com/post/what-is-a-rummy-in-blackjack/
class SideBets:
    def __init__(self, deck, playerId):
        self.deck = deck
        self.playerId = playerId

    def rummy(self):
        playerHand = self.deck.hands[self.playerId]
        if len(self.deck.dealerHand) < 1:
            return "Dealer's upcard is not available yet."
        dealerUpcard = self.deck.dealerHand[0]
        combinedHand = playerHand + [dealerUpcard]
        suits = [card[1] for card in combinedHand]
        values = [card[0] for card in combinedHand]
        valueCounts = {value: values.count(value) for value in values}
        if 3 in valueCounts.values():
            return "Rummy win: Set (Three of a Kind)!"
        valueOrder = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        valueIndices = sorted([valueOrder.index(v) for v in values])
        if all(suits[0] == s for s in suits) and all(
                valueIndices[i] + 1 == valueIndices[i + 1] for i in range(len(valueIndices) - 1)
        ):
            return "Rummy win: Run (Straight Flush)!"
        return "No Rummy win."

    def pairs(self):
        hand = self.deck.hands[self.playerId]
        if len(hand) >= 2 and hand[0][0] == hand[1][0]:
            return f"Pairs win: Player {self.playerId} has a pair of {hand[0][0]}!"
        return "No pairs win."

    def luckyLadies(self):
        hand = self.deck.hands[self.playerId]
        if len(hand) == 2 and all(card[0] == 'Q' for card in hand):
            return "Lucky Ladies win: Two Queens!"
        return "No Lucky Ladies win."


class BlackjackGame:
    def __init__(self, deck, table):
        self.table = table
        self.deck = deck
        self.player_hand = []
        self.dealer_hand = []

    def deal_card(self):
        print(1)
        return self.deck.pop()

    def format_card_name(value, suit):
        return f"{value.lower()}of{suit.lower()}"

    def start_round(self):
        self.player_hand = [self.deck.deal_card(), self.deck.deal_card()]
        self.dealer_hand = [self.deck.deal_card(), "hidden"]

        print(f"1start_round - Player's Hand: {self.player_hand}")
        print(f"1start_round - Dealer's Hand: {self.dealer_hand}")

    def format_card_name(value, suit):
        return f"{value.lower()}of{suit.lower()}"

    def hit(self, dealer=False):
        if dealer:
            card = self.deal_card()
            self.dealer_hand.append(card)
            print(f"Dealer hits and gets {card}. Dealer's Hand: {self.dealer_hand}")
        else:
            card = self.deal_card()
            self.player_hand.append(card)
            print(f"Player hits and gets {card}. Player's Hand: {self.player_hand}")

    def stand(self):
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        while dealer_value < 17:
            card = self.deal_card()
            self.dealer_hand.append(card)
            dealer_value = self.calculate_hand_value(self.dealer_hand)

        self.table.update_hand_values()
        self.table.show_cards(self.player_hand, self.dealer_hand)

    def calculate_hand_value(self, hand):
        value = 0
        aces = 0
        for card in hand:
            card_value = card.split('_')[0]
            if card_value in ['J', 'Q', 'K']:
                value += 10
            elif card_value == 'A':
                aces += 1
                value += 11
            else:
                value += int(card_value)

        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value





class CardDeck:
    def __init__(self):
        self.deck = self.createDeck()

    def createDeck(self):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [f"{value}_{suit}" for suit in suits for value in values]
        random.shuffle(deck)
        return deck

    def deal_card(self):
        if self.deck:
            return self.deck.pop()
        else:
            raise ValueError("No more cards in the deck")

    def calculateHandValue(self, hand):
        value = 0
        aces = 0
        for card, _ in hand:
            if card in ['J', 'Q', 'K']:
                value += 10
            elif card == 'A':
                aces += 1
                value += 11
            else:
                value += int(card)
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        return value


    def __repr__(self):
        representation = []
        dealerValue = self.calculateHandValue(self.dealerHand)
        representation.append(f"Dealer: {self.dealerHand} | Value: {dealerValue}")
        for playerId, hand in self.hands.items():
            handValue = self.calculateHandValue(hand)
            representation.append(f"Player {playerId}: {hand} | Value: {handValue}")
        return "\n".join(representation)

class EasyDeck(CardDeck):
    def __init__(self):
        super().__init__()
        self.deck = self.createDeck()
        random.shuffle(self.deck)

    def deal_card(self):
        if self.deck:
            return self.deck.pop()
        else:
            raise ValueError("No more cards in the deck")


class MediumDeck(CardDeck):
    def __init__(self):
        super().__init__()
        self.deck = self.createDeck()
        random.shuffle(self.deck)

    def setup_dealer_hand(self):
        self.dealerHand = []
        if random.random() < 0.15:
            self.dealerHand.append(("A", random.choice(['Hearts', 'Diamonds', 'Clubs', 'Spades'])))
            self.dealerHand.append((random.choice(['10', 'J', 'Q', 'K']),
                                     random.choice(['Hearts', 'Diamonds', 'Clubs', 'Spades'])))
        else:
            self.dealCard(toDealer=True)
            self.dealCard(toDealer=True)


class HardDeck(CardDeck):
    def __init__(self):
        super().__init__()
        self.deck = self.createDeck()
        random.shuffle(self.deck)

    def setup_dealer_hand(self):
        self.dealerHand = []
        if random.random() < 0.25:
            self.dealerHand.append(("A", random.choice(['Hearts', 'Diamonds', 'Clubs', 'Spades'])))
            self.dealerHand.append((random.choice(['10', 'J', 'Q', 'K']),
                                     random.choice(['Hearts', 'Diamonds', 'Clubs', 'Spades'])))
        else:
            self.dealCard(toDealer=True)
            self.dealCard(toDealer=True)



class BlackjackTable:
    def __init__(self, app, difficulty):
        self.app = app
        self.difficulty = difficulty
        self.deck = self.createDeck()
        self.selectedSideBet = None
        self.mainBetAmount = 0
        self.width = 1550
        self.height = 1000
        self.table_image = "/Users/jonghyunyoon/Desktop/blackjackcloth.png"
        self.player_hand = []
        self.dealer_hand = []
        self.balance = 1000
        self.card_images_directory = "/Users/jonghyunyoon/Desktop/cards/"
        self.card_positions = {
            "player": [(400, 500), (500, 500), (600, 500),(700,500),(800,500),(900,500),(1000,500),(1100,500)],
            "dealer": [(400, 200), (500, 200), (600, 200),(700,200),(800,200),(900,200),(1000,200),(1100,200)],
        }
        self.phase = "sidebets"
        self.sideBets = {
            "Rummies": 0,
            "Triple 7s": 0,
            "Pairs": 0,
        }
        self.winner_display = None

        self.chips = [
            {"value": 1, "pos": (89, 107), "realx" : 185, "realy" : 214,  "image": "/Users/jonghyunyoon/Desktop/ones.png"},
            {"value": 10, "pos": (89, 307), "realx" : 185, "realy": 404, "image": "/Users/jonghyunyoon/Desktop/ten.png"},
            {"value": 100, "pos": (89, 507), "realx": 185, "realy" : 794, "image": "/Users/jonghyunyoon/Desktop/hundred.png"},
            {"value": 500, "pos": (89, 707), "realx": 185, "realy": 795, "image": "/Users/jonghyunyoon/Desktop/fivehundred.png"}
        ]
        self.dragged_chip = None
        self.sidebet_buttons = [
            {"name":"trips", "pos": (740, 205), "image": "/Users/jonghyunyoon/Desktop/trips.png"},
            {"name": "rummies","pos": (498, 205), "image": "/Users/jonghyunyoon/Desktop/rummies.png"},
            {"name": "pairs", "pos": (632, 469), "image": "/Users/jonghyunyoon/Desktop/pairs.png"}
        ]

        self.main_bet_button = {"label": "Main Bet", "pos": (self.width // 2, self.height // 2 + 50)}

        self.action_buttons = [
            {"name": "stand", "pos": (880, 680), "image": "/Users/jonghyunyoon/Desktop/stand.png"},
            {"name": "hit", "pos": (500, 670),"image": "/Users/jonghyunyoon/Desktop/hit.png"},
            {"name": "earlypayout", "pos": (675, 665),"image": "/Users/jonghyunyoon/Desktop/earlypayout.png"}
        ]
    def deal_card(self):
        if self.deck:
            print(1,self.deck)
            return self.deck.pop()
        else:
            raise ValueError("No more cards in the deck")

    def earlyPayout(self):

        if not self.deck:
            print("[ERROR] Deck is not initialized correctly.")
            return "Error: Unable to calculate early payout."

        playerHand = self.player_hand
        dealerUpcard = self.dealer_hand[0]
        remainingDeck = self.deck

        playerValue = self.calculateHandValue(playerHand)
        dealerValue = self.calculateHandValue([dealerUpcard])

        winProbability = self.simulateOutcomes(playerValue, dealerValue, remainingDeck)
        print(f"[DEBUG] Win Probability = {winProbability:.2f}")

        betAmount = self.mainBetAmount
        earlyPayoutOffer = max(0, betAmount * winProbability * 0.8)

        if earlyPayoutOffer < betAmount:
            return f"Early Payout Offer: ${earlyPayoutOffer:.2f}"
        else:
            return "Early payout not favorable. Continue playing."

    def simulateOutcomes(self, playerValue, dealerValue, remainingDeck):
        totalSimulations = 0
        playerWins = 0

        for i, card in enumerate(remainingDeck):
            cardValue = self.getCardValue(card)
            newDeck = remainingDeck[:i] + remainingDeck[i + 1:]

            if self.simulate(playerValue, dealerValue + cardValue, newDeck, isDealerTurn=True):
                playerWins += 1
            totalSimulations += 1

        return playerWins / totalSimulations if totalSimulations > 0 else 0

    def simulate(self, playerValue, dealerValue, remainingDeck, isDealerTurn):
        if playerValue > 21:
            return False
        if dealerValue > 21:
            return True
        if isDealerTurn and dealerValue >= 17:
            return dealerValue < playerValue
        outcomes = []
        for i, card in enumerate(remainingDeck):
            cardValue = self.getCardValue(card)
            newDeck = remainingDeck[:i] + remainingDeck[i + 1:]

            if isDealerTurn:
                result = self.simulate(playerValue, dealerValue + cardValue, newDeck, True)
            else:
                result = self.simulate(playerValue + cardValue, dealerValue, newDeck, not isDealerTurn)

            outcomes.append(result)

        wins = outcomes.count(True)
        losses = outcomes.count(False)

        return wins > losses

    def getCardValue(self,card):
        value, suit = card
        if value in ['J', 'Q', 'K']:
            return 10
        elif value == 'A':
            return 11
        return int(value)

    def start_round(self):
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), "hidden"]

        print(f"1start_round - Player's Hand: {self.player_hand}")
        print(f"1start_round - Dealer's Hand: {self.dealer_hand}")
    def hit(self, dealer=False):
        if dealer:
            card = self.deal_card()
            self.dealer_hand.append(card)
            print(f"Dealer hits and gets {card}. Dealer's Hand: {self.dealer_hand}")
        else:
            card = self.deal_card()
            self.player_hand.append(card)
            print(f"Player hits and gets {card}. Player's Hand: {self.player_hand}")

    def stand(self):
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        while dealer_value < 17:
            card = self.deal_card()
            self.dealer_hand.append(card)
            dealer_value = self.calculate_hand_value(self.dealer_hand)

        self.table.update_hand_values()
        self.table.show_cards(self.player_hand, self.dealer_hand)

    def calculateHandValue(self, hand):
        value = 0
        aces = 0

        for card in hand:
            if isinstance(card, tuple):
                cardValue = card[0]
                if cardValue in ['J', 'Q', 'K']:
                    value += 10
                elif cardValue == 'A':
                    aces += 1
                    value += 11
                else:
                    value += int(cardValue)
            else:
                print(f"[DEBUG] Invalid card: {card}")
                continue

        while value > 21 and aces > 0:
            value -= 10
            aces -= 1

        return value

    def calculate_hand_value(self, hand):
        value = 0
        aces = 0

        for card in hand:
            if isinstance(card, tuple):
                card_value = card[0]
                if card_value in ['J', 'Q', 'K']:
                    value += 10
                elif card_value == 'A':
                    aces += 1
                    value += 11
                else:
                    value += int(card_value)
            else:
                print(f"[DEBUG] Invalid card: {card}")
                continue

        while value > 21 and aces > 0:
            value -= 10
            aces -= 1

        return value

    def createDeck(self):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [(value, suit) for suit in suits for value in values]
        random.shuffle(deck)
        return deck

    def deal_card_image(self, card, position):
        if type(card) == tuple:
            value, suit = card
            card_image = f"{self.card_images_directory}/{value}_{suit}.png"
            drawImage(card_image, position[0], position[1], width=100, height=150)
        else:
            drawImage(f"{self.card_images_directory}/hidden.png", self.card_positions["dealer"][1][0],
                      self.card_positions["dealer"][1][1], width=100, height=150)

    def initializeDeck(self, difficulty):
        if difficulty == "Easy":
            return EasyDeck()
        elif difficulty == "Medium":
            return MediumDeck()
        elif difficulty == "Hard":
            return HardDeck()
        else:
            raise ValueError("Invalid difficulty level")
    def handleSidebet(self, sidebet):
        bet_amount = 5
        if self.balance < bet_amount:
            print(f"Not enough balance to place a ${bet_amount} bet on {sidebet}.")
            return
        self.balance -= bet_amount
        self.sidebets[sidebet] = bet_amount
        print(f"${bet_amount} placed on {sidebet}. Remaining balance: ${self.balance}.")
        self.phase = "main_bet"

    def handleMainBet(self):
        main_bet_amount = 50
        if self.balance < main_bet_amount:
            print("Insufficient balance to place the main bet.")
            return
        self.balance -= main_bet_amount
        print(f"${main_bet_amount} main bet placed. Remaining balance: ${self.balance}.")

    def startGame(self):
        print("Starting a new round. Dealing initial cards...")
        self.start_round()
        print(f"BlackjackTable.startGame - Player's Hand: {self.player_hand}")
        print(f"BlackjackTable.startGame - Dealer's Hand: {self.dealer_hand}")

    def handleHit(self):
        print("Player chose to hit.")
        card = self.deck.pop()
        print(card)
        self.player_hand.append(card)
        player_value = self.calculate_hand_value(self.player_hand)
        print(f"Player's Hand: {self.player_hand} | Value: {player_value}")
        if player_value > 21:
            self.endRound(winner="Dealer", reason="Player Busted!")
    def rummy(self):
        playerHand = self.player_hand
        if len(self.dealer_hand) < 1:
            return "Dealer's upcard is not available yet."
        dealerUpcard = self.dealer_hand[0]
        combinedHand = playerHand + [dealerUpcard]
        suits = [card[1] for card in combinedHand]
        values = [card[0] for card in combinedHand]
        valueCounts = {value: values.count(value) for value in values}
        if 3 in valueCounts.values():
            return "Rummy win: Set (Three of a Kind)!"
        valueOrder = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        valueIndices = sorted([valueOrder.index(v) for v in values])
        if all(suits[0] == s for s in suits) and all(
                valueIndices[i] + 1 == valueIndices[i + 1] for i in range(len(valueIndices) - 1)
        ):
            return "Rummy win: Run (Straight Flush)!"
        return "No Rummy win."

    def pairs(self):
        hand = self.deck.hands[self.playerId]
        if len(hand) >= 2 and hand[0][0] == hand[1][0]:
            return f"Pairs win: Player {self.playerId} has a pair of {hand[0][0]}!"
        return "No pairs win."

    def trips(self):
        hand = self.deck.hands[self.playerId]
        if len(playerHand) == 3 and all(card[0] == '7' for card in playerHand):
            return "trips: 3 7s!"
        return "No trips win."

    def checkSideBets(self):
        print("[DEBUG] Checking side bets...")
        for sidebet, amount in self.sidebets.items():
            if sidebet == "Pairs" and self.check_pairs(self.player_hand):
                self.balance += 15
                print("Side bet 'Pairs' hit! Player earns $15.")
            elif sidebet == "trips" and self.trips(self.player_hand):
                self.balance += 15
                print("Side bet 'Ladies' hit! Player earns $15.")
            elif sidebet == "Rummy" and self.check_rummy(self.player_hand):
                self.balance += 15
                print("Side bet 'Rummy' hit! Player earns $15.")

    def handleStand(self):
        if 'hidden' in self.dealer_hand:
            self.dealer_hand[1] = self.deck[0]
        print("Player chose to stand.")
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        player_value = self.calculate_hand_value(self.player_hand)

        while dealer_value < 17:
            self.hit(dealer=True)
            dealer_value = self.calculate_hand_value(self.dealer_hand)

        print(f"Dealer's Final Hand: {self.dealer_hand} | Value: {dealer_value}")

        if player_value > 21:
            self.winner_message = "Dealer wins! Player busted."
        elif dealer_value > 21:
            self.winner_message = "Player wins! Dealer busted."
            self.balance += self.mainBetAmount*2
        elif player_value > dealer_value:
            self.winner_message = "Player wins!"
            self.balance += self.mainBetAmount*2
        elif player_value < dealer_value:
            self.winner_message = "Dealer wins!"
        else:
            self.winner_message = "It's a Tie!"
            self.balance += self.mainBetAmount

        self.phase = "display_winner"

        self.phase = "display_winner"

    def endRound(self, winner, reason):
        print(reason)
        self.player_hand = []
        self.dealer_hand = []
        self.sidebets = {}
        self.recentEarnings = 0

        self.winner_message = f"{winner} wins!" if winner != "None" else "It's a Tie!"
        self.phase = "display_winner"

    def resetGame(self):
        print("Resetting the game for the next round...")
        self.winner_display = None
        self.phase = "sidebets"

    def onMousePress(self, mouseX, mouseY):
        print(mouseX, mouseY)

        if self.phase == "sidebets":

            if 541 <= mouseX <= 778 and 238 <= mouseY <= 470:
                self.selectedSideBet = "Rummies"
                print("Selected side bet: Rummies")
                return
            if 652 <= mouseX <= 920 and 495 <= mouseY <= 728:
                self.selectedSideBet = "Pairs"
                print("Selected side bet: Pairs")
                return
            if 783 <= mouseX <= 1031 and 241 <= mouseY <= 467:
                self.selectedSideBet = "Triple 7s"
                print("Selected side bet: Triple 7s")
                return

            if 1399 <= mouseX <= 1523 and 766 <= mouseY <= 894:
                print("Next button pressed. Transitioning to Main Bet phase.")
                self.phase = "main_bet"
                return

        if self.phase == "sidebets" or self.phase == "main_bet":
            if 104 <= mouseX <= 281:
                if 117 <= mouseY <= 298:
                    self.handleChipClick(1)
                    return
                if 318 <= mouseY <= 496:
                    self.handleChipClick(10)
                    return
                if 529 <= mouseY <= 703:
                    self.handleChipClick(100)
                    return
                if 721 <= mouseY <= 898:
                    self.handleChipClick(500)
                    return
            if 1399 <= mouseX <= 1523 and 766 <= mouseY <= 894:
                self.phase = "deal"
                self.startGame()
                return
        elif self.phase == "display_winner":
            self.resetGame()
            return
        elif self.phase == "main_bet":
            x, y = self.main_bet_button["pos"]
            if x - 100 <= mouseX <= x + 100 and y - 25 <= mouseY <= y + 25:
                self.handleMainBet()
                return
        elif self.phase == "actions":
            if 526 <= mouseX <= 777 and 697 <= mouseY <= 839:
                self.handleHit()
                return
            elif 707 <= mouseX <= 876 and 697 <= mouseY <= 839:
                self.handleEarlyPayout()
                return
            elif 891 <= mouseX <= 1063 and 697 <= mouseY <= 839:
                self.handleStand()
                return


    def handleChipClick(self, chipValue):
        if self.phase == "sidebets":
            if self.selectedSideBet and self.balance >= chipValue:
                self.sideBets[self.selectedSideBet] += chipValue
                self.balance -= chipValue
                print(f"Added ${chipValue} to {self.selectedSideBet}. New balance: ${self.balance}")
            elif not self.selectedSideBet:
                print("Please select a side bet first.")
            else:
                print("Insufficient balance.")
        elif self.phase == "main_bet":
            if self.balance >= chipValue:
                self.mainBetAmount += chipValue
                self.balance -= chipValue
                print(f"Added ${chipValue} to main bet. New balance: ${self.balance}")
            else:
                print("Insufficient balance.")

    def handleEarlyPayout(self):
        playerHand = self.player_hand
        dealerUpcard = self.dealer_hand[0] if len(self.dealer_hand) > 0 else None
        remainingDeck = self.deck

        if not dealerUpcard or not remainingDeck:
            print("[ERROR] Dealer's upcard or remaining deck is missing.")
            return "Error: Unable to process early payout."

        playerValue = self.calculate_hand_value(playerHand)
        dealerValue = self.calculate_hand_value([dealerUpcard])
        winProbability = self.simulateOutcomes(playerValue, dealerValue, remainingDeck)

        winProbability = max(0, min(1, winProbability))

        print(f"[DEBUG] Win Probability = {winProbability:.2f}")

        if winProbability < 0.5:
            payoutAmount = self.mainBetAmount * winProbability
        elif winProbability == 0.5:
            payoutAmount = self.mainBetAmount
        else:
            payoutAmount = self.mainBetAmount * (1 + winProbability)

        payoutAmount = rounded(payoutAmount)

        self.balance += payoutAmount
        self.resetGame()
    def redrawAll(self):
        drawImage(self.table_image, 0, 0, width=self.width, height=self.height)


        for chip in self.chips:
            x, y = chip["pos"]
            if chip["value"] ==10:
                drawImage(chip["image"], x, y, width=195, height=195)
            else:
                drawImage(chip["image"], x, y, width=200, height=200)

        drawRect(0, 900, self.width, 100, fill="black")
        drawLabel(f"Balance: ${self.balance}", 100, 950, size=20, fill="white")
        if self.phase == "sidebets":
            drawLabel("Place SideBets", 800, 100, size=100, fill="white", align="center", bold=True, font="Georgia")

            for button in self.sidebet_buttons:
                x, y = button["pos"]
                if button["name"] == "trips":
                    drawImage(button["image"], x, y, width=315, height=315)
                else:
                    drawImage(button["image"], x, y, width=300, height=300)

            drawImage("/Users/jonghyunyoon/Desktop/next.png", 1360, 740, width=220, height=200)
        elif self.phase == "main_bet":
            drawLabel("Place Bets!", 800, 100, size=100, fill="white", align="center", bold=True, font="Georgia")
            drawLabel(
                f"Total Bet: ${self.mainBetAmount}",
                self.width // 2,
                self.height // 2 - 50,
                size=100,
                fill="gold",
                align="center",
                font="Georgia",
                bold=True
            )
            drawImage("/Users/jonghyunyoon/Desktop/next.png", 1360, 740, width=220, height=200)

        elif self.phase == "deal":
            for i, card in enumerate(self.dealer_hand):
                if i == 1:
                    drawImage(f"{self.card_images_directory}/hidden.png", self.card_positions["dealer"][i][0],
                              self.card_positions["dealer"][i][1], width=100, height=150)
                else:
                    self.deal_card_image(card, self.card_positions["dealer"][i])
            for i, card in enumerate(self.player_hand):
                self.deal_card_image(card, self.card_positions["player"][i])
                self.phase =  "actions"

        elif self.phase == "actions":
            for button in self.action_buttons:
                x, y = button["pos"]
                if button["name"] == "hit":
                    drawImage(button["image"], x, y, width=200, height=225)
                elif button["name"] == "earlypayout":
                    drawImage(button["image"], x, y, width=250, height=225)

                else:
                    drawImage(button["image"], x, y, width=200, height=200)
            for i, card in enumerate(self.dealer_hand):
                if i == 1:
                    drawImage(f"{self.card_images_directory}/hidden.png", self.card_positions["dealer"][i][0],
                              self.card_positions["dealer"][i][1], width=100, height=150)
                else:
                    self.deal_card_image(card, self.card_positions["dealer"][i])
            for i, card in enumerate(self.player_hand):
                self.deal_card_image(card, self.card_positions["player"][i])

            earlyPayoutMessage = self.earlyPayout()
            if isinstance(earlyPayoutMessage, str) and "Early Payout Offer" in earlyPayoutMessage:
                payoutAmount = earlyPayoutMessage.split("$")[-1].strip()
                drawLabel(f"Early Payout Offer: ${payoutAmount}", self.width // 2, 950, size=40,
                          fill="white", bold=True, align="center",font="Georgia")

        elif self.phase == "display_winner":
            for i, card in enumerate(self.dealer_hand):
                    self.deal_card_image(card, self.card_positions["dealer"][i])
            for i, card in enumerate(self.player_hand):
                self.deal_card_image(card, self.card_positions["player"][i])
            if self.winner_message:
                drawLabel(
                    self.winner_message, self.width // 2, 400, size=70, fill="gold", font="Brush Script MT",
                    align="center"
                )


class VideoApp:
    def __init__(self, videoPath, app, showButtons=True):
        self.videoPath = videoPath
        self.app = app
        self.screenWidth = 1540
        self.screenHeight = 1000
        self.startTime = 30
        self.endTime = 5 * 60
        self.showButtons = showButtons

        self.cap = cv2.VideoCapture(self.videoPath)
        if not self.cap.isOpened():
            print("Error: Could not open video file.")
            sys.exit()
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.startFrame = int(self.startTime * self.fps)
        self.endFrame = int(self.endTime * self.fps)
        self.tempImagePath = "current_frame.jpg"
        self.currentImage = None
        self.playGameBtn = {"x": self.screenWidth // 2 - 160, "y": self.screenHeight // 2 - 50, "width": 300, "height": 100}
        self.instructionsBtn = {"x": self.screenWidth // 2 - 160+8, "y": (self.screenHeight // 2) + 140, "width": 300, "height": 100}

    def updateFrame(self):
        if not self.cap.isOpened():
            return

        currentFramePos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        if currentFramePos >= self.endFrame:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.startFrame)

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.resize(frame, (self.screenWidth, self.screenHeight), interpolation=cv2.INTER_AREA)
            self.currentFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            cv2.imwrite(self.tempImagePath, frame)
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.startFrame)

    def redrawAll(self):
        if self.tempImagePath:
            drawImage(self.tempImagePath, 0, 0, width=self.screenWidth, height=self.screenHeight)

        if self.showButtons:
            overlayImagePath = "/Users/jonghyunyoon/Desktop/blackjackintro.jpeg"
            playbuttonimage = "/Users/jonghyunyoon/Desktop/gamebutton.png"
            instructionsimage = "/Users/jonghyunyoon/Desktop/instructions.png"
            drawImage(overlayImagePath, 500, 0, width=500, height=500)
            drawImage(playbuttonimage,self.playGameBtn["x"], self.playGameBtn["y"] + 100, width=300, height=100)
#            drawImage(instructionsimage, self.instructionsBtn["x"], self.instructionsBtn["y"], width=300, height=100)

    def onMousePress(self, mouseX, mouseY):
        if self.showButtons:
            if 629 <= mouseX <= 893 and \
                    563 <= mouseY <= 634:
                self.app.navigate("difficulty")

            if 630 <= mouseX <= 901 and \
                    659<= mouseY <= 709:
                print("Instructions Button Pressed")

    def onStep(self):
        self.updateFrame()


class DifficultySelection:
    def __init__(self, videoPath, app):
        self.app = app
        self.videoApp = VideoApp(videoPath, app, showButtons=False)
        self.screenWidth = 1550
        self.screenHeight = 1000

        self.easyBtn = {"x": self.screenWidth // 2 - 75, "y": self.screenHeight // 2 - 100, "width": 150, "height": 50}
        self.mediumBtn = {"x": self.screenWidth // 2 - 75, "y": self.screenHeight // 2, "width": 150, "height": 50}
        self.hardBtn = {"x": self.screenWidth // 2 - 75, "y": self.screenHeight // 2 + 100, "width": 150, "height": 50}

        self.image1Path = "/Users/jonghyunyoon/Downloads/difficulty.png"
        self.image2Path = "/Users/jonghyunyoon/Downloads/easy.png"


    def selectDifficulty(self, difficulty):
        print(f"Selected Difficulty: {difficulty}")
        self.app.startBlackjack(difficulty)

    def redrawAll(self):

        self.videoApp.redrawAll()

        drawImage(self.image1Path, 500, 0, width=450, height=450)
        drawImage(self.image2Path, 500, 450, width=450, height=450)


    def onMousePress(self, mouseX, mouseY):
        print(f"Mouse clicked at: ({mouseX}, {mouseY})")
        if 543 <= mouseX <= 900 and \
                495 <= mouseY <= 601:
            self.selectDifficulty("Easy")

        if 543 <= mouseX <= 900 and \
                628 <= mouseY <= 721:
            self.selectDifficulty("Medium")

        if 543 <= mouseX <= 900 and \
                755 <=mouseY<= 866:
            self.selectDifficulty("Hard")

    def onStep(self):
        self.videoApp.onStep()



def onAppStart(app):
    app.controller = App()
    app.phase = "sidebets"
    app.timer = 5000
    app.timer_max = 5000
    app.sidebets = {}
    app.main_bet = 0
    app.player_has_acted = False

def redrawAll(app):
    app.controller.redrawAll()

def onStep(app):
    app.controller.onStep()

def onMousePress(app, mouseX, mouseY):
    app.controller.onMousePress(mouseX, mouseY)

def onKeyPress(app, key):
    if app.phase == "actions":
        app.player_has_acted = True
        app.controller.onKeyPress(key)

class App:
    def __init__(self):
        self.currentScreen = "videoApp"
        self.videoApp = VideoApp("/Users/jonghyunyoon/Downloads/videoplayback.mp4", self)
        self.difficultyScreen = DifficultySelection("/Users/jonghyunyoon/Downloads/difficulty.mp4", self)
        self.blackjackTable = None

    def startBlackjack(self, difficulty):
        self.blackjackTable = BlackjackTable(self, difficulty)
        self.blackjackTable.phase = "sidebets"
        self.navigate("blackjackTable")

    def navigate(self, screen):
        self.currentScreen = screen

    def redrawAll(self):
        if self.currentScreen == "videoApp":
            self.videoApp.redrawAll()
        elif self.currentScreen == "difficulty":
            self.difficultyScreen.redrawAll()
        elif self.currentScreen == "blackjackTable":
            self.blackjackTable.redrawAll()

    def onMousePress(self, mouseX, mouseY):
        if self.currentScreen == "videoApp":
            self.videoApp.onMousePress(mouseX, mouseY)
        elif self.currentScreen == "difficulty":
            self.difficultyScreen.onMousePress(mouseX, mouseY)
        elif self.currentScreen == "blackjackTable":
            self.blackjackTable.onMousePress(mouseX, mouseY)

    def onKeyPress(self, key):
        if self.currentScreen == "blackjackTable":
            self.blackjackTable.onKeyPress(key)

    def onStep(self):
        if self.currentScreen == "videoApp":
            self.videoApp.onStep()
        elif self.currentScreen == "difficulty":
            self.difficultyScreen.onStep()

# Main entry point
def main():
    runApp(width=1540, height=1000)

if __name__ == "__main__":
    main()
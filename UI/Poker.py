import tkinter as tk
from tkinter import messagebox
import random

# ---------------------------
# Play-Money Blackjack
# ---------------------------

suits = ["♠", "♥", "♦", "♣"]
ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

card_values = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10, "A": 11
}


class BlackjackGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Basic Blackjack")
        self.root.geometry("700x500")
        self.root.protocol("WM_DELETE_WINDOW", self.close_game)

        self.money = 100
        self.bet = 10

        self.deck = []
        self.player_hand = []
        self.dealer_hand = []
        self.game_active = False
        self.player_stands = False
        self.doubled_down = False

        self.build_ui()
        self.update_labels()

    def build_ui(self):
        self.title_label = tk.Label(self.root, text="Play-Money Blackjack", font=("Arial", 18, "bold"))
        self.title_label.pack(pady=10)

        self.money_label = tk.Label(self.root, text="", font=("Arial", 14))
        self.money_label.pack()

        self.bet_label = tk.Label(self.root, text="", font=("Arial", 12))
        self.bet_label.pack(pady=5)

        self.status_label = tk.Label(self.root, text="Place a bet and click Deal.", font=("Arial", 12, "italic"))
        self.status_label.pack(pady=10)

        self.dealer_cards_label = tk.Label(self.root, text="Dealer: ", font=("Arial", 13))
        self.dealer_cards_label.pack(pady=10)

        self.dealer_value_label = tk.Label(self.root, text="Dealer Value: ?", font=("Arial", 12))
        self.dealer_value_label.pack()

        self.player_cards_label = tk.Label(self.root, text="Player: ", font=("Arial", 13))
        self.player_cards_label.pack(pady=10)

        self.player_value_label = tk.Label(self.root, text="Player Value: 0", font=("Arial", 12))
        self.player_value_label.pack()

        self.button_frame = tk.Frame(self.root)
        self.button_frame.pack(pady=20)

        self.bet_up_button = tk.Button(self.button_frame, text="Bet +10", width=12, command=self.increase_bet)
        self.bet_up_button.grid(row=0, column=0, padx=5, pady=5)

        self.bet_down_button = tk.Button(self.button_frame, text="Bet -10", width=12, command=self.decrease_bet)
        self.bet_down_button.grid(row=0, column=1, padx=5, pady=5)

        self.deal_button = tk.Button(self.button_frame, text="Deal", width=12, command=self.start_round)
        self.deal_button.grid(row=0, column=2, padx=5, pady=5)

        self.hit_button = tk.Button(self.button_frame, text="Hit", width=12, command=self.hit, state="disabled")
        self.hit_button.grid(row=1, column=0, padx=5, pady=5)

        self.stand_button = tk.Button(self.button_frame, text="Stand", width=12, command=self.stand, state="disabled")
        self.stand_button.grid(row=1, column=1, padx=5, pady=5)

        self.double_button = tk.Button(self.button_frame, text="Double Down", width=12, command=self.double_down, state="disabled")
        self.double_button.grid(row=1, column=2, padx=5, pady=5)

        self.exit_button = tk.Button(self.root, text="Exit", width=12, command=self.close_game)
        self.exit_button.pack(pady=10)

    def create_deck(self):
        deck = []
        for suit in suits:
            for rank in ranks:
                deck.append((rank, suit))
        random.shuffle(deck)
        return deck

    def hand_to_string(self, hand, hide_second=False):
        cards = []
        for i, (rank, suit) in enumerate(hand):
            if hide_second and i == 1:
                cards.append("[Hidden]")
            else:
                cards.append(f"{rank}{suit}")
        return "  ".join(cards)

    def hand_value(self, hand):
        total = 0
        aces = 0

        for rank, suit in hand:
            total += card_values[rank]
            if rank == "A":
                aces += 1

        while total > 21 and aces > 0:
            total -= 10
            aces -= 1

        return total

    def update_labels(self, reveal_dealer=False):
        self.money_label.config(text=f"Money: ${self.money}")
        self.bet_label.config(text=f"Current Bet: ${self.bet}")

        if reveal_dealer:
            self.dealer_cards_label.config(text="Dealer: " + self.hand_to_string(self.dealer_hand))
            self.dealer_value_label.config(text=f"Dealer Value: {self.hand_value(self.dealer_hand)}")
        else:
            if len(self.dealer_hand) >= 2:
                self.dealer_cards_label.config(text="Dealer: " + self.hand_to_string(self.dealer_hand, hide_second=True))
                first_card_value = card_values[self.dealer_hand[0][0]]
                self.dealer_value_label.config(text=f"Dealer Value: {first_card_value}+?")
            else:
                self.dealer_cards_label.config(text="Dealer: ")
                self.dealer_value_label.config(text="Dealer Value: ?")

        self.player_cards_label.config(text="Player: " + self.hand_to_string(self.player_hand))
        self.player_value_label.config(text=f"Player Value: {self.hand_value(self.player_hand) if self.player_hand else 0}")

    def set_action_buttons(self, enabled):
        state = "normal" if enabled else "disabled"
        self.hit_button.config(state=state)
        self.stand_button.config(state=state)
        self.double_button.config(state=state if enabled else "disabled")

    def increase_bet(self):
        if not self.game_active and self.bet + 10 <= self.money:
            self.bet += 10
            self.update_labels()

    def decrease_bet(self):
        if not self.game_active and self.bet - 10 >= 10:
            self.bet -= 10
            self.update_labels()

    def start_round(self):
        if self.game_active:
            return

        if self.money <= 0:
            messagebox.showinfo("Game Over", "You are out of money.")
            return

        if self.bet > self.money:
            messagebox.showwarning("Invalid Bet", "Your bet is higher than your money.")
            return

        self.deck = self.create_deck()
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]
        self.game_active = True
        self.player_stands = False
        self.doubled_down = False

        self.status_label.config(text="Your turn.")
        self.update_labels(reveal_dealer=False)
        self.set_action_buttons(True)

        player_total = self.hand_value(self.player_hand)
        dealer_total = self.hand_value(self.dealer_hand)

        # Natural blackjack checks
        if player_total == 21 or dealer_total == 21:
            self.finish_naturals()

    def finish_naturals(self):
        self.set_action_buttons(False)
        self.game_active = False

        player_total = self.hand_value(self.player_hand)
        dealer_total = self.hand_value(self.dealer_hand)

        self.update_labels(reveal_dealer=True)

        if player_total == 21 and dealer_total == 21:
            self.status_label.config(text="Both have Blackjack. Push.")
        elif player_total == 21:
            winnings = int(self.bet * 1.5)
            self.money += winnings
            self.status_label.config(text=f"Blackjack. You win ${winnings}.")
        elif dealer_total == 21:
            self.money -= self.bet
            self.status_label.config(text=f"Dealer has Blackjack. You lose ${self.bet}.")

        self.fix_money_and_bet()
        self.update_labels(reveal_dealer=True)

    def hit(self):
        if not self.game_active:
            return

        self.player_hand.append(self.deck.pop())
        self.update_labels(reveal_dealer=False)

        if self.hand_value(self.player_hand) > 21:
            self.money -= self.bet
            self.status_label.config(text=f"You busted. You lose ${self.bet}.")
            self.end_round()

    def stand(self):
        if not self.game_active:
            return

        self.player_stands = True
        self.dealer_turn()

    def double_down(self):
        if not self.game_active:
            return

        if self.money < self.bet * 2:
            messagebox.showwarning("Not Enough Money", "You do not have enough money to double down.")
            return

        self.bet *= 2
        self.doubled_down = True
        self.player_hand.append(self.deck.pop())
        self.update_labels(reveal_dealer=False)

        if self.hand_value(self.player_hand) > 21:
            self.money -= self.bet
            self.status_label.config(text=f"You busted after doubling down. You lose ${self.bet}.")
            self.end_round()
        else:
            self.dealer_turn()

    def dealer_turn(self):
        self.set_action_buttons(False)

        while self.hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self.deck.pop())

        self.resolve_winner()

    def resolve_winner(self):
        player_total = self.hand_value(self.player_hand)
        dealer_total = self.hand_value(self.dealer_hand)

        if dealer_total > 21:
            self.money += self.bet
            self.status_label.config(text=f"Dealer busted. You win ${self.bet}.")
        elif player_total > dealer_total:
            self.money += self.bet
            self.status_label.config(text=f"You win ${self.bet}.")
        elif player_total < dealer_total:
            self.money -= self.bet
            self.status_label.config(text=f"Dealer wins. You lose ${self.bet}.")
        else:
            self.status_label.config(text="Push. Your bet is returned.")

        self.end_round()

    def end_round(self):
        self.game_active = False
        self.set_action_buttons(False)
        self.fix_money_and_bet()
        self.update_labels(reveal_dealer=True)

        if self.money <= 0:
            messagebox.showinfo("Game Over", "You are out of money.")

    def fix_money_and_bet(self):
        if self.money < 0:
            self.money = 0

        if self.money > 0 and self.bet > self.money:
            self.bet = self.money

        if self.bet < 10 and self.money >= 10:
            self.bet = 10

    def close_game(self):
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    game = BlackjackGame(root)
    root.mainloop()
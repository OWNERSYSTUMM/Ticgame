from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def build_board(board):
    keyboard = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            index = i + j
            text = board[index] if board[index] != " " else "◻️"
            row.append(
                InlineKeyboardButton(text, callback_data=f"move_{index}")
            )
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def check_winner(board):
    combos = [
        (0,1,2),(3,4,5),(6,7,8),
        (0,3,6),(1,4,7),(2,5,8),
        (0,4,8),(2,4,6)
    ]
    for a,b,c in combos:
        if board[a] == board[b] == board[c] and board[a] != " ":
            return board[a]
    if " " not in board:
        return "Draw"
    return None


def ai_move(board):
    for i in range(9):
        if board[i] == " ":
            return i
    return None

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def new_board():
    return [" "] * 9


def build_keyboard(board, game_over=False):
    keyboard = []

    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            index = i + j
            text = board[index] if board[index] != " " else "⬜"

            if game_over:
                callback = "ignore"
            else:
                callback = f"ttt_{index}"

            row.append(
                InlineKeyboardButton(text, callback_data=callback)
            )
        keyboard.append(row)

    # Restart Button
    keyboard.append(
        [InlineKeyboardButton("🔄 Restart Game", callback_data="restart")]
    )

    return InlineKeyboardMarkup(keyboard)


def check_winner(board):
    win_patterns = [
        (0,1,2),(3,4,5),(6,7,8),
        (0,3,6),(1,4,7),(2,5,8),
        (0,4,8),(2,4,6)
    ]

    for a,b,c in win_patterns:
        if board[a] == board[b] == board[c] and board[a] != " ":
            return board[a]

    if " " not in board:
        return "Draw"

    return None

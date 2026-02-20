games = {}

def create_game(message_id, player_id, name, symbol, ai=False):
    games[message_id] = {
        "board": [" "] * 9,
        "player1": player_id,
        "player1_name": name,
        "symbol1": symbol,
        "symbol2": "⭕" if symbol == "❌" else "❌",
        "player2": None,
        "player2_name": None,
        "turn": symbol,
        "ai": ai
    }

def get_game(message_id):
    return games.get(message_id)

def delete_game(message_id):
    if message_id in games:
        del games[message_id]

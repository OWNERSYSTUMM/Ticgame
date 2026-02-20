import uuid
import random
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    CommandHandler,
    InlineQueryHandler,
)

from config import BOT_TOKEN, OWNER_ID
from tictactoe import build_board, check_winner, ai_move
from game_manager import create_game, get_game, delete_game
import database as db


# ───────── GAME TEXT BUILDER ─────────
def build_game_text(game):
    player1 = game["player1_name"]
    player2 = game["player2_name"] if game["player2_name"] else "Waiting..."

    turn_name = (
        player1 if game["turn"] == game["symbol1"]
        else player2
    )

    return (
        "🎮 Tic Tac Toe\n\n"
        f"{game['symbol1']} {player1}\n"
        f"{game['symbol2']} {player2}\n\n"
        f"👉 Turn: {turn_name}"
    )


# ───────── INLINE PLAY CARD ─────────
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❌", callback_data="choose_X"),
            InlineKeyboardButton("⭕", callback_data="choose_O"),
        ],
        [InlineKeyboardButton("🤖 AI", callback_data="choose_AI")]
    ])

    result = InlineQueryResultArticle(
        id=str(uuid.uuid4()),
        title="🎮 Tic Tac Toe",
        description="Start a new game",
        input_message_content=InputTextMessageContent("🎮 Tic Tac Toe"),
        reply_markup=keyboard,
    )

    await query.answer([result], cache_time=0)


# ───────── BUTTON HANDLER ─────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    data = query.data

    game_key = query.inline_message_id or (
        query.message.message_id if query.message else None
    )

    if not game_key:
        return

    # ───── Choose Symbol ─────
    if data.startswith("choose_"):
        symbol = "❌" if data == "choose_X" else "⭕"
        ai = True if data == "choose_AI" else False

        create_game(game_key, user.id, user.first_name, symbol, ai)
        db.get_user(user.id, user.first_name)
        game = get_game(game_key)

        if ai:
            await query.edit_message_text(
                build_game_text(game),
                reply_markup=build_board(game["board"])
            )
        else:
            join_btn = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join", callback_data="join")]]
            )
            await query.edit_message_text(
                f"🎮 Tic Tac Toe\n\n"
                f"{symbol} {user.first_name}\n\n"
                "Waiting for opponent...",
                reply_markup=join_btn
            )
        return

    # ───── Join Game ─────
    if data == "join":
        game = get_game(game_key)
        if not game:
            return

        if user.id == game["player1"]:
            await query.answer(
                text="Tu already game me hai 😏",
                show_alert=True
            )
            return

        if game["player2"]:
            await query.answer(
                text="Game full ho chuka hai 😎",
                show_alert=True
            )
            return

        game["player2"] = user.id
        game["player2_name"] = user.first_name
        db.get_user(user.id, user.first_name)

        await query.edit_message_text(
            build_game_text(game),
            reply_markup=build_board(game["board"])
        )
        return

    # ───── Move ─────
    if data.startswith("move_"):
        game = get_game(game_key)
        if not game:
            return

        # 🔒 Spectator Click
        if user.id not in [game["player1"], game["player2"]]:
            await query.answer(
                text="🚫 Na munna! Ye tera game nahi hai.",
                show_alert=True
            )
            return

        # Identify turn player
        current_turn_player = (
            game["player1"]
            if game["turn"] == game["symbol1"]
            else game["player2"]
        )

        # 🔒 Wrong Turn Click
        if user.id != current_turn_player:
            funny_msgs = [
                f"😂 Oye {user.first_name}! Abhi tera turn nahi hai!",
                "⏳ Ruk ja bhai, hero mat ban!",
                "😏 Sabka time aata hai...",
                "🫵 Abhi tera number nahi aaya!"
            ]
            await query.answer(
                text=random.choice(funny_msgs),
                show_alert=True
            )
            return

        index = int(data.split("_")[1])

        if game["board"][index] != " ":
            await query.answer(
                text="❌ Ye box already filled hai!",
                show_alert=True
            )
            return

        # ✅ Valid Move
        game["board"][index] = game["turn"]
        winner = check_winner(game["board"])

        if winner:
            if winner == "Draw":
                db.add_draw(game["player1"])
                if game["player2"]:
                    db.add_draw(game["player2"])
                text = "🤝 It's a Draw!"
            else:
                winner_name = (
                    game["player1_name"]
                    if winner == game["symbol1"]
                    else game["player2_name"]
                )

                winner_id = (
                    game["player1"]
                    if winner == game["symbol1"]
                    else game["player2"]
                )

                loser_id = (
                    game["player2"]
                    if winner_id == game["player1"]
                    else game["player1"]
                )

                db.add_win(winner_id)
                if loser_id:
                    db.add_loss(loser_id)

                text = f"🏆 Winner: {winner_name}"

            await query.edit_message_text(text)
            delete_game(game_key)
            return

        # 🔄 Switch Turn
        game["turn"] = (
            game["symbol2"]
            if game["turn"] == game["symbol1"]
            else game["symbol1"]
        )

        await query.edit_message_text(
            build_game_text(game),
            reply_markup=build_board(game["board"])
        )


# ───────── COMMANDS ─────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 Tic Tac Toe Bot\n\nUse me inline:\n@YourBotUsername"
    )


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = db.leaderboard()
    text = "🏆 Leaderboard\n\n"
    for i, user in enumerate(top, 1):
        text += f"{i}. {user['name']} - {user['wins']} wins\n"
    await update.message.reply_text(text)


async def owner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text("MongoDB Connected ✅")


# ───────── MAIN ─────────
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("owner", owner))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()

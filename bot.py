import uuid
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
        input_message_content=InputTextMessageContent("‎"),
        reply_markup=keyboard,
    )

    await query.answer([result], cache_time=0)


# ───────── BUTTON HANDLER ─────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    message_id = query.message.message_id
    user = query.from_user
    data = query.data

    if data.startswith("choose_"):
        symbol = "❌" if data == "choose_X" else "⭕"
        ai = True if data == "choose_AI" else False

        create_game(message_id, user.id, user.first_name, symbol, ai)
        db.get_user(user.id, user.first_name)

        if ai:
            await query.edit_message_reply_markup(
                reply_markup=build_board(get_game(message_id)["board"])
            )
        else:
            join_btn = InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join", callback_data="join")]]
            )
            await query.edit_message_reply_markup(reply_markup=join_btn)
        return

    if data == "join":
        game = get_game(message_id)
        if not game or user.id == game["player1"]:
            return

        game["player2"] = user.id
        game["player2_name"] = user.first_name
        db.get_user(user.id, user.first_name)

        await query.edit_message_reply_markup(
            reply_markup=build_board(game["board"])
        )
        return

    if data.startswith("move_"):
        game = get_game(message_id)
        if not game:
            return

        index = int(data.split("_")[1])
        if game["board"][index] != " ":
            return

        game["board"][index] = game["turn"]
        winner = check_winner(game["board"])

        if winner:
            if winner == "Draw":
                db.add_draw(game["player1"])
                if game["player2"]:
                    db.add_draw(game["player2"])
                text = "🤝 Draw!"
            else:
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
                text = f"🏆 {user.first_name} Wins!"

            await query.edit_message_text(text)
            delete_game(message_id)
            return

        if game["ai"]:
            ai_index = ai_move(game["board"])
            if ai_index is not None:
                game["board"][ai_index] = game["symbol2"]

        game["turn"] = (
            game["symbol2"]
            if game["turn"] == game["symbol1"]
            else game["symbol1"]
        )

        await query.edit_message_reply_markup(
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

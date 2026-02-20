import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from tictactoe import new_board, build_keyboard, check_winner


load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\nType /ttt to start Tic Tac Toe 🎮"
    )


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["board"] = new_board()
    context.chat_data["turn"] = "❌"

    await update.message.reply_text(
        "🎮 Tic Tac Toe\n\nTurn: ❌",
        reply_markup=build_keyboard(context.chat_data["board"])
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "ignore":
        return

    if data == "restart":
        context.chat_data["board"] = new_board()
        context.chat_data["turn"] = "❌"

        await query.edit_message_text(
            "🎮 Tic Tac Toe\n\nTurn: ❌",
            reply_markup=build_keyboard(context.chat_data["board"])
        )
        return

    board = context.chat_data.get("board")
    turn = context.chat_data.get("turn")

    if not board:
        return

    index = int(data.split("_")[1])

    if board[index] != " ":
        return

    board[index] = turn

    winner = check_winner(board)

    if winner:
        if winner == "Draw":
            text = "🤝 It's a Draw!"
        else:
            text = f"🏆 Winner: {winner}"

        await query.edit_message_text(
            text,
            reply_markup=build_keyboard(board, game_over=True)
        )

        return

    # Switch turn
    context.chat_data["turn"] = "⭕" if turn == "❌" else "❌"

    await query.edit_message_text(
        f"🎮 Tic Tac Toe\n\nTurn: {context.chat_data['turn']}",
        reply_markup=build_keyboard(board)
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ttt", start_game))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()

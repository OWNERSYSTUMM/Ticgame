import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from tictactoe import new_board, build_keyboard, check_winner

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")


# 🎮 Start Game in Group
async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ This game works only in groups.")
        return

    context.chat_data.clear()

    context.chat_data["player1"] = update.effective_user.id
    context.chat_data["player1_name"] = update.effective_user.first_name

    join_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Join Game", callback_data="join_game")]
    ])

    await update.message.reply_text(
        f"🎮 Tic Tac Toe\n\n"
        f"Player 1: {update.effective_user.first_name} (❌)\n\n"
        f"Waiting for Player 2...",
        reply_markup=join_button
    )


# 🎮 Button Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    # 🔹 Join Game
    if data == "join_game":
        if user_id == context.chat_data.get("player1"):
            return

        context.chat_data["player2"] = user_id
        context.chat_data["player2_name"] = query.from_user.first_name
        context.chat_data["board"] = new_board()
        context.chat_data["turn"] = "❌"

        await query.edit_message_text(
            f"🎮 Tic Tac Toe Started!\n\n"
            f"{context.chat_data['player1_name']} = ❌\n"
            f"{context.chat_data['player2_name']} = ⭕\n\n"
            f"Turn: {context.chat_data['player1_name']}",
            reply_markup=build_keyboard(context.chat_data["board"])
        )
        return

    # 🔹 Game Move
    if data.startswith("ttt_"):
        board = context.chat_data.get("board")
        turn = context.chat_data.get("turn")

        if not board:
            return

        # 🔐 Turn Validation
        if turn == "❌" and user_id != context.chat_data.get("player1"):
            return
        if turn == "⭕" and user_id != context.chat_data.get("player2"):
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
                winner_name = (
                    context.chat_data["player1_name"]
                    if winner == "❌"
                    else context.chat_data["player2_name"]
                )
                text = f"🏆 Winner: {winner_name}"

            await query.edit_message_text(
                text,
                reply_markup=build_keyboard(board, game_over=True)
            )
            context.chat_data.clear()
            return

        # Switch Turn
        context.chat_data["turn"] = "⭕" if turn == "❌" else "❌"

        next_player = (
            context.chat_data["player1_name"]
            if context.chat_data["turn"] == "❌"
            else context.chat_data["player2_name"]
        )

        await query.edit_message_text(
            f"🎮 Tic Tac Toe\n\n"
            f"{context.chat_data['player1_name']} = ❌\n"
            f"{context.chat_data['player2_name']} = ⭕\n\n"
            f"Turn: {next_player}",
            reply_markup=build_keyboard(board)
        )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("ttt", start_game))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()

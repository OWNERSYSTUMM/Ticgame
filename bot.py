import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from tictactoe import new_board, build_keyboard, check_winner

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")


# 🎮 When bot is mentioned
async def mention_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❌ Play as X", callback_data="choose_X"),
            InlineKeyboardButton("⭕ Play as O", callback_data="choose_O"),
        ]
    ])

    await update.message.reply_text(
        "🎮 Tic Tac Toe\n\nChoose your side:",
        reply_markup=keyboard
    )


# 🎮 Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    # 🔹 Choose Symbol
    if data.startswith("choose_"):
        if context.chat_data.get("player1"):
            return

        symbol = "❌" if data == "choose_X" else "⭕"
        opposite = "⭕" if symbol == "❌" else "❌"

        context.chat_data["player1"] = user.id
        context.chat_data["player1_name"] = user.first_name
        context.chat_data["player1_symbol"] = symbol
        context.chat_data["player2_symbol"] = opposite
        context.chat_data["waiting"] = True

        join_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Join Game", callback_data="join_game")]
        ])

        await query.edit_message_text(
            f"🎮 Tic Tac Toe\n\n"
            f"{user.first_name} chose {symbol}\n"
            f"Waiting for opponent...",
            reply_markup=join_btn
        )
        return

    # 🔹 Join Game
    if data == "join_game":
        if user.id == context.chat_data.get("player1"):
            return

        context.chat_data["player2"] = user.id
        context.chat_data["player2_name"] = user.first_name
        context.chat_data["board"] = new_board()
        context.chat_data["turn"] = context.chat_data["player1_symbol"]
        context.chat_data["waiting"] = False

        await query.edit_message_text(
            f"🎮 Game Started!\n\n"
            f"{context.chat_data['player1_name']} = {context.chat_data['player1_symbol']}\n"
            f"{context.chat_data['player2_name']} = {context.chat_data['player2_symbol']}\n\n"
            f"Turn: {context.chat_data['player1_name']}",
            reply_markup=build_keyboard(context.chat_data["board"])
        )
        return

    # 🔹 Game Moves
    if data.startswith("ttt_"):
        if context.chat_data.get("waiting"):
            return

        board = context.chat_data.get("board")
        turn = context.chat_data.get("turn")

        if not board:
            return

        # Turn validation
        if turn == context.chat_data["player1_symbol"] and user.id != context.chat_data["player1"]:
            return

        if turn == context.chat_data["player2_symbol"] and user.id != context.chat_data["player2"]:
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
                    if winner == context.chat_data["player1_symbol"]
                    else context.chat_data["player2_name"]
                )
                text = f"🏆 Winner: {winner_name}"

            await query.edit_message_text(
                text,
                reply_markup=build_keyboard(board, game_over=True)
            )
            context.chat_data.clear()
            return

        # Switch turn
        context.chat_data["turn"] = (
            context.chat_data["player2_symbol"]
            if turn == context.chat_data["player1_symbol"]
            else context.chat_data["player1_symbol"]
        )

        next_player = (
            context.chat_data["player1_name"]
            if context.chat_data["turn"] == context.chat_data["player1_symbol"]
            else context.chat_data["player2_name"]
        )

        await query.edit_message_text(
            f"🎮 Tic Tac Toe\n\n"
            f"{context.chat_data['player1_name']} = {context.chat_data['player1_symbol']}\n"
            f"{context.chat_data['player2_name']} = {context.chat_data['player2_symbol']}\n\n"
            f"Turn: {next_player}",
            reply_markup=build_keyboard(board)
        )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Detect mention
    app.add_handler(MessageHandler(filters.Entity("mention"), mention_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()

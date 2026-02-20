import uuid
import random
import asyncio
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


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Play", callback_data="start_game")],
        [InlineKeyboardButton("AI Mode", callback_data="start_ai")]
    ])

    result = InlineQueryResultArticle(
        id=str(uuid.uuid4()),
        title="🎮 Tic Tac Toe",
        description="Start a new match",
        input_message_content=InputTextMessageContent("🎮 Tic Tac Toe"),
        reply_markup=keyboard,
    )

    await query.answer([result], cache_time=0)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    data = query.data

    game_key = query.inline_message_id or (
        query.message.message_id if query.message else None
    )

    if not game_key:
        return

    # ───── START MULTIPLAYER ─────
    if data == "start_game":
        create_game(game_key, user.id, user.first_name, "❌", ai=False)
        db.get_user(user.id, user.first_name)

        join_btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Join", callback_data="join")]]
        )

        await query.edit_message_text(
            f"🎮 Tic Tac Toe\n\n"
            f"❌ {user.first_name}\n\n"
            "Waiting for opponent...",
            reply_markup=join_btn
        )
        return

    # ───── START AI MODE ─────
    if data == "start_ai":
        create_game(game_key, user.id, user.first_name, "❌", ai=True)
        db.get_user(user.id, user.first_name)

        game = get_game(game_key)
        game["player2"] = 0
        game["player2_name"] = "AI 🤖"

        await query.edit_message_text(
            build_game_text(game),
            reply_markup=build_board(game["board"])
        )
        return

    # ───── JOIN ─────
    if data == "join":
        game = get_game(game_key)
        if not game or user.id == game["player1"]:
            return

        if game["player2"]:
            await query.answer("Game full 😎", show_alert=True)
            return

        game["player2"] = user.id
        game["player2_name"] = user.first_name
        db.get_user(user.id, user.first_name)

        await query.edit_message_text(
            build_game_text(game),
            reply_markup=build_board(game["board"])
        )
        return

    # ───── MOVE ─────
    if data.startswith("move_"):
        game = get_game(game_key)
        if not game:
            return

        if user.id not in [game["player1"], game["player2"]]:
            await query.answer("🚫 Ye tera game nahi hai!", show_alert=True)
            return

        current_turn_player = (
            game["player1"]
            if game["turn"] == game["symbol1"]
            else game["player2"]
        )

        if user.id != current_turn_player:
            await query.answer("✋ Tera turn nahi hai!", show_alert=True)
            return

        index = int(data.split("_")[1])

        if game["board"][index] != " ":
            await query.answer("❌ Already filled!", show_alert=True)
            return

        game["board"][index] = game["turn"]
        winner = check_winner(game["board"])

        # 🔥 WINNER BLOCK UPDATED
        if winner:

            if winner == "Draw":
                result_text = "🤝 It's a Draw!"
            else:
                winner_name = (
                    game["player1_name"]
                    if winner == game["symbol1"]
                    else game["player2_name"]
                )

                loser_name = (
                    game["player2_name"]
                    if winner == game["symbol1"]
                    else game["player1_name"]
                )

                result_text = (
                    f"🏆 Winner: {winner_name}\n"
                    f"💀 Loser: {loser_name}"
                )

            await query.edit_message_text(
                build_game_text(game) + "\n" + result_text,
                reply_markup=build_board(game["board"])
            )

            delete_game(game_key)
            return

        game["turn"] = (
            game["symbol2"]
            if game["turn"] == game["symbol1"]
            else game["symbol1"]
        )

        await query.edit_message_text(
            build_game_text(game),
            reply_markup=build_board(game["board"])
        )

        # 🔥 AI DELAYED MOVE
        if game["ai"] and game["turn"] == game["symbol2"]:

            await query.edit_message_text(
                build_game_text(game) + "\n\n🤖 AI is thinking...",
                reply_markup=build_board(game["board"])
            )

            await asyncio.sleep(2)

            ai_index = ai_move(
                game["board"],
                game["symbol2"],
                game["symbol1"]
            )

            if ai_index is not None:
                game["board"][ai_index] = game["symbol2"]

            winner = check_winner(game["board"])

            # 🔥 AI WINNER BLOCK UPDATED
            if winner:

                if winner == "Draw":
                    result_text = "🤝 It's a Draw!"
                else:
                    winner_name = (
                        game["player1_name"]
                        if winner == game["symbol1"]
                        else game["player2_name"]
                    )

                    loser_name = (
                        game["player2_name"]
                        if winner == game["symbol1"]
                        else game["player1_name"]
                    )

                    result_text = (
                        f"🏆 Winner: {winner_name}\n"
                        f"💀 Loser: {loser_name}"
                    )

                await query.edit_message_text(
                    build_game_text(game) + "\n" + result_text,
                    reply_markup=build_board(game["board"])
                )

                delete_game(game_key)
                return

            game["turn"] = game["symbol1"]

            await query.edit_message_text(
                build_game_text(game),
                reply_markup=build_board(game["board"])
            )


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = db.get_leaderboard()
    text = "🏆 Leaderboard\n\n"

    for i, user in enumerate(top, 1):
        text += f"{i}. {user['name']} - {user['wins']} wins\n"

    await update.message.reply_text(text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Owner", url="https://t.me/APNA_SYSTEM"),
            InlineKeyboardButton("Support", url="https://t.me/SystemQuizUpdates"),
        ]
    ])

    text = (
        "🎮 *Welcome to Tic Tac Toe Bot!*\n\n"
        "Play classic ❌⭕ battles with friends directly in groups.\n\n"
        "✨ *Features:*\n"
        "• Inline instant game\n"
        "• Multiplayer mode\n"
        "• AI mode\n"
        "• Leaderboard & Coins\n\n"
        "🚀 *How to Play?*\n"
        "Type:\n"
        "`@YourBotUsername`\n\n"
        "Select game → Invite friend → Start playing!\n\n"
        "👇 Need help? Use buttons below."
    )

    await update.message.reply_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()

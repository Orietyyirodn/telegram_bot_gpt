# bot.py (Частина 1)

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

import credentials
from gpt import ChatGptService
from util import (
    load_message,
    load_prompt,
    send_text,
    send_image,
    send_text_buttons,
    show_main_menu,
)

chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)

# ===========================
# START
# ===========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()
    context.user_data["mode"] = "MENU"

    await send_image(update, context, "main")

    await send_text(
        update,
        context,
        load_message("main")
    )

    await show_main_menu(
        update,
        context,
        {
            "start": "Головне меню",
            "random": "Дізнатися випадковий цікавий факт 🧠",
            "gpt": "Задати питання ChatGPT 🤖",
            "talk": "Поговорити з відомою особистістю 👤",
            "quiz": "Взяти участь у квізі ❓"
        }
    )


# ===========================
# RANDOM FACT
# ===========================

async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["mode"] = "RANDOM"

    await send_image(update, context, "random")

    prompt = load_prompt("random")

    response = await chat_gpt.send_question(
        prompt,
        "Дай один цікавий факт."
    )

    await send_text_buttons(
        update,
        context,
        response,
        buttons={
            "random_more": "🧠 Хочу ще факт",
            "random_finish": "🏠 Закінчити"
        }
    )


async def random_callback(update: Update, context):

    query = update.callback_query.data

    await update.callback_query.answer()

    if query == "random_more":
        await random(update, context)

    elif query == "random_finish":
        await start(update, context)


# ===========================
# GPT
# ===========================

async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["mode"] = "GPT_WAIT"

    await send_image(update, context, "gpt")

    await send_text(
        update,
        context,
        load_message("gpt")
    )


# ===========================
# TALK
# ===========================

async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["mode"] = "TALK_SELECT"

    await send_image(update, context, "talk")

    await send_text_buttons(
        update,
        context,
        "Оберіть співрозмовника:",
        buttons={
            "talk_cobain": "🎸 Курт Кобейн",
            "talk_hawking": "🌌 Стівен Гокінг",
            "talk_nietzsche": "📚 Фрідріх Ніцше",
            "talk_queen": "👑 Королева Єлизавета II",
            "talk_tolkien": "🧙 Джон Рональд Руел Толкін"
        }
    )

PERSON_PROMPTS = {
    "talk_cobain": "talk_cobain",
    "talk_hawking": "talk_hawking",
    "talk_nietzsche": "talk_nietzsche",
    "talk_queen": "talk_queen",
    "talk_tolkien": "talk_tolkien",
}


async def talk_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query.data
    await update.callback_query.answer()

    if query not in PERSON_PROMPTS:
        return

    context.user_data["mode"] = "TALK"

    # Завантажуємо промпт із папки prompts
    context.user_data["person_prompt"] = load_prompt(
        PERSON_PROMPTS[query]
    )

    await send_image(
        update,
        context,
        PERSON_PROMPTS[query]
    )

    await send_text(
        update,
        context,
        "Тепер можете поставити будь-яке питання."
    )

# ===========================
# QUIZ
# ===========================

TOPICS = {
    "quiz_python": "Python",
    "quiz_history": "Історія",
    "quiz_science": "Наука",
    "quiz_sport": "Спорт"
}


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["mode"] = "QUIZ_SELECT"

    await send_image(update, context, "quiz")

    await send_text_buttons(
        update,
        context,
        "Оберіть тему квізу:",
        buttons={
            "quiz_python": "🐍 Python",
            "quiz_history": "📜 Історія",
            "quiz_science": "🔬 Наука",
            "quiz_sport": "⚽ Спорт"
        }
    )


async def quiz_callback(update: Update, context):

    query = update.callback_query.data

    await update.callback_query.answer()

    if query not in TOPICS:
        return

    context.user_data["mode"] = "QUIZ"

    context.user_data["quiz_topic"] = TOPICS[query]

    context.user_data["quiz_score"] = 0

    context.user_data["quiz_number"] = 1

    prompt = f"""
Створи питання для квізу на тему {TOPICS[query]}.

Постав одне питання.

Напиши після нього правильну відповідь окремим рядком:

Правильна відповідь: ...
"""

    response = await chat_gpt.send_question(prompt, "")

    context.user_data["quiz_answer"] = response.split(
        "Правильна відповідь:"
    )[-1].strip()

    question = response.split(
        "Правильна відповідь:"
    )[0]

    await send_text(update, context, question)


# ===========================
# TEXT HANDLER
# ===========================

async def plain_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    mode = context.user_data.get("mode")

    text = update.message.text

    # ---------------- GPT ----------------

    if mode == "GPT_WAIT":

        response = await chat_gpt.send_question(
            load_prompt("gpt"),
            text
        )

        await send_text_buttons(
            update,
            context,
            response,
            buttons={
                "gpt_next": "🔄 Наступне питання",
                "gpt_finish": "🏠 Закінчити"
            }
        )

        return

    # ---------------- TALK ----------------

    if mode == "TALK":

        response = await chat_gpt.send_question(
            context.user_data["person_prompt"],
            text
        )

        await send_text_buttons(
            update,
            context,
            response,
            buttons={
                "talk_finish": "🏠 Закінчити"
            }
        )

        return

    # ---------------- QUIZ ----------------

    if mode == "QUIZ":

        answer = context.user_data["quiz_answer"]

        check_prompt = f"""
Правильна відповідь:

{answer}

Відповідь користувача:

{text}

Напиши лише YES або NO.
"""

        result = await chat_gpt.send_question(
            check_prompt,
            ""
        )

        if "YES" in result.upper():

            context.user_data["quiz_score"] += 1

            await send_text(
                update,
                context,
                "✅ Правильно!"
            )

        else:

            await send_text(
                update,
                context,
                f"❌ Неправильно.\n\nПравильна відповідь:\n{answer}"
            )

        number = context.user_data["quiz_number"]

        if number >= 3:

            score = context.user_data["quiz_score"]

            await send_text_buttons(
                update,
                context,
                f"🏆 Квіз завершено!\n\nПравильних відповідей: {score}/3",
                buttons={
                    "quiz_again": "🔄 Ще квіз",
                    "quiz_finish": "🏠 Закінчити"
                }
            )

            context.user_data["mode"] = "MENU"

            return

        context.user_data["quiz_number"] += 1

        prompt = f"""
Створи ще одне питання на тему
{context.user_data['quiz_topic']}.

Напиши:

Питання

Правильна відповідь: ...
"""

        response = await chat_gpt.send_question(prompt, "")

        context.user_data["quiz_answer"] = response.split(
            "Правильна відповідь:"
        )[-1].strip()

        question = response.split(
            "Правильна відповідь:"
        )[0]

        await send_text(update, context, question)

# ===========================
# CALLBACKS
# ===========================

async def gpt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query.data

    await update.callback_query.answer()

    if query == "gpt_finish":

        await start(update, context)

    elif query == "gpt_next":

        context.user_data["mode"] = "GPT_WAIT"

        await send_text(
            update,
            context,
            "✍️ Напишіть наступне питання."
        )


async def talk_finish_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.callback_query.answer()

    await start(update, context)


async def quiz_finish_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query.data

    await update.callback_query.answer()

    if query == "quiz_again":

        await quiz(update, context)

    elif query == "quiz_finish":

        await start(update, context)


# ===========================
# APPLICATION
# ===========================

app = ApplicationBuilder().token(
    credentials.BOT_TOKEN
).build()


# ===========================
# COMMANDS
# ===========================

app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

app.add_handler(
    CommandHandler(
        "random",
        random
    )
)

app.add_handler(
    CommandHandler(
        "gpt",
        gpt
    )
)

app.add_handler(
    CommandHandler(
        "talk",
        talk
    )
)

app.add_handler(
    CommandHandler(
        "quiz",
        quiz
    )
)


# ===========================
# TEXT
# ===========================

app.add_handler(

    MessageHandler(

        filters.TEXT
        &
        ~filters.COMMAND,

        plain_text_handler

    )

)


# ===========================
# CALLBACK RANDOM
# ===========================

app.add_handler(

    CallbackQueryHandler(

        random_callback,

        pattern="^random_"

    )

)


# ===========================
# CALLBACK GPT
# ===========================

app.add_handler(

    CallbackQueryHandler(

        gpt_callback,

        pattern="^gpt_"

    )

)


# ===========================
# CALLBACK TALK
# ===========================

app.add_handler(
    CallbackQueryHandler(
        talk_callback,
        pattern="^talk_(cobain|hawking|nietzsche|queen|tolkien)$"
    )
)

app.add_handler(

    CallbackQueryHandler(

        talk_finish_callback,

        pattern="^talk_finish$"

    )

)


# ===========================
# CALLBACK QUIZ
# ===========================

app.add_handler(

    CallbackQueryHandler(

        quiz_callback,

        pattern="^quiz_python|^quiz_history|^quiz_science|^quiz_sport"

    )

)

app.add_handler(

    CallbackQueryHandler(

        quiz_finish_callback,

        pattern="^quiz_again$|^quiz_finish$"

    )

)


# ===========================
# RUN
# ===========================

print("Bot started...")

app.run_polling()

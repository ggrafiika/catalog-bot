import asyncio
import os
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789))

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

CATALOG_FILE = "catalog.json"

def load_catalog():
    if os.path.exists(CATALOG_FILE):
        try:
            with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "встроенные": [], "боты-менеджеры": [], "общение": [], "обучение": [],
        "музыка": [], "фото/видео": [], "деньги": [], "другое": []
    }

def save_catalog(catalog):
    with open(CATALOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

catalog = load_catalog()

all_categories = ["встроенные", "боты-менеджеры", "общение", "обучение", 
                   "музыка", "фото/видео", "деньги", "другое"]
page_1_categories = all_categories[0:4]
page_2_categories = all_categories[4:8]

class AddBotStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_name = State()
    waiting_for_function = State()
    waiting_for_link = State()
    waiting_for_ad = State()
    waiting_for_author = State()

def start_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Каталог", callback_data="open_catalog")
    builder.button(text="➕ Добавить бота", callback_data="add_bot")
    builder.button(text="ℹ️ О нас", callback_data="about")
    builder.adjust(1)
    return builder.as_markup()

def catalog_menu(page=1):
    builder = InlineKeyboardBuilder()
    if page == 1:
        categories_to_show = page_1_categories
    else:
        categories_to_show = page_2_categories
    
    for cat in categories_to_show:
        count = len(catalog.get(cat, []))
        button_text = f"{cat.capitalize()} ({count})" if count > 0 else cat.capitalize()
        builder.button(text=button_text, callback_data=f"cat_{cat}")
    
    nav_buttons = []
    if page == 1 and page_2_categories:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Далее", callback_data="catalog_page_2"))
    elif page == 2:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog_page_1"))
    
    nav_buttons.append(InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_start"))
    builder.row(*nav_buttons)
    builder.adjust(2)
    return builder.as_markup()

def back_to_catalog_button():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад в каталог", callback_data="open_catalog")
    builder.button(text="🏠 В меню", callback_data="back_to_start")
    builder.adjust(1)
    return builder.as_markup()

def category_keyboard():
    builder = InlineKeyboardBuilder()
    for cat in all_categories:
        builder.button(text=cat.capitalize(), callback_data=f"add_cat_{cat}")
    builder.button(text="🔙 Отмена", callback_data="cancel_add")
    builder.adjust(2)
    return builder.as_markup()

@dp.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "🤖 *Добро пожаловать в Каталог ботов!*\n\nВыбери действие:",
        reply_markup=start_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "open_catalog")
async def open_catalog(callback: CallbackQuery):
    await callback.message.edit_text(
        "📚 *КАТАЛОГ БОТОВ*\n\nВыбери категорию (страница 1/2):",
        reply_markup=catalog_menu(page=1),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "about")
async def about(callback: CallbackQuery):
    about_text = (
        "ℹ️ *О проекте*\n\n"
        "Этот бот-каталог создан в рамках школьного проекта.\n\n"
        "📌 *Автор:* @ggrafiika\n\n"
        "💝 *Поддержать:* напиши @ggrafiika\n\nСпасибо! 🙏"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 В меню", callback_data="back_to_start")
    await callback.message.edit_text(about_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    await callback.message.edit_text(
        "🤖 *Каталог ботов*\n\nВыбери действие:",
        reply_markup=start_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("catalog_page_"))
async def change_catalog_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    await callback.message.edit_text(
        f"📚 *КАТАЛОГ БОТОВ*\n\nВыбери категорию (страница {page}/2):",
        reply_markup=catalog_menu(page=page),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def show_category(callback: CallbackQuery):
    category = callback.data.split("_")[1]
    bots = catalog.get(category, [])
    
    if not bots:
        await callback.message.edit_text(
            f"📭 *Категория: {category.capitalize()}*\n\nПока нет ботов.",
            reply_markup=back_to_catalog_button(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    text = f"📁 *{category.capitalize()}*\n\n"
    for i, b in enumerate(bots, 1):
        text += f"*{i}. {b['name']}*\n📌 {b['function']}\n🔗 [Ссылка]({b['link']})\n📢 {b['ad']}\n👤 {b['author']}\n—————————\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=back_to_catalog_button(),
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    await callback.answer()

@dp.callback_query(F.data == "add_bot")
async def start_add_bot(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 *ДОБАВЛЕНИЕ БОТА*\n\nВыбери категорию:",
        reply_markup=category_keyboard(),
        parse_mode="Markdown"
    )
    await state.set_state(AddBotStates.waiting_for_category)
    await callback.answer()

@dp.callback_query(AddBotStates.waiting_for_category, F.data.startswith("add_cat_"))
async def get_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split("_", 2)[2]
    await state.update_data(category=category)
    await callback.message.edit_text(
        f"📝 *Шаг 1/5*\nВведи *название* бота:",
        parse_mode="Markdown"
    )
    await state.set_state(AddBotStates.waiting_for_name)
    await callback.answer()

@dp.message(AddBotStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📝 *Шаг 2/5*\n*Описание:* что умеет бот?", parse_mode="Markdown")
    await state.set_state(AddBotStates.waiting_for_function)

@dp.message(AddBotStates.waiting_for_function)
async def get_function(message: Message, state: FSMContext):
    await state.update_data(function=message.text)
    await message.answer("📝 *Шаг 3/5*\n*Ссылка:* https://t.me/...", parse_mode="Markdown")
    await state.set_state(AddBotStates.waiting_for_link)

@dp.message(AddBotStates.waiting_for_link)
async def get_link(message: Message, state: FSMContext):
    link = message.text.strip()
    if not (link.startswith("https://t.me/") or link.startswith("http://t.me/")):
        await message.answer("❌ Ссылка должна быть на Telegram бота.")
        return
    await state.update_data(link=link)
    await message.answer("📝 *Шаг 4/5*\n*Реклама:* есть или нет?", parse_mode="Markdown")
    await state.set_state(AddBotStates.waiting_for_ad)

@dp.message(AddBotStates.waiting_for_ad)
async def get_ad(message: Message, state: FSMContext):
    await state.update_data(ad=message.text)
    await message.answer("📝 *Шаг 5/5*\n*Автор:* @username", parse_mode="Markdown")
    await state.set_state(AddBotStates.waiting_for_author)

@dp.message(AddBotStates.waiting_for_author)
async def get_author(message: Message, state: FSMContext):
    await state.update_data(author=message.text)
    data = await state.get_data()
    
    from aiogram.types import InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"approve_{message.from_user.id}"),
         InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{message.from_user.id}")]
    ])
    
    text = f"📨 *Заявка*\n👤 {message.from_user.full_name}\n🤖 {data['name']}\n📂 {data['category']}"
    await bot.send_message(ADMIN_ID, text, reply_markup=keyboard, parse_mode="Markdown")
    await message.answer("✅ *Заявка отправлена!*", reply_markup=start_menu(), parse_mode="Markdown")
    await state.clear()

@dp.callback_query(F.data == "cancel_add")
async def cancel_add(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await back_to_start(callback)

@dp.callback_query(F.data.startswith("approve_"))
async def approve_bot(callback: CallbackQuery):
    await callback.message.edit_text(f"✅ *Одобрено*\n{callback.message.text}", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("reject_"))
async def reject_bot(callback: CallbackQuery):
    await callback.message.edit_text(f"❌ *Отклонено*\n{callback.message.text}", parse_mode="Markdown")
    await callback.answer()

async def main():
    print("🤖 Бот запущен!")
    print(f"👑 Админ ID: {ADMIN_ID}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

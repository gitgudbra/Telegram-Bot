import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatMemberUpdated
from aiogram.filters import Command

BOT_TOKEN = "BOT_TOKEN_HERE"
CHANNEL_ID = CHANNEL_ID
DISCUSSION_GROUP_ID = DISCUSSION_ID
ADMIN_IDS = [ADMIN_IDS]

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.chat_member()
async def on_channel_leave(event: ChatMemberUpdated):
    """Когда кто-то покидает канал - кик из группы"""
    if event.chat.id != CHANNEL_ID:
        return
    
    user = event.new_chat_member.user
    user_id = user.id
    
    old_status = event.old_chat_member.status if event.old_chat_member else None
    new_status = event.new_chat_member.status
    
    was_member = old_status in ['member', 'administrator', 'creator']
    is_removed = new_status in ['left', 'kicked', 'banned']
    
    if was_member and is_removed:
        try:
            member = await bot.get_chat_member(DISCUSSION_GROUP_ID, user_id)
            
            if member.status in ['member', 'administrator']:
                await bot.ban_chat_member(DISCUSSION_GROUP_ID, user_id, revoke_messages=False)
                await bot.unban_chat_member(DISCUSSION_GROUP_ID, user_id)
                
                logging.info(f"Исключен: {user.username or user_id}")
                
                # Отправляем всем админам уведомление
                for admin_id in ADMIN_IDS:
                    try:
                        await bot.send_message(
                            admin_id,
                            f"🚫 @{user.username or 'нет_username'} ({user.first_name}) исключен из группы.\n"
                            f"Причина: Подписка истекла или покинул канал"
                        )
                    except:
                        pass

                try:
                    await bot.send_message(
                        user_id, 
                        "⚠️ Ваша подписка истекла. Вы были удалены из группы.\n"
                        "Продлите подписку, чтобы вернуть доступ."
                    )
                except:
                    pass
                    
        except Exception as e:
            logging.error(f"Ошибка: {e}")

@dp.message(Command("check"))
async def check_setup(message: types.Message):
    """Проверка настроек бота"""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        chat = await bot.get_chat(CHANNEL_ID)
        group = await bot.get_chat(DISCUSSION_GROUP_ID)
        await message.answer(
            f"✅ Канал: {chat.title}\n"
            f"✅ Группа: {group.title}\n"
            f"🤖 Бот работает!"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("myid"))
async def show_my_id(message: types.Message):
    """Показывает ID пользователя"""
    await message.answer(f"🆔 Ваш ID: `{message.from_user.id}`")

@dp.message(Command("help"))
async def help_command(message: types.Message):
    """Справка для админов"""
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer(
        "📋 Команды:\n"
        "/check - проверить подключение\n"
        "/myid - узнать свой ID\n"
        "/help - эта справка\n\n"
        "Бот автоматически исключает из группы тех, кто покинул канал (истекла подписка)."
    )

async def main():
    logging.info("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

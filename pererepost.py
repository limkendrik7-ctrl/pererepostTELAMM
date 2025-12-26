import os
import asyncio
import logging
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

# =====================
# Загрузка ENV
# =====================
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

SOURCE_CHAT = os.getenv("SOURCE_CHAT")
TARGET_CHAT = os.getenv("TARGET_CHAT")

POST_LIMIT = int(os.getenv("POST_LIMIT", 200))
DELAY_SECONDS = int(os.getenv("DELAY_SECONDS", 10))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# =====================
# Логирование
# =====================
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("repost.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# =====================
# Клиент
# =====================
client = TelegramClient("user_session", API_ID, API_HASH)


async def repost_messages():
    await client.start()
    logger.info("Клиент Telegram запущен")

    source = await client.get_entity(SOURCE_CHAT)
    target = await client.get_entity(TARGET_CHAT)

    logger.info(f"Источник: {SOURCE_CHAT}")
    logger.info(f"Цель: {TARGET_CHAT}")
    logger.info(f"Лимит сообщений: {POST_LIMIT}")

    messages = await client.get_messages(
        source,
        limit=POST_LIMIT
    )

    messages = list(reversed(messages))  # чтобы публиковать в хронологическом порядке

    for i, msg in enumerate(messages, start=1):
        try:
            if not msg:
                continue

            logger.info(f"[{i}/{POST_LIMIT}] Репост сообщения ID={msg.id}")

            # ===== Альбомы (группы медиа) =====
            if msg.grouped_id:
                logger.info("Сообщение является частью альбома — пропуск (обработается автоматически)")
                continue

            # ===== Текст =====
            if msg.text and not msg.media:
                await client.send_message(
                    target,
                    msg.text,
                    formatting_entities=msg.entities
                )

            # ===== Фото / Видео / Документы =====
            elif msg.media:
                await client.send_file(
                    target,
                    msg.media,
                    caption=msg.text or "",
                    formatting_entities=msg.entities
                )

            await asyncio.sleep(DELAY_SECONDS)

        except Exception as e:
            logger.error(f"Ошибка при репосте ID={msg.id}: {e}")
            await asyncio.sleep(DELAY_SECONDS * 2)

    logger.info("Репост завершён")


async def main():
    try:
        await repost_messages()
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

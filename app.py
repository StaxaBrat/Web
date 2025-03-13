# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
if not GUILD_ID:
    raise ValueError("❌ Помилка: DISCORD_GUILD_ID не знайдено в змінних середовища! Додайте його в Render.")
GUILD_ID = int(GUILD_ID)


# Ініціалізація бота
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)

# 📌 **Функція ініціалізації бази даних**
def init_db():
    conn = sqlite3.connect('status.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        status TEXT
                    )''')
    conn.commit()
    conn.close()

init_db()

# 📌 **Головна сторінка**
@app.route('/')
def index():
    conn = sqlite3.connect('status.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, status FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('index.html', users=users)

# 📌 **Оновлення статусу через сайт**
@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.json
    username = data.get('username')
    status = data.get('status')
    
    conn = sqlite3.connect('status.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, status) VALUES (?, ?) ON CONFLICT(username) DO UPDATE SET status = ?", 
                   (username, status, status))
    conn.commit()
    conn.close()

    # Оновлення ролі в Discord
    bot.loop.create_task(update_discord_role(username, status))
    
    return jsonify({'message': 'Статус оновлено!'}), 200

# 📌 **Оновлення ролі користувача в Discord**
async def update_discord_role(username, status):
    await bot.wait_until_ready()
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("❌ Сервер не знайдено!")
        return

    member = discord.utils.find(lambda m: m.name == username, guild.members)
    if not member:
        print(f"❌ Користувач {username} не знайдений у Discord!")
        return

    role_mapping = {
        "На роботі": "Працює",
        "Відпочиває": "Відпочиває",
        "Не на роботі": "Неактивний"
    }

    new_role_name = role_mapping.get(status)
    if not new_role_name:
        return

    for role in role_mapping.values():
        existing_role = discord.utils.get(guild.roles, name=role)
        if existing_role in member.roles:
            await member.remove_roles(existing_role)

    new_role = discord.utils.get(guild.roles, name=new_role_name)
    if new_role:
        await member.add_roles(new_role)
        print(f"✅ Роль {new_role_name} видана {username}!")

# 📌 **Запуск бота**
@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user.name} запущено!')

import threading

if __name__ == '__main__':
    import asyncio

    async def main():
        async with bot:
            await bot.start(TOKEN)

    loop = asyncio.get_event_loop()
    loop.create_task(main())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)


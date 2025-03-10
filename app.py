from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))  # ID сервера

# Ініціалізація Flask
app = Flask(__name__)

# Підключення до бази
def get_db_connection():
    conn = sqlite3.connect('status.db')
    conn.row_factory = sqlite3.Row
    return conn

# Головна сторінка: список співробітників
@app.route('/')
def index():
    conn = get_db_connection()
    employees = conn.execute("SELECT username, status FROM users").fetchall()
    conn.close()
    return render_template('index.html', employees=employees)

# Оновлення статусу співробітника
@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.json
    username = data['username']
    new_status = data['status']

    # Оновлюємо базу даних
    conn = get_db_connection()
    conn.execute("UPDATE users SET status = ? WHERE username = ?", (new_status, username))
    conn.commit()
    conn.close()

    # Надсилаємо оновлення в Discord
    update_discord_status(username, new_status)

    return jsonify({"message": "Статус оновлено!"})

# Додавання нового співробітника
@app.route('/add_employee', methods=['POST'])
def add_employee():
    data = request.json
    username = data['username']

    conn = get_db_connection()
    conn.execute("INSERT INTO users (username, status) VALUES (?, ?)", (username, "Не на роботі"))
    conn.commit()
    conn.close()

    return jsonify({"message": "Співробітника додано!"})

# Функція для оновлення статусу в Discord
def update_discord_status(username, new_status):
    ROLE_MAPPING = {
        "✅На роботі": "Працює",
        "💤Відпочиває": "Відпочиває",
        "❌Не на роботі": "Неактивний"
    }

    role_name = ROLE_MAPPING.get(new_status)
    if not role_name:
        return

    bot = commands.Bot(command_prefix="!")

    @bot.event
    async def on_ready():
        guild = bot.get_guild(GUILD_ID)
        member = discord.utils.get(guild.members, name=username)
        if member:
            for role in ROLE_MAPPING.values():
                existing_role = discord.utils.get(guild.roles, name=role)
                if existing_role in member.roles:
                    await member.remove_roles(existing_role)

            new_role = discord.utils.get(guild.roles, name=role_name)
            if new_role:
                await member.add_roles(new_role)

        await bot.close()

    bot.run(TOKEN)

if __name__ == '__main__':
    app.run(debug=True)

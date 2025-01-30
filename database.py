from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGO_URI"))
db = client["telegram_bot"]

def save_user(first_name, username, chat_id, phone_number=None):
    if db.users.find_one({"chat_id": chat_id}):
        return False  # User already exists

    db.users.insert_one({"first_name": first_name, "username": username, "chat_id": chat_id, "phone_number": phone_number})
    return True

def save_chat(chat_id, user_message, bot_response):
    db.chats.insert_one({"chat_id": chat_id, "user_message": user_message, "bot_response": bot_response})

def save_image(chat_id, file_path, description):
    db.files.insert_one({"chat_id": chat_id, "file_path": file_path, "description": description})

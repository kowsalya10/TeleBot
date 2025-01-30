import os
from PIL import Image
from google.cloud import vision
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from transformers import pipeline
import torch
from io import BytesIO

# Load environment variables
load_dotenv()

# Load API keys from environment
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_CLOUD_API_KEY = os.getenv("GOOGLE_CLOUD_API_KEY")

# Set up Google Cloud Vision Client
client = vision.ImageAnnotatorClient()

# Initialize sentiment analysis model using Hugging Face
sentiment_analyzer = pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english', device=0 if torch.cuda.is_available() else -1)

# Command handler to greet the user
async def start(update: Update, context):
    # Create a keyboard with a contact button
    contact_keyboard = [[KeyboardButton("Share Contact", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(contact_keyboard, one_time_keyboard=True)

    await update.message.reply_text(
        "Welcome! 🤖 I am your AI assistant. Feel free to ask me anything!\n\nPlease share your contact to continue.",
        reply_markup=reply_markup
    )

# AI-powered chat function using Google Gemini and Sentiment Analysis
async def chat(update: Update, context):
    user_message = update.message.text

    try:
        # Sentiment Analysis
        sentiment = sentiment_analyzer(user_message)
        sentiment_label = sentiment[0]['label']
        sentiment_score = sentiment[0]['score']

        # Respond with sentiment analysis
        sentiment_reply = f"Sentiment: {sentiment_label} (Confidence: {sentiment_score * 100:.2f}%)\n"

        # Use Gemini to generate response (assuming you still want to use Gemini for chat)
        # Example for Gemini (Replace with actual call if applicable)
        response = "Example response from Gemini"
        ai_reply = response if response else "Sorry, I couldn't generate a response."

        # Combine sentiment analysis result with AI response
        full_reply = sentiment_reply + ai_reply

    except Exception as e:
        full_reply = "An error occurred while processing your request."

    await update.message.reply_text(full_reply)

# Handler to process images sent by the user using Google Cloud Vision
async def analyze_image(update: Update, context):
    try:
        # Download the image from the message
        file = await update.message.photo[-1].get_file()
        file_path = f"downloads/{file.file_unique_id}.jpg"
        await file.download_to_drive(custom_path=file_path)

        await update.message.reply_text("📷 Image received. Processing...")

        # Open the image using PIL (Pillow)
        img = Image.open(file_path).convert("RGB")

        # Convert image to BytesIO
        img_byte_array = BytesIO()
        img.save(img_byte_array, format="JPEG")
        img_byte_array.seek(0)  # Move pointer to the start

        # Perform image analysis with Google Vision API
        image = vision.Image(content=img_byte_array.getvalue())
        response = client.label_detection(image=image)

        # Extract labels and descriptions from the response
        labels = response.label_annotations
        description = "I found the following in the image:\n"
        for label in labels:
            description += f"{label.description} (Confidence: {label.score * 100:.2f}%)\n"

        if not description:
            description = "Sorry, I couldn't analyze the image."

        await update.message.reply_text(f"📷 Image Analysis:\n{description}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error analyzing image: {str(e)}")

# Handler to process contact sharing
async def handle_contact(update: Update, context):
    contact = update.message.contact
    user_name = contact.first_name
    phone_number = contact.phone_number
    await update.message.reply_text(f"Thanks for sharing your contact, {user_name}! 📞")

# Main function to set up the bot
def main():
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))  # AI-powered chat with sentiment analysis
    application.add_handler(MessageHandler(filters.PHOTO, analyze_image))  # Image analysis
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))  # Handle contact sharing

    application.run_polling()

if __name__ == "__main__":
    main()

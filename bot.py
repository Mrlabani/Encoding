import os
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from moviepy.editor import VideoFileClip
from io import BytesIO

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Define the API token for your bot
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to the Video Encoding Bot! Please send me a video file (MP4 or MKV) to encode.")

# Handle video messages
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video_file = update.message.video.file_id
    new_file = await context.bot.get_file(video_file)
    video_stream = BytesIO()
    await new_file.download(video_stream)
    video_stream.seek(0)  # Move to the beginning of the BytesIO stream

    # Save the video temporarily
    input_file = 'input_video.mp4'
    with open(input_file, 'wb') as f:
        f.write(video_stream.read())

    # Prompt user for resolution selection
    keyboard = [
        [InlineKeyboardButton("🔹 480p", callback_data='480p')],
        [InlineKeyboardButton("🔸 720p", callback_data='720p')],
        [InlineKeyboardButton("🔹 1080p", callback_data='1080p')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎥 Please choose a resolution:", reply_markup=reply_markup)

    # Store input file in user data
    context.user_data['input_file'] = input_file

# Handle resolution selection
async def handle_resolution_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback
    resolution = query.data
    context.user_data['resolution'] = resolution

    # Prompt user for the new name
    await query.message.reply_text("✏️ Please provide a new name for the output video (without extension):")

# Handle text messages (for renaming)
async def handle_rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'input_file' in context.user_data and 'resolution' in context.user_data:
        new_name = update.message.text.strip()
        input_file = context.user_data['input_file']
        resolution = context.user_data['resolution']
        output_file = f"{new_name}.mp4"  # Set the new name with .mp4 extension

        # Inform user about encoding start
        await update.message.reply_text("🔄 Encoding your video, please wait...")

        # Process video (encode)
        await encode_video(update, input_file, output_file, resolution)

        # Send back the processed video
        with open(output_file, 'rb') as video:
            await update.message.reply_video(video, caption="✅ Here is your encoded video:")

        # Clean up files
        os.remove(input_file)
        os.remove(output_file)

        # Clear user data
        del context.user_data['input_file']
        del context.user_data['resolution']
    else:
        await update.message.reply_text("⚠️ Please send a video file first.")

async def encode_video(update: Update, input_file: str, output_file: str, resolution: str):
    """Encode the video with specified resolution and quality settings."""
    clip = VideoFileClip(input_file)

    # Set resolution
    if resolution == '480p':
        clip = clip.resize(height=480)
    elif resolution == '720p':
        clip = clip.resize(height=720)
    elif resolution == '1080p':
        clip = clip.resize(height=1080)

    # Write the output video with high-quality settings
    await update.message.reply_text("🔄 Encoding... This may take a moment.")
    clip.write_videofile(output_file, codec='libx264', audio_codec='aac', bitrate="3000k")

    # Inform when encoding is complete
    await update.message.reply_text("✅ Encoding complete!")

# Main function to run the bot
async def main():
    application = ApplicationBuilder().token(API_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Video, handle_video))
    application.add_handler(CallbackQueryHandler(handle_resolution_selection))  # Handle resolution selection
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rename))

    # Start the bot
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
  

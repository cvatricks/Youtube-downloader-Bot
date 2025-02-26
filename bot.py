from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from pytube import YouTube
import re
import os

# Add your API ID, API Hash, and Bot Token here
api_id = 'YOUR_API_ID'
api_hash = 'YOUR_API_HASH'
bot_token = 'YOUR_BOT_TOKEN'

# Initialize the Pyrogram client
app = Client("youtube_downloader_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Start message with an inline keyboard
start_message = (
    "🎬 Welcome to the YouTube Video Downloader Bot!\n"
    "Send me a YouTube video URL to get started."
)

keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("📖 How to Use", url="https://yourwebsite.com/how-to-use")],
        [InlineKeyboardButton("💌 Feedback", url="https://yourwebsite.com/feedback")],
        [InlineKeyboardButton("ℹ️ About Bot", callback_data="about")],
    ]
)

# Start command handler
@app.on_message(filters.command("start"))
def start_command(client, message):
    message.reply_text(start_message, reply_markup=keyboard)

# About command handler
@app.on_callback_query(filters.regex("about"))
def about_command(client, callback_query):
    about_text = (
        "🤖 This bot allows you to download and stream YouTube videos.\n"
        "Created with ❤️ by Your Name.\n"
        "For more information, visit our website: [Website Link](https://yourwebsite.com/about)"
    )
    callback_query.message.edit_text(about_text, parse_mode="markdown")

# Handle incoming messages containing YouTube video URLs
@app.on_message(filters.regex(r"https://www\.youtube\.com/watch\?v=.+"))
def handle_download(client, message):
    chat_id = message.chat.id
    url = message.text

    yt = YouTube(url)
    download_directory = "downloads"
    os.makedirs(download_directory, exist_ok=True)

    format_buttons = []
    available_formats = []

    for stream in yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc():
        if stream.includes_video_track:
            available_formats.append(stream)

    if not available_formats:
        client.send_message(chat_id, "No video formats available for this URL.")
        return

    for resolution in ["240p", "360p", "720p", "1080p"]:
        format_found = False
        for stream in available_formats:
            if resolution in stream.resolution:
                format_buttons.append([InlineKeyboardButton(resolution, callback_data=f"format_{available_formats.index(stream)}|{url}|{download_directory}")])
                format_found = True
                break
        if not format_found:
            format_buttons.append([InlineKeyboardButton(f"No {resolution}", callback_data=f"no_format|{url}|{download_directory}")])

    reply_markup = InlineKeyboardMarkup(format_buttons)

    message.reply("Processing the link and available formats:")
    message.reply("Choose a format to download or stream:", reply_markup=reply_markup)

# Handle callback queries for format selection
@app.on_callback_query(filters.regex(r"^(format_\d+|no_format)\|.+\|.+"))
def callback_handler(client, callback_query):
    chat_id = callback_query.message.chat.id
    callback_data = callback_query.data.split('|')
    format_choice, url, download_directory = callback_data

    if format_choice == "no_format":
        client.send_message(chat_id, "No video format available for streaming.")
        return

    format_choice = int(format_choice.replace("format_", ""))
    yt = YouTube(url)

    try:
        selected_stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc()[format_choice]
        video_title = re.sub(r'[\/:*?"<>|]', '-', yt.title)
        video_path = os.path.join(download_directory, video_title + ".mp4")
        selected_stream.download(output_path=download_directory, filename=video_title)
        video_file = open(video_path, "rb")
        client.send_video(chat_id, video=InputFile(video_file))
        os.remove(video_path)
        video_file.close()

    except Exception as e:
        callback_query.answer(text=f"Error: {str(e)}")

# Start the bot
if __name__ == "__main__":
    app.run()

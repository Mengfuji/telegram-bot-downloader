import yt_dlp
import os
import sys
import asyncio
import re
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# កំណត់ token bot របស់អ្នក
BOT_TOKEN = "8523601140:AAG8bCsbvOxvaUGhd8AUOVLauyaMiit8S7Y"

def auto_download_social_media(url, format_choice='mp4'):
    """Download media from social media platforms"""
    try:
        # Create folders
        folders = {
            'youtube': 'youtube_downloads',
            'tiktok': 'tiktok_downloads', 
            'facebook': 'facebook_downloads',
            'instagram': 'instagram_downloads'
        }
        
        # Detect platform with better pattern matching
        url_lower = url.lower()
        
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            platform = 'youtube'
        elif 'tiktok.com' in url_lower or 'vm.tiktok.com' in url_lower or 'vt.tiktok.com' in url_lower:
            platform = 'tiktok'
        elif 'facebook.com' in url_lower or 'fb.watch' in url_lower or 'fb.com' in url_lower:
            platform = 'facebook'
        elif 'instagram.com' in url_lower or 'instagr.am' in url_lower:
            platform = 'instagram'
        else:
            platform = 'other'
        
        print(f"🔍 Detected platform: {platform}")
        
        # Create folder
        folder_path = folders.get(platform, 'downloads')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Base download settings
        ydl_opts = {
            'outtmpl': f'{folder_path}/%(title)s.%(ext)s',
            'quiet': False,
            'no_warnings': False,
        }
        
        # Format selection
        if format_choice == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:  # mp4
            # Use simpler format selection for better compatibility
            ydl_opts.update({
                'format': 'best[ext=mp4]/best[ext=webm]/best',
            })
        
        # Platform-specific settings with better compatibility
        common_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        if platform == 'facebook':
            ydl_opts.update({
                'http_headers': common_headers
            })
                
        elif platform == 'instagram':
            ydl_opts.update({
                'http_headers': common_headers,
                # Try without cookies first
                'format': 'best' if format_choice == 'mp4' else 'bestaudio/best',
            })
            
        elif platform == 'tiktok':
            ydl_opts.update({
                'http_headers': {
                    **common_headers,
                    'Referer': 'https://www.tiktok.com/',
                },
                'format': 'best[ext=mp4]/best' if format_choice == 'mp4' else 'bestaudio/best',
            })
        
        print(f"📥 Downloading from {platform} as {format_choice}...")
        print(f"📋 Using options: {ydl_opts}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first to get title
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            
            # Clean filename from invalid characters
            title_clean = re.sub(r'[<>:"/\\|?*]', '', title)
            
            # Download the media
            ydl.download([url])
            
            # Get the actual filename
            filename = ydl.prepare_filename(info)
            
            if format_choice == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'
            
            return {
                'success': True,
                'filename': filename,
                'title': title_clean,
                'platform': platform,
                'format': format_choice
            }
            
    except Exception as e:
        print(f"❌ Download error: {e}")
        return {
            'success': False,
            'error': str(e)
        }

async def handle_download_error(update: Update, error_msg: str, platform: str):
    """Handle download errors with platform-specific solutions"""
    if 'instagram' in error_msg.lower():
        solution = "\n\n💡 **ដំណោះស្រាយ Instagram:**\n• វីដេអូត្រូវតែសាធារណៈ\n• ប្រើ cookies.txt សម្រាប់គណនីឯកជន"
    elif 'facebook' in error_msg.lower():
        solution = "\n\n💡 **ដំណោះស្រាយ Facebook:**\n• វីដេអូត្រូវតែសាធារណៈ\n• ពិនិត្យ URL ថាត្រឹមត្រូវ"
    elif 'tiktok' in error_msg.lower():
        solution = "\n\n💡 **ដំណោះស្រាយ TikTok:**\n• URL អាចផ្លាស់ប្តូរ\n• ពិនិត្យការតភ្ជាប់អ៊ីនធឺណិត"
    else:
        solution = "\n\n💡 ពិនិត្យ URL និងការតភ្ជាប់អ៊ីនធឺណិត"
    
    await update.message.reply_text(f"❌ ទាញយកមិនជោគជ័យ: {error_msg}{solution}")

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🎬 **Social Media Downloader Bot**

ខ្ញុំអាចទាញយកវីដេអូ និងសំលេងពី៖
• 📹 YouTube
• 🎵 TikTok  
• 👥 Facebook
• 📸 Instagram

**របៀបប្រើប្រាស់៖**
**Private Chat:** ផ្ញើ URL → ជ្រើសរើស MP4/MP3
**Group:** ផ្ញើ URL → ជ្រើសរើស MP4/MP3 (inline buttons)
**Channel:** ផ្ញើ URL → ទាញយក MP4 ស្វ័យប្រវត្តិ

**Commands:**
/start - បង្ហាញសារនេះ
/mp3 [url] - ទាញយកជា MP3 ត្រង់
/mp4 [url] - ទាញយកជា MP4 ត្រង់
/help - ជំនួយ
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command with platform-specific tips"""
    help_text = """
📖 **ជំនួយ**

**បណ្តាញសង្គមដែលគាំទ្រ៖**
- 📹 YouTube (youtube.com, youtu.be)
- 🎵 TikTok (tiktok.com, vm.tiktok.com, vt.tiktok.com)
- 👥 Facebook (facebook.com, fb.watch, fb.com)
- 📸 Instagram (instagram.com, instagr.am)

**របៀបប្រើប្រាស់នៅ Group៖**
ផ្ញើ URL → ជ្រើសរើស MP4/MP3 តាម inline buttons

**របៀបប្រើប្រាស់នៅ Channel៖**
ផ្ញើ URL → ទាញយក MP4 ស្វ័យប្រវត្តិ

**បញ្ហាធម្មតា៖**
• Instagram: វីដេអូត្រូវតែសាធារណៈ
• Facebook: វីដេអូត្រូវតែសាធារណៈ  
• TikTok: URL អាចផ្លាស់ប្តូររហូត
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def mp3_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Direct MP3 download command"""
    if not context.args:
        await update.message.reply_text("❌ សូមផ្ញើ URL បន្ទាប់ពីពាក្យបញ្ជា:\n/mp3 https://youtube.com/...")
        return
    
    url = context.args[0]
    await update.message.reply_text("⏬ កំពុងទាញយកជា MP3...")
    
    result = auto_download_social_media(url, 'mp3')
    
    if result['success']:
        try:
            file_size = os.path.getsize(result['filename'])
            
            if file_size > 50 * 1024 * 1024:
                await update.message.reply_text(
                    f"📁 ឯកសារធំពេក ({file_size//1024//1024}MB)។ "
                    f"សូមព្យាយាមទាញយកពី URL ផ្សេង។"
                )
            else:
                await update.message.reply_audio(
                    audio=open(result['filename'], 'rb'),
                    caption=f"🎵 {result['title']}\nប្រភព: {result['platform']}\nទម្រង់: MP3",
                    title=result['title']
                )
                await update.message.reply_text("✅ ទាញយក MP3 រួចរាល់!")
                
        except Exception as e:
            await update.message.reply_text(f"❌ កំហុស: {str(e)}")
        
        # Clean up downloaded file
        try:
            os.remove(result['filename'])
        except:
            pass
            
    else:
        await handle_download_error(update, result['error'], result.get('platform', 'unknown'))

async def mp4_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Direct MP4 download command"""
    if not context.args:
        await update.message.reply_text("❌ សូមផ្ញើ URL បន្ទាប់ពីពាក្យបញ្ជា:\n/mp4 https://youtube.com/...")
        return
    
    url = context.args[0]
    await update.message.reply_text("⏬ កំពុងទាញយកជា MP4...")
    
    result = auto_download_social_media(url, 'mp4')
    
    if result['success']:
        try:
            file_size = os.path.getsize(result['filename'])
            
            if file_size > 50 * 1024 * 1024:
                await update.message.reply_text(
                    f"📁 ឯកសារធំពេក ({file_size//1024//1024}MB)។ "
                    f"សូមព្យាយាមទាញយកជា MP3 វិញ (/mp3)"
                )
            else:
                await update.message.reply_video(
                    video=open(result['filename'], 'rb'),
                    caption=f"🎬 {result['title']}\nប្រភព: {result['platform']}\nទម្រង់: MP4"
                )
                await update.message.reply_text("✅ ទាញយក MP4 រួចរាល់!")
                
        except Exception as e:
            await update.message.reply_text(f"❌ កំហុស: {str(e)}")
        
        # Clean up downloaded file
        try:
            os.remove(result['filename'])
        except:
            pass
            
    else:
        await handle_download_error(update, result['error'], result.get('platform', 'unknown'))

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages in private chat - REPLY KEYBOARD"""
    text = update.message.text
    
    # Check if message contains URL from supported platforms
    supported_domains = [
        'youtube.com', 'youtu.be', 
        'tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com',
        'facebook.com', 'fb.watch', 'fb.com',
        'instagram.com', 'instagr.am'
    ]
    
    if any(domain in text.lower() for domain in supported_domains):
        # Store URL in context for format selection
        context.user_data['last_url'] = text
        
        # Ask for format choice with REPLY keyboard (PRIVATE CHAT ONLY)
        keyboard = [
            ["MP4 🎥", "MP3 🎵"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            "📁 **ជ្រើសរើសប្រភេទឯកសារ:**\n\n"
            "• MP4 🎥 - ទាញយកជាវីដេអូ\n"
            "• MP3 🎵 - ទាញយកជាសំលេង",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    elif text in ["MP4 🎥", "MP3 🎵"] and 'last_url' in context.user_data:
        # User selected format
        url = context.user_data['last_url']
        format_choice = 'mp4' if "MP4" in text else 'mp3'
        
        await update.message.reply_text(
            f"⏬ កំពុងទាញយកជា {format_choice.upper()}... សូមរង់ចាំ!",
            reply_markup=None  # Remove keyboard
        )
        
        result = auto_download_social_media(url, format_choice)
        
        if result['success']:
            try:
                file_size = os.path.getsize(result['filename'])
                
                if file_size > 50 * 1024 * 1024:
                    await update.message.reply_text(
                        f"📁 ឯកសារធំពេក ({file_size//1024//1024}MB)។ "
                        f"សូមព្យាយាមទាញយកជា MP3 វិញ។"
                    )
                else:
                    if format_choice == 'mp4':
                        await update.message.reply_video(
                            video=open(result['filename'], 'rb'),
                            caption=f"🎬 {result['title']}\nប្រភព: {result['platform']}\nទម្រង់: MP4"
                        )
                    else:
                        await update.message.reply_audio(
                            audio=open(result['filename'], 'rb'),
                            caption=f"🎵 {result['title']}\nប្រភព: {result['platform']}\nទម្រង់: MP3",
                            title=result['title']
                        )
                    await update.message.reply_text("✅ ទាញយករួចរាល់!")
                    
            except Exception as e:
                await update.message.reply_text(f"❌ កំហុស: {str(e)}")
            
            # Clean up downloaded file
            try:
                os.remove(result['filename'])
            except:
                pass
                
        else:
            await handle_download_error(update, result['error'], result.get('platform', 'unknown'))
        
        # Clear stored URL
        context.user_data.pop('last_url', None)
        
    else:
        await update.message.reply_text(
            "សូមផ្ញើ URL ពី៖\n"
            "• YouTube\n• TikTok\n• Facebook\n• Instagram"
        )

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages in group - INLINE KEYBOARD"""
    text = update.message.text
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    
    # Check if message contains URL from supported platforms
    supported_domains = [
        'youtube.com', 'youtu.be', 
        'tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com',
        'facebook.com', 'fb.watch', 'fb.com',
        'instagram.com', 'instagr.am'
    ]
    
    if any(domain in text.lower() for domain in supported_domains):
        # Store URL in context for callback
        context.user_data[f'url_{chat_id}_{message_id}'] = text
        
        # Create INLINE keyboard for group
        keyboard = [
            [
                InlineKeyboardButton("MP4 🎥", callback_data=f"mp4_{chat_id}_{message_id}"),
                InlineKeyboardButton("MP3 🎵", callback_data=f"mp3_{chat_id}_{message_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📁 **ជ្រើសរើសប្រភេទឯកសារ:**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages in channel - AUTO DOWNLOAD MP4 (NO BUTTONS)"""
    if update.channel_post:
        text = update.channel_post.text
        chat_id = update.channel_post.chat_id
        
        # Check if message contains URL
        supported_domains = [
            'youtube.com', 'youtu.be', 
            'tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com',
            'facebook.com', 'fb.watch', 'fb.com',
            'instagram.com', 'instagr.am'
        ]
        
        if any(domain in text.lower() for domain in supported_domains):
            
            # Send processing message to channel
            processing_msg = await context.bot.send_message(
                chat_id=chat_id,
                text="⏬ កំពុងទាញយកវីដេអូ...",
                reply_to_message_id=update.channel_post.message_id
            )
            
            # Auto download as MP4 for channel (NO BUTTONS IN CHANNEL)
            result = auto_download_social_media(text, 'mp4')
            
            if result['success']:
                try:
                    file_size = os.path.getsize(result['filename'])
                    
                    if file_size > 50 * 1024 * 1024:
                        # If file too large, try MP3
                        await context.bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=processing_msg.message_id,
                            text="📁 ឯកសារធំពេក កំពុងទាញយកជា MP3..."
                        )
                        
                        # Try MP3 instead
                        result = auto_download_social_media(text, 'mp3')
                        
                        if result['success']:
                            await context.bot.send_audio(
                                chat_id=chat_id,
                                audio=open(result['filename'], 'rb'),
                                caption=f"🎵 {result['title']}\nប្រភព: {result['platform']}",
                                reply_to_message_id=update.channel_post.message_id
                            )
                            await context.bot.delete_message(chat_id=chat_id, message_id=processing_msg.message_id)
                        else:
                            await context.bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=processing_msg.message_id,
                                text=f"❌ ទាញយក MP3 មិនជោគជ័យ: {result['error']}"
                            )
                    else:
                        # Send video
                        await context.bot.send_video(
                            chat_id=chat_id,
                            video=open(result['filename'], 'rb'),
                            caption=f"🎬 {result['title']}\nប្រភព: {result['platform']}",
                            reply_to_message_id=update.channel_post.message_id
                        )
                        await context.bot.delete_message(chat_id=chat_id, message_id=processing_msg.message_id)
                    
                except Exception as e:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=processing_msg.message_id,
                        text=f"❌ កំហុស: {str(e)}"
                    )
                
                # Clean up
                try:
                    os.remove(result['filename'])
                except:
                    pass
                    
            else:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=processing_msg.message_id,
                    text=f"❌ ទាញយកមិនជោគជ័យ: {result['error']}"
                )

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    chat_id = query.message.chat.id
    message_id = query.message.message_id
    
    # Extract format choice and IDs from callback data
    if callback_data.startswith(('mp4_', 'mp3_')):
        format_choice = 'mp4' if callback_data.startswith('mp4_') else 'mp3'
        
        # Extract original message IDs from callback data
        parts = callback_data.split('_')
        if len(parts) >= 3:
            original_chat_id = parts[1]
            original_message_id = parts[2]
            
            # Get stored URL
            url_key = f'url_{original_chat_id}_{original_message_id}'
            url = context.user_data.get(url_key)
            
            if url:
                await query.edit_message_text(f"⏬ កំពុងទាញយកជា {format_choice.upper()}...")
                
                result = auto_download_social_media(url, format_choice)
                
                if result['success']:
                    try:
                        file_size = os.path.getsize(result['filename'])
                        
                        if file_size > 50 * 1024 * 1024:
                            await query.edit_message_text(
                                f"📁 ឯកសារធំពេក ({file_size//1024//1024}MB)។ "
                                f"សូមព្យាយាមទាញយកជា MP3 វិញ។"
                            )
                        else:
                            if format_choice == 'mp4':
                                await context.bot.send_video(
                                    chat_id=chat_id,
                                    video=open(result['filename'], 'rb'),
                                    caption=f"🎬 {result['title']}\nប្រភព: {result['platform']}\nទម្រង់: MP4",
                                    reply_to_message_id=int(original_message_id)
                                )
                            else:
                                await context.bot.send_audio(
                                    chat_id=chat_id,
                                    audio=open(result['filename'], 'rb'),
                                    caption=f"🎵 {result['title']}\nប្រភព: {result['platform']}\nទម្រង់: MP3",
                                    title=result['title'],
                                    reply_to_message_id=int(original_message_id)
                                )
                            await query.edit_message_text("✅ ទាញយករួចរាល់!")
                            
                    except Exception as e:
                        await query.edit_message_text(f"❌ កំហុស: {str(e)}")
                    
                    # Clean up
                    try:
                        os.remove(result['filename'])
                    except:
                        pass
                else:
                    await query.edit_message_text(f"❌ ទាញយកមិនជោគជ័យ: {result['error']}")
                
                # Clean up stored URL
                context.user_data.pop(url_key, None)

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route messages to appropriate handler"""
    if update.channel_post:
        # Message in channel - auto download (NO BUTTONS)
        await handle_channel_message(update, context)
    elif update.message:
        if update.message.chat.type == "private":
            # Private message - reply keyboard
            await handle_private_message(update, context)
        elif update.message.chat.type in ["group", "supergroup"]:
            # Group message - inline keyboard
            await handle_group_message(update, context)

def main():
    print("🚀 Starting Telegram Bot - Full Support (Private, Group, Channel)...")
    
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("mp3", mp3_command))
        application.add_handler(CommandHandler("mp4", mp4_command))
        
        # Add callback query handler for inline keyboards
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Handler for all messages (private, group, channel)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
        
        print("🤖 Bot is running with FULL support:")
        print("   💬 PRIVATE: Reply keyboard buttons")
        print("   👥 GROUP: Inline keyboard buttons") 
        print("   📢 CHANNEL: Auto-download MP4")
        print("📦 Supported platforms: YouTube, TikTok, Facebook, Instagram")
        print("🔧 Enhanced download settings for better compatibility")
        
        application.run_polling()
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
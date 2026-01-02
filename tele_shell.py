import os
import re
import subprocess
import psutil
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = "YOUR_BOT_TOKEN_HERE"  # <--- PASTE YOUR TOKEN HERE
AUTHORIZED_USER_ID = 123456789  # <--- PASTE YOUR ID HERE
HOME_DIR = os.path.expanduser("~")

# --- LISTS ---
# 1. BLOCKED: These freeze the bot because they never exit (Interactive CLI)
BLOCKED_COMMANDS = [
    "cmatrix", "vim", "nano", "htop", "top", "less", "more", "man", 
    "watch", "tmux", "screen"
]

# 2. GUI APPS: These will be launched in the background (Non-blocking)
GUI_COMMANDS = [
    "firefox", "google-chrome", "chromium", "brave-browser", 
    "gedit", "nautilus", "vlc", "mpv", "code"
]

# --- UTILS ---
def clean_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

async def check_user(update: Update):
    if update.effective_user.id != AUTHORIZED_USER_ID: return False
    return True

# --- COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user(update): return
    context.user_data['cwd'] = HOME_DIR
    await update.message.reply_text(
        "⚡ **TeLinux Online**\n\n"
        "✅ **System Ready**\n"
        "🔹 **Blocklist Active:** `cmatrix` and interactive tools blocked.\n"
        "🔹 **GUI Mode:** Firefox/Chrome launch instantly on PC.\n\n"
        "Type `/help` for commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user(update): return
    help_text = (
        "📚 **TeLinux Command List**\n\n"
        "⌨️ **Shell:** Type any command (`ls`, `whoami`, `dnf update`)\n"
        "🖥️ **GUI:** Type `firefox` or `chrome` to open on PC\n"
        "📂 **Files:** `/pull filename` (Download) or Send File (Upload)\n"
        "📊 **Stats:** `/health` (CPU/RAM Usage)\n"
        "🛑 **Safety:** `cmatrix`, `vim`, etc. are blocked."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user(update): return
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    health_msg = (
        "📊 **System Health**\n"
        f"🖥️ **CPU:** {cpu}%\n"
        f"📟 **RAM:** {ram.percent}% ({ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB)\n"
        f"💽 **Disk:** {disk.percent}% used"
    )
    await update.message.reply_text(health_msg)

async def handle_shell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user(update): return
    
    raw_text = update.message.text.strip()
    if not raw_text: return
    
    # 1. SMART PARSING
    parts = raw_text.split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    cmd_full = f"{command} {args}".strip()
    cwd = context.user_data.get('cwd', HOME_DIR)

    # 2. BLOCKLIST CHECK
    if command in BLOCKED_COMMANDS:
        await update.message.reply_text(f"🛑 **Blocked:** `{command}` is interactive and will freeze the bot.")
        return

    # 3. GUI LAUNCHER (Fire-and-Forget)
    if command in GUI_COMMANDS:
        try:
            # We use Popen so Python DOES NOT WAIT for the app to close
            env = os.environ.copy()
            env["DISPLAY"] = ":0" # Force open on Laptop Screen
            subprocess.Popen(cmd_full, shell=True, cwd=cwd, env=env, start_new_session=True)
            await update.message.reply_text(f"🚀 **Launched:** `{command}` on PC display.")
        except Exception as e:
            await update.message.reply_text(f"⚠️ **Launch Error:** `{str(e)}`")
        return

    # 4. STANDARD SHELL EXECUTION (Blocking)
    # CD Command
    if command == "cd":
        target = args if args else HOME_DIR
        new_path = os.path.normpath(os.path.join(cwd, target))
        if os.path.isdir(new_path):
            context.user_data['cwd'] = new_path
            await update.message.reply_text(f"📁 **Directory:** `{new_path}`")
        else:
            await update.message.reply_text(f"❌ Not found: `{args}`")
        return

    # Auto-Sudo
    privileged = ['dnf', 'reboot', 'shutdown', 'systemctl']
    if any(p == command for p in privileged) and not cmd_full.startswith('sudo'):
        cmd_full = f"sudo {cmd_full}"

    try:
        env = os.environ.copy()
        env["PATH"] = "/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin"
        
        # Run command with 30s timeout
        process = subprocess.run(cmd_full, shell=True, cwd=cwd, env=env, capture_output=True, text=True, timeout=30)
        output = clean_ansi(process.stdout + process.stderr)
        
        if not output.strip(): output = "(Done)"
        
        await update.message.reply_text(f"💻 **Output:**\n```\n{output[:4000]}```", parse_mode="Markdown")
        
    except subprocess.TimeoutExpired:
        await update.message.reply_text("⏱️ **Timeout:** Command took too long.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ **Error:** `{str(e)}`")

async def pull_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user(update): return
    if not context.args:
        await update.message.reply_text("❓ Usage: `/pull filename`")
        return

    filename = " ".join(context.args)
    cwd = context.user_data.get('cwd', HOME_DIR)
    path = os.path.abspath(os.path.join(cwd, filename))
    
    if os.path.isfile(path):
        try:
            await update.message.reply_document(document=open(path, 'rb'))
        except Exception as e:
            await update.message.reply_text(f"❌ **Failed:** `{str(e)}` (Max 50MB)")
    else:
        await update.message.reply_text(f"❌ **Not found:** `{filename}`")

async def push_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_user(update): return
    cwd = context.user_data.get('cwd', HOME_DIR)
    file = await context.bot.get_file(update.message.document.file_id)
    file_path = os.path.join(cwd, update.message.document.file_name)
    await file.download_to_drive(file_path)
    await update.message.reply_text(f"📥 **Saved to:** `{file_path}`")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(CommandHandler("pull", pull_file))
    app.add_handler(MessageHandler(filters.Document.ALL, push_file))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_shell))
    print("TeLinux Bot Started...")
    app.run_polling()
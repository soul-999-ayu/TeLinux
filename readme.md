# ⚡ TeLinux v2 - Hybrid Remote Control

**TeLinux v2** is a secure, Python-based automation tool that allows you to control your Linux machine remotely through a Telegram bot. 

It features a **Hybrid Architecture**:
1.  **Chat Shell:** For quick, non-blocking commands (`ls`, `whoami`, `dnf`).
2.  **Web Terminal:** A full interactive terminal inside Telegram for complex tasks (`cmatrix`, `vim`, `htop`).

---

## 🌟 Key Features

* **💻 Hybrid Terminal:** * **Standard:** Text-based output for simple commands.
    * **Interactive (New!):** Launches a secure Web App for tools that require live input.
* **🛡️ Smart Freeze Protection:** The bot detects interactive commands (like `top` or `nano`) and automatically offers to open them in the Web Terminal instead of freezing the chat.
* **🌐 Cloudflare Tunneling:** Secure, unlimited access to your terminal over the internet without port forwarding.
* **🚀 Fire-and-Forget GUI:** Launch graphical apps (`firefox`, `vscode`) on your PC screen instantly.
* **📂 Bidirectional File Transfer:** Download (`/pull`) or Upload files easily.
* **⚡ Auto-Sudo:** Privileged commands (`dnf`, `systemctl`) are automatically run with sudo.

---

## 🛠️ Requirements

* **OS:** Fedora, Ubuntu, Debian, Arch, etc.
* **Python:** 3.12+
* **Core Tools:** `python3-pip`, `ttyd`, `cloudflared`
* **Telegram:** Bot Token from [@BotFather](https://t.me/BotFather).

---

## ⚙️ Setup & Installation

### 1. Install System Dependencies

**Fedora:**
```bash
sudo dnf install python3-pip ttyd cloudflared
```
*(If cloudflared is missing: `sudo dnf config-manager --add-repo https://pkg.cloudflare.com/cloudflared-ascii.repo`)*

**Ubuntu / Debian:**
```bash
sudo apt install python3-pip ttyd
# Note: You must manually download the 'cloudflared' .deb from Cloudflare's website.
```

### 2. Install Python Libraries
```bash
pip install python-telegram-bot psutil
```

### 3. Setup the Startup Script
This script handles the complex startup of the Web Terminal, the Tunnel, and the Bot automatically.

1.  **Create the script in your Home folder:**
    ```bash
    nano ~/start_telinux.sh
    ```

2.  **Paste the following code:**
    *(⚠️ IMPORTANT: Replace `/home/youruser` with your actual home path!)*

    ```bash
    #!/bin/bash

    # --- CONFIGURATION ---
    # SET THIS TO YOUR ACTUAL USER HOME PATH
    USER_HOME="/home/youruser" 
    BOT_SCRIPT="$USER_HOME/TeLinux/tele_shell.py"

    # 1. Cleanup old processes
    killall ttyd cloudflared 2>/dev/null
    sleep 2

    # 2. Start Web Terminal (ttyd)
    cd $USER_HOME
    nohup ttyd -p 7681 -W bash > $USER_HOME/ttyd.log 2>&1 &
    sleep 5

    # 3. Start Cloudflare Tunnel (Stable Mode: IPv4 + HTTP2)
    nohup cloudflared tunnel --edge-ip-version 4 --protocol http2 --url [http://127.0.0.1:7681](http://127.0.0.1:7681) > $USER_HOME/tunnel.log 2>&1 &
    sleep 15

    # 4. Extract Dynamic URL
    grep -o 'https://.*\.trycloudflare\.com' $USER_HOME/tunnel.log | head -n 1 > $USER_HOME/current_url.txt

    # 5. Start the Bot
    python3 $BOT_SCRIPT
    ```

3.  **Make it executable:**
    ```bash
    chmod +x ~/start_telinux.sh
    ```

### 4. Setup Autostart (Systemd)
To run the bot 24/7 in the background:

1.  **Create the service file:**
    ```bash
    mkdir -p ~/.config/systemd/user
    nano ~/.config/systemd/user/pcbot.service
    ```

2.  **Paste this configuration:**
    *(⚠️ Check the `ExecStart` path matches your script location)*

    ```ini
    [Unit]
    Description=TeLinux Hybrid System
    After=network.target

    [Service]
    # UPDATE THIS PATH TO MATCH YOUR SCRIPT
    ExecStart=/home/youruser/start_telinux.sh
    Restart=always
    RestartSec=10
    Environment=PYTHONUNBUFFERED=1

    [Install]
    WantedBy=default.target
    ```

3.  **Enable and Start:**
    ```bash
    systemctl --user daemon-reload
    systemctl --user enable --now pcbot.service
    ```

### 5. Configure the Bot
Edit `tele_shell.py` to add your credentials:
```python
TOKEN = "YOUR_BOT_TOKEN_HERE"
AUTHORIZED_USER_ID = 123456789
```

---

## 📱 Bot Commands

| Command | Description |
| :--- | :--- |
| `/start` | Initialize connection and check status. |
| `/help` | View all available features. |
| `/health` | View CPU, RAM, and Disk usage stats. |
| `/pull [file]` | Download a file to your phone. |
| `cmatrix` / `top` | **New:** Opens the interactive Web Terminal. |
| `ls` / `dnf` | Standard chat-based execution. |

---

## 🛡️ Safety Architecture (v2)

TeLinux v2 uses a **Traffic Controller** logic:

1.  **Interactive Commands:** Apps like `vim`, `nano`, `adb shell` are detected and redirected to the **Web Terminal**.
2.  **Background Tasks:** Apps like `firefox` are launched in a detached session on the host display.
3.  **Standard Tasks:** Simple outputs are sent back as chat messages.

## 📝 License
This project is open-source. Feel free to fork and customize!
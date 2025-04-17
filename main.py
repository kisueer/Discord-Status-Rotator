import requests
import time
import json
import os
from colorama import init, Fore

def read_statuses(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        return [line.strip() for line in file.readlines()]

def read_ascii_art(file_name):
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "ASCII Art not found. Create 'ascii_art.txt' file."

def get_user_info(token):
    header ={
        'authorization': token
    }
    r = requests.get("https://discord.com/api/v10/users/@me", headers=header)
    if r.status_code == 200:
        user_info = r.json()
        return user_info["username"], True
    else:
        return "Invalid token", False

def change_status(token, message, emoji_name, emoji_id, status):
    header = {
        'authorization': token
    }

    current_status = requests.get("https://discord.com/api/v10/users/@me/settings", headers=header).json()

    custom_status = current_status.get("custom_status", {})
    if custom_status is None:
        custom_status = {}
    custom_status["text"] = message
    custom_status["emoji_name"] = emoji_name
    if emoji_id:  
        custom_status["emoji_id"] = emoji_id

    jsonData = {
        "custom_status": custom_status,
        "activities": current_status.get("activities", []),
        "status": status
    }

    r = requests.patch("https://discord.com/api/v10/users/@me/settings", headers=header, json=jsonData)
    return r.status_code

def clear_console():
    os.system('cls' if os.name=='nt' else 'clear')

def load_config():
    with open("config.json", "r") as file:
        return json.load(file)

def color_text(text, color_code):
    return f"{color_code}{text}{Fore.RESET}"

def display_header(ascii_art, user_info, token_masked, is_valid_token):
    clear_console()
    # Display ASCII art in gray
    gray_ascii = color_text(ascii_art, Fore.LIGHTBLACK_EX)
    print(gray_ascii)
    print("-" * 50)
    
    # Always display token and username in green regardless of validity
    token_info = f"{token_masked} | {user_info}"
    token_colored = color_text(token_info, Fore.GREEN)
    print(f"Account: {token_colored}")
    
    # Only show invalid token warning in red if needed
    if not is_valid_token:
        print(color_text("WARNING: Token appears to be invalid!", Fore.RED))
    
    print("-" * 50)

def format_log_line(status):
    # Time in purple
    time_str = time.strftime("%I:%M %p:")
    time_part = color_text(time_str, Fore.MAGENTA)
    
    # Slash in dark blue
    slash_part = color_text("/", Fore.BLUE)
    
    # Rest of message in cyan
    message_part = color_text(f" Rotating Status -> {status}", Fore.CYAN)
    
    return f"[{time_part}][{slash_part}]{message_part}"

init()  

config = load_config()
token = config["token"]
clear_enabled = config["clear_enabled"]
clear_interval = config["clear_interval"]
speed_rotator = config["speed_rotator"]
status_sequence = config["status_sequence"]

status_count = 0  
emoji_count = 0

# Read ASCII art at startup
ascii_art = read_ascii_art("ascii_art.txt")

# Get initial user info
user_info, is_valid_token = get_user_info(token)
token_masked = token[:6] + "******"

# Display initial header
display_header(ascii_art, user_info, token_masked, is_valid_token)

log_lines = []
max_log_lines = 10  # Number of status update lines to show

while True:
    current_status = status_sequence[status_count % len(status_sequence)]
    statuses = read_statuses("text.txt")
    emojis = read_statuses("emojis.txt")

    status = statuses[status_count % len(statuses)]

    emoji_data = emojis[emoji_count % len(emojis)].split(":")  
    if len(emoji_data) == 2:
        emoji_name, emoji_id = emoji_data
    elif len(emoji_data) == 1:
        emoji_name = emoji_data[0]
        emoji_id = None
    else:
        error_message = color_text(f"Invalid emoji: {emojis[emoji_count % len(emojis)]}", Fore.CYAN)
        log_lines.append(error_message)
        if len(log_lines) > max_log_lines:
            log_lines.pop(0)
        
        display_header(ascii_art, user_info, token_masked, is_valid_token)
        print("\n".join(log_lines))
        continue

    status_result = change_status(token, status, emoji_name, emoji_id, current_status)
    
    # Format log line with multi-colored elements
    log_line = format_log_line(status)
    log_lines.append(log_line)
    
    if len(log_lines) > max_log_lines:
        log_lines.pop(0)
    
    # Refresh display with ASCII art and latest status updates
    display_header(ascii_art, user_info, token_masked, is_valid_token)
    print("\n".join(log_lines))
    
    status_count += 1
    emoji_count += 1

    time.sleep(speed_rotator)
    
    # Periodically check if token is still valid
    if status_count % 10 == 0:
        user_info, is_valid_token = get_user_info(token)
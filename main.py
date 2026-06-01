"""
English Quiz Telegram Bot
A bot that conducts English language quizzes for students with progress tracking,
ranking system, and voice answer functionality.
Supports 102 levels of increasing difficulty.

New features:
- Competition leagues (like Duolingo)
- Friend system with support/hearts
- Level decay after 1 day of inactivity
- Placement test for new users
- Book mode with images from imagebook
- Vocabulary mode with 100 levels
"""

import logging
import json
import os
import asyncio
import math
import tempfile
import time
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
BOT_TOKEN = os.getenv("BOT_TOKEN")
from database import db, get_user_by_id, save_user_by_id
from questions import get_questions, get_total_levels, get_level_range
from translations import (
    get_question_translation,
    get_generated_question_translation,
    get_generated_option_translation,
    get_ui_translation,
)
from translator import translate_text, get_translation_for_word, get_random_word, TRANSLATION_DICT
from book_dialogues import get_dialogue_for_page, DEFAULT_DIALOGUE

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# File for storing user data
USERS_DATA_FILE = "users_data.json"

# League/Competition configuration (like Duolingo)
LEAGUES = [
    {"name": "Bronze League", "icon": "🥉", "top_promote": 5, "bottom_demote": 3},
    {"name": "Silver League", "icon": "🥈", "top_promote": 5, "bottom_demote": 3},
    {"name": "Gold League", "icon": "🥇", "top_promote": 5, "bottom_demote": 3},
    {"name": "Platinum League", "icon": "💎", "top_promote": 5, "bottom_demote": 3},
    {"name": "Diamond League", "icon": "💠", "top_promote": 5, "bottom_demote": 3},
    {"name": "Master League", "icon": "👑", "top_promote": 3, "bottom_demote": 2},
    {"name": "Champion League", "icon": "🏆", "top_promote": 0, "bottom_demote": 5},
]

LEAGUE_SIZE = 30  # Number of users per league
WEEKLY_RESET_DAYS = 7  # Days before league reset

# Decay configuration
DECAY_INACTIVE_DAYS = 1  # Days before level decay starts
DECAY_LEVELS_LOST = 1  # Levels lost per decay
DECAY_MAX_LEVEL = 1  # Minimum level (won't decay below this)

# Hearts/Support configuration
MAX_HEARTS = 5  # Maximum hearts a user can have
HEARTS_REGEN_TIME = 3600  # Seconds to regenerate one heart (1 hour)
SUPPORT_HEARTS_AMOUNT = 1  # Hearts given per support action

# Get total levels from questions module
TOTAL_LEVELS = get_total_levels()
LEVEL_RANGE = get_level_range()

# Ranking system configuration (like Free Fire)
RANKS = [
    {"name": "Bronze", "min_points": 0, "icon": "🥉"},
    {"name": "Silver", "min_points": 50, "icon": "🥈"},
    {"name": "Gold", "min_points": 150, "icon": "🥇"},
    {"name": "Platinum", "min_points": 300, "icon": "💎"},
    {"name": "Diamond", "min_points": 500, "icon": "💠"},
    {"name": "Master", "min_points": 800, "icon": "👑"},
    {"name": "Grand Master", "min_points": 1200, "icon": "🏆"},
    {"name": "Legend", "min_points": 2000, "icon": "⚜️"},
]

# Points awarded per correct answer
POINTS_PER_CORRECT = 2

# Voice answer configuration
VOICE_ANSWER_ENABLED = True

# Levels per page in the level selection menu
LEVELS_PER_PAGE = 10

# Placement test questions for determining user level
PLACEMENT_TEST_QUESTIONS = [
    {
        "question": "What ___ your name?",
        "options": ["is", "are", "am", "be"],
        "correct": 0,
        "level": "beginner"
    },
    {
        "question": "She ___ to school every day.",
        "options": ["go", "goes", "going", "went"],
        "correct": 1,
        "level": "beginner"
    },
    {
        "question": "They ___ football yesterday.",
        "options": ["play", "plays", "played", "playing"],
        "correct": 2,
        "level": "elementary"
    },
    {
        "question": "I have ___ finished my homework.",
        "options": ["just", "yet", "already", "since"],
        "correct": 2,
        "level": "elementary"
    },
    {
        "question": "If I ___ rich, I would travel the world.",
        "options": ["am", "was", "were", "been"],
        "correct": 2,
        "level": "pre-intermediate"
    },
]

# Level thresholds for placement test
LEVEL_THRESHOLDS = {
    "pre-intermediate": 4,  # 4-5 correct = levels 1-15 unlocked
    "elementary": 2,        # 2-3 correct = levels 1-10 unlocked
    "beginner": 0,          # 0-1 correct = levels 1-5 unlocked
}

# Maximum levels to unlock based on detected level
MAX_LEVELS_TO_UNLOCK = {
    "pre-intermediate": 15,
    "elementary": 10,
    "beginner": 5,
}

# Total book pages (based on images in imagebook folder)
TOTAL_BOOK_PAGES = 100


def load_user_data():
    """Load user data from database (with JSON fallback for migration)."""
    # Try to load from database first
    users = {}
    try:
        all_users = db.get_all_users()
        for user_entry in all_users:
            users[user_entry["user_id"]] = user_entry["data"]
    except Exception as e:
        logging.warning(f"Database load failed, trying JSON fallback: {e}")
        if os.path.exists(USERS_DATA_FILE):
            try:
                with open(USERS_DATA_FILE, "r", encoding="utf-8") as f:
                    users = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
    return users


def save_user_data(data):
    """Save user data to database (with JSON fallback)."""
    try:
        for user_id, user_data in data.items():
            db.save_user(user_id, user_data)
    except Exception as e:
        logging.error(f"Database save failed, using JSON fallback: {e}")
        with open(USERS_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def get_or_create_user(user_id: int) -> dict:
    """Get user data or create new user entry."""
    users = load_user_data()
    user_id_str = str(user_id)
    if user_id_str not in users:
        users[user_id_str] = {
            "total_points": 0,
            "total_correct": 0,
            "total_answered": 0,
            "current_level": 1,
            "highest_level": 1,
            "unlocked_levels": [1],
            "rank": "Bronze",
            "level_scores": {},  # Store best score for each level
            # New fields for competition
            "league_points": 0,  # Points for current league competition
            "league_name": "Bronze League",  # Current league
            "league_join_time": time.time(),  # When joined current league
            # New fields for decay system
            "last_active": time.time(),  # Last time user played
            "hearts": MAX_HEARTS,  # Current hearts (like Duolingo)
            "hearts_last_regen": time.time(),  # Last heart regeneration
            # New fields for friend system
            "friends": [],  # List of friend user IDs
            "pending_friend_requests": [],  # Incoming friend requests
            "sent_friend_requests": [],  # Outgoing friend requests
            # Language preference for translations
            "language": "tj",  # Default: Tajik. Options: "tj", "ru", "none"
        }
        save_user_data(users)
    else:
        # Ensure existing users have all required keys (for migration)
        user = users[user_id_str]
        defaults = {
            "total_points": 0,
            "total_correct": 0,
            "total_answered": 0,
            "current_level": 1,
            "highest_level": 1,
            "unlocked_levels": [1],
            "rank": "Bronze",
            "level_scores": {},
            "league_points": 0,
            "league_name": "Bronze League",
            "league_join_time": time.time(),
            "last_active": time.time(),
            "hearts": MAX_HEARTS,
            "hearts_last_regen": time.time(),
            "friends": [],
            "pending_friend_requests": [],
            "sent_friend_requests": [],
            "language": "tj",  # Default: Tajik
        }
        # Migrate old "level" key to "current_level" and "highest_level"
        if "level" in user and "current_level" not in user:
            user["current_level"] = user["level"]
            user["highest_level"] = user["level"]
            del user["level"]
        # Add missing keys
        for key, default_value in defaults.items():
            if key not in user:
                user[key] = default_value
        users[user_id_str] = user
        save_user_data(users)
    return users[user_id_str]


def update_user_progress(user_id: int, correct_answers: int, total_questions: int, level: int):
    """Update user progress after completing a level."""
    users = load_user_data()
    user_id_str = str(user_id)
    user = users.get(user_id_str)

    if not user:
        user = get_or_create_user(user_id)

    # Update last active time
    user["last_active"] = time.time()

    # Update total stats
    user["total_correct"] += correct_answers
    user["total_answered"] += total_questions
    user["total_points"] += correct_answers * POINTS_PER_CORRECT

    # Update league points (competition)
    user["league_points"] += correct_answers * POINTS_PER_CORRECT

    # Update best score for this level
    level_key = f"level_{level}"
    user["level_scores"][level_key] = max(
        user["level_scores"].get(level_key, 0), correct_answers
    )

    # Update current level
    user["current_level"] = max(user.get("current_level", 1), level)

    # Unlock next level if completed with good score (>= 60%)
    if correct_answers >= total_questions * 0.6:
        next_level = level + 1
        if next_level <= TOTAL_LEVELS and next_level not in user.get("unlocked_levels", []):
            user["unlocked_levels"] = user.get("unlocked_levels", [1]) + [next_level]

    # Update highest level reached
    user["highest_level"] = max(user.get("highest_level", 1), level)

    # Update rank based on total points
    user["rank"] = calculate_rank(user["total_points"])

    users[user_id_str] = user
    save_user_data(users)
    return user


def check_and_apply_decay(user_id: int) -> tuple:
    """Check if user should lose levels due to inactivity. Returns (decayed, new_level, old_level)."""
    users = load_user_data()
    user_id_str = str(user_id)
    user = users.get(user_id_str)

    if not user:
        return False, 1, 1

    last_active = user.get("last_active", time.time())
    current_level = user.get("current_level", 1)
    days_inactive = (time.time() - last_active) / 86400  # Convert seconds to days

    if days_inactive >= DECAY_INACTIVE_DAYS and current_level > DECAY_MAX_LEVEL:
        old_level = current_level
        # Lose 1 level for each full day of inactivity
        levels_to_lose = min(int(days_inactive), current_level - DECAY_MAX_LEVEL)
        new_level = max(current_level - levels_to_lose, DECAY_MAX_LEVEL)

        user["current_level"] = new_level
        user["last_active"] = time.time()  # Reset decay timer

        # Remove unlocked levels above new level
        user["unlocked_levels"] = [l for l in user.get("unlocked_levels", [1]) if l <= new_level]
        if new_level not in user["unlocked_levels"]:
            user["unlocked_levels"].append(new_level)

        users[user_id_str] = user
        save_user_data(users)
        return True, new_level, old_level

    # Update last active even if no decay
    user["last_active"] = time.time()
    users[user_id_str] = user
    save_user_data(users)
    return False, current_level, current_level


def regenerate_hearts(user_id: int) -> int:
    """Regenerate hearts based on time passed. Returns current hearts."""
    users = load_user_data()
    user_id_str = str(user_id)
    user = users.get(user_id_str)

    if not user:
        return MAX_HEARTS

    current_hearts = user.get("hearts", MAX_HEARTS)
    last_regen = user.get("hearts_last_regen", time.time())
    time_passed = time.time() - last_regen

    # Calculate hearts to regenerate
    hearts_to_add = int(time_passed / HEARTS_REGEN_TIME)
    new_hearts = min(current_hearts + hearts_to_add, MAX_HEARTS)

    if new_hearts != current_hearts:
        user["hearts"] = new_hearts
        user["hearts_last_regen"] = time.time()
        users[user_id_str] = user
        save_user_data(users)

    return new_hearts


def get_league_members(league_name: str) -> list:
    """Get all members of a specific league sorted by league points."""
    users = load_user_data()
    members = []

    for user_id_str, user in users.items():
        if user.get("league_name") == league_name:
            members.append({
                "user_id": int(user_id_str),
                "league_points": user.get("league_points", 0),
                "total_points": user.get("total_points", 0),
                "rank": user.get("rank", "Bronze"),
            })

    # Sort by league points (descending)
    members.sort(key=lambda x: x["league_points"], reverse=True)
    return members


def get_user_league_position(user_id: int) -> dict:
    """Get user's position in their current league."""
    user = get_or_create_user(user_id)
    league_name = user.get("league_name", "Bronze League")
    members = get_league_members(league_name)

    position = 0
    for i, member in enumerate(members):
        if member["user_id"] == user_id:
            position = i + 1
            break

    league_info = next((l for l in LEAGUES if l["name"] == league_name), LEAGUES[0])

    return {
        "position": position,
        "total_members": len(members),
        "league_name": league_name,
        "league_icon": league_info["icon"],
        "league_points": user.get("league_points", 0),
        "top_promote": league_info["top_promote"],
        "bottom_demote": league_info["bottom_demote"],
    }


def reset_league_weekly():
    """Reset league points weekly and promote/demote users."""
    users = load_user_data()
    current_time = time.time()

    for user_id_str, user in users.items():
        league_name = user.get("league_name", "Bronze League")
        league_info = next((l for l in LEAGUES if l["name"] == league_name), LEAGUES[0])
        join_time = user.get("league_join_time", current_time)

        # Check if week has passed
        if (current_time - join_time) >= (WEEKLY_RESET_DAYS * 86400):
            league_idx = LEAGUES.index(league_info) if league_info in LEAGUES else 0
            members = get_league_members(league_name)
            position = 0
            for i, member in enumerate(members):
                if member["user_id"] == int(user_id_str):
                    position = i + 1
                    break

            # Check for promotion
            if league_info["top_promote"] > 0 and position <= league_info["top_promote"]:
                if league_idx < len(LEAGUES) - 1:
                    user["league_name"] = LEAGUES[league_idx + 1]["name"]
            # Check for demotion
            elif league_info["bottom_demote"] > 0 and position > len(members) - league_info["bottom_demote"]:
                if league_idx > 0:
                    user["league_name"] = LEAGUES[league_idx - 1]["name"]

            # Reset league points and join time
            user["league_points"] = 0
            user["league_join_time"] = current_time

    save_user_data(users)


def calculate_rank(points: int) -> str:
    """Calculate user rank based on total points."""
    current_rank = "Bronze"
    for rank_info in RANKS:
        if points >= rank_info["min_points"]:
            current_rank = rank_info["name"]
    return current_rank


def get_rank_info(user_id: int) -> dict:
    """Get rank information for a user."""
    user = get_or_create_user(user_id)
    rank_name = user.get("rank", "Bronze")
    rank_info = next((r for r in RANKS if r["name"] == rank_name), RANKS[0])

    # Calculate progress to next rank
    next_rank = None
    progress = 100
    for r in RANKS:
        if r["min_points"] > user["total_points"]:
            next_rank = r["name"]
            next_points = r["min_points"]
            current_min = rank_info["min_points"]
            progress = int(
                ((user["total_points"] - current_min) / (next_points - current_min)) * 100
            ) if next_points > current_min else 100
            break

    return {
        "rank": rank_name,
        "icon": rank_info["icon"],
        "points": user["total_points"],
        "next_rank": next_rank,
        "progress": min(progress, 100),
    }


def get_level_difficulty(level: int) -> str:
    """Get difficulty label for a level."""
    if level == 1:
        return "🟢 Beginner"
    elif level == 2:
        return "🟡 Elementary"
    elif level <= 10:
        return "🟠 Pre-Intermediate"
    elif level <= 25:
        return "🔵 Intermediate"
    elif level <= 50:
        return "🟣 Upper-Intermediate"
    elif level <= 75:
        return "🔴 Advanced"
    else:
        return "⚫ Proficient"


# Dictionary to store user quiz state (temporary, for current session)
user_states = {}


def create_main_keyboard() -> InlineKeyboardMarkup:
    """Create main menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📚 Интихоби сатҳ", callback_data="select_level_1")
    builder.button(text="📖 Луғат", callback_data="vocabulary_mode")
    builder.button(text="📊 Пешрафти ман", callback_data="my_progress")
    builder.button(text="📕 Китоб", callback_data="book_mode")
    builder.button(text="🏆 Лига", callback_data="league_standings")
    builder.button(text="👥 Дӯстон", callback_data="friends_menu")
    builder.button(text="💎 Дилҳо", callback_data="hearts_info")
    builder.adjust(2)
    return builder.as_markup()


def create_level_page_keyboard(page: int) -> InlineKeyboardMarkup:
    """Create keyboard for level selection with pagination."""
    builder = InlineKeyboardBuilder()
    
    start_level = (page - 1) * LEVELS_PER_PAGE + 1
    end_level = min(page * LEVELS_PER_PAGE, TOTAL_LEVELS)
    
    for level in range(start_level, end_level + 1):
        builder.button(text=f"📚 Сатҳи {level}", callback_data=f"start_level_{level}")
    
    builder.adjust(2)
    
    # Add pagination buttons
    if page > 1:
        builder.button(text="⬅️ Ба қафо", callback_data=f"select_level_{page - 1}")
    if end_level < TOTAL_LEVELS:
        builder.button(text="➡️ Пеш", callback_data=f"select_level_{page + 1}")
    
    builder.button(text="🔙 Ба меню", callback_data="back_to_menu")
    builder.adjust(2)
    
    return builder.as_markup()


def create_answer_keyboard(question_index: int, user_id: int) -> InlineKeyboardMarkup:
    """Create keyboard with answer options for a question."""
    builder = InlineKeyboardBuilder()
    state = user_states.get(user_id)
    if not state:
        return builder.as_markup()
    
    questions = state["questions"]
    question = questions[question_index]

    for i, option in enumerate(question["options"]):
        builder.button(text=option, callback_data=f"answer_{i}")

    builder.adjust(2)
    return builder.as_markup()


def create_restart_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with restart option."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Аз нав сар кардан", callback_data="restart")
    builder.button(text="🔙 Ба менюи асосӣ", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


def create_continue_keyboard(next_level: int) -> InlineKeyboardMarkup:
    """Create keyboard with continue and restart options."""
    builder = InlineKeyboardBuilder()
    if next_level <= TOTAL_LEVELS:
        builder.button(
            text=f"➡️ Гузариш ба сатҳи {next_level}",
            callback_data=f"continue_level_{next_level}"
        )
    builder.button(text="🔄 Аз нав сар кардан", callback_data="restart")
    builder.button(text="🔙 Ба менюи асосӣ", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


async def send_question(user_id: int):
    """Send the next question to the user."""
    state = user_states.get(user_id)
    if not state:
        return

    current_question = state["current_question"]
    questions = state["questions"]

    if current_question >= len(questions):
        await finish_quiz(user_id)
        return

    question = questions[current_question]
    level = state["level"]
    difficulty = get_level_difficulty(level)
    
    # Get user's language preference
    user = get_or_create_user(user_id)
    user_lang = user.get("language", "tj")
    
    # Build question text
    question_text = (
        f"📝 {get_ui_translation('level', user_lang)} {level} - {difficulty} | "
        f"{get_ui_translation('question_label', user_lang)} {current_question + 1}/{len(questions)}\n\n"
        f"🇬🇧 {question['question']}"
    )
    
    # Add translation if available and user wants it
    if user_lang in ["tj", "ru"]:
        translation = get_question_translation(level, current_question, user_lang)
        if not translation:
            translation = get_generated_question_translation(question['question'], user_lang)
        
        if translation:
            lang_label = "🇹🇯" if user_lang == "tj" else "🇷🇺"
            question_text += f"\n\n{lang_label} {translation}"
    
    await bot.send_message(
        chat_id=user_id,
        text=question_text,
        reply_markup=create_answer_keyboard(current_question, user_id)
    )


async def finish_quiz(user_id: int, auto_continue: bool = False):
    """Finish the quiz and show results."""
    state = user_states.get(user_id)
    if not state:
        return

    score = state["score"]
    total = len(state["questions"])
    level = state["level"]
    difficulty = get_level_difficulty(level)

    result_text = f"🏆 Тест ба охир расид!\n\n"
    result_text += f"📊 Сатҳи {level} - {difficulty}\n"
    result_text += f"✅ Ҷавобҳои дуруст: {score}/{total}\n"
    result_text += f"🎯 Натиҷа: {int(score / total * 100)}%\n\n"

    # Calculate points earned
    points_earned = score * POINTS_PER_CORRECT
    result_text += f"⭐ Холҳои гирифташуда: +{points_earned}\n\n"

    # Get updated rank info
    rank_info = get_rank_info(user_id)
    result_text += f"{rank_info['icon']} Рутба: {rank_info['rank']}\n"
    result_text += f"📈 Ҳамагӣ холҳо: {rank_info['points']}\n\n"

    if score >= total * 0.9:
        result_text += "🎉 Аъло! Натиҷаи комил! Ин экранро ба муаллим нишон диҳед."
    elif score >= total * 0.8:
        result_text += "🌟 Олӣ! Шумо ҷавонмард!"
    elif score >= total * 0.6:
        result_text += "👍 Хуб! Ҳамин тавр давом диҳед!"
    else:
        result_text += "💪 Таслим нашавед! Дар маротибаи дигар беҳтар мешавад!"

    # Update user progress in the database
    update_user_progress(user_id, score, total, level)

    # Determine which keyboard to show
    next_level = level + 1
    user = get_or_create_user(user_id)
    
    if next_level <= TOTAL_LEVELS and next_level in user.get("unlocked_levels", []):
        keyboard = create_continue_keyboard(next_level)
    else:
        keyboard = create_restart_keyboard()

    await bot.send_message(
        chat_id=user_id,
        text=result_text,
        reply_markup=keyboard
    )

    # Clean up user state only if not continuing
    if user_id in user_states and not auto_continue:
        del user_states[user_id]


async def process_voice_answer(user_id: int, voice_file_id: str):
    """Process voice message and convert to text answer."""
    tmp_filename = None
    wav_filename = None
    
    try:
        logging.info(f"[VOICE] Starting voice processing for user {user_id}")
        
        # Download voice file
        file = await bot.get_file(voice_file_id)
        logging.info(f"[VOICE] Got file info: {file.file_id}, path: {file.file_path}")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_file:
            tmp_filename = tmp_file.name
        
        logging.info(f"[VOICE] Downloading voice file to: {tmp_filename}")
        await bot.download_file(file.file_path, tmp_filename)
        logging.info(f"[VOICE] File downloaded successfully, size: {os.path.getsize(tmp_filename)} bytes")

        # Try to convert OGG to WAV for speech recognition
        try:
            logging.info("[VOICE] Attempting to convert OGG to WAV using pydub...")
            from pydub import AudioSegment
            try:
                audio = AudioSegment.from_ogg(tmp_filename)
                wav_filename = tmp_filename.replace(".ogg", ".wav")
                audio.export(wav_filename, format="wav")
                logging.info(f"[VOICE] Conversion successful, WAV file: {wav_filename}")
            except Exception as conv_error:
                logging.error(f"[VOICE] pydub conversion error: {conv_error}")
                wav_filename = tmp_filename  # Use original file
        except ImportError:
            logging.warning("[VOICE] pydub not installed, using original file")
            wav_filename = tmp_filename

        # Recognize speech
        recognized_text = None
        try:
            logging.info("[VOICE] Starting speech recognition...")
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            
            try:
                with sr.AudioFile(wav_filename) as source:
                    logging.info(f"[VOICE] Reading audio file: {wav_filename}")
                    audio_data = recognizer.record(source)
                    logging.info(f"[VOICE] Audio data recorded")
                    
                    try:
                        # Try to recognize using Google's free API
                        text = recognizer.recognize_google(audio_data, language="en-US")
                        recognized_text = text.lower().strip()
                        logging.info(f"[VOICE] Recognition successful: '{recognized_text}'")
                    except sr.UnknownValueError:
                        logging.warning("[VOICE] Could not understand audio")
                    except sr.RequestError as e:
                        logging.error(f"[VOICE] Speech recognition service error: {e}")
            except Exception as audio_error:
                logging.error(f"[VOICE] Audio file processing error: {audio_error}")
        except ImportError:
            logging.error("[VOICE] SpeechRecognition library not installed")
        finally:
            # Clean up temporary files
            try:
                if tmp_filename and os.path.exists(tmp_filename):
                    os.unlink(tmp_filename)
                if wav_filename and wav_filename != tmp_filename and os.path.exists(wav_filename):
                    os.unlink(wav_filename)
            except OSError:
                pass

        if recognized_text:
            await handle_voice_recognized_answer(user_id, recognized_text)
        else:
            await bot.send_message(
                chat_id=user_id,
                text="❌ Не удалось распознать голос. Попробуйте снова или выберите ответ кнопкой."
            )

    except Exception as e:
        logging.error(f"[VOICE] Unexpected error: {e}")
        await bot.send_message(
            chat_id=user_id,
            text="❌ Ошибка обработки голосового сообщения. Попробуйте снова или выберите ответ кнопкой."
        )


async def handle_voice_recognized_answer(user_id: int, recognized_text: str):
    """Handle the recognized text from voice message."""
    state = user_states.get(user_id)
    if not state:
        await bot.send_message(chat_id=user_id, text="Пожалуйста, начните тест командой /start")
        return

    current_question = state["current_question"]
    questions = state["questions"]

    if current_question >= len(questions):
        await finish_quiz(user_id)
        return

    question = questions[current_question]
    correct_answer = question["correct"]
    correct_text = question["options"][correct_answer].lower().strip()

    # Check if recognized text matches any option
    matched_index = None
    for i, option in enumerate(question["options"]):
        if recognized_text in option.lower().strip() or option.lower().strip() in recognized_text:
            matched_index = i
            break

    if matched_index is not None:
        # Simulate button click with the matched answer
        is_correct = matched_index == correct_answer
        if is_correct:
            state["score"] += 1

        result_emoji = "✅" if is_correct else "❌"
        result_text = f"🎤 Распознано: '{recognized_text}'\n"
        result_text += f"{result_emoji} Ваш ответ: {question['options'][matched_index]}\n"
        if not is_correct:
            result_text += f"Правильный ответ: {question['options'][correct_answer]}\n"

        state["current_question"] += 1

        await bot.send_message(
            chat_id=user_id,
            text=f"📝 Question {current_question + 1}/{len(questions)}\n\n{question['question']}\n\n{result_text}"
        )

        await asyncio.sleep(1.5)

        if state["current_question"] >= len(questions):
            await finish_quiz(user_id)
        else:
            await send_question(user_id)
    else:
        await bot.send_message(
            chat_id=user_id,
            text=f"❌ Не удалось сопоставить ваш ответ '{recognized_text}' с вариантами.\n\n"
                 f"Варианты: {', '.join(question['options'])}\n\n"
                 "Попробуйте снова или нажмите кнопку."
        )


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Handle /start command."""
    user_id = message.from_user.id
    user = get_or_create_user(user_id)
    
    # Check if this is a new user (no levels completed yet)
    is_new_user = (
        user.get("total_answered", 0) == 0 and 
        len(user.get("unlocked_levels", [1])) <= 1
    )
    
    if is_new_user:
        # Start placement test for new users
        await start_placement_test(user_id, message)
    else:
        # Show main menu for existing users
        rank_info = get_rank_info(user_id)
    welcome_text = (
        f"🇬🇧 **Хуш омадед ба боти омӯзиши забони англисӣ!** 🇬🇧\n\n"
        f"Дониши забони англисии худро санҷед!\n"
        f"📚 **{TOTAL_LEVELS} сатҳ** дастрас аст - аз навомӯз то касбӣ!\n\n"
        f"{rank_info['icon']} Рутбаи шумо: **{rank_info['rank']}**\n"
        f"⭐ Ҳамагӣ холҳо: **{rank_info['points']}**\n"
        f"📊 Сатҳҳои гузашта: **{user.get('highest_level', 1)}**\n\n"
        f"Амалро интихоб кунед:"
    )
    await message.answer(
        text=welcome_text,
        reply_markup=create_main_keyboard(),
        parse_mode="Markdown"
    )


async def start_placement_test(user_id: int, message: types.Message):
    """Start placement test for new users."""
    # Store placement test state
    user_states["placement_test"] = user_states.get("placement_test", {})
    user_states["placement_test"][user_id] = {
        "current_question": 0,
        "score": 0,
    }
    
    # Send first question
    await send_placement_question(user_id)


async def send_placement_question(user_id: int):
    """Send the next placement test question."""
    placement_state = user_states.get("placement_test", {}).get(user_id)
    if not placement_state:
        return
    
    current_question = placement_state["current_question"]
    
    if current_question >= len(PLACEMENT_TEST_QUESTIONS):
        await finish_placement_test(user_id)
        return
    
    question = PLACEMENT_TEST_QUESTIONS[current_question]
    
    question_text = (
        f"📝 **Определение уровня**\n\n"
        f"Вопрос {current_question + 1}/{len(PLACEMENT_TEST_QUESTIONS)}\n\n"
        f"🇬🇧 {question['question']}\n\n"
        f"Выберите правильный ответ:"
    )
    
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(question["options"]):
        builder.button(text=option, callback_data=f"placement_answer_{i}")
    builder.adjust(2)
    
    await bot.send_message(
        chat_id=user_id,
        text=question_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


async def finish_placement_test(user_id: int):
    """Finish placement test and unlock levels based on score."""
    placement_state = user_states.get("placement_test", {}).get(user_id)
    if not placement_state:
        return
    
    score = placement_state["score"]
    total = len(PLACEMENT_TEST_QUESTIONS)
    
    # Determine level based on score
    detected_level = "beginner"
    for level_name, threshold in LEVEL_THRESHOLDS.items():
        if score >= threshold:
            detected_level = level_name
            break
    
    max_unlock = MAX_LEVELS_TO_UNLOCK[detected_level]
    
    # Unlock levels for the user
    users = load_user_data()
    user_id_str = str(user_id)
    if user_id_str in users:
        # Create list of unlocked levels
        unlocked = list(range(1, min(max_unlock, TOTAL_LEVELS) + 1))
        users[user_id_str]["unlocked_levels"] = unlocked
        users[user_id_str]["highest_level"] = max_unlock
        users[user_id_str]["last_active"] = time.time()
        save_user_data(users)
    
    # Determine level name in user's language
    level_names = {
        "pre-intermediate": "🟠 Pre-Intermediate",
        "elementary": "🟡 Elementary",
        "beginner": "🟢 Beginner"
    }
    level_name = level_names.get(detected_level, detected_level)
    
    result_text = (
        f"🎉 **Тест завершён!**\n\n"
        f"✅ Правильных ответов: {score}/{total}\n\n"
        f"🏆 **Ваш уровень: {level_name}**\n\n"
        f"🔓 **Открыто уровней: 1-{max_unlock}**\n\n"
        f"Теперь вы можете проходить уровни до {max_unlock}!\n"
        f"Проходите уровни, чтобы открывать следующие!"
    )
    
    # Clean up placement test state
    if user_id in user_states.get("placement_test", {}):
        del user_states["placement_test"][user_id]
    
    # Show main menu
    rank_info = get_rank_info(user_id)
    welcome_text = (
        f"{result_text}\n\n"
        f"{rank_info['icon']} Ваше звание: **{rank_info['rank']}**\n"
        f"⭐ Всего очков: **{rank_info['points']}**\n\n"
        f"Выберите действие:"
    )
    
    await bot.send_message(
        chat_id=user_id,
        text=welcome_text,
        reply_markup=create_main_keyboard(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("placement_answer_"))
async def process_placement_answer(callback: types.CallbackQuery):
    """Handle placement test answer."""
    user_id = callback.from_user.id
    placement_state = user_states.get("placement_test", {}).get(user_id)
    
    if not placement_state:
        await callback.answer("Пожалуйста, начните с /start", show_alert=True)
        return
    
    current_question = placement_state["current_question"]
    selected_answer = int(callback.data.split("_")[-1])
    correct_answer = PLACEMENT_TEST_QUESTIONS[current_question]["correct"]
    
    # Check if correct
    is_correct = selected_answer == correct_answer
    if is_correct:
        placement_state["score"] += 1
    
    # Show result
    result_emoji = "✅" if is_correct else "❌"
    correct_text = PLACEMENT_TEST_QUESTIONS[current_question]["options"][correct_answer]
    
    result_text = (
        f"{result_emoji} Ваш ответ: {PLACEMENT_TEST_QUESTIONS[current_question]['options'][selected_answer]}\n"
    )
    if not is_correct:
        result_text += f"Правильный ответ: {correct_text}\n"
    
    placement_state["current_question"] += 1
    
    await callback.message.edit_text(
        text=f"📝 Вопрос {current_question + 1}/{len(PLACEMENT_TEST_QUESTIONS)}\n\n"
             f"🇬🇧 {PLACEMENT_TEST_QUESTIONS[current_question]['question']}\n\n"
             f"{result_text}",
        reply_markup=None
    )
    
    await asyncio.sleep(1.5)
    
    # Send next question or finish
    if placement_state["current_question"] >= len(PLACEMENT_TEST_QUESTIONS):
        await finish_placement_test(user_id)
    else:
        await send_placement_question(user_id)
    
    await callback.answer()


@dp.callback_query(F.data == "back_to_menu")
async def process_back_to_menu(callback: types.CallbackQuery):
    """Handle back to menu button."""
    user_id = callback.from_user.id

    # Clean up any existing state
    if user_id in user_states:
        del user_states[user_id]

    user = get_or_create_user(user_id)
    rank_info = get_rank_info(user_id)

    welcome_text = (
        f"🇬🇧 **Бот для изучения английского** 🇬🇧\n\n"
        f"📚 Доступно **{TOTAL_LEVELS} уровней**\n\n"
        f"{rank_info['icon']} Звание: **{rank_info['rank']}** | "
        f"⭐ Очков: **{rank_info['points']}**\n\n"
        f"Выберите действие:"
    )

    await callback.message.edit_text(
        text=welcome_text,
        reply_markup=create_main_keyboard(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("select_level_"))
async def process_select_level(callback: types.CallbackQuery):
    """Handle level selection with pagination."""
    page = int(callback.data.split("_")[-1])
    total_pages = math.ceil(TOTAL_LEVELS / LEVELS_PER_PAGE)
    
    start_level = (page - 1) * LEVELS_PER_PAGE + 1
    end_level = min(page * LEVELS_PER_PAGE, TOTAL_LEVELS)
    
    user_id = callback.from_user.id
    user = get_or_create_user(user_id)
    unlocked = user.get("unlocked_levels", [1])
    
    level_text = ""
    for level in range(start_level, end_level + 1):
        difficulty = get_level_difficulty(level)
        status = "🔓" if level in unlocked else "🔒"
        best = user.get("level_scores", {}).get(f"level_{level}", 0)
        if best > 0:
            questions = get_questions(level)
            pct = int(best / len(questions) * 100) if questions else 0
            level_text += f"{status} **Level {level}** - {difficulty} (Best: {best}/{len(questions)} = {pct}%)\n"
        else:
            level_text += f"{status} **Level {level}** - {difficulty}\n"
    
    text = (
        f"📚 **Выберите уровень** (Страница {page}/{total_pages})\n\n"
        f"{level_text}\n"
        f"🔒 Пройдите уровень с результатом 60%+, чтобы открыть следующий!"
    )
    
    await callback.message.edit_text(
        text=text,
        reply_markup=create_level_page_keyboard(page),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("start_level_"))
async def process_start_level(callback: types.CallbackQuery):
    """Handle starting a specific level."""
    level = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    # Check if level is unlocked
    user = get_or_create_user(user_id)
    if level not in user.get("unlocked_levels", [1]):
        await callback.answer(
            f"❌ Уровень {level} заблокирован! Пройдите предыдущие уровни, чтобы открыть.",
            show_alert=True
        )
        return

    questions = get_questions(level)
    if not questions:
        await callback.answer("❌ Вопросы для этого уровня недоступны.", show_alert=True)
        return

    # Initialize user state with voice mode always enabled
    user_states[user_id] = {
        "level": level,
        "score": 0,
        "current_question": 0,
        "questions": questions,
        "voice_mode": True,
    }

    difficulty = get_level_difficulty(level)
    
    # Create keyboard
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Начать тест", callback_data=f"begin_level_{level}")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text=f"📚 **Уровень {level} - {difficulty}**\n\n"
             f"📝 {len(questions)} вопросов\n\n"
             f"Выберите действие:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("begin_level_"))
async def process_begin_level(callback: types.CallbackQuery):
    """Handle beginning a level test."""
    level = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    # Check if level is unlocked
    user = get_or_create_user(user_id)
    if level not in user.get("unlocked_levels", [1]):
        await callback.answer(
            f"❌ Уровень {level} заблокирован! Пройдите предыдущие уровни, чтобы открыть.",
            show_alert=True
        )
        return

    questions = get_questions(level)
    if not questions:
        await callback.answer("❌ Вопросы для этого уровня недоступны.", show_alert=True)
        return

    # Initialize user state with voice mode always enabled
    user_states[user_id] = {
        "level": level,
        "score": 0,
        "current_question": 0,
        "questions": questions,
        "voice_mode": True,
    }

    difficulty = get_level_difficulty(level)
    await callback.message.edit_text(
        text=f"📚 **Уровень {level} - {difficulty}**\n\n"
             f"📝 {len(questions)} вопросов\n\n"
             f"Начнём! Отвечайте на вопросы:"
    )

    await send_question(user_id)


@dp.callback_query(F.data == "my_progress")
async def process_my_progress(callback: types.CallbackQuery):
    """Handle My Progress button."""
    user_id = callback.from_user.id
    user = get_or_create_user(user_id)
    rank_info = get_rank_info(user_id)

    # Calculate accuracy
    total_answered = user.get("total_answered", 0)
    total_correct = user.get("total_correct", 0)
    accuracy = int((total_correct / total_answered) * 100) if total_answered > 0 else 0

    # Get unlocked levels count
    unlocked_count = len(user.get("unlocked_levels", [1]))

    # Calculate completion percentage
    completion = int((unlocked_count / TOTAL_LEVELS) * 100)

    # Get best scores summary
    level_scores = user.get("level_scores", {})
    completed_levels = len(level_scores)

    progress_text = (
        f"📊 **Пешрафти шумо**\n\n"
        f"{rank_info['icon']} **Рутба: {rank_info['rank']}**\n"
        f"⭐ **Ҳамагӣ холҳо: {rank_info['points']}**\n\n"
        f"📈 **Омор:**\n"
        f"✅ Ҷавобҳои дуруст: {total_correct}\n"
        f"📝 Ҳамагӣ ҷавоб дода шуд: {total_answered}\n"
        f"🎯 Дақиқӣ: {accuracy}%\n\n"
        f"📚 **Сатҳҳо:**\n"
        f"🔓 Кушода шуд: {unlocked_count}/{TOTAL_LEVELS} ({completion}%)\n"
        f"🏆 Гузашта шуд: {completed_levels} сатҳ\n"
        f"📊 Сатҳи максималӣ: {user.get('highest_level', 1)}\n\n"
    )

    if rank_info["next_rank"]:
        progress_text += f"🎯 Рутбаи навбатӣ: **{rank_info['next_rank']}** (пешрафт {rank_info['progress']}%)"

    await callback.message.answer(
        text=progress_text,
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "rankings")
async def process_rankings(callback: types.CallbackQuery):
    """Handle Rankings button."""
    user_id = callback.from_user.id
    user = get_or_create_user(user_id)
    rank_info = get_rank_info(user_id)

    rankings_text = (
        f"🏆 **Системаи рутбаҳо**\n\n"
        f"Рутбаи ҳозираи шумо: {rank_info['icon']} **{rank_info['rank']}**\n\n"
        f"**Талабот ба рутбаҳо:**\n"
    )

    for r in RANKS:
        icon = r["icon"]
        name = r["name"]
        points = r["min_points"]
        current = "👈 **ШУМО**" if name == rank_info["rank"] else ""
        rankings_text += f"{icon} **{name}**: {points}+ хол {current}\n"

    rankings_text += "\n💡 Холҳоро бо ҷавобҳои дуруст ба саволҳо ба даст оред!\n"
    rankings_text += f"Ҳар як ҷавоби дуруст = {POINTS_PER_CORRECT} хол"

    await callback.message.answer(
        text=rankings_text,
        parse_mode="Markdown"
    )


# ============== LEAGUE & COMPETITION HANDLERS ==============

@dp.callback_query(F.data == "league_standings")
async def process_league_standings(callback: types.CallbackQuery):
    """Handle League Standings button."""
    user_id = callback.from_user.id
    user = get_or_create_user(user_id)

    # Check for decay first
    decayed, new_level, old_level = check_and_apply_decay(user_id)

    league_info = get_user_league_position(user_id)
    members = get_league_members(league_info["league_name"])

    # Build league standings text
    standings_text = (
        f"{league_info['league_icon']} **{league_info['league_name']}**\n\n"
        f"📊 **Мавқеи шумо: #{league_info['position']}/{league_info['total_members']}**\n"
        f"⭐ Холҳо дар лига: **{league_info['league_points']}**\n\n"
    )

    # Show top 10 members
    standings_text += "**🏅 Иштирокчиёни беҳтарин:**\n"
    for i, member in enumerate(members[:10]):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        is_current_user = "👈 **ШУМО**" if member["user_id"] == user_id else ""
        standings_text += f"{medal} Корбари #{member['user_id']}: {member['league_points']} хол {is_current_user}\n"

    # Promotion/Demotion info
    if league_info["top_promote"] > 0:
        standings_text += f"\n📈 Топ-{league_info['top_promote']} **БОЛО РАФТАНД**!\n"
    if league_info["bottom_demote"] > 0:
        standings_text += f"📉 Охирин {league_info['bottom_demote']} **ПАСТ РАФТАНД**!\n"

    # Show decay warning if applicable
    if decayed:
        standings_text += f"\n⚠️ **Сатҳ гум шуд!** Шумо аз {old_level} ба {new_level} сатҳ афтодед!"

    # Hearts display
    current_hearts = regenerate_hearts(user_id)
    hearts_display = "❤️" * current_hearts + "🖤" * (MAX_HEARTS - current_hearts)
    standings_text += f"\n\n{hearts_display} Дилҳо: {current_hearts}/{MAX_HEARTS}"

    # Keyboard for league actions
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Ба меню", callback_data="back_to_menu")
    builder.adjust(1)

    await callback.message.answer(
        text=standings_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


# ============== FRIEND SYSTEM HANDLERS ==============

@dp.callback_query(F.data == "friends_menu")
async def process_friends_menu(callback: types.CallbackQuery):
    """Handle Friends menu."""
    user_id = callback.from_user.id
    user = get_or_create_user(user_id)

    friends = user.get("friends", [])
    pending_requests = user.get("pending_friend_requests", [])
    sent_requests = user.get("sent_friend_requests", [])

    friends_text = (
        f"👥 **Друзья**\n\n"
        f"📋 **Ваши друзья ({len(friends)}):**\n"
    )

    if friends:
        for friend_id in friends[:10]:
            friend_user = get_or_create_user(friend_id)
            friend_league = friend_user.get("league_name", "Неизвестно")
            friend_level = friend_user.get("current_level", 1)
            friends_text += f"• Пользователь #{friend_id} - Уровень {friend_level} ({friend_league})\n"
    else:
        friends_text += "_Пока нет друзей. Добавьте друзей, чтобы соревноваться и поддерживать друг друга!_\n"

    if pending_requests:
        friends_text += f"\n📨 **Входящие заявки ({len(pending_requests)}):**\n"
        for req_id in pending_requests[:5]:
            friends_text += f"• Пользователь #{req_id}\n"

    if sent_requests:
        friends_text += f"\n⏳ **Исходящие заявки ({len(sent_requests)}):**\n"
        for req_id in sent_requests[:5]:
            friends_text += f"• Пользователь #{req_id}\n"

    # Keyboard for friend actions
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить друга", callback_data="add_friend")
    if pending_requests:
        builder.button(text="✅ Принять заявку", callback_data=f"accept_friend_{pending_requests[0]}")
    if friends:
        builder.button(text="💝 Поддержать друга", callback_data="support_friend")
    builder.button(text="🔙 В меню", callback_data="back_to_menu")
    builder.adjust(2)

    await callback.message.answer(
        text=friends_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "add_friend")
async def process_add_friend(callback: types.CallbackQuery):
    """Handle add friend command."""
    await callback.message.answer(
        text="➕ **Добавить друга**\n\n"
        "Чтобы добавить друга, используйте команду:\n"
        "`/addfriend <user_id>`\n\n"
        "Вы можете узнать свой ID командой `/myid`.\n\n"
        "Пример: `/addfriend 123456789`",
        parse_mode="Markdown"
    )


@dp.message(Command("myid"))
async def cmd_myid(message: types.Message):
    """Handle /myid command - show user's ID."""
    await message.answer(
        f"📋 **Ваш User ID:** `{message.from_user.id}`\n\n"
        "Поделитесь этим ID с друзьями, чтобы они могли вас добавить!",
        parse_mode="Markdown"
    )


@dp.message(Command("addfriend"))
async def cmd_add_friend(message: types.Message):
    """Handle /addfriend command."""
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        await message.answer("❌ Пожалуйста, укажите ID пользователя. Использование: `/addfriend <user_id>`", parse_mode="Markdown")
        return

    try:
        friend_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный ID. Пожалуйста, введите числовой ID.")
        return

    if friend_id == user_id:
        await message.answer("❌ Вы не можете добавить себя в друзья!")
        return

    # Get or create both users
    user = get_or_create_user(user_id)
    friend_user = get_or_create_user(friend_id)

    # Check if already friends
    if friend_id in user.get("friends", []):
        await message.answer("❌ Этот пользователь уже ваш друг!")
        return

    # Check if request already sent
    if friend_id in user.get("sent_friend_requests", []):
        await message.answer("❌ Заявка в друзья уже отправлена этому пользователю.")
        return

    # Check if already pending from them
    if user_id in friend_user.get("pending_friend_requests", []):
        await message.answer("❌ У этого пользователя уже есть ожидающая заявка от вас.")
        return

    # Send friend request
    friend_user["pending_friend_requests"].append(user_id)
    user["sent_friend_requests"].append(friend_id)
    save_user_data({str(user_id): user, str(friend_id): friend_user})

    await message.answer(
        f"✅ Заявка в друзья отправлена пользователю #{friend_id}!\n\n"
        f"Они могут принять её командой: `/acceptfriend {user_id}`"
    )


@dp.message(Command("acceptfriend"))
async def cmd_accept_friend(message: types.Message):
    """Handle /acceptfriend command."""
    user_id = message.from_user.id
    args = message.text.split()

    if len(args) < 2:
        await message.answer("❌ Пожалуйста, укажите ID пользователя. Использование: `/acceptfriend <user_id>`", parse_mode="Markdown")
        return

    try:
        requester_id = int(args[1])
    except ValueError:
        await message.answer("❌ Неверный ID. Пожалуйста, введите числовой ID.")
        return

    # Get both users
    user = get_or_create_user(user_id)
    requester = get_or_create_user(requester_id)

    # Check if request exists
    if requester_id not in user.get("pending_friend_requests", []):
        await message.answer("❌ Нет ожидающей заявки от этого пользователя.")
        return

    # Add to friends list
    user["friends"].append(requester_id)
    requester["friends"].append(user_id)

    # Remove from pending/sent
    if requester_id in user.get("pending_friend_requests", []):
        user["pending_friend_requests"].remove(requester_id)
    if user_id in requester.get("sent_friend_requests", []):
        requester["sent_friend_requests"].remove(user_id)

    save_user_data({str(user_id): user, str(requester_id): requester})

    await message.answer(
        f"🎉 Теперь вы друзья с пользователем #{requester_id}!\n\n"
        f"Вы можете поддерживать друг друга и соревноваться в лигах!"
    )


@dp.callback_query(F.data == "support_friend")
async def process_support_friend(callback: types.CallbackQuery):
    """Handle support friend action - give hearts to a friend."""
    user_id = callback.from_user.id
    user = get_or_create_user(user_id)

    friends = user.get("friends", [])
    if not friends:
        await callback.message.answer("❌ У вас пока нет друзей. Сначала добавьте друзей!")
        return

    current_hearts = regenerate_hearts(user_id)
    if current_hearts <= 1:
        await callback.message.answer(
            f"❌ Нужно минимум 2 сердца, чтобы поддержать друга. У вас {current_hearts} сердечек."
        )
        return

    # Build friend selection keyboard
    builder = InlineKeyboardBuilder()
    for friend_id in friends[:10]:
        friend_user = get_or_create_user(friend_id)
        friend_hearts = regenerate_hearts(friend_id)
        if friend_hearts < MAX_HEARTS:
            builder.button(
                text=f"💝 Пользователь #{friend_id} ({friend_hearts}/{MAX_HEARTS} ❤️)",
                callback_data=f"give_hearts_{friend_id}"
            )

    builder.button(text="🔙 Назад", callback_data="friends_menu")
    builder.adjust(1)

    await callback.message.answer(
        text=f"💝 **Поддержать друга**\n\nВыберите друга, чтобы отправить {SUPPORT_HEARTS_AMOUNT} сердце.\nУ вас {current_hearts} сердечек.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("give_hearts_"))
async def process_give_hearts(callback: types.CallbackQuery):
    """Handle giving hearts to a friend."""
    user_id = callback.from_user.id
    friend_id = int(callback.data.split("_")[-1])

    users = load_user_data()
    user_id_str = str(user_id)
    friend_id_str = str(friend_id)

    user = users.get(user_id_str)
    friend_user = users.get(friend_id_str)

    if not user or not friend_user:
        await callback.answer("❌ Пользователь не найден.", show_alert=True)
        return

    # Check if still friends
    if friend_id not in user.get("friends", []):
        await callback.answer("❌ Этот пользователь больше не ваш друг.", show_alert=True)
        return

    current_hearts = regenerate_hearts(user_id)
    if current_hearts <= 1:
        await callback.answer("❌ Недостаточно сердец для поддержки.", show_alert=True)
        return

    friend_hearts = regenerate_hearts(friend_id)
    if friend_hearts >= MAX_HEARTS:
        await callback.answer("❌ У вашего друга уже максимум сердец!", show_alert=True)
        return

    # Transfer hearts
    user["hearts"] = max(current_hearts - SUPPORT_HEARTS_AMOUNT, 0)
    friend_user["hearts"] = min(friend_hearts + SUPPORT_HEARTS_AMOUNT, MAX_HEARTS)
    friend_user["hearts_last_regen"] = time.time()

    users[user_id_str] = user
    users[friend_id_str] = friend_user
    save_user_data(users)

    await callback.answer(
        f"💝 Вы отправили {SUPPORT_HEARTS_AMOUNT} сердце пользователю #{friend_id}!",
        show_alert=True
    )


@dp.callback_query(F.data.startswith("accept_friend_"))
async def process_accept_friend_callback(callback: types.CallbackQuery):
    """Handle accepting friend request via callback."""
    user_id = callback.from_user.id
    requester_id = int(callback.data.split("_")[-1])

    users = load_user_data()
    user_id_str = str(user_id)
    requester_id_str = str(requester_id)

    user = users.get(user_id_str)
    requester = users.get(requester_id_str)

    if not user or not requester:
        await callback.answer("❌ Пользователь не найден.", show_alert=True)
        return

    # Check if request exists
    if requester_id not in user.get("pending_friend_requests", []):
        await callback.answer("❌ Нет ожидающей заявки.", show_alert=True)
        return

    # Add to friends list
    user["friends"].append(requester_id)
    requester["friends"].append(user_id)

    # Remove from pending/sent
    if requester_id in user.get("pending_friend_requests", []):
        user["pending_friend_requests"].remove(requester_id)
    if user_id in requester.get("sent_friend_requests", []):
        requester["sent_friend_requests"].remove(user_id)

    users[user_id_str] = user
    users[requester_id_str] = requester
    save_user_data(users)

    await callback.answer(
        f"🎉 Теперь вы друзья с пользователем #{requester_id}!",
        show_alert=True
    )


# ============== HEARTS SYSTEM HANDLERS ==============

@dp.callback_query(F.data == "hearts_info")
async def process_hearts_info(callback: types.CallbackQuery):
    """Handle Hearts info button."""
    user_id = callback.from_user.id
    user = get_or_create_user(user_id)

    current_hearts = regenerate_hearts(user_id)
    hearts_display = "❤️" * current_hearts + "🖤" * (MAX_HEARTS - current_hearts)

    # Calculate time until next heart
    last_regen = user.get("hearts_last_regen", time.time())
    time_passed = time.time() - last_regen
    time_until_next = HEARTS_REGEN_TIME - (time_passed % HEARTS_REGEN_TIME)
    minutes = int(time_until_next / 60)

    # Check decay status
    decayed, new_level, old_level = check_and_apply_decay(user_id)

    hearts_text = (
        f"💎 **Система сердец**\n\n"
        f"{hearts_display}\n"
        f"**Сердца: {current_hearts}/{MAX_HEARTS}**\n\n"
        f"⏱️ Следующее сердце через: ~{minutes} мин.\n\n"
        f"**Как работают сердца:**\n"
        f"• Сердца восстанавливаются со временем (1 сердце в час)\n"
        f"• Сердца нужны для прохождения уровней\n"
        f"• Друзья могут отправлять вам сердца\n\n"
        f"**⚠️ Предупреждение о потере уровня:**\n"
        f"Если не играть 1 день, ваш уровень уменьшится!\n"
        f"Текущий уровень: {user.get('current_level', 1)}\n"
    )

    if decayed:
        hearts_text += f"\n📉 **УРОВЕНЬ ПОТЕРЯН!** Вы упали с {old_level} на {new_level}!"

    builder = InlineKeyboardBuilder()
    if user.get("friends", []):
        builder.button(text="💝 Отправить сердце другу", callback_data="support_friend")
    builder.button(text="🔙 В меню", callback_data="back_to_menu")
    builder.adjust(1)

    await callback.message.answer(
        text=hearts_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


# ============== DECAY CHECK ON START ==============

@dp.message(Command("decay"))
async def cmd_decay_info(message: types.Message):
    """Handle /decay command - show decay status."""
    user_id = message.from_user.id
    user = get_or_create_user(user_id)

    last_active = user.get("last_active", time.time())
    days_inactive = (time.time() - last_active) / 86400
    current_level = user.get("current_level", 1)

    if days_inactive >= DECAY_INACTIVE_DAYS and current_level > DECAY_MAX_LEVEL:
        levels_to_lose = min(int(days_inactive), current_level - DECAY_MAX_LEVEL)
        status_text = (
            f"⚠️ **ПРЕДУПРЕЖДЕНИЕ О ПОТЕРЕ УРОВНЯ!**\n\n"
            f"Вы неактивны **{days_inactive:.1f} дней**.\n"
            f"Вы потеряете **{levels_to_lose} уровень(я)** при следующем запуске!\n"
            f"Текущий уровень: {current_level}\n"
            f"После потери: {current_level - levels_to_lose}\n\n"
            f"Пройдите тест сейчас, чтобы сбросить таймер!"
        )
    else:
        status_text = (
            f"✅ **Нет риска потери уровня**\n\n"
            f"Последняя активность: {days_inactive:.1f} дней назад\n"
            f"Текущий уровень: {current_level}\n\n"
            f"Продолжайте играть, чтобы сохранить уровень!"
        )

    await message.answer(status_text, parse_mode="Markdown")


@dp.callback_query(F.data.startswith("answer_"))
async def process_answer(callback: types.CallbackQuery):
    """Handle answer selection."""
    user_id = callback.from_user.id

    state = user_states.get(user_id)
    if not state:
        await callback.answer("Пожалуйста, начните тест командой /start", show_alert=True)
        return

    current_question = state["current_question"]
    questions = state["questions"]

    if current_question >= len(questions):
        await finish_quiz(user_id)
        return

    question = questions[current_question]
    selected_answer = int(callback.data.split("_")[1])
    correct_answer = question["correct"]

    # Check if answer is correct
    is_correct = selected_answer == correct_answer
    if is_correct:
        state["score"] += 1

    # Show result for current question
    result_emoji = "✅" if is_correct else "❌"
    result_text = f"{result_emoji} Ваш ответ: {question['options'][selected_answer]}\n"
    if not is_correct:
        result_text += f"Правильный ответ: {question['options'][correct_answer]}\n"

    # Move to next question
    state["current_question"] += 1

    user = get_or_create_user(user_id)
    user_lang = user.get("language", "tj")
    
    question_label = get_ui_translation("question_label", user_lang)
    
    await callback.message.edit_text(
        text=f"📝 {question_label} {current_question + 1}/{len(questions)}\n\n{question['question']}\n\n{result_text}",
        reply_markup=None
    )

    # Send next question after a short delay
    await asyncio.sleep(1.5)

    # Check if there are more questions
    if state["current_question"] >= len(questions):
        await finish_quiz(user_id)
    else:
        await send_question(user_id)


@dp.callback_query(F.data.startswith("continue_level_"))
async def process_continue_level(callback: types.CallbackQuery):
    """Handle continue to next level button."""
    user_id = callback.from_user.id
    next_level = int(callback.data.split("_")[-1])

    questions = get_questions(next_level)
    if not questions:
        await callback.answer("Questions not available for this level.", show_alert=True)
        return

    # Initialize user state for next level with voice mode always enabled
    user_states[user_id] = {
        "level": next_level,
        "score": 0,
        "current_question": 0,
        "questions": questions,
        "voice_mode": True,
    }

    difficulty = get_level_difficulty(next_level)
    await callback.message.edit_text(
        text=f"📚 **Продолжаем: Уровень {next_level} - {difficulty}!**\n\n"
             f"Продолжим! Отвечайте на вопросы:"
    )

    await send_question(user_id)


@dp.callback_query(F.data == "restart")
async def process_restart(callback: types.CallbackQuery):
    """Handle restart button."""
    user_id = callback.from_user.id

    # Clean up any existing state
    if user_id in user_states:
        del user_states[user_id]

    user = get_or_create_user(user_id)
    rank_info = get_rank_info(user_id)

    welcome_text = (
        f"🇬🇧 **Добро пожаловать в бот для изучения английского!** 🇬🇧\n\n"
        f"📚 Доступно **{TOTAL_LEVELS} уровней**\n\n"
        f"{rank_info['icon']} Звание: **{rank_info['rank']}** | "
        f"⭐ Очков: **{rank_info['points']}**\n\n"
        f"Проверьте свои знания английской грамматики и лексики!\n\n"
        f"Выберите действие:"
    )

    await callback.message.edit_text(
        text=welcome_text,
        reply_markup=create_main_keyboard(),
        parse_mode="Markdown"
    )


@dp.message(Command("language"))
async def cmd_language(message: types.Message):
    """Handle /language command - show language selection."""
    user_id = message.from_user.id
    user = get_or_create_user(user_id)
    current_lang = user.get("language", "tj")
    
    lang_names = {
        "tj": "🇹🇯 Тоҷикӣ",
        "ru": "🇷🇺 Русский",
        "none": "🇬🇧 English only"
    }
    
    current_name = lang_names.get(current_lang, current_lang)
    
    text = (
        f"🌐 **Забонро интихоб кунед / Выберите язык / Select language**\n\n"
        f"Забони ҳозира / Текущий язык: **{current_name}**\n\n"
        f"Тарҷумаи саволҳои англисиро ба забони тоҷикӣ ё русӣ фаъол кунед.\n"
        f"Включите перевод английских вопросов на таджикский или русский язык.\n\n"
        f"Забонҳоро интихоб кунед:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🇹🇯 Тоҷикӣ", callback_data="lang_tj")
    builder.button(text="🇷🇺 Русский", callback_data="lang_ru")
    builder.button(text="🇬🇧 English only", callback_data="lang_none")
    builder.adjust(1)
    
    await message.answer(
        text=text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("lang_"))
async def process_language_change(callback: types.CallbackQuery):
    """Handle language selection."""
    user_id = callback.from_user.id
    new_lang = callback.data.split("_", 1)[1]
    
    # Update user language
    users = load_user_data()
    user_id_str = str(user_id)
    if user_id_str in users:
        users[user_id_str]["language"] = new_lang
        save_user_data(users)
    
    lang_names = {
        "tj": "🇹🇯 Тоҷикӣ",
        "ru": "🇷🇺 Русский",
        "none": "🇬🇧 English only"
    }
    
    new_name = lang_names.get(new_lang, new_lang)
    
    await callback.answer(
        f"✅ Забон иваз шуд! / Язык изменён! / Language changed!\n\n"
        f"Шумо забони {new_name}-ро интихоб кардед.\n"
        f"Вы выбрали {new_name}.\n"
        f"You selected {new_name}.",
        show_alert=True
    )


@dp.message(Command("translate"))
async def cmd_translate(message: types.Message):
    """Handle /translate command - translate English text to Tajik/Russian."""
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "📝 **Тарҷума / Перевод / Translate**\n\n"
            "Истифодабарӣ / Использование:\n"
            "`/translate <матн>` - тарҷума ба забони шумо\n"
            "`/translate tj <матн>` - тарҷума ба тоҷикӣ\n"
            "`/translate ru <матн>` - тарҷума ба русӣ\n\n"
            "Пример:\n"
            "`/translate hello world`\n"
            "`/translate tj thank you`\n"
            "`/translate ru good morning`",
            parse_mode="Markdown"
        )
        return
    
    user = get_or_create_user(message.from_user.id)
    user_lang = user.get("language", "tj")
    
    # Check if first argument is a language code
    text_to_translate = args[1]
    target_lang = user_lang
    
    if args[1].lower() in ["tj", "ru"]:
        target_lang = args[1].lower()
        if len(args) > 2:
            text_to_translate = " ".join(args[2:])
        else:
            await message.answer("❌ Матнро ворид кунед / Введите текст / Enter text")
            return
    
    # Translate the text
    translation = translate_text(text_to_translate, target_lang)
    
    if translation:
        lang_label = "🇹🇯" if target_lang == "tj" else "🇷🇺"
        lang_name = "тоҷикӣ" if target_lang == "tj" else "русский"
        
        await message.answer(
            f"📝 **Тарҷума / Перевод**\n\n"
            f"🇬🇧 {text_to_translate}\n\n"
            f"{lang_label} {translation}",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            f"❌ Тарҷума ёфт нашуд / Перевод не найден / Translation not found\n\n"
            f"Матн: {text_to_translate}\n\n"
            "Кӯшиш кунед калимаҳои дигар истифода баред.\n"
            "Попробуйте использовать другие слова.\n"
            "Try using different words."
        )


@dp.message(F.voice)
async def handle_voice_message(message: types.Message):
    """Handle voice messages for voice answer mode. Voice mode is always active during quiz."""
    user_id = message.from_user.id
    state = user_states.get(user_id)

    # Check if user is in a quiz (voice mode is always enabled)
    if not state:
        await message.answer(
            "🎤 Отправьте голосовое сообщение во время теста, чтобы ответить на вопрос."
        )
        return

    voice_file_id = message.voice.file_id
    await process_voice_answer(user_id, voice_file_id)


# ============== VOCABULARY MODE HANDLERS ==============

# Vocabulary words organized by levels (100 levels, 10 words each)
# Each level has a list of English words
VOCABULARY_LEVELS = {}

# Level 1-10: Basic words (pronouns, common verbs, numbers)
VOCABULARY_LEVELS[1] = ["i", "you", "he", "she", "we", "they", "am", "is", "are", "be"]
VOCABULARY_LEVELS[2] = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]
VOCABULARY_LEVELS[3] = ["have", "has", "had", "do", "does", "did", "will", "can", "could", "may"]
VOCABULARY_LEVELS[4] = ["my", "your", "his", "her", "our", "their", "its", "me", "him", "us"]
VOCABULARY_LEVELS[5] = ["go", "come", "get", "make", "take", "see", "know", "think", "say", "tell"]
VOCABULARY_LEVELS[6] = ["man", "woman", "child", "boy", "girl", "father", "mother", "friend", "people", "family"]
VOCABULARY_LEVELS[7] = ["day", "night", "morning", "evening", "week", "month", "year", "time", "hour", "today"]
VOCABULARY_LEVELS[8] = ["house", "room", "home", "door", "window", "table", "chair", "bed", "kitchen", "bathroom"]
VOCABULARY_LEVELS[9] = ["water", "food", "bread", "milk", "coffee", "tea", "apple", "sugar", "salt", "fire"]
VOCABULARY_LEVELS[10] = ["sun", "moon", "star", "sky", "earth", "tree", "flower", "grass", "mountain", "river"]

# Level 11-20: Common adjectives and adverbs
VOCABULARY_LEVELS[11] = ["good", "bad", "big", "small", "hot", "cold", "new", "old", "young", "happy"]
VOCABULARY_LEVELS[12] = ["fast", "slow", "long", "short", "high", "low", "full", "empty", "clean", "dirty"]
VOCABULARY_LEVELS[13] = ["beautiful", "ugly", "strong", "weak", "rich", "poor", "easy", "hard", "right", "wrong"]
VOCABULARY_LEVELS[14] = ["always", "never", "often", "sometimes", "usually", "here", "there", "now", "then", "today"]
VOCABULARY_LEVELS[15] = ["very", "really", "quite", "too", "also", "just", "only", "well", "much", "more"]
VOCABULARY_LEVELS[16] = ["important", "possible", "impossible", "sure", "free", "busy", "ready", "late", "early", "safe"]
VOCABULARY_LEVELS[17] = ["different", "same", "true", "false", "whole", "clear", "dark", "light", "soft", "hard"]
VOCABULARY_LEVELS[18] = ["open", "close", "start", "finish", "begin", "end", "leave", "stay", "keep", "hold"]
VOCABULARY_LEVELS[19] = ["sweet", "sour", "bitter", "salty", "fresh", "stale", "smooth", "rough", "sharp", "dull"]
VOCABULARY_LEVELS[20] = ["wet", "dry", "warm", "cool", "deep", "shallow", "thick", "thin", "wide", "narrow"]

# Level 21-30: Places and locations
VOCABULARY_LEVELS[21] = ["city", "town", "village", "country", "street", "road", "bridge", "park", "school", "hospital"]
VOCABULARY_LEVELS[22] = ["shop", "market", "bank", "library", "cinema", "theater", "museum", "station", "airport", "hotel"]
VOCABULARY_LEVELS[23] = ["office", "factory", "farm", "garden", "field", "forest", "desert", "island", "beach", "lake"]
VOCABULARY_LEVELS[24] = ["sea", "ocean", "river", "mountain", "valley", "hill", "cliff", "cave", "volcano", "glacier"]
VOCABULARY_LEVELS[25] = ["world", "continent", "state", "region", "area", "place", "space", "ground", "floor", "ceiling"]
VOCABULARY_LEVELS[26] = ["wall", "corner", "center", "side", "top", "bottom", "front", "back", "left", "right"]
VOCABULARY_LEVELS[27] = ["north", "south", "east", "west", "above", "below", "inside", "outside", "near", "far"]
VOCABULARY_LEVELS[28] = ["classroom", "laboratory", "gymnasium", "stadium", "playground", "swimming pool", "restaurant", "cafe", "bar", "club"]
VOCABULARY_LEVELS[29] = ["church", "temple", "mosque", "palace", "castle", "tower", "building", "apartment", "garage", "warehouse"]
VOCABULARY_LEVELS[30] = ["university", "college", "institute", "academy", "department", "company", "organization", "government", "parliament", "court"]

# Level 31-40: Animals and nature
VOCABULARY_LEVELS[31] = ["dog", "cat", "horse", "cow", "sheep", "pig", "chicken", "duck", "goat", "rabbit"]
VOCABULARY_LEVELS[32] = ["lion", "tiger", "elephant", "bear", "wolf", "fox", "deer", "monkey", "snake", "bird"]
VOCABULARY_LEVELS[33] = ["fish", "whale", "shark", "dolphin", "octopus", "crab", "lobster", "shrimp", "frog", "turtle"]
VOCABULARY_LEVELS[34] = ["butterfly", "bee", "ant", "spider", "fly", "mosquito", "worm", "snail", "ladybug", "dragonfly"]
VOCABULARY_LEVELS[35] = ["rose", "tulip", "daisy", "sunflower", "orchid", "lily", "cactus", "fern", "moss", "bamboo"]
VOCABULARY_LEVELS[36] = ["oak", "pine", "maple", "willow", "palm", "olive", "cherry", "lemon", "orange", "banana"]
VOCABULARY_LEVELS[37] = ["rain", "snow", "wind", "storm", "cloud", "fog", "thunder", "lightning", "hail", "frost"]
VOCABULARY_LEVELS[38] = ["spring", "summer", "autumn", "winter", "season", "weather", "climate", "temperature", "humidity", "pressure"]
VOCABULARY_LEVELS[39] = ["metal", "wood", "stone", "glass", "plastic", "rubber", "cloth", "leather", "paper", "cardboard"]
VOCABULARY_LEVELS[40] = ["gold", "silver", "copper", "iron", "steel", "aluminum", "diamond", "crystal", "marble", "granite"]

# Level 41-50: Body parts and health
VOCABULARY_LEVELS[41] = ["head", "face", "eye", "ear", "nose", "mouth", "tooth", "tongue", "lip", "chin"]
VOCABULARY_LEVELS[42] = ["neck", "shoulder", "arm", "elbow", "wrist", "hand", "finger", "thumb", "nail", "fist"]
VOCABULARY_LEVELS[43] = ["chest", "back", "stomach", "waist", "hip", "leg", "knee", "ankle", "foot", "toe"]
VOCABULARY_LEVELS[44] = ["heart", "brain", "lung", "liver", "kidney", "muscle", "bone", "skin", "blood", "nerve"]
VOCABULARY_LEVELS[45] = ["health", "disease", "illness", "pain", "fever", "cold", "cough", "headache", "injury", "wound"]
VOCABULARY_LEVELS[46] = ["medicine", "drug", "pill", "tablet", "injection", "surgery", "treatment", "therapy", "diagnosis", "prescription"]
VOCABULARY_LEVELS[47] = ["doctor", "nurse", "surgeon", "dentist", "pharmacist", "therapist", "patient", "clinic", "ambulance", "emergency"]
VOCABULARY_LEVELS[48] = ["exercise", "fitness", "yoga", "meditation", "relaxation", "massage", "diet", "vitamin", "supplement", "nutrition"]
VOCABULARY_LEVELS[49] = ["happy", "sad", "angry", "afraid", "surprised", "disgusted", "excited", "nervous", "calm", "bored"]
VOCABULARY_LEVELS[50] = ["love", "hate", "hope", "fear", "joy", "sorrow", "pride", "shame", "guilt", "envy"]

# Level 51-60: Clothing and fashion
VOCABULARY_LEVELS[51] = ["shirt", "pants", "dress", "skirt", "jacket", "coat", "sweater", "blouse", "suit", "uniform"]
VOCABULARY_LEVELS[52] = ["shoe", "boot", "sandal", "slipper", "sock", "stocking", "glove", "mittens", "scarf", "hat"]
VOCABULARY_LEVELS[53] = ["belt", "tie", "button", "zipper", "pocket", "sleeve", "collar", "hem", "seam", "fabric"]
VOCABULARY_LEVELS[54] = ["fashion", "style", "trend", "design", "pattern", "color", "size", "fit", "brand", "model"]
VOCABULARY_LEVELS[55] = ["jewelry", "ring", "necklace", "bracelet", "earring", "watch", "glasses", "sunglasses", "crown", "medal"]
VOCABULARY_LEVELS[56] = ["makeup", "perfume", "shampoo", "soap", "towel", "comb", "brush", "razor", "mirror", "cosmetics"]
VOCABULARY_LEVELS[57] = ["laundry", "wash", "dry", "iron", "fold", "hang", "store", "wear", "remove", "change"]
VOCABULARY_LEVELS[58] = ["cotton", "wool", "silk", "linen", "polyester", "nylon", "denim", "velvet", "fur", "lace"]
VOCABULARY_LEVELS[59] = ["tailor", "seamstress", "designer", "model", "mannequin", "fitting room", "wardrobe", "closet", "drawer", "hanger"]
VOCABULARY_LEVELS[60] = ["casual", "formal", "elegant", "stylish", "trendy", "classic", "vintage", "modern", "traditional", "ethnic"]

# Level 61-70: Technology and communication
VOCABULARY_LEVELS[61] = ["computer", "laptop", "tablet", "phone", "smartphone", "keyboard", "mouse", "screen", "monitor", "printer"]
VOCABULARY_LEVELS[62] = ["internet", "website", "email", "message", "chat", "video", "audio", "file", "folder", "document"]
VOCABULARY_LEVELS[63] = ["software", "hardware", "program", "application", "system", "network", "server", "database", "code", "algorithm"]
VOCABULARY_LEVELS[64] = ["robot", "machine", "device", "tool", "equipment", "instrument", "gadget", "appliance", "mechanism", "engine"]
VOCABULARY_LEVELS[65] = ["electricity", "battery", "cable", "wire", "circuit", "chip", "processor", "memory", "storage", "backup"]
VOCABULARY_LEVELS[66] = ["download", "upload", "install", "update", "delete", "copy", "paste", "save", "print", "scan"]
VOCABULARY_LEVELS[67] = ["social media", "blog", "forum", "comment", "like", "share", "follow", "subscribe", "notification", "alert"]
VOCABULARY_LEVELS[68] = ["artificial intelligence", "machine learning", "data science", "cybersecurity", "blockchain", "cryptocurrency", "virtual reality", "augmented reality", "cloud computing", "big data"]
VOCABULARY_LEVELS[69] = ["satellite", "antenna", "signal", "frequency", "bandwidth", "modem", "router", "bluetooth", "wifi", "gps"]
VOCABULARY_LEVELS[70] = ["innovation", "invention", "discovery", "research", "experiment", "hypothesis", "theory", "analysis", "conclusion", "evidence"]

# Level 71-80: Work and business
VOCABULARY_LEVELS[71] = ["job", "work", "career", "profession", "occupation", "employment", "salary", "wage", "income", "bonus"]
VOCABULARY_LEVELS[72] = ["manager", "director", "supervisor", "employee", "colleague", "assistant", "secretary", "intern", "consultant", "contractor"]
VOCABULARY_LEVELS[73] = ["meeting", "conference", "presentation", "interview", "negotiation", "discussion", "agreement", "contract", "proposal", "report"]
VOCABULARY_LEVELS[74] = ["project", "task", "deadline", "schedule", "plan", "strategy", "goal", "objective", "target", "milestone"]
VOCABULARY_LEVELS[75] = ["marketing", "advertising", "sales", "customer", "client", "consumer", "product", "service", "brand", "market"]
VOCABULARY_LEVELS[76] = ["finance", "accounting", "budget", "investment", "profit", "loss", "revenue", "expense", "tax", "audit"]
VOCABULARY_LEVELS[77] = ["economy", "trade", "import", "export", "supply", "demand", "competition", "monopoly", "inflation", "recession"]
VOCABULARY_LEVELS[78] = ["law", "legal", "court", "judge", "lawyer", "jury", "trial", "verdict", "sentence", "appeal"]
VOCABULARY_LEVELS[79] = ["politics", "government", "democracy", "election", "vote", "president", "minister", "senator", "mayor", "policy"]
VOCABULARY_LEVELS[80] = ["education", "teaching", "learning", "training", "course", "lesson", "exam", "grade", "diploma", "degree"]

# Level 81-90: Travel and transportation
VOCABULARY_LEVELS[81] = ["travel", "trip", "journey", "voyage", "tour", "excursion", "expedition", "adventure", "vacation", "holiday"]
VOCABULARY_LEVELS[82] = ["car", "bus", "train", "plane", "boat", "bicycle", "motorcycle", "taxi", "subway", "tram"]
VOCABULARY_LEVELS[83] = ["ticket", "passport", "visa", "luggage", "suitcase", "backpack", "map", "guide", "reservation", "booking"]
VOCABULARY_LEVELS[84] = ["airport", "station", "port", "terminal", "gate", "platform", "runway", "hangar", "dock", "pier"]
VOCABULARY_LEVELS[85] = ["drive", "ride", "fly", "sail", "walk", "hike", "cycle", "commute", "transfer", "navigate"]
VOCABULARY_LEVELS[86] = ["tourist", "tourism", "attraction", "sightseeing", "landmark", "monument", "museum", "gallery", "theater", "stadium"]
VOCABULARY_LEVELS[87] = ["hotel", "motel", "hostel", "resort", "camping", "cabin", "apartment", "villa", "cruise", "yacht"]
VOCABULARY_LEVELS[88] = ["customs", "immigration", "border", "checkpoint", "security", "screening", "declaration", "duty", "quarantine", "inspection"]
VOCABULARY_LEVELS[89] = ["traffic", "accident", "jam", "delay", "detour", "route", "direction", "distance", "speed", "fuel"]
VOCABULARY_LEVELS[90] = ["adventure", "exploration", "discovery", "experience", "memory", "souvenir", "postcard", "photo", "video", "diary"]

# Level 91-100: Advanced and abstract concepts
VOCABULARY_LEVELS[91] = ["philosophy", "ethics", "morality", "justice", "freedom", "equality", "rights", "responsibility", "duty", "virtue"]
VOCABULARY_LEVELS[92] = ["science", "physics", "chemistry", "biology", "mathematics", "geometry", "algebra", "calculus", "statistics", "probability"]
VOCABULARY_LEVELS[93] = ["art", "painting", "sculpture", "drawing", "photography", "music", "dance", "theater", "cinema", "literature"]
VOCABULARY_LEVELS[94] = ["religion", "faith", "belief", "worship", "prayer", "ritual", "ceremony", "tradition", "culture", "heritage"]
VOCABULARY_LEVELS[95] = ["environment", "ecology", "pollution", "conservation", "sustainability", "renewable", "recycling", "organic", "natural", "ecosystem"]
VOCABULARY_LEVELS[96] = ["psychology", "behavior", "personality", "intelligence", "consciousness", "emotion", "motivation", "perception", "cognition", "memory"]
VOCABULARY_LEVELS[97] = ["society", "community", "civilization", "population", "generation", "class", "group", "individual", "collective", "institution"]
VOCABULARY_LEVELS[98] = ["technology", "engineering", "architecture", "construction", "manufacturing", "automation", "robotics", "nanotechnology", "biotechnology", "aerospace"]
VOCABULARY_LEVELS[99] = ["globalization", "international", "multicultural", "diversity", "integration", "cooperation", "diplomacy", "alliance", "partnership", "collaboration"]
VOCABULARY_LEVELS[100] = ["future", "progress", "evolution", "transformation", "revolution", "innovation", "breakthrough", "advancement", "development", "achievement"]

# Total vocabulary levels
TOTAL_VOCAB_LEVELS = 100


@dp.callback_query(F.data == "vocabulary_mode")
async def process_vocabulary_mode(callback: types.CallbackQuery):
    """Handle Vocabulary mode button."""
    user_id = callback.from_user.id
    user = get_or_create_user(user_id)
    user_lang = user.get("language", "tj")
    
    vocab_text = (
        f"📖 **Режим словаря**\n\n"
        f"Практикуйте перевод английских слов!\n\n"
        f"**Как это работает:**\n"
        f"• Бот показывает английское слово\n"
        f"• Вы переводите его на таджикский/русский\n"
        f"• Бот проверяет ваш перевод\n\n"
        f"**Доступно 100 уровней сложности!**\n\n"
        f"**Выберите режим:**"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Тест: Выбор уровня", callback_data="vocab_select_level_1")
    builder.button(text="📖 Учить слова", callback_data="vocab_learn_mode")
    builder.button(text="🔙 В меню", callback_data="back_to_menu")
    builder.adjust(1)
    
    await callback.message.answer(
        text=vocab_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("vocab_select_level_"))
async def process_vocab_select_level(callback: types.CallbackQuery):
    """Handle vocabulary level selection with pagination."""
    page = int(callback.data.split("_")[-1])
    total_pages = math.ceil(TOTAL_VOCAB_LEVELS / LEVELS_PER_PAGE)
    
    start_level = (page - 1) * LEVELS_PER_PAGE + 1
    end_level = min(page * LEVELS_PER_PAGE, TOTAL_VOCAB_LEVELS)
    
    user_id = callback.from_user.id
    user = get_or_create_user(user_id)
    
    level_text = ""
    for level in range(start_level, end_level + 1):
        difficulty = get_level_difficulty(level)
        word_count = len(VOCABULARY_LEVELS.get(level, []))
        level_text += f"📚 **Уровень {level}** - {difficulty} ({word_count} слов)\n"
    
    text = (
        f"📖 **Выберите уровень словаря** (Страница {page}/{total_pages})\n\n"
        f"{level_text}\n"
        f"Каждый уровень содержит слова определенной тематики!"
    )
    
    builder = InlineKeyboardBuilder()
    for level in range(start_level, end_level + 1):
        builder.button(text=f"📖 Уровень {level}", callback_data=f"vocab_start_level_{level}")
    builder.adjust(2)
    
    if page > 1:
        builder.button(text="⬅️ Назад", callback_data=f"vocab_select_level_{page - 1}")
    if end_level < TOTAL_VOCAB_LEVELS:
        builder.button(text="➡️ Вперёд", callback_data=f"vocab_select_level_{page + 1}")
    builder.button(text="🔙 В меню", callback_data="back_to_menu")
    builder.adjust(2)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("vocab_start_level_"))
async def process_vocab_start_level(callback: types.CallbackQuery):
    """Start vocabulary test for a specific level."""
    level = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    user = get_or_create_user(user_id)
    user_lang = user.get("language", "tj")
    
    # Get words for this level
    words = VOCABULARY_LEVELS.get(level, [])
    if not words:
        await callback.answer("❌ Слова для этого уровня не найдены.", show_alert=True)
        return
    
    # Store vocabulary state
    if "vocab_state" not in user_states:
        user_states["vocab_state"] = {}
    
    user_states["vocab_state"][user_id] = {
        "level": level,
        "words": words,
        "current_word_index": 0,
        "score": 0,
        "target_lang": user_lang,
    }
    
    difficulty = get_level_difficulty(level)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Начать тест", callback_data=f"vocab_begin_level_{level}")
    builder.button(text="🔙 Назад", callback_data="vocabulary_mode")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text=f"📖 **Уровень {level} - {difficulty}**\n\n"
             f"📝 {len(words)} слов для перевода\n\n"
             f"Выберите действие:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("vocab_begin_level_"))
async def process_vocab_begin_level(callback: types.CallbackQuery):
    """Begin vocabulary test for a level."""
    level = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    user = get_or_create_user(user_id)
    user_lang = user.get("language", "tj")
    
    words = VOCABULARY_LEVELS.get(level, [])
    if not words:
        await callback.answer("❌ Слова для этого уровня не найдены.", show_alert=True)
        return
    
    # Store vocabulary state
    if "vocab_state" not in user_states:
        user_states["vocab_state"] = {}
    
    user_states["vocab_state"][user_id] = {
        "level": level,
        "words": words,
        "current_word_index": 0,
        "score": 0,
        "target_lang": user_lang,
    }
    
    await send_vocab_question(user_id)


async def send_vocab_question(user_id: int):
    """Send the next vocabulary question."""
    vocab_state = user_states.get("vocab_state", {}).get(user_id)
    if not vocab_state:
        return
    
    current_index = vocab_state["current_word_index"]
    words = vocab_state["words"]
    
    if current_index >= len(words):
        await finish_vocab_quiz(user_id)
        return
    
    english_word = words[current_index]
    level = vocab_state["level"]
    target_lang = vocab_state["target_lang"]
    
    lang_label = "🇹🇯" if target_lang == "tj" else "🇷🇺"
    lang_name = "тоҷикӣ" if target_lang == "tj" else "русский"
    
    question_text = (
        f"📖 **Уровень {level}** | Слово {current_index + 1}/{len(words)}\n\n"
        f"🇬🇧 **{english_word}**\n\n"
        f"Переведите это слово на {lang_name}.\n"
        f"Напишите перевод в сообщении.\n\n"
        f"Чтобы пропустить, напишите: /skip"
    )
    
    await bot.send_message(
        chat_id=user_id,
        text=question_text,
        parse_mode="Markdown"
    )


async def finish_vocab_quiz(user_id: int):
    """Finish vocabulary quiz and show results."""
    vocab_state = user_states.get("vocab_state", {}).get(user_id)
    if not vocab_state:
        return
    
    score = vocab_state["score"]
    total = len(vocab_state["words"])
    level = vocab_state["level"]
    difficulty = get_level_difficulty(level)
    
    result_text = (
        f"🏆 **Тест на словарь завершён!**\n\n"
        f"📊 Уровень {level} - {difficulty}\n"
        f"✅ Правильных переводов: {score}/{total}\n"
        f"🎯 Результат: {int(score / total * 100)}%\n\n"
    )
    
    # Add points
    points_earned = score
    users = load_user_data()
    user_id_str = str(user_id)
    if user_id_str in users:
        users[user_id_str]["total_points"] += points_earned
        users[user_id_str]["total_correct"] += score
        users[user_id_str]["total_answered"] += total
        users[user_id_str]["last_active"] = time.time()
        save_user_data(users)
    
    if score >= total * 0.9:
        result_text += "🎉 Отлично! Идеальный результат!"
    elif score >= total * 0.7:
        result_text += "🌟 Великолепно! Вы молодец!"
    elif score >= total * 0.5:
        result_text += "👍 Хорошо! Продолжайте в том же духе!"
    else:
        result_text += "💪 Не сдавайтесь! В следующий раз получится лучше!"
    
    # Clear vocab state
    if user_id in user_states.get("vocab_state", {}):
        del user_states["vocab_state"][user_id]
    
    builder = InlineKeyboardBuilder()
    next_level = level + 1
    if next_level <= TOTAL_VOCAB_LEVELS:
        builder.button(text=f"➡️ Следующий уровень ({next_level})", callback_data=f"vocab_start_level_{next_level}")
    builder.button(text="🔙 В меню словаря", callback_data="vocabulary_mode")
    builder.button(text="🔙 В главное меню", callback_data="back_to_menu")
    builder.adjust(1)
    
    await bot.send_message(
        chat_id=user_id,
        text=result_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


async def handle_vocab_answer(message: types.Message):
    """Handle user's translation answer in vocabulary test mode."""
    user_id = message.from_user.id
    
    # Check if user is in vocabulary test mode
    if "vocab_state" not in user_states or user_id not in user_states["vocab_state"]:
        return  # Not in vocab test mode
    
    vocab_state = user_states["vocab_state"][user_id]
    user_answer = message.text.strip().lower()
    current_index = vocab_state["current_word_index"]
    words = vocab_state["words"]
    target_lang = vocab_state["target_lang"]
    
    if current_index >= len(words):
        await finish_vocab_quiz(user_id)
        return
    
    english_word = words[current_index]
    english_word_lower = english_word.lower().strip()
    
    # Check for skip command
    if user_answer == "/skip":
        await message.answer(f"⏭️ Пропущено. Слово: {english_word}")
        vocab_state["current_word_index"] += 1
        await send_vocab_question(user_id)
        return
    
    # Get correct translation
    if english_word_lower in TRANSLATION_DICT:
        correct_translation = TRANSLATION_DICT[english_word_lower].get(target_lang, english_word)
    else:
        correct_translation = "translation not available"
    
    # Check if answer is correct
    is_correct = (
        user_answer == correct_translation.lower() or
        correct_translation.lower() in user_answer or
        user_answer in correct_translation.lower()
    )
    
    if is_correct:
        result_text = (
            f"✅ **Правильно!**\n\n"
            f"🇬🇧 {english_word}\n"
            f"📝 Ваш ответ: {message.text.strip()}\n"
            f"💡 Перевод: {correct_translation}"
        )
        vocab_state["score"] += 1
    else:
        result_text = (
            f"❌ **Неправильно**\n\n"
            f"🇬🇧 {english_word}\n"
            f"📝 Ваш ответ: {message.text.strip()}\n"
            f"✅ Правильный ответ: {correct_translation}"
        )
    
    vocab_state["current_word_index"] += 1
    
    await message.answer(
        text=result_text,
        parse_mode="Markdown"
    )
    
    await asyncio.sleep(1.5)
    
    if vocab_state["current_word_index"] >= len(words):
        await finish_vocab_quiz(user_id)
    else:
        await send_vocab_question(user_id)


@dp.message(F.text)
async def handle_text_messages(message: types.Message):
    """Handle all text messages - check for various modes."""
    user_id = message.from_user.id
    
    # Check if user is in book dialogue mode (Mini Dialogue)
    if "book_dialogue_state" in user_states and user_id in user_states["book_dialogue_state"]:
        await handle_book_dialogue_answer(message)
        return
    
    # Check if user is in book practice mode (Quick Practice)
    if "book_practice_state" in user_states and user_id in user_states["book_practice_state"]:
        await handle_book_practice_answer(message)
        return
    
    # Check if user is in vocabulary test mode
    if "vocab_state" in user_states and user_id in user_states["vocab_state"]:
        await handle_vocab_answer(message)
        return
    
    # No active mode - ignore the message


@dp.callback_query(F.data == "vocab_learn_mode")
async def process_vocab_learn_mode(callback: types.CallbackQuery):
    """Start vocabulary learning mode with levels."""
    user_id = callback.from_user.id
    user = get_or_create_user(user_id)
    user_lang = user.get("language", "tj")
    
    learn_text = (
        f"📖 **Режим обучения**\n\n"
        f"Выберите уровень для изучения слов:"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Выбрать уровень", callback_data="vocab_select_level_1")
    builder.button(text="🔙 В меню словаря", callback_data="vocabulary_mode")
    builder.adjust(1)
    
    await callback.message.edit_text(
        text=learn_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


# ============== BOOK MODE HANDLERS ==============


@dp.callback_query(F.data == "book_mode")
async def process_book_mode(callback: types.CallbackQuery):
    """Handle Book mode button."""
    user_id = callback.from_user.id
    
    book_text = (
        f"📕 **Книга**\n\n"
        f"Добро пожаловать в нашу библиотеку!\n\n"
        f"📖 **Доступно страниц:** {TOTAL_BOOK_PAGES}\n\n"
        f"Здесь вы можете читать учебные материалы и упражнения.\n"
        f"Каждая страница содержит изображение с учебным материалом.\n\n"
        f"**Выберите действие:**"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📖 Выбрать страницу", callback_data="book_select_page_1")
    builder.button(text="🔙 В меню", callback_data="back_to_menu")
    builder.adjust(1)
    
    await callback.message.answer(
        text=book_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("book_select_page_"))
async def process_book_select_page(callback: types.CallbackQuery):
    """Handle book page selection with pagination."""
    page = int(callback.data.split("_")[-1])
    total_pages = math.ceil(TOTAL_BOOK_PAGES / LEVELS_PER_PAGE)
    
    start_page = (page - 1) * LEVELS_PER_PAGE + 1
    end_page = min(page * LEVELS_PER_PAGE, TOTAL_BOOK_PAGES)
    
    page_text = ""
    for p in range(start_page, end_page + 1):
        # Check if page image exists
        image_path = f"imagebook/page_{p}.png"
        if not os.path.exists(image_path):
            image_path = f"imagebook/page_{p}.jpg"
        
        status = "📄" if os.path.exists(image_path) else "⬜"
        page_text += f"{status} **Страница {p}**\n"
    
    text = (
        f"📕 **Выберите страницу книги** (Страница {page}/{total_pages})\n\n"
        f"{page_text}\n"
        f"📄 - страница доступна, ⬜ - страница не добавлена"
    )
    
    builder = InlineKeyboardBuilder()
    for p in range(start_page, end_page + 1):
        builder.button(text=f"📄 Стр. {p}", callback_data=f"book_view_page_{p}")
    builder.adjust(2)
    
    if page > 1:
        builder.button(text="⬅️ Назад", callback_data=f"book_select_page_{page - 1}")
    if end_page < TOTAL_BOOK_PAGES:
        builder.button(text="➡️ Вперёд", callback_data=f"book_select_page_{page + 1}")
    builder.button(text="🔙 В меню книги", callback_data="book_mode")
    builder.adjust(2)
    
    await callback.message.edit_text(
        text=text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("book_view_page_"))
async def process_book_view_page(callback: types.CallbackQuery):
    """Handle viewing a specific book page."""
    page = int(callback.data.split("_")[-1])
    
    # Find page image
    image_path = f"imagebook/page_{page}.png"
    if not os.path.exists(image_path):
        image_path = f"imagebook/page_{page}.jpg"
    
    if not os.path.exists(image_path):
        await callback.answer(
            f"❌ Страница {page} ещё не добавлена.\n"
            f"Добавьте файл page_{page}.jpg или page_{page}.png в папку imagebook.",
            show_alert=True
        )
        return
    
    try:
        photo = FSInputFile(image_path)
        
        builder = InlineKeyboardBuilder()
        if page > 1:
            builder.button(text="⬅️ Предыдущая", callback_data=f"book_view_page_{page - 1}")
        if page < TOTAL_BOOK_PAGES:
            builder.button(text="Следующая ➡️", callback_data=f"book_view_page_{page + 1}")
        builder.button(text="💬 Mini Dialogue", callback_data=f"book_mini_dialogue_{page}")
        builder.button(text="⚡ Quick Practice", callback_data=f"book_quick_practice_{page}")
        builder.button(text="🔙 K списку страниц", callback_data="book_select_page_1")
        builder.adjust(2)
        
        await callback.message.answer_photo(
            photo=photo,
            caption=f"📕 **Страница {page} из {TOTAL_BOOK_PAGES}**\n\nВыберите режим практики:",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer(f"✅ Страница {page} показана!", show_alert=False)
    except Exception as e:
        logging.error(f"Error sending book page {page}: {e}")
        await callback.answer("❌ Ошибка при отправке страницы.", show_alert=True)


@dp.callback_query(F.data.startswith("book_mini_dialogue_"))
async def process_book_mini_dialogue(callback: types.CallbackQuery):
    """Handle Mini Dialogue mode for a book page - Bot asks in English, user answers in English."""
    page = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    # Get dialogue content for this page
    dialogue_data = get_dialogue_for_page(page)
    title = dialogue_data["title"]
    mini_dialogue = dialogue_data["mini_dialogue"]
    
    # Store practice state for mini dialogue
    if "book_dialogue_state" not in user_states:
        user_states["book_dialogue_state"] = {}
    
    user_states["book_dialogue_state"][user_id] = {
        "page": page,
        "questions": mini_dialogue,
        "current_index": 0,
        "score": 0,
    }
    
    # Build dialogue header text
    dialogue_text = f"💬 **Mini Dialogue - Страница {page}**\n\n"
    dialogue_text += f"📝 **{title}**\n\n"
    dialogue_text += f"Бот задаст вам вопросы на английском языке.\n"
    dialogue_text += f"Отвечайте на английском языке.\n\n"
    dialogue_text += f"Вопрос {1}/{len(mini_dialogue)}:"
    
    # Send first question
    first_question = mini_dialogue[0]
    question_text = first_question.get("bot_question_en", "")
    
    dialogue_text += f"\n\n🤖 {question_text}"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Пропустить", callback_data=f"book_skip_dialogue_{page}")
    builder.button(text="🔙 K странице", callback_data=f"book_view_page_{page}")
    builder.adjust(1)
    
    await callback.message.answer(
        text=dialogue_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("book_quick_practice_"))
async def process_book_quick_practice(callback: types.CallbackQuery):
    """Handle Quick Practice mode for a book page - Bot asks in English, user translates to Tajik."""
    page = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    # Get dialogue content for this page
    dialogue_data = get_dialogue_for_page(page)
    title = dialogue_data["title"]
    quick_practice = dialogue_data["quick_practice"]
    
    # Store practice state
    if "book_practice_state" not in user_states:
        user_states["book_practice_state"] = {}
    
    user_states["book_practice_state"][user_id] = {
        "page": page,
        "questions": quick_practice,
        "current_index": 0,
        "score": 0,
    }
    
    practice_text = f"⚡ **Амaliёти зуд - Саҳифаи {page}**\n\n"
    practice_text += f"📝 **{title}**\n\n"
    practice_text += f"Бот саволҳоро ба забони англисӣ медиҳад.\n"
    practice_text += f"Онҳоро ба забони тоҷикӣ тарҷума кунед.\n\n"
    practice_text += f"Саволи {1}/{len(quick_practice)}:"
    
    # Send first question (always in English)
    first_question = quick_practice[0]
    question_text = first_question.get("bot_question_en", "")
    
    practice_text += f"\n\n🤖 {question_text}"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Гузаштан", callback_data=f"book_skip_practice_{page}")
    builder.button(text="🔙 Ба саҳифа", callback_data=f"book_view_page_{page}")
    builder.adjust(1)
    
    await callback.message.answer(
        text=practice_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("book_skip_dialogue_"))
async def process_book_skip_dialogue(callback: types.CallbackQuery):
    """Handle skipping a mini dialogue question."""
    page = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    dialogue_state = user_states.get("book_dialogue_state", {}).get(user_id)
    if not dialogue_state:
        await callback.answer("❌ Вы не в режиме диалога.", show_alert=True)
        return
    
    current_index = dialogue_state["current_index"]
    questions = dialogue_state["questions"]
    
    if current_index < len(questions):
        question = questions[current_index]
        expected_answer = question.get("expected_answer_en", "")
        
        await callback.message.answer(
            text=f"⏭️ Пропущено.\n\n✅ Правильный ответ:\n{expected_answer}",
            parse_mode="Markdown"
        )
        
        dialogue_state["current_index"] += 1
        
        await asyncio.sleep(1.5)
        
        # Send next question or finish
        if dialogue_state["current_index"] >= len(questions):
            await finish_book_dialogue(user_id)
        else:
            await send_next_dialogue_question(user_id)
    
    await callback.answer()


@dp.callback_query(F.data.startswith("book_skip_practice_"))
async def process_book_skip_practice(callback: types.CallbackQuery):
    """Handle skipping a practice question."""
    page = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    practice_state = user_states.get("book_practice_state", {}).get(user_id)
    if not practice_state:
        await callback.answer("❌ Вы не в режиме практики.", show_alert=True)
        return
    
    current_index = practice_state["current_index"]
    questions = practice_state["questions"]
    
    if current_index < len(questions):
        question = questions[current_index]
        user_lang = get_or_create_user(user_id).get("language", "tj")
        
        # Show correct answer
        if user_lang == "tj":
            correct_answer = question.get("expected_answer_tj", question.get("expected_answer_en", ""))
        else:
            correct_answer = question.get("expected_answer_en", question.get("expected_answer_tj", ""))
        
        await callback.message.answer(
            text=f"⏭️ Пропущено.\n\n✅ Правильный ответ:\n{correct_answer}",
            parse_mode="Markdown"
        )
        
        practice_state["current_index"] += 1
        
        await asyncio.sleep(1.5)
        
        # Send next question or finish
        if practice_state["current_index"] >= len(questions):
            await finish_book_practice(user_id)
        else:
            await send_next_practice_question(user_id)
    
    await callback.answer()


async def send_next_practice_question(user_id: int):
    """Send the next practice question - always in English for translation."""
    practice_state = user_states.get("book_practice_state", {}).get(user_id)
    if not practice_state:
        return
    
    current_index = practice_state["current_index"]
    questions = practice_state["questions"]
    page = practice_state["page"]
    
    if current_index >= len(questions):
        await finish_book_practice(user_id)
        return
    
    question = questions[current_index]
    # Always send question in English for translation practice
    question_text = question.get("bot_question_en", "")
    
    practice_text = f"⚡ **Quick Practice - Страница {page}**\n\n"
    practice_text += f"Вопрос {current_index + 1}/{len(questions)}:\n\n"
    practice_text += f"🤖 {question_text}"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Пропустить", callback_data=f"book_skip_practice_{page}")
    builder.button(text="🔙 K странице", callback_data=f"book_view_page_{page}")
    builder.adjust(1)
    
    await bot.send_message(
        chat_id=user_id,
        text=practice_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


async def send_next_dialogue_question(user_id: int):
    """Send the next mini dialogue question - Bot asks in English, user answers in English."""
    dialogue_state = user_states.get("book_dialogue_state", {}).get(user_id)
    if not dialogue_state:
        return
    
    current_index = dialogue_state["current_index"]
    questions = dialogue_state["questions"]
    page = dialogue_state["page"]
    
    if current_index >= len(questions):
        await finish_book_dialogue(user_id)
        return
    
    question = questions[current_index]
    question_text = question.get("bot_question_en", "")
    
    dialogue_text = f"💬 **Mini Dialogue - Страница {page}**\n\n"
    dialogue_text += f"Вопрос {current_index + 1}/{len(questions)}:\n\n"
    dialogue_text += f"🤖 {question_text}\n\n"
    dialogue_text += f"Ответьте на английском языке."
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Пропустить", callback_data=f"book_skip_dialogue_{page}")
    builder.button(text="🔙 K странице", callback_data=f"book_view_page_{page}")
    builder.adjust(1)
    
    await bot.send_message(
        chat_id=user_id,
        text=dialogue_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


async def finish_book_dialogue(user_id: int):
    """Finish book mini dialogue and show results."""
    dialogue_state = user_states.get("book_dialogue_state", {}).get(user_id)
    if not dialogue_state:
        return
    
    score = dialogue_state["score"]
    total = len(dialogue_state["questions"])
    page = dialogue_state["page"]
    
    result_text = f"🏆 **Mini Dialogue завершён!**\n\n"
    result_text += f"📊 Страница {page}\n"
    result_text += f"✅ Правильных ответов: {score}/{total}\n"
    result_text += f"🎯 Результат: {int(score / total * 100)}%\n\n"
    
    if score >= total * 0.8:
        result_text += "🎉 Отлично! Вы молодец!"
    elif score >= total * 0.5:
        result_text += "👍 Хорошо! Продолжайте практиковаться!"
    else:
        result_text += "💪 Не сдавайтесь! Попробуйте ещё раз!"
    
    # Clear dialogue state
    if user_id in user_states.get("book_dialogue_state", {}):
        del user_states["book_dialogue_state"][user_id]
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Попробовать снова", callback_data=f"book_mini_dialogue_{page}")
    builder.button(text="🔙 K странице", callback_data=f"book_view_page_{page}")
    builder.adjust(1)
    
    await bot.send_message(
        chat_id=user_id,
        text=result_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.message(F.text)
async def handle_book_dialogue_answer(message: types.Message):
    """Handle user's answer in mini dialogue mode."""
    user_id = message.from_user.id
    
    # Check if user is in book dialogue mode
    if "book_dialogue_state" not in user_states or user_id not in user_states["book_dialogue_state"]:
        return  # Not in book dialogue mode
    
    dialogue_state = user_states["book_dialogue_state"][user_id]
    user_answer = message.text.strip()
    current_index = dialogue_state["current_index"]
    questions = dialogue_state["questions"]
    
    if current_index >= len(questions):
        await finish_book_dialogue(user_id)
        return
    
    question = questions[current_index]
    expected_answer_en = question.get("expected_answer_en", "").lower().strip()
    user_answer_lower = user_answer.lower().strip()
    
    # Check if answer is correct (partial match allowed)
    is_correct = (
        user_answer_lower == expected_answer_en or
        expected_answer_en in user_answer_lower or
        user_answer_lower in expected_answer_en
    )
    
    if is_correct:
        result_text = f"✅ **Правильно!**\n\n"
        result_text += f"📝 Ваш ответ: {user_answer}\n"
        result_text += f"💡 Правильный ответ: {expected_answer_en}"
        dialogue_state["score"] += 1
    else:
        result_text = f"❌ **Неправильно**\n\n"
        result_text += f"📝 Ваш ответ: {user_answer}\n"
        result_text += f"✅ Правильный ответ: {expected_answer_en}"
    
    dialogue_state["current_index"] += 1
    
    await message.answer(
        text=result_text,
        parse_mode="Markdown"
    )
    
    await asyncio.sleep(1.5)
    
    if dialogue_state["current_index"] >= len(questions):
        await finish_book_dialogue(user_id)
    else:
        await send_next_dialogue_question(user_id)


async def finish_book_practice(user_id: int):
    """Finish book practice and show results."""
    practice_state = user_states.get("book_practice_state", {}).get(user_id)
    if not practice_state:
        return
    
    score = practice_state["score"]
    total = len(practice_state["questions"])
    page = practice_state["page"]
    
    # Add points
    points_earned = score
    users = load_user_data()
    user_id_str = str(user_id)
    if user_id_str in users:
        users[user_id_str]["total_points"] += points_earned
        users[user_id_str]["total_correct"] += score
        users[user_id_str]["total_answered"] += total
        users[user_id_str]["last_active"] = time.time()
        save_user_data(users)
    
    result_text = f"🏆 **Quick Practice завершён!**\n\n"
    result_text += f"📊 Страница {page}\n"
    result_text += f"✅ Правильных ответов: {score}/{total}\n"
    result_text += f"🎯 Результат: {int(score / total * 100)}%\n\n"
    
    if score >= total * 0.8:
        result_text += "🎉 Отлично! Вы молодец!"
    elif score >= total * 0.5:
        result_text += "👍 Хорошо! Продолжайте практиковаться!"
    else:
        result_text += "💪 Не сдавайтесь! Попробуйте ещё раз!"
    
    # Clear practice state
    if user_id in user_states.get("book_practice_state", {}):
        del user_states["book_practice_state"][user_id]
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Попробовать снова", callback_data=f"book_quick_practice_{page}")
    builder.button(text="🔙 K странице", callback_data=f"book_view_page_{page}")
    builder.adjust(1)
    
    await bot.send_message(
        chat_id=user_id,
        text=result_text,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.message(F.text)
async def handle_book_practice_answer(message: types.Message):
    """Handle user's answer in book practice mode - user translates English to Tajik."""
    user_id = message.from_user.id
    
    # Check if user is in book practice mode
    if "book_practice_state" not in user_states or user_id not in user_states["book_practice_state"]:
        return  # Not in book practice mode
    
    practice_state = user_states["book_practice_state"][user_id]
    user_answer = message.text.strip()
    current_index = practice_state["current_index"]
    questions = practice_state["questions"]
    
    if current_index >= len(questions):
        await finish_book_practice(user_id)
        return
    
    question = questions[current_index]
    
    # Get expected answers - user should translate to Tajik
    expected_tj = question.get("expected_answer_tj", "").lower().strip()
    user_answer_lower = user_answer.lower().strip()
    
    # For Quick Practice, user translates English to Tajik
    # Check if answer matches the Tajik translation
    is_correct = False
    
    if expected_tj:
        # Check for exact match or partial match with Tajik
        is_correct = (
            user_answer_lower == expected_tj or
            expected_tj in user_answer_lower or
            user_answer_lower in expected_tj
        )
    
    # If no Tajik answer expected, check English (fallback)
    if not expected_tj:
        expected_en = question.get("expected_answer_en", "").lower().strip()
        is_correct = (
            user_answer_lower == expected_en or
            expected_en in user_answer_lower or
            user_answer_lower in expected_en
        )
    
    if is_correct:
        result_text = f"✅ **Дуруст!**\n\n"
        result_text += f"📝 Ҷавоби шумо: {user_answer}\n"
        result_text += f"💡 Тарҷумаи дуруст: {expected_tj or question.get('expected_answer_en', '')}"
        practice_state["score"] += 1
    else:
        result_text = f"❌ **Нодуруст**\n\n"
        result_text += f"📝 Ҷавоби шумо: {user_answer}\n"
        result_text += f"✅ Ҷавоби дуруст: {expected_tj or question.get('expected_answer_en', '')}"
    
    practice_state["current_index"] += 1
    
    await message.answer(
        text=result_text,
        parse_mode="Markdown"
    )
    
    await asyncio.sleep(1.5)
    
    if practice_state["current_index"] >= len(questions):
        await finish_book_practice(user_id)
    else:
        await send_next_practice_question(user_id)


async def main():
    """Main function to run the bot."""
    # Initialize user data file if it doesn't exist
    if not os.path.exists(USERS_DATA_FILE):
        save_user_data({})

    logging.info(f"Bot started! Total levels: {TOTAL_LEVELS}")
    logging.info(f"Total book pages: {TOTAL_BOOK_PAGES}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped!")
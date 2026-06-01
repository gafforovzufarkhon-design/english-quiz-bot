"""
Book Dialogues and Quick Practice for English Learning Bot
Contains dialogues and practice exercises for each book page.
"""

# Dialogues organized by page number
# Each page has a mini dialogue and quick practice exercises
BOOK_DIALOGUES = {
    1: {
        "title": "Shopping - Asking about prices",
        "mini_dialogue": [
            {"bot_question_en": "How much is this?", "expected_answer_en": "It is 20 dollars."},
            {"bot_question_en": "What color is this jacket?", "expected_answer_en": "It is blue."},
            {"bot_question_en": "Do you want this?", "expected_answer_en": "Yes, I like it."},
            {"bot_question_en": "How much is this jacket?", "expected_answer_en": "It is 50 dollars."},
            {"bot_question_en": "Can I try it on?", "expected_answer_en": "Yes, of course."},
        ],
        "quick_practice": [
            {
                "bot_question_en": "How much is this?",
                "expected_answer_tj": "Ин чанд пул аст?",
                "expected_answer_ru": "Сколько это стоит?"
            },
            {
                "bot_question_en": "What color is this jacket?",
                "expected_answer_tj": "Ин курт кадом ранг аст?",
                "expected_answer_ru": "Какого цвета эта куртка?"
            },
            {
                "bot_question_en": "Do you want this?",
                "expected_answer_tj": "Шумо инро мехоҳед?",
                "expected_answer_ru": "Вы хотите это?"
            },
            {
                "bot_question_en": "It is 50 dollars.",
                "expected_answer_tj": "Ин 50 доллар аст.",
                "expected_answer_ru": "Это 50 долларов."
            },
            {
                "bot_question_en": "Can I try it on?",
                "expected_answer_tj": "Оё ман метавонам онро пӯшам?",
                "expected_answer_ru": "Могу ли я примерить это?"
            },
        ]
    },
    2: {
        "title": "At the Restaurant - Ordering food",
        "mini_dialogue": [
            {"bot_question_en": "What would you like?", "expected_answer_en": "I would like a pizza, please."},
            {"bot_question_en": "Anything to drink?", "expected_answer_en": "Yes, a glass of water."},
            {"bot_question_en": "Is everything okay?", "expected_answer_en": "Yes, the food is delicious."},
            {"bot_question_en": "Would you like dessert?", "expected_answer_en": "Yes, I'll have ice cream."},
            {"bot_question_en": "Can I have the bill, please?", "expected_answer_en": "Of course, here you are."},
        ],
        "quick_practice": [
            {
                "bot_question_en": "What would you like?",
                "expected_answer_tj": "Шумо чӣ мехоҳед?",
                "expected_answer_ru": "Что вы хотите?"
            },
            {
                "bot_question_en": "I would like a pizza.",
                "expected_answer_tj": "Ман як питса мехоҳам.",
                "expected_answer_ru": "Я хочу пиццу."
            },
            {
                "bot_question_en": "Anything to drink?",
                "expected_answer_tj": "Нӯшокиҳо ҳам ҳастед?",
                "expected_answer_ru": "Что-нибудь выпить?"
            },
            {
                "bot_question_en": "The food is delicious.",
                "expected_answer_tj": "Хӯрок болаззат аст.",
                "expected_answer_ru": "Еда вкусная."
            },
            {
                "bot_question_en": "Can I have the bill?",
                "expected_answer_tj": "Оё ман метавонам ҳисобро гирам?",
                "expected_answer_ru": "Могу ли я получить счёт?"
            },
        ]
    },
    3: {
        "title": "Greetings - Meeting people",
        "mini_dialogue": [
            {"bot_question_en": "Hello, who are you?", "expected_answer_en": "Hi, I'm John. Nice to meet you."},
            {"bot_question_en": "Where are you from?", "expected_answer_en": "I'm from England."},
            {"bot_question_en": "What do you do?", "expected_answer_en": "I'm a student."},
            {"bot_question_en": "How old are you?", "expected_answer_en": "I'm twenty years old."},
            {"bot_question_en": "Do you speak English?", "expected_answer_en": "Yes, I speak English."},
        ],
        "quick_practice": [
            {
                "bot_question_en": "Hello, who are you?",
                "expected_answer_tj": "Салом, шумо кӣ ҳастед?",
                "expected_answer_ru": "Привет, кто вы?"
            },
            {
                "bot_question_en": "Where are you from?",
                "expected_answer_tj": "Шумо аз куҷо ҳастед?",
                "expected_answer_ru": "Откуда вы?"
            },
            {
                "bot_question_en": "I'm from England.",
                "expected_answer_tj": "Ман аз Англия ҳастам.",
                "expected_answer_ru": "Я из Англии."
            },
            {
                "bot_question_en": "What do you do?",
                "expected_answer_tj": "Шумо чӣ кор мекунед?",
                "expected_answer_ru": "Чем вы занимаетесь?"
            },
            {
                "bot_question_en": "I'm a student.",
                "expected_answer_tj": "Ман донишҷӯ ҳастам.",
                "expected_answer_ru": "Я студент."
            },
        ]
    },
    4: {
        "title": "Daily Routine - Talking about habits",
        "mini_dialogue": [
            {"bot_question_en": "What time do you go to bed?", "expected_answer_en": "I usually go to bed at 10 PM."},
            {"bot_question_en": "When do you wake up?", "expected_answer_en": "I wake up at 6 AM."},
            {"bot_question_en": "Do you exercise every day?", "expected_answer_en": "Yes, I exercise every morning."},
            {"bot_question_en": "What time do you eat breakfast?", "expected_answer_en": "I eat breakfast at 7 AM."},
            {"bot_question_en": "Do you like your routine?", "expected_answer_en": "Yes, it's very healthy."},
        ],
        "quick_practice": [
            {
                "bot_question_en": "What time do you go to bed?",
                "expected_answer_tj": "Шумо ҳар рӯз соати чанд мехобед?",
                "expected_answer_ru": "Во сколько вы ложитесь спать?"
            },
            {
                "bot_question_en": "I usually go to bed at 10 PM.",
                "expected_answer_tj": "Ман одатан соати 10 шаб мехобам.",
                "expected_answer_ru": "Я обычно ложусь спать в 10 вечера."
            },
            {
                "bot_question_en": "When do you wake up?",
                "expected_answer_tj": "Ва шумо кай бедор мешавед?",
                "expected_answer_ru": "А когда вы просыпаетесь?"
            },
            {
                "bot_question_en": "I wake up at 6 AM.",
                "expected_answer_tj": "Ман соати 6 субҳ бедор мешавам.",
                "expected_answer_ru": "Я просыпаюсь в 6 утра."
            },
            {
                "bot_question_en": "Do you exercise every day?",
                "expected_answer_tj": "Шумо ҳар рӯз варзиш мекунед?",
                "expected_answer_ru": "Вы занимаетесь спортом каждый день?"
            },
        ]
    },
    5: {
        "title": "Travel - Asking for directions",
        "mini_dialogue": [
            {"bot_question_en": "Excuse me, where is the library?", "expected_answer_en": "Go straight and turn left."},
            {"bot_question_en": "Is it far from here?", "expected_answer_en": "No, it's just 5 minutes walk."},
            {"bot_question_en": "Where is the bus station?", "expected_answer_en": "It's next to the supermarket."},
            {"bot_question_en": "How can I get to the airport?", "expected_answer_en": "Take a taxi or bus number 5."},
            {"bot_question_en": "Thank you for your help!", "expected_answer_en": "You're welcome!"},
        ],
        "quick_practice": [
            {
                "bot_question_en": "Excuse me, where is the library?",
                "expected_answer_tj": "Бахшиш, китобхона куҷост?",
                "expected_answer_ru": "Извините, где библиотека?"
            },
            {
                "bot_question_en": "Go straight and turn left.",
                "expected_answer_tj": "Рост равед ва ба чап гардиш кунед.",
                "expected_answer_ru": "Идите прямо и поверните налево."
            },
            {
                "bot_question_en": "Is it far from here?",
                "expected_answer_tj": "Оё он аз ин ҷо дур аст?",
                "expected_answer_ru": "Это далеко отсюда?"
            },
            {
                "bot_question_en": "It's just 5 minutes walk.",
                "expected_answer_tj": "Он ҳамагӣ 5 дақиқа роҳ аст.",
                "expected_answer_ru": "Это всего 5 минут ходьбы."
            },
            {
                "bot_question_en": "Where is the bus station?",
                "expected_answer_tj": "Истгоҳи автобус куҷост?",
                "expected_answer_ru": "Где автобусная станция?"
            },
        ]
    },
}

# Default dialogue for pages without specific content
DEFAULT_DIALOGUE = {
    "title": "General Practice",
    "mini_dialogue": [
        {"bot_question_en": "Hello! How are you?", "expected_answer_en": "I'm fine, thank you!"},
        {"bot_question_en": "What are you doing today?", "expected_answer_en": "I'm studying English."},
        {"bot_question_en": "Do you like learning English?", "expected_answer_en": "Yes, it's very interesting."},
        {"bot_question_en": "How long have you been studying?", "expected_answer_en": "I've been studying for 2 years."},
        {"bot_question_en": "What's your favorite subject?", "expected_answer_en": "I like speaking practice."},
    ],
    "quick_practice": [
        {
            "bot_question_en": "Hello! How are you?",
            "expected_answer_tj": "Салом! Чӣ хел шумо?",
            "expected_answer_ru": "Привет! Как дела?"
        },
        {
            "bot_question_en": "I'm fine, thank you!",
            "expected_answer_tj": "Ман хубам, раҳмат!",
            "expected_answer_ru": "Я в порядке, спасибо!"
        },
        {
            "bot_question_en": "What are you doing today?",
            "expected_answer_tj": "Имрӯз чӣ кор мекунед?",
            "expected_answer_ru": "Что вы делаете сегодня?"
        },
        {
            "bot_question_en": "I'm studying English.",
            "expected_answer_tj": "Ман забони англисӣ мехонам.",
            "expected_answer_ru": "Я изучаю английский."
        },
        {
            "bot_question_en": "Do you like learning English?",
            "expected_answer_tj": "Шумо омӯзиши забони англисиро дӯст медоред?",
            "expected_answer_ru": "Вам нравится изучать английский?"
        },
    ]
}


def get_dialogue_for_page(page: int) -> dict:
    """Get dialogue content for a specific page."""
    return BOOK_DIALOGUES.get(page, DEFAULT_DIALOGUE)


def get_total_dialogue_pages() -> int:
    """Get total number of pages with dialogues."""
    return max(len(BOOK_DIALOGUES), 100)  # At least 100 pages
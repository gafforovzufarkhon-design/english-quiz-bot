"""
English Quiz Questions Database
Contains questions for 102 levels, from beginner to advanced.
Each question has 4 answer options and the index of the correct answer (0-3)
"""

# Level 1 - Easy Questions (Basic grammar and vocabulary)
LEVEL_1_QUESTIONS = [
    {
        "question": "Choose the correct form of the verb 'to be': She ___ a student.",
        "options": ["am", "is", "are", "be"],
        "correct": 1  # "is"
    },
    {
        "question": "What is the past simple form of 'go'?",
        "options": ["goed", "gone", "went", "going"],
        "correct": 2  # "went"
    },
    {
        "question": "Choose the correct plural form: one child, two ___.",
        "options": ["childs", "children", "childrens", "childes"],
        "correct": 1  # "children"
    },
    {
        "question": "Which word is an opposite of 'hot'?",
        "options": ["warm", "cold", "cool", "freezing"],
        "correct": 1  # "cold"
    },
    {
        "question": "Complete the sentence: I ___ breakfast at 7 AM every day.",
        "options": ["have", "has", "having", "had"],
        "correct": 0  # "have"
    },
    {
        "question": "What is the comparative form of 'good'?",
        "options": ["gooder", "more good", "better", "best"],
        "correct": 2  # "better"
    },
    {
        "question": "Choose the correct article: ___ elephant is a big animal.",
        "options": ["A", "An", "The", "-"],
        "correct": 1  # "An"
    },
    {
        "question": "What is the opposite of 'happy'?",
        "options": ["angry", "sad", "tired", "bored"],
        "correct": 1  # "sad"
    },
    {
        "question": "Complete: They ___ to school every day.",
        "options": ["goes", "going", "go", "gone"],
        "correct": 2  # "go"
    },
    {
        "question": "Which word means 'not difficult'?",
        "options": ["hard", "easy", "heavy", "light"],
        "correct": 1  # "easy"
    },
]

# Level 2 - Hard Questions (Advanced grammar and vocabulary)
LEVEL_2_QUESTIONS = [
    {
        "question": "Choose the correct form: If I ___ you, I would study harder.",
        "options": ["was", "were", "am", "have been"],
        "correct": 1  # "were" (Second Conditional)
    },
    {
        "question": "Select the correct Present Perfect form: She ___ in London for five years.",
        "options": ["lives", "has lived", "is living", "lived"],
        "correct": 1  # "has lived"
    },
    {
        "question": "What is the meaning of the phrasal verb 'give up'?",
        "options": ["to start", "to continue", "to stop/quit", "to improve"],
        "correct": 2  # "to stop/quit"
    },
    {
        "question": "Choose the correct passive voice: 'Someone stole my bike' → 'My bike ___.",
        "options": ["was stolen", "is stolen", "has been stolen", "had stolen"],
        "correct": 0  # "was stolen"
    },
    {
        "question": "Which word is a synonym for 'enormous'?",
        "options": ["tiny", "huge", "average", "narrow"],
        "correct": 1  # "huge"
    },
    {
        "question": "Complete with the correct preposition: She is interested ___ learning French.",
        "options": ["on", "at", "in", "for"],
        "correct": 2  # "in"
    },
    {
        "question": "What is the superlative form of 'far'?",
        "options": ["farest", "farthest/the farthest", "more far", "most far"],
        "correct": 1  # "farthest"
    },
    {
        "question": "Choose the correct modal verb: You ___ smoke in the hospital. It's forbidden.",
        "options": ["don't have to", "mustn't", "needn't", "shouldn't"],
        "correct": 1  # "mustn't"
    },
    {
        "question": "What does the idiom 'break the ice' mean?",
        "options": ["to make people feel comfortable", "to freeze something", "to break something", "to start a fight"],
        "correct": 0  # "to make people feel comfortable"
    },
    {
        "question": "Select the correct reported speech: He said, 'I am tired.' → He said that he ___ tired.",
        "options": ["am", "is", "was", "has been"],
        "correct": 2  # "was"
    }
]

# Generate levels 3-100 with progressive difficulty
# Each level has 10 questions

def generate_questions_for_level(level):
    """Generate questions for a specific level (3-102)"""
    questions = []
    
    # Question pools organized by topic and difficulty
    grammar_questions = [
        # Present Simple
        {
            "question": "Choose the correct form: He ___ to work every day.",
            "options": ["go", "goes", "going", "gone"],
            "correct": 1
        },
        {
            "question": "She ___ not like coffee.",
            "options": ["do", "does", "is", "are"],
            "correct": 1
        },
        {
            "question": "___ you speak English?",
            "options": ["Does", "Do", "Is", "Are"],
            "correct": 1
        },
        # Present Continuous
        {
            "question": "They ___ TV right now.",
            "options": ["watch", "watches", "are watching", "watched"],
            "correct": 2
        },
        {
            "question": "I ___ a book at the moment.",
            "options": ["read", "am reading", "reads", "reading"],
            "correct": 1
        },
        # Past Simple
        {
            "question": "Yesterday, I ___ to the cinema.",
            "options": ["go", "went", "gone", "going"],
            "correct": 1
        },
        {
            "question": "She ___ her homework last night.",
            "options": ["finish", "finishes", "finished", "finishing"],
            "correct": 2
        },
        {
            "question": "We ___ pizza for dinner yesterday.",
            "options": ["eat", "ate", "eaten", "eating"],
            "correct": 1
        },
        # Past Continuous
        {
            "question": "I ___ when you called.",
            "options": ["sleep", "slept", "was sleeping", "am sleeping"],
            "correct": 2
        },
        {
            "question": "They ___ football at 5 PM yesterday.",
            "options": ["play", "played", "were playing", "are playing"],
            "correct": 2
        },
        # Present Perfect
        {
            "question": "I ___ to Paris twice.",
            "options": ["go", "went", "have been", "has been"],
            "correct": 2
        },
        {
            "question": "She ___ just ___ her lunch.",
            "options": ["has/finished", "have/finished", "did/finish", "is/finishing"],
            "correct": 0
        },
        {
            "question": "___ you ever ___ sushi?",
            "options": ["Have/eaten", "Has/eaten", "Did/eat", "Do/eat"],
            "correct": 0
        },
        # Future forms
        {
            "question": "I think it ___ tomorrow.",
            "options": ["will rain", "rains", "is raining", "rained"],
            "correct": 0
        },
        {
            "question": "Look at those clouds! It ___.",
            "options": ["will rain", "is going to rain", "rains", "rained"],
            "correct": 1
        },
        {
            "question": "I ___ my grandparents this weekend.",
            "options": ["visit", "am visiting", "will visit", "visited"],
            "correct": 1
        },
        # Conditionals
        {
            "question": "If it rains, I ___ at home.",
            "options": ["stay", "will stay", "would stay", "stayed"],
            "correct": 1
        },
        {
            "question": "If I had money, I ___ a new car.",
            "options": ["buy", "will buy", "would buy", "bought"],
            "correct": 2
        },
        {
            "question": "If you heat ice, it ___.",
            "options": ["melts", "will melt", "would melt", "melted"],
            "correct": 0
        },
        # Passive voice
        {
            "question": "The book ___ by Mark Twain.",
            "options": ["wrote", "was written", "is written", "has written"],
            "correct": 1
        },
        {
            "question": "English ___ in many countries.",
            "options": ["speaks", "is spoken", "was spoken", "has spoken"],
            "correct": 1
        },
        # Reported speech
        {
            "question": "He said he ___ tired.",
            "options": ["is", "was", "were", "has been"],
            "correct": 1
        },
        {
            "question": "She told me she ___ the day before.",
            "options": ["arrives", "arrived", "had arrived", "has arrived"],
            "correct": 2
        },
        # Modals
        {
            "question": "You ___ wear a seatbelt in the car.",
            "options": ["must", "can", "may", "might"],
            "correct": 0
        },
        {
            "question": "___ I borrow your pen, please?",
            "options": ["Must", "Can", "Should", "Need"],
            "correct": 1
        },
        {
            "question": "It's cloudy. It ___ rain later.",
            "options": ["must", "might", "should", "need"],
            "correct": 1
        },
        # Gerunds and Infinitives
        {
            "question": "I enjoy ___ books.",
            "options": ["read", "to read", "reading", "readed"],
            "correct": 2
        },
        {
            "question": "She wants ___ a doctor.",
            "options": ["become", "becoming", "to become", "became"],
            "correct": 2
        },
        {
            "question": "He avoided ___ me the answer.",
            "options": ["tell", "to tell", "telling", "told"],
            "correct": 2
        },
        # Comparatives and Superlatives
        {
            "question": "This is the ___ movie I've ever seen.",
            "options": ["good", "better", "best", "most good"],
            "correct": 2
        },
        {
            "question": "My car is ___ than yours.",
            "options": ["fast", "faster", "fastest", "more fast"],
            "correct": 1
        },
        {
            "question": "She is the ___ student in the class.",
            "options": ["intelligent", "more intelligent", "most intelligent", "intelligenter"],
            "correct": 2
        },
        # Articles
        {
            "question": "I saw ___ interesting film yesterday.",
            "options": ["a", "an", "the", "-"],
            "correct": 1
        },
        {
            "question": "___ Sun is very hot.",
            "options": ["A", "An", "The", "-"],
            "correct": 2
        },
        {
            "question": "She goes to school by ___ bus.",
            "options": ["a", "an", "the", "-"],
            "correct": 3
        },
        # Prepositions
        {
            "question": "The book is ___ the table.",
            "options": ["in", "on", "at", "to"],
            "correct": 1
        },
        {
            "question": "I'll meet you ___ 5 o'clock.",
            "options": ["in", "on", "at", "to"],
            "correct": 2
        },
        {
            "question": "My birthday is ___ May.",
            "options": ["in", "on", "at", "to"],
            "correct": 0
        },
        {
            "question": "We traveled ___ train.",
            "options": ["in", "on", "by", "with"],
            "correct": 2
        },
        # Phrasal verbs
        {
            "question": "Please ___ the light when you leave.",
            "options": ["turn off", "turn on", "turn up", "turn down"],
            "correct": 0
        },
        {
            "question": "I need to ___ my grandmother this weekend.",
            "options": ["look after", "look for", "look at", "look up"],
            "correct": 0
        },
        {
            "question": "Can you ___ the music? It's too loud.",
            "options": ["turn off", "turn down", "turn up", "turn on"],
            "correct": 1
        },
    ]
    
    vocabulary_questions = [
        # Basic vocabulary
        {
            "question": "What is the opposite of 'big'?",
            "options": ["large", "small", "tall", "huge"],
            "correct": 1
        },
        {
            "question": "What is the opposite of 'fast'?",
            "options": ["quick", "rapid", "slow", "speedy"],
            "correct": 2
        },
        {
            "question": "What is a synonym for 'beautiful'?",
            "options": ["ugly", "pretty", "plain", "dull"],
            "correct": 1
        },
        {
            "question": "What is a synonym for 'intelligent'?",
            "options": ["stupid", "smart", "silly", "slow"],
            "correct": 1
        },
        # Colors
        {
            "question": "What color is the sky on a clear day?",
            "options": ["green", "blue", "red", "yellow"],
            "correct": 1
        },
        {
            "question": "What color do you get when you mix red and white?",
            "options": ["purple", "pink", "orange", "brown"],
            "correct": 1
        },
        # Numbers
        {
            "question": "What comes after ninety-nine?",
            "options": ["ninety-ten", "one hundred", "ninety-eleven", "thousand"],
            "correct": 1
        },
        {
            "question": "How many days are there in a week?",
            "options": ["five", "six", "seven", "eight"],
            "correct": 2
        },
        # Family
        {
            "question": "Your mother's sister is your ___.",
            "options": ["grandmother", "aunt", "cousin", "sister"],
            "correct": 1
        },
        {
            "question": "Your father's mother is your ___.",
            "options": ["aunt", "mother", "grandmother", "sister"],
            "correct": 2
        },
        # Time
        {
            "question": "What time of day comes after noon?",
            "options": ["morning", "afternoon", "evening", "night"],
            "correct": 1
        },
        {
            "question": "What comes between Tuesday and Thursday?",
            "options": ["Monday", "Wednesday", "Friday", "Saturday"],
            "correct": 1
        },
        # Food
        {
            "question": "What do you use to eat soup?",
            "options": ["fork", "knife", "spoon", "chopsticks"],
            "correct": 2
        },
        {
            "question": "What is a fruit?",
            "options": ["carrot", "apple", "potato", "lettuce"],
            "correct": 1
        },
        # Animals
        {
            "question": "Which animal says 'meow'?",
            "options": ["dog", "cat", "cow", "horse"],
            "correct": 1
        },
        {
            "question": "What is the largest land animal?",
            "options": ["lion", "elephant", "giraffe", "whale"],
            "correct": 1
        },
        # Weather
        {
            "question": "What falls from the sky when it rains?",
            "options": ["snow", "water drops", "hail", "wind"],
            "correct": 1
        },
        {
            "question": "What do you call frozen rain?",
            "options": ["sleet", "snow", "hail", "frost"],
            "correct": 2
        },
        # Body parts
        {
            "question": "You use your ___ to see.",
            "options": ["ears", "eyes", "nose", "mouth"],
            "correct": 1
        },
        {
            "question": "You use your ___ to hear.",
            "options": ["eyes", "ears", "nose", "mouth"],
            "correct": 1
        },
        # Clothes
        {
            "question": "What do you wear on your feet?",
            "options": ["gloves", "hat", "shoes", "scarf"],
            "correct": 2
        },
        {
            "question": "What do you wear on your head?",
            "options": ["gloves", "hat", "shoes", "socks"],
            "correct": 1
        },
        # House
        {
            "question": "Where do you sleep?",
            "options": ["kitchen", "bathroom", "bedroom", "living room"],
            "correct": 2
        },
        {
            "question": "Where do you cook?",
            "options": ["bedroom", "bathroom", "kitchen", "garage"],
            "correct": 2
        },
        # Jobs
        {
            "question": "Who teaches students?",
            "options": ["doctor", "teacher", "farmer", "chef"],
            "correct": 1
        },
        {
            "question": "Who works in a hospital and helps doctors?",
            "options": ["nurse", "teacher", "pilot", "engineer"],
            "correct": 0
        },
        # Sports
        {
            "question": "What sport uses a round ball and a net?",
            "options": ["tennis", "basketball", "golf", "baseball"],
            "correct": 1
        },
        {
            "question": "What sport is played on ice with sticks?",
            "options": ["football", "hockey", "tennis", "golf"],
            "correct": 1
        },
        # Travel
        {
            "question": "What do you need to travel to another country?",
            "options": ["ticket", "passport", "map", "camera"],
            "correct": 1
        },
        {
            "question": "What vehicle flies in the sky?",
            "options": ["car", "train", "airplane", "boat"],
            "correct": 2
        },
        # Shopping
        {
            "question": "Where do you buy food?",
            "options": ["cinema", "supermarket", "library", "school"],
            "correct": 1
        },
        {
            "question": "What do you use to pay in a store?",
            "options": ["book", "money", "pen", "phone"],
            "correct": 1
        },
        # Health
        {
            "question": "What should you do when you're sick?",
            "options": ["go to school", "see a doctor", "play sports", "go to work"],
            "correct": 1
        },
        {
            "question": "What do you take when you have a headache?",
            "options": ["food", "medicine", "water", "candy"],
            "correct": 1
        },
        # Nature
        {
            "question": "What do plants need to grow?",
            "options": ["sunlight and water", "darkness and sand", "cold and ice", "wind and snow"],
            "correct": 0
        },
        {
            "question": "What is H2O?",
            "options": ["air", "water", "fire", "earth"],
            "correct": 1
        },
        # Emotions
        {
            "question": "How do you feel when something good happens?",
            "options": ["sad", "happy", "angry", "tired"],
            "correct": 1
        },
        {
            "question": "How do you feel when you lose something important?",
            "options": ["happy", "excited", "upset", "proud"],
            "correct": 2
        },
        # Advanced vocabulary
        {
            "question": "What does 'enormous' mean?",
            "options": ["tiny", "very large", "average", "small"],
            "correct": 1
        },
        {
            "question": "What does 'exhausted' mean?",
            "options": ["energetic", "very tired", "hungry", "excited"],
            "correct": 1
        },
        {
            "question": "What does 'delicious' mean?",
            "options": ["tastes bad", "tastes good", "looks bad", "smells bad"],
            "correct": 1
        },
        {
            "question": "What does 'ancient' mean?",
            "options": ["very new", "very old", "modern", "future"],
            "correct": 1
        },
        {
            "question": "What does 'generous' mean?",
            "options": ["stingy", "giving", "selfish", "mean"],
            "correct": 1
        },
        {
            "question": "What does 'furious' mean?",
            "options": ["happy", "very angry", "calm", "sad"],
            "correct": 1
        },
        {
            "question": "What does 'brilliant' mean?",
            "options": ["stupid", "very clever", "dark", "boring"],
            "correct": 1
        },
        {
            "question": "What does 'terrified' mean?",
            "options": ["brave", "very scared", "calm", "confident"],
            "correct": 1
        },
        {
            "question": "What does 'peculiar' mean?",
            "options": ["normal", "strange", "common", "usual"],
            "correct": 1
        },
        {
            "question": "What does 'reluctant' mean?",
            "options": ["eager", "unwilling", "happy", "excited"],
            "correct": 1
        },
    ]
    
    # Select questions based on level number to create variety
    # Use modular arithmetic to cycle through questions
    num_grammar = len(grammar_questions)
    num_vocab = len(vocabulary_questions)
    
    # For each level, select 10 questions (mix of grammar and vocabulary)
    # The selection is deterministic based on level number
    selected_grammar = set()
    selected_vocab = set()
    seed = level * 7  # Simple deterministic seed
    
    # Pick 6 grammar questions
    grammar_count = 0
    i = 0
    while grammar_count < 6 and i < num_grammar * 2:
        idx = (seed + i * 13) % num_grammar
        if idx not in selected_grammar:
            selected_grammar.add(idx)
            questions.append(grammar_questions[idx])
            grammar_count += 1
        i += 1
    
    # Pick 4 vocabulary questions
    vocab_count = 0
    i = 0
    while vocab_count < 4 and i < num_vocab * 2:
        idx = (seed + i * 17) % num_vocab
        if idx not in selected_vocab:
            selected_vocab.add(idx)
            questions.append(vocabulary_questions[idx])
            vocab_count += 1
        i += 1
    
    return questions


# Build a dictionary of all levels
ALL_LEVELS = {}
ALL_LEVELS[1] = LEVEL_1_QUESTIONS
ALL_LEVELS[2] = LEVEL_2_QUESTIONS

# Generate levels 3-100
for lvl in range(3, 101):
    ALL_LEVELS[lvl] = generate_questions_for_level(lvl)


def get_questions(level: int):
    """
    Returns questions for the specified level.
    Args:
        level: 1-100 (1=Easy, 2=Hard, 3-100=Progressive difficulty)
    Returns:
        List of question dictionaries (10 questions per level)
    """
    return ALL_LEVELS.get(level, [])


def get_total_levels():
    """Returns the total number of available levels."""
    return len(ALL_LEVELS)


def get_level_range():
    """Returns the range of available levels."""
    return (1, len(ALL_LEVELS))
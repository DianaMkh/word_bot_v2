# Chatbot in Python using SQLite3

## Purpose

Development of a chatbot in Python that interacts with the user through a text interface. The bot uses a SQLite3 database to store data and supports adding new word pairs and a training mode.

## Functional Requirements

### 1. Bot Interface

**Main Menu:**
- **Add New Couple of Words**: to add new word pairs.
- **Let's Train**: to start training mode.

**Training Mode:**
- **Tip**: to get hints.
- **Pass**: to show the full word and its translation.
- **Stop Training**: to end training mode and return to the main menu.

### 2. Adding a New Word Pair

When selecting the **Add New Couple of Words** command, the bot prompts the user to enter a string in the format:

```
word or few words - translation or few words
```

**String Format:**
- The string must contain a `-` separator that separates the original word or phrase (in the user's language) from the translation (in the foreign language).
- If the separator is missing, the string is considered invalid, and the bot notifies the user about the incorrect format.
- Spaces before and after words or phrases are removed, and multiple spaces inside the string are replaced with a single space.

**Example:**
```
Input: " word or few words - translation or few words "
Result: "word or few words - translation or few words"
```

### 3. Data Storage

- All word pairs entered by the user are saved in a SQLite3 database.
- The table has three columns:
  - `user` (username or identifier)
  - `native_word` (original word or phrase)
  - `foreign_word` (translation of the word or phrase)

### 4. Training Mode

- When selecting the **Let's Train** command, the bot randomly selects a word pair from the database and shows one of the words to the user. The user must enter the translation of the word.
- **Answer Checking:**
  - After entering the answer, the bot compares it with the correct translation.
  - If the answer is correct, the bot congratulates the user.
  - If the answer is incorrect, the bot informs the user and shows the correct translation.
- **Hints (Tip):**
  - First press: shows the first quarter of the word (for words with four or more letters).
  - Second press: shows half of the word.
  - Third press: shows the full word.
- **Pass:**
  - Immediately shows the full word and the correct translation.
- **Stop Training:**
  - Ends the training mode and returns the user to the main menu.
  - Available only in training mode.
  - As long as training is active, the user is continuously offered words for translation. After two consecutive correct answers, the bot displays the current streak (the number of correct answers in a row).

## Technical Details

### 1. Using SQLite3

- The database is created and managed using the `sqlite3` library.
- The table in the database is created on the bot’s first launch or when initializing the database.

### 2. Functionality

- The bot processes user input, checks the string format, and saves correct word pairs to the database.
- In training mode, the bot randomly selects word pairs, checks the answers, provides hints, and allows skipping.
- A **Stop Training** button is implemented to exit training mode and return to the main menu.

### 3. Hints and Skipping

- Hints display parts of the word depending on the number of **Tip** button presses.
- The **Pass** button immediately shows the full word and translation.

### 4. Interface Update

- The bot interface has been updated with new buttons and functions for training mode.
- The **Stop Training** button is only available in training mode.

### 5. Streak (Consecutive Correct Answers)

- Tracks the number of consecutive correct answers in training mode.
- Displays the current streak after two consecutive correct answers.

---

Copy this text and paste it into the `README.md` file of your project on GitHub.

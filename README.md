# 🏫 Room Locator ChatBot App (No API Keys Required)

An intelligent Room Locator system powered by a chatbot, built using **Python** and **Kivy**, with offline NLP using **Hugging Face DialoGPT** and **Text-to-Speech** via `pyttsx3`. This app allows users to find room locations, ask general queries, and perform simple system commands — all without needing any API keys!

---

## ✨ Features

- 🗣 **Offline Chatbot** using Hugging Face `DialoGPT-medium`
- 🔊 **Text-to-Speech** capability for dynamic voice responses
- 💾 **SQLite3 Database** for storing user and room data
- 🧠 **Wikipedia Integration** for general knowledge queries
- 🖥️ **System Command Execution**: open Notepad, Calculator, File Explorer
- 🎵 **Sound Effects** on button click for better UX
- 🖼️ **Custom Background & Image Interface**
- 🎯 Built completely **offline** — No API keys needed

---

## 🧠 Technologies Used

| Technology     | Purpose                      |
|----------------|------------------------------|
| `Kivy`         | GUI development              |
| `pyttsx3`      | Text-to-Speech               |
| `wikipedia`    | Knowledge fetching           |
| `sqlite3`      | Local database               |
| `transformers` | NLP/Chatbot model            |
| `os`           | System commands              |
| `torch`        | Backend for NLP model        |

---

## 📂 Project Structure

```bash
room-locator-chatbot/
│
├── main.py                  # Main Kivy app logic
├── room_locator.db          # SQLite database (auto-created)
├── assets/
│   ├── download.png         # App icon
│   ├── background.jpg       # Background image
│   └── click.mp3            # Sound for button click
├── README.md                # Project documentation
└── requirements.txt         # Dependencies list
```
# 🚀  How to run
## 1. Clone the Repository
```bash
git clone https://github.com/yourusername/room-locator-chatbot.git
cd room-locator-chatbot
```
## 2. Install required packages
```bash
pip install kivy pyttsx3 wikipedia torch transformers
```
## 3. Rum the app
```bash
python main.py
```
### 💡 Note: Ensure audio files and image files exist at the given paths or change them in the code.


## 🔒 Privacy First

- ✅ No API Keys required
- ✅ Works completely offline
- ✅ No data is sent to any server
- ✅ Your information stays on your device



## 🙋‍♂️ Author

**Shriyansh Singh Rathore**  
📧 [shreyanshsinghrathore7@gmail.com](mailto:shreyanshsinghrathore7@gmail.com)  
🎓 B.Tech AI & Data Science, Poornima University  
📱 +91 8619277114  




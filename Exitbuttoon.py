import sys
import random
import re
import json
import nltk
import threading
import sqlite3
import pyttsx3
import requests
import os

# Try importing speech_recognition with fallback to Vosk
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
    VOSK_AVAILABLE = False
    print("Using SpeechRecognition module")
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    # Try importing Vosk as fallback
    try:
        from vosk import Model, KaldiRecognizer
        import pyaudio
        VOSK_AVAILABLE = True
        print("Using Vosk for speech recognition")
    except ImportError:
        VOSK_AVAILABLE = False
        print("Neither SpeechRecognition nor Vosk available. Voice input will be disabled.")

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QToolButton
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread

# Download necessary NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

def speak(audio):
    def run():
        engine = pyttsx3.init('sapi5')
        voices = engine.getProperty('voices')
        try:
            engine.setProperty('voice', voices[1].id)
        except IndexError:
            engine.setProperty('voice', voices[0].id)
        engine.say(audio)
        engine.runAndWait()
    # Run in a separate thread to avoid conflicts
    threading.Thread(target=run, daemon=True).start()

# Voice recognition thread that supports both SpeechRecognition and Vosk
class VoiceRecognitionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    status = pyqtSignal(str)
    
    def run(self):
        # First try using SpeechRecognition if available
        if SPEECH_RECOGNITION_AVAILABLE:
            self._run_speech_recognition()
        # Then try Vosk if available
        elif VOSK_AVAILABLE:
            self._run_vosk_recognition()
        # If neither is available
        else:
            self.error.emit("No speech recognition module available. Please install either 'SpeechRecognition' or 'vosk'.")
    
    def _run_speech_recognition(self):
        """Original SpeechRecognition implementation"""
        recognizer = sr.Recognizer()
        
        self.status.emit("Listening...")
        
        try:
            with sr.Microphone() as source:
                self.status.emit("Adjusting for ambient noise...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                self.status.emit("Speak now...")
                audio = recognizer.listen(source, timeout=5)
                
                self.status.emit("Processing your speech...")
                
                try:
                    text = recognizer.recognize_google(audio)
                    self.finished.emit(text)
                except sr.UnknownValueError:
                    self.error.emit("Sorry, I couldn't understand your speech.")
                except sr.RequestError as e:
                    self.error.emit(f"Could not request results; {e}")
        except Exception as e:
            self.error.emit(f"Error with microphone: {str(e)}")
    
    def _run_vosk_recognition(self):
        """New Vosk implementation"""
        self.status.emit("Initializing speech recognition...")
        
        try:
            # Check if model exists, if not provide instructions
            model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vosk-model")
            if not os.path.exists(model_path):
                self.status.emit("Setting up Vosk model...")
                # Create the directory if it doesn't exist
                os.makedirs(model_path, exist_ok=True)
                self.error.emit("Vosk model not found. Please download a model from https://alphacephei.com/vosk/models and extract it to the 'vosk-model' directory.")
                return
            
            model = Model(model_path)
            self.status.emit("Listening...")
            
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            stream.start_stream()
            
            recognizer = KaldiRecognizer(model, 16000)
            
            # Listen for 5 seconds max or until speech is recognized
            speech_detected = False
            max_iterations = int(16000 / 8000 * 5)  # 5 seconds
            
            for i in range(max_iterations):
                data = stream.read(8000, exception_on_overflow=False)
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get('text', '')
                    if text:
                        speech_detected = True
                        self.finished.emit(text)
                        break
            
            if not speech_detected:
                # Get final result if nothing was captured above
                result = json.loads(recognizer.FinalResult())
                text = result.get('text', '')
                if text:
                    self.finished.emit(text)
                else:
                    self.error.emit("Sorry, couldn't detect any speech.")
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            self.error.emit(f"Error with Vosk speech recognition: {str(e)}")

# Database setup
def setup_database():
    """Set up the database with proper error handling and connection management"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "room_locator.db")
    
    try:
        # Use proper connection context management
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Create tables with proper SQL syntax
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    room_number INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    room_number INTEGER PRIMARY KEY,
                    location TEXT NOT NULL
                )
            """)
            
            # Commit changes
            conn.commit()
            
            # Check if rooms table is empty
            cursor.execute("SELECT COUNT(*) FROM rooms")
            if cursor.fetchone()[0] == 0:
                room_data = [
                    (142, "First Floor"),
                    (143, "First Floor"),
                    (147, "H.O.D's Office"),
                    (1, "Admin Block"),
                    (11, "PIHM Student Rooms"),
                    (20, "Ground Floor"),
                    (201, "Second Floor"),
                    (301, "Third Floor"),
                    (401, "Fourth Floor"),
                ]
                cursor.executemany("INSERT INTO rooms VALUES (?, ?)", room_data)
                conn.commit()
            
            print(f"Database setup complete. Database path: {db_path}")
            return True
    except sqlite3.Error as e:
        print(f"Database error during setup: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error during database setup: {str(e)}")
        return False

def save_to_database(name, room_number):
    """Save user room query to database with proper error handling."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "room_locator.db")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, room_number) VALUES (?, ?)", (name, room_number))
            conn.commit()
            print(f"Saved to database: {name}, Room {room_number}")
            return True
    except sqlite3.Error as e:
        print(f"SQLite error saving to database: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error saving to database: {str(e)}")
        return False

def get_room_info_from_db(room_number):
    """Retrieve room information from the database."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "room_locator.db")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT location FROM rooms WHERE room_number = ?", (room_number,))
            result = cursor.fetchone()
            return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Error retrieving room info: {str(e)}")
        return None

def get_db_info():
    """Get information about the database for debugging."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "room_locator.db")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get user count
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            # Get room count
            cursor.execute("SELECT COUNT(*) FROM rooms")
            room_count = cursor.fetchone()[0]
            
            # Get recent queries with error handling
            try:
                cursor.execute("SELECT name, room_number, timestamp FROM users ORDER BY timestamp DESC LIMIT 5")
                recent_queries = cursor.fetchall()
            except sqlite3.Error:
                recent_queries = []
            
            return {
                "user_count": user_count,
                "room_count": room_count,
                "recent_queries": recent_queries,
                "db_path": os.path.abspath(db_path)
            }
    except sqlite3.Error as e:
        return {"error": str(e), "db_path": os.path.abspath(db_path)}

# Room locator data
room_info = [
    {"range": range(142, 153), "response": "Your room is on the First Floor. Right wing in FCE department"},
    {"range": range(1, 11), "response": "This is the Admin Block Rooms. You can Submit your Documents here"},
    {"range": range(11, 20), "response": "These rooms are for PIHM Students."},
    {"range": range(20, 60), "response": "Your room is on the Ground Floor. on the side of Seminar hall"},
    {"range": range(147, 148), "response": "This is the H.O.D's office. You can meet him there"},
    {"range": range(200, 257), "response": "Your room is on the Second Floor. Right wing in FCE department"},
    {"range": range(300, 357), "response": "Your room is on the Third Floor. Right eing in FCE department"},
    {"range": range(400, 457), "response": "Your room is on the Fourth Floor.  Right wing in FCE department"},
    {"range": range(457, 500), "response": "Your room is on the Fourth Floor.  Left wing in Artitecture department"},
    {"range": range(357, 400), "response": "Your room is on the Third Floor.  Left wing in Artitecture department"},
    {"range": range(257, 300), "response": "Your room is on the Second Floor.  Left wing in Artitecture department"}
]

def get_room_location(room_number):
    """Get room location with database backup."""
    try:
        room_number = int(room_number)
        
        # First try to get from database
        db_location = get_room_info_from_db(room_number)
        if db_location:
            return f"Your room is in {db_location}."
        
        # Fallback to hardcoded data
        for room in room_info:
            if room_number in room["range"]:
                return room["response"]
        
        return "Your room is not in our database."
    except ValueError:
        return "Please enter a valid room number."

# Integrated Mistral Chatbot
class MistralChatbot:
    def __init__(self, api_key=None):
        """ Initialize the chatbot with API key and necessary NLP tools """
        self.api_key = api_key or "LmSgvKjSfvxWb5ckRj1q2lw0hba2mioZ"
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.conversation_history = []
        
        self.patterns = {
            'greeting': r'(?i)h(i|ello|ey|owdy)|greetings|good (morning|afternoon|evening)',
            'farewell': r'(?i)bye|goodbye|see you|exit|quit',
            'thanks': r'(?i)thank(s| you)|appreciate',
            'room': r'(?i)room|locate|find|where is|location',
        }
        
        self.local_responses = {
            'greeting': [
                "Hello! How can I help you today?",
                "Hi there! What can I assist you with?",
                "Greetings! What would you like to know?"
            ],
            'farewell': [
                "Goodbye! Have a great day!",
                "See you later! Feel free to come back if you have more questions.",
                "Bye! It was nice chatting with you."
            ],
            'thanks': [
                "You're welcome!",
                "Happy to help!",
                "Anytime! Need anything else?"
            ],
            'room': [
                "I can help you find a room. Please enter a room number.",
                "Looking for a room? Just type the room number and I'll tell you where it is.",
                "Need to locate a room? Enter the room number and I'll help you find it."
            ]
        }

    def preprocess(self, text):
        """ Tokenizes, removes stopwords, and lemmatizes the input text """
        tokens = word_tokenize(text.lower())
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens if token.isalnum() and token not in self.stop_words]
        return " ".join(tokens)

    def match_simple_pattern(self, text):
        """ Matches user input with predefined patterns """
        for intent, pattern in self.patterns.items():
            if re.search(pattern, text):
                return intent
        return None

    def get_mistral_response(self, user_message):
        """ Fetches response from Mistral AI API """
        try:
            self.conversation_history.append({"role": "user", "content": user_message})

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            data = {
                "model": "mistral-large-latest",
                "messages": self.conversation_history,
                "max_tokens": 1024,
                "temperature": 0.7
            }

            response = requests.post(self.api_url, json=data, headers=headers)

            if response.status_code == 200:
                response_text = response.json()['choices'][0]['message']['content']
                self.conversation_history.append({"role": "assistant", "content": response_text})
                return response_text
            else:
                return f"Error from Mistral API: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Error connecting to Mistral API: {str(e)}"
        
    def handle_locally(self, intent):
        """ Handles simple interactions locally """
        return random.choice(self.local_responses.get(intent, ["I'm not sure how to respond to that."]))

    def generate_response(self, user_input):
        """ Generates a response based on user input """
        # Check if input is a room number
        if user_input.isdigit():
            return get_room_location(user_input)
        
        # Check for room-related queries
        words = user_input.lower().split()
        for word in words:
            if word.isdigit():
                return get_room_location(word)
        
        # Determines whether to use local handling or call the API
        intent = self.match_simple_pattern(user_input)
        return self.handle_locally(intent) if intent else self.get_mistral_response(user_input)
        
    def clear_history(self):
        """ Clears the conversation history """
        self.conversation_history = []

# Main Room Locator App
class RoomLocatorApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Room Locator")
        self.setGeometry(100, 100, 400, 500)
        self.setStyleSheet("background-color: #2E2E2E; color: white;")
        self.user_name = None
        self.voice_thread = None
        
        # Initialize database
        db_status = setup_database()
        if not db_status:
            QMessageBox.warning(self, "Database Warning", "Database initialization failed. Some features may not work correctly.")

        # Mistral API Key
        API_KEY = os.getenv("MISTRAL_API_KEY", "LmSgvKjSfvxWb5ckRj1q2lw0hba2mioZ")
        self.chatbot = MistralChatbot(api_key=API_KEY)

        self.setup_ui()
        speak("Welcome to the Room Locator App! Enter your name to begin.")
        
        # Display speech recognition availability status
        if SPEECH_RECOGNITION_AVAILABLE:
            print("Using Google Speech Recognition")
        elif VOSK_AVAILABLE:
            print("Using Vosk Speech Recognition")
            # Inform user if Vosk model is missing
            model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vosk-model")
            if not os.path.exists(model_path):
                print(f"Vosk model not found. Please download a model from https://alphacephei.com/vosk/models and extract it to: {model_path}")
        else:
            print("Speech recognition is disabled. Install SpeechRecognition or Vosk package to enable.")

    def setup_ui(self):
        layout = QVBoxLayout()

        # Try to load logo
        self.logo_label = QLabel(self)
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download.png")
        try:
            pixmap_logo = QPixmap(logo_path)
            if not pixmap_logo.isNull():
                self.logo_label.setPixmap(pixmap_logo.scaled(100, 100, Qt.KeepAspectRatio))
            else:
                self.logo_label.setText("ROOM LOCATOR")
                self.logo_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        except:
            self.logo_label.setText("ROOM LOCATOR")
            self.logo_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo_label)

        welcome_label = QLabel("Welcome! Enter your name and query.", self)
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(welcome_label)

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Enter your name")
        self.name_input.setStyleSheet("background-color: #444444; color: white; padding: 8px;")
        layout.addWidget(self.name_input)

        name_button = QPushButton("Submit Name", self)
        name_button.setStyleSheet("background-color: #555555; color: white; padding: 8px;")
        name_button.clicked.connect(self.store_name)
        layout.addWidget(name_button)

        # Chat input with voice button
        chat_input_layout = QVBoxLayout()
        
        # Status label for voice recognition
        self.voice_status_label = QLabel("", self)
        self.voice_status_label.setStyleSheet("color: #AAAAAA; font-style: italic;")
        chat_input_layout.addWidget(self.voice_status_label)
        
        # Input field with voice button
        input_with_voice = QVBoxLayout()
        self.chat_input = QLineEdit(self)
        self.chat_input.setPlaceholderText("Ask anything or enter a room number")
        self.chat_input.setStyleSheet("background-color: #444444; color: white; padding: 8px;")
        self.chat_input.returnPressed.connect(self.process_query)
        
        input_row = QVBoxLayout()
        input_field_row = QVBoxLayout()
        input_field_row.addWidget(self.chat_input)
        
        # Voice button
        voice_button_layout = QVBoxLayout()
        self.voice_button = QToolButton(self)
        
        # Try to load microphone icon
        mic_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mic.png")
        try:
            icon = QIcon(mic_icon_path)
            if not icon.isNull():
                self.voice_button.setIcon(icon)
                self.voice_button.setIconSize(QSize(24, 24))
            else:
                self.voice_button.setText("🎤")
                self.voice_button.setStyleSheet("font-size: 18px;")
        except:
            self.voice_button.setText("🎤")
            self.voice_button.setStyleSheet("font-size: 18px;")
        
        self.voice_button.setStyleSheet("""background-color: #444444; color: white; padding: 8px;""")
        # Add this line to set tooltip style globally
        self.voice_button.setToolTip("Click to Speak")
        QApplication.instance().setStyleSheet("QToolTip { color: black; background-color: #F0F0F0; border: 1px solid #767676; }")
        self.voice_button.clicked.connect(self.start_voice_recognition)
        voice_button_layout.addWidget(self.voice_button)
        
        input_and_voice = QVBoxLayout()
        input_and_voice.addLayout(input_field_row)
        input_and_voice.addLayout(voice_button_layout)
        
        input_row.addLayout(input_and_voice)
        input_with_voice.addLayout(input_row)
        chat_input_layout.addLayout(input_with_voice)
        
        layout.addLayout(chat_input_layout)

        self.chat_output = QLabel("", self)
        self.chat_output.setStyleSheet("background-color: #333333; padding: 10px; border-radius: 5px;")
        self.chat_output.setWordWrap(True)
        self.chat_output.setMinimumHeight(100)
        layout.addWidget(self.chat_output)

        chat_button = QPushButton("Submit Query", self)
        chat_button.setStyleSheet("background-color: #555555; color: white; padding: 8px;")
        chat_button.clicked.connect(self.process_query)
        layout.addWidget(chat_button)

        reset_button = QPushButton("Reset", self)
        reset_button.setStyleSheet("background-color: #555555; color: white; padding: 8px;")
        reset_button.clicked.connect(self.reset_fields)
        layout.addWidget(reset_button)

        debug_button = QPushButton("Debug DB", self)
        debug_button.setStyleSheet("background-color: #724444; color: white; padding: 8px;")
        debug_button.clicked.connect(self.show_db_debug)
        layout.addWidget(debug_button)
        
        # Check speech recognition availability and update UI
        if not SPEECH_RECOGNITION_AVAILABLE and not VOSK_AVAILABLE:
            self.voice_button.setEnabled(False)
            self.voice_button.setToolTip("Speech recognition not available")
            self.voice_status_label.setText("Speech recognition not available. Install SpeechRecognition or Vosk package.")

        self.setLayout(layout)

        # Try to set background image
        try:
            self.set_background_image()
        except:
            pass

    def set_background_image(self):
        try:
            bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download (1)774.jpg")
            pixmap = QPixmap(bg_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding)
                
                self.background_label = QLabel(self)
                self.background_label.setPixmap(scaled_pixmap)
                self.background_label.setGeometry(0, 0, self.width(), self.height())
                self.background_label.lower()
        except Exception as e:
            print(f"Error setting background: {str(e)}")

    def start_voice_recognition(self):
        """Start voice recognition in a separate thread"""
        if not SPEECH_RECOGNITION_AVAILABLE and not VOSK_AVAILABLE:
            QMessageBox.warning(self, "Feature Not Available", 
                               "Speech recognition is not available.\n"
                               "Please install either 'SpeechRecognition' or 'vosk' package.")
            return
            
        self.voice_button.setEnabled(False)
        self.voice_status_label.setText("Initializing voice recognition...")
        
        # Create and start the voice recognition thread
        self.voice_thread = VoiceRecognitionThread()
        self.voice_thread.finished.connect(self.on_voice_recognized)
        self.voice_thread.error.connect(self.on_voice_error)
        self.voice_thread.status.connect(self.on_voice_status)
        self.voice_thread.start()

    def on_voice_status(self, status):
        """Update voice recognition status"""
        self.voice_status_label.setText(status)

    def on_voice_recognized(self, text):
        """Handle recognized voice input"""
        self.chat_input.setText(text)
        self.voice_status_label.setText(f"Recognized: {text}")
        self.voice_button.setEnabled(True)
        
        # Optionally, automatically process the query
        self.process_query()

    def on_voice_error(self, error_msg):
        """Handle voice recognition errors"""
        self.voice_status_label.setText(error_msg)
        self.voice_button.setEnabled(True)
        QMessageBox.warning(self, "Voice Recognition Error", error_msg)

    def store_name(self):
        name = self.name_input.text().strip()
        if name:
            self.user_name = name
            self.name_input.setEnabled(False)
            speak(f"Hello, {self.user_name}. You can now ask about room locations or chat.")
            self.chat_output.setText(f"Hello, {self.user_name}! You can now ask about room locations or chat with me.")
        else:
            speak("Please enter a valid name.")

    def process_query(self):
        user_input = self.chat_input.text().strip()
        if not user_input:
            return

        if not self.user_name:
            speak("Please enter your name first.")
            self.chat_output.setText("Please enter your name first.")
            return

        response = self.chatbot.generate_response(user_input)
        self.chat_output.setText(response)
        speak(response)
        
        # Save to database if it's a room number query
        if user_input.isdigit():
            try:
                room_number = int(user_input)
                success = save_to_database(self.user_name, room_number)
                if success:
                    print(f"Saved query: {self.user_name}, Room {room_number}")
                else:
                    print("Failed to save to database")
            except Exception as e:
                print(f"Database error: {str(e)}")
        
        # Check if there's a room number in the query text
        else:
            words = user_input.lower().split()
            for word in words:
                if word.isdigit():
                    try:
                        room_number = int(word)
                        success = save_to_database(self.user_name, room_number)
                        if success:
                            print(f"Saved query: {self.user_name}, Room {room_number}")
                        else:
                            print("Failed to save to database")
                        break
                    except Exception as e:
                        print(f"Database error: {str(e)}")
        
        self.chat_input.clear()
        self.voice_status_label.clear()

    def reset_fields(self):
        self.name_input.clear()
        self.name_input.setEnabled(True)
        self.chat_input.clear()
        self.chat_output.clear()
        self.voice_status_label.clear()
        self.user_name = None
        speak("Fields have been reset. Enter new information.")

    def show_db_debug(self):
        try:
            info = get_db_info()
            if "error" in info:
                debug_text = f"Database Error: {info['error']}\n"
                debug_text += f"Database Path: {info['db_path']}\n"
                debug_text += "Try to fix the database connection."
            else:
                debug_text = f"Database Path: {info['db_path']}\n"
                debug_text += f"User Count: {info['user_count']}\n"
                debug_text += f"Room Count: {info['room_count']}\n\n"
                debug_text += "Recent Queries:\n"
                for query in info['recent_queries']:
                    debug_text += f"- {query[0]}: Room {query[1]} ({query[2]})\n"
            
            QMessageBox.information(self, "Database Info", debug_text)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error accessing database: {str(e)}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Resize background if it exists
        if hasattr(self, 'background_label'):
            try:
                bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "download (1)774.jpg")
                pixmap = QPixmap(bg_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding)
                    self.background_label.setPixmap(scaled_pixmap)
                    self.background_label.setGeometry(0, 0, self.width(), self.height())
            except:
                pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RoomLocatorApp()
    window.show()
    sys.exit(app.exec_())

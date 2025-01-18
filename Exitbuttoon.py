import sqlite3
import pyttsx3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.audio import SoundLoader
from kivy.uix.image import Image  # Import the Image widget
from transformers import AutoModelForCausalLM, AutoTokenizer

# Initialize text-to-speech engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # Selects the second voice

def speak(audio):
    """Speaks the provided audio string."""
    engine.say(audio)
    engine.runAndWait()

# Database setup
def setup_database():
    """Creates the database and table if not already exists."""
    with sqlite3.connect("room_locator.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                room_number INTEGER NOT NULL
            )
        """)
        conn.commit()

def save_to_database(name, room_number):
    """Saves user data to the database."""
    with sqlite3.connect("room_locator.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, room_number) VALUES (?, ?)", (name, room_number))
        conn.commit()

# Chatbot setup using Hugging Face DialoGPT
model_name = "microsoft/DialoGPT-medium"  # DialoGPT model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

def chatbot_response(user_input):
    """Generates a chatbot response."""
    try:
        input_ids = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors="pt")
        chat_history_ids = model.generate(
            input_ids,
            max_length=200,
            pad_token_id=tokenizer.eos_token_id,
            temperature=0.7,
            top_k=50,
        )
        response = tokenizer.decode(chat_history_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
        return response
    except Exception as e:
        print(f"Error: {e}")
        return "Sorry, I couldn't process that. Can you try again?"

class MyApp(App):
    def build(self):
        self.title = 'Room Locator with Chatbot'
        self.icon = 'c:\\Users\\SIMT TECH\\Downloads\\download.png'  # App icon

        # Load sound for button clicks
        self.button_click_sound = SoundLoader.load('c:\\Users\\SIMT TECH\\Downloads\\game-start-6104.mp3')

        # Create the main layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Replace the video with an image that fills the screen
        self.image = Image(source='c:\\Users\\SIMT TECH\\Downloads\\download (1)774.jpg', 
                           size_hint=(1, 0.7), allow_stretch=True, keep_ratio=False)
        layout.add_widget(self.image)

        # Add introductory text
        intro_label = Label(
            text="Welcome to the Room Locator with Chatbot. Please enter your name.",
            size_hint_y=None, height=80,
            color=(0, 0, 0, 1),
            font_size='20sp',
            halign='center',
            valign='middle'
        )
        intro_label.bind(size=intro_label.setter('text_size'))
        layout.add_widget(intro_label)

        # Add input field for name
        self.name_input = TextInput(hint_text="Enter your name", size_hint_y=None, height=40)
        name_button = Button(text="Submit Name", size_hint_y=None, height=50)
        name_button.bind(on_press=self.store_name)

        layout.add_widget(self.name_input)
        layout.add_widget(name_button)

        # Chatbot interface (simplified room locator input)
        self.chat_input = TextInput(hint_text="Ask the chatbot anything, or enter your room number.", size_hint_y=None, height=40)
        self.chatbot_output = Label(text="", size_hint_y=None, height=80)
        chat_button = Button(text="Submit", size_hint_y=None, height=50)
        chat_button.bind(on_press=self.chatbot_query)

        layout.add_widget(self.chat_input)
        layout.add_widget(chat_button)
        layout.add_widget(self.chatbot_output)

        # Reset button to clear fields
        reset_button = Button(text="Reset", size_hint_y=None, height=50)
        reset_button.bind(on_press=self.reset_fields)
        layout.add_widget(reset_button)

        # Call speak function when the app starts
        speak("Hello and welcome to the Room Locator App! Please enter your name to begin.")

        return layout

    def play_button_click_sound(self):
        """Plays a sound when a button is clicked."""
        if self.button_click_sound:
            self.button_click_sound.play()

    def store_name(self, instance):
        """Store the user's name and update the UI."""
        self.play_button_click_sound()  # Play button click sound

        name = self.name_input.text.strip()
        if name:
            self.user_name = name
            self.name_input.text = ''
            speak(f"Hello, {self.user_name}. You can now ask about room locations or chat.")
        else:
            speak("Please enter a valid name.")

    def chatbot_query(self, instance):
        """Handles the chatbot query input."""
        self.play_button_click_sound()  # Play button click sound

        user_input = self.chat_input.text.strip()

        if user_input:
            if user_input.isdigit():  # If the input is a number, it's likely a room number query
                self.room_locator_query(int(user_input))
            else:  # Otherwise, treat it as a chatbot query
                response = chatbot_response(user_input)
                self.chatbot_output.text = response
                speak(response)

    def room_locator_query(self, room_number):
        """Provides the location based on room number."""
        result_text = ""  # Empty string to hold result message

        # Determine room location
        if 142 <= room_number <= 152:
            result_text = f"{self.user_name}, your room is on the First floor."
        elif 1 <= room_number <= 10:
            result_text = f"{self.user_name}, this is the Admin Block Room, not your room."
        elif 11 <= room_number <= 19:
            result_text = f"{self.user_name}, these rooms are allotted to PIHM Students."
        elif 20 <= room_number <= 90:
            result_text = f"{self.user_name}, your room is on the Ground Floor."
        elif room_number == 147:
            result_text = f"{self.user_name}, this room is the H.O.D's office."
        elif 201 <= room_number <= 256:
            result_text = f"{self.user_name}, your room is on the Second Floor."
        elif 301 <= room_number <= 356:
            result_text = f"{self.user_name}, your room is on the Third Floor."
        elif 401 <= room_number <= 456:
            result_text = f"{self.user_name}, your room is on the Fourth Floor."
        else:
            result_text = f"{self.user_name}, your room is not in our database. Please contact the admin."

        self.chatbot_output.text = result_text
        speak(result_text)

        # Save to database (using the stored name)
        save_to_database(self.user_name, room_number)

    def reset_fields(self, instance):
        """Resets the input fields and output label."""
        self.name_input.text = ''
        self.chat_input.text = ''
        self.chatbot_output.text = ''
        speak("All fields have been reset. You can enter new information")

if __name__ == '__main__':
    setup_database()  # Create the database if it doesn't exist
    MyApp().run()

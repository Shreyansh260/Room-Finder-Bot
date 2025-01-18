# Projects
#This is a project based on Room finding Using ChatBot without using API keys.
import os
import sqlite3
import pyttsx3
import wikipedia
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.audio import SoundLoader
from kivy.uix.image import Image
from transformers import AutoModelForCausalLM, AutoTokenizer

# Initialize text-to-speech engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)  # Select the second voice

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
model_name = "microsoft/DialoGPT-medium"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

def handle_system_commands(command):
    """Handles system commands like opening applications or files."""
    try:
        if "open notepad" in command.lower():
            os.system("notepad.exe")
            return "Opening Notepad."
        elif "open calculator" in command.lower():
            os.system("calc.exe")
            return "Opening Calculator."
        elif "show files" in command.lower():
            os.system("explorer.exe")
            return "Opening File Explorer."
        else:
            return "Sorry, I can't perform that system command."
    except Exception as e:
        return f"Error handling system command: {e}"

def handle_wikipedia_query(query):
    """Fetches a summary from Wikipedia based on the query."""
    try:
        result = wikipedia.summary(query, sentences=2)
        return result
    except wikipedia.DisambiguationError as e:
        return f"Your query is too ambiguous. Please be more specific. Suggestions: {e.options[:5]}"
    except wikipedia.PageError:
        return "No matching article found on Wikipedia."
    except Exception as e:
        return f"Error fetching Wikipedia data: {e}"

def chatbot_response(user_input):
    """Enhanced chatbot response to include system commands and Wikipedia queries."""
    if "open" in user_input.lower() or "show" in user_input.lower():
        return handle_system_commands(user_input)
    elif "who is" in user_input.lower() or "tell me about" in user_input.lower():
        query = user_input.replace("who is", "").replace("tell me about", "").strip()
        return handle_wikipedia_query(query)
    else:
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
        self.icon = 'c:\\Users\\SIMT TECH\\Downloads\\download.png'

       #Load sound for button clicks
        
  self.button_click_sound = SoundLoader.load('c:\\Users\\SIMT TECH\\Downloads\\game-start-6104.mp3')

  layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

  self.image = Image(source='c:\\Users\\SIMT TECH\\Downloads\\download (1)774.jpg', 
                           size_hint=(1, 0.7), allow_stretch=True, keep_ratio=False)
        layout.add_widget(self.image)

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

  self.name_input = TextInput(hint_text="Enter your name", size_hint_y=None, height=40)
        name_button = Button(text="Submit Name", size_hint_y=None, height=50)
        name_button.bind(on_press=self.store_name)

  layout.add_widget(self.name_input)
        layout.add_widget(name_button)
      self.chat_input = TextInput(hint_text="Ask the chatbot anything, or enter your room number.", size_hint_y=None, height=40)
        self.chatbot_output = Label(text="", size_hint_y=None, height=80)
        chat_button = Button(text="Submit", size_hint_y=None, height=50)
        chat_button.bind(on_press=self.chatbot_query)

   layout.add_widget(self.chat_input)
        layout.add_widget(chat_button)
        layout.add_widget(self.chatbot_output)

  reset_button = Button(text="Reset", size_hint_y=None, height=50)
        reset_button.bind(on_press=self.reset_fields)
        layout.add_widget(reset_button)

  speak("Hello and welcome to the Room Locator App! Please enter your name to begin.")

   return layout

   def play_button_click_sound(self):
        if self.button_click_sound:
            self.button_click_sound.play()

  def store_name(self, instance):
        self.play_button_click_sound()
        name = self.name_input.text.strip()
        if name:
            self.user_name = name
            self.name_input.text = ''
            speak(f"Hello, {self.user_name}. You can now ask about room locations or chat.")
        else:
            speak("Please enter a valid name.")

   def chatbot_query(self, instance):
        self.play_button_click_sound()
        user_input = self.chat_input.text.strip()
        if user_input:
            response = chatbot_response(user_input)
            self.chatbot_output.text = response
            speak(response)

  def reset_fields(self, instance):
        self.name_input.text = ''
        self.chat_input.text = ''
        self.chatbot_output.text = ''
        speak("All fields have been reset. You can enter new information.")

if __name__ == '__main__':
    setup_database()
    MyApp().run()

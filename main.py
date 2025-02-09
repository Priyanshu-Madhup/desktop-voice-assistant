import pygame
import numpy as np
import sounddevice as sd
import math
import threading
import speech_recognition as sr
import pyttsx3
import ollama
import google.generativeai as genai
import os
import subprocess
import webbrowser
import requests
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz

# Initialize Pygame
pygame.init()

# Window settings
WIDTH, HEIGHT = 600, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Syra Ai")
icon_image = pygame.image.load("syra_img.png")
pygame.display.set_icon(icon_image)

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)

# Function to capture microphone input
def get_audio_amplitude(indata, frames, time, status):
    global amplitude
    amplitude = np.linalg.norm(indata) * 500  # Increase the scaling factor

# Start recording
amplitude = 0
stream = sd.InputStream(callback=get_audio_amplitude)
stream.start()

def draw_gradient_background(screen, color1, color2, width, height):
    for i in range(height):
        color = [
            color1[j] + (color2[j] - color1[j]) * i // height
            for j in range(3)
        ]
        pygame.draw.line(screen, color, (0, i), (width, i))

def draw_3d_sphere(screen, x, y, radius, amplitude, width, height, color):
    for i in range(0, 360, 10):
        for j in range(0, 360, 10):
            theta = math.radians(i)
            phi = math.radians(j)
            r = radius + amplitude * 2 * math.sin(theta * 5) * math.cos(phi * 5)  # Double the amplitude effect
            x3d = r * math.sin(theta) * math.cos(phi)
            y3d = r * math.sin(theta) * math.sin(phi)
            z3d = r * math.cos(theta)
            scale = 500 / (500 + z3d)
            x2d = x + x3d * scale
            y2d = y + y3d * scale
            if 0 <= x2d < width and 0 <= y2d < height:  # Bounds checking
                pygame.draw.circle(screen, color, (int(x2d), int(y2d)), 2)

# Initialize the speech recognizer and text-to-speech engine
recognizer = sr.Recognizer()
tts_engine = pyttsx3.init()
tts_lock = threading.Lock()
tts_busy = False
tts_interrupted = False

# List available voices
voices = tts_engine.getProperty('voices')
for index, voice in enumerate(voices):
    print(f"Voice {index}: {voice.name}")

# Set the desired voice (e.g., change the index to select a different voice)
desired_voice_index = 1  # Change this index to select a different voice
tts_engine.setProperty('voice', voices[desired_voice_index].id)

# Function to listen for the wake word
def listen_for_wake_word():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            print("Listening for wake word...")
            audio = recognizer.listen(source)
            try:
                transcription = recognizer.recognize_google(audio)
                if "Jarvis" in transcription or "Sairah" in transcription or "Saira" in transcription or "Sayrah" in transcription or "Sayra" in transcription:
                    print("Wake word detected!")
                    with tts_lock:
                        global tts_busy, tts_interrupted
                        if tts_busy:
                            tts_interrupted = True
                            tts_engine.stop()
                        else:
                            tts_busy = True
                            tts_engine.say("How can I help you?")
                            tts_engine.runAndWait()
                            tts_busy = False
                    if not tts_interrupted:
                        listen_for_commands()
                    break
            except sr.UnknownValueError:
                continue

# Function to listen for commands
def listen_for_commands():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            print("Listening for your command...")
            audio = recognizer.listen(source)
            try:
                transcription = recognizer.recognize_google(audio, language="en-IN")
                if "Saira close" in transcription:
                    print("Exiting...")
                    with tts_lock:
                        global tts_busy
                        tts_busy = True
                        tts_engine.say("Goodbye!")
                        tts_engine.runAndWait()
                        tts_busy = False
                    pygame.quit()
                    break
                else:
                    print(f"Query: {transcription}")
                    get_response(transcription)
            except sr.UnknownValueError:
                if not tts_busy:
                    with tts_lock:
                        tts_engine.runAndWait()

# Function to get response from the chat bot
def get_response(prompt):
    #if "introduce yourself" in prompt or "tell me about yourself" in prompt or "tell me something about yourself" in prompt:
     #   give_intro()
    # Configure the Gemini model
    genai.configure(api_key="")#Enter your api key
    generation_config = {"temperature":0.9, "top_p":1, "top_k":1, "max_output_tokens":2048}
    model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)

    # Ask the Gemini model to determine the user's intent
    response = model.generate_content([f"Determine if the user is asking to open a file Return 1 if it's a file, 2 if it's an app. Return 3 if it's a website which needs to be opened on browser for example youtube or chatgpt and etc are websites but not apps. Return 4 if weather report or weather conditions prompt. Return 5 if there is a word 'time' in the prompt. Return 6 if prompt contains anything related to introduce yourself or give an introduction, Return 0 for general knowledge or general questions for example who is the ceo of of a company, etc otherwise. Prompt: {prompt}"])
    response_text = response.text.strip()

    # Extract the intent from the response
    if "1" in response_text:
        intent = 1
    elif "2" in response_text:
        intent = 2
    elif "3" in response_text:
        intent = 3
    elif "4" in response_text:
        intent = 4
    elif "5" in response_text:
        intent = 5
    elif "6" in response_text:
        intent = 6
    else:
        intent = 0

    if intent == 1:
        extract_file_name_and_search(prompt)
    elif intent == 2:
        open_app(prompt)
    elif intent == 3:
        open_browser(prompt)
    elif intent == 4:
        get_current_city_weather(prompt)
    elif intent == 5:
        get_time(prompt)
    elif intent == 6:
        give_intro(prompt)
    else:
        model = 'llama3.2:1b'
        model2 = 'qwen:1.8b'
            
        '''stream = ollama.chat(
            model=model2,
            messages=[{'role': 'user', 'content': "(Limit your response in 50-100 words)If this prompt involves asking anything about introduction or who created or how are you then always answer that your name is Syra and you were created by a Legendary developer named Priyanshu Madhup who is currently a Machine Learning developer and is right now a college student pursuing engineering in CMR Institute of Technology, India , if nothing such asked then continue normally : " + prompt}],
            stream=True,
        )
        response=""
        for chunk in stream:
            content = chunk['message']['content']
            response += content + ""
        print(f"Syra: {response.strip()}")
        tts_thread = threading.Thread(target=speak_response, args=(response.strip(),))
        tts_thread.start() '''
        # Collect all Llama-generated responses into a single string
        response = ""
        stream = ollama.chat(
            model=model,
            messages=[{'role': 'user', 'content': " (Limit your response in 50-100 words)always remember that your name is Syra Ai, and use that name when ever necessary in your responses, if nothing such asked then continue normallyand also remember Limit your responses in 100 words :" + prompt}],
            stream=True,
        )
        
        response = ""
        for chunk in stream:
            content = chunk['message']['content']
            response += content + ""
        
        # Print and speak the collected response
        print(f"Syra: {response.strip()}")
        tts_thread = threading.Thread(target=speak_response, args=(response.strip(),))
        tts_thread.start()

def speak_response(response):
    with tts_lock:
        global tts_busy, tts_interrupted
        tts_busy = True
        tts_interrupted = False 
        tts_engine.say(str(response).strip())
        tts_engine.runAndWait()
        tts_busy = False
        if tts_interrupted:
            print("Speech interrupted by wake word.")
   
    
def give_intro(prompt):
    model = 'qwen:1.8b'
    stream = ollama.chat(
        model=model,
        messages=[{'role': 'user', 'content': "Generate a message saying that your name is Syra who is basically an Ai model who was created by a Legendary Machine Learning Developer Mr.Priyanshu Madhup, who is currently pursuing his engineering in CMR Institute of Technology, Syra Ai was created on 2nd Feb, 2025 prompt : "+prompt}],
        stream=True,
    )
        
    response = ""
    for chunk in stream:
        content = chunk['message']['content']
        response += content + ""
    tts_thread = threading.Thread(target=speak_response, args=(response.strip(),))
    tts_thread.start()
    
def get_time(prompt):
    # Configure the Gemini model
    genai.configure(api_key="")#Enter your api key
    generation_config = {"temperature":0.9, "top_p":1, "top_k":1, "max_output_tokens":2048}
    model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)

    # Ask the Gemini model for the current time
    response = model.generate_content([f"What is location name in tis prompt, only write the name and nothing else, incase there is no location in prompt just write the word empty : {prompt}"])
    city_name = response.text.strip()
    if city_name == "empty":
        current_time = datetime.now().time()
    city_name = "Bangalore"
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.geocode(city_name)

    if location:
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
        
        if timezone_str:
            timezone = pytz.timezone(timezone_str)
            local_time = datetime.now(timezone)
            current_time =  f"Local Time in {city_name}: {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
        else:
            return "Timezone not found"
    else:
        return "City not found"

    # Print and speak the collected response
    print(f"Current Time: {current_time}")
    tts_thread = threading.Thread(target=speak_response, args=(current_time,))
    tts_thread.start()
        
def get_current_city_weather(prompt):
    response = requests.get("https://ipinfo.io/json")
    data1 = response.json()
    
    
    city_name = data1.get("city", "Unknown")
    genai.configure(api_key="")#Enter your api key
    generation_config = {"temperature":0.9, "top_p":1, "top_k":1, "max_output_tokens":2048}
    model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)

    # Ask the Gemini model to determine the user's intent
    response = model.generate_content([f"Determine if the city name is entered in the prompt, if the city name is entered then just write which city name is entered, don't write anything else if city name is not entered in the prompt and user has just asked about weather without mentioning the location then just write the word empty : {prompt}"])
    response = response.text.strip()
    if (str(response)=="empty" or str(response)=="Empty"):
        pass
    else:
        city_name = str(response)
    region = data1.get("region", "Unknown")
    country = data1.get("country", "Unknown")
    print(f"Current Location: {response}")
    API_KEY = ""#Enter your api key
    BASE_URL = "http://api.openweathermap.org/data/2.5/weather"
    url = f"{BASE_URL}?q={city_name}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data2 = response.json()
    # Check if the request was successful
    if data2.get("cod") != 200:
        print(f"Error: {data2.get('message', 'City not found')}")
        return
    # Extract weather details
    city_name = data2["name"]
    temp = data2["main"]["temp"]
    weather_desc = data2["weather"][0]["description"]
    humidity = data2["main"]["humidity"]
    wind_speed = data2["wind"]["speed"]
    
    genai.configure(api_key="")#Enter your api key
    generation_config = {"temperature":0.9, "top_p":1, "top_k":1, "max_output_tokens":2048}
    model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)

    response = model.generate_content([f"(write this report in 2-4 lines) This is the json file for weather report brief this report in one paragraph : "+str(data2)])
    
    model = 'llama3.2:1b' 
    #prompt = f"Generate a brief weather report for {city_name}. The temperature is {temp}°C with {weather_desc}. The humidity is {humidity}% and the wind speed is {wind_speed} m/s."
    
    stream = ollama.chat(
        model=model,
        messages=[{'role': 'user', 'content': str(response.text.strip())}],
        stream=True,
    )

    # Collect all LLaMA-generated responses into a single string
    response2 = ""
    for chunk in stream:
        content = chunk['message']['content']
        response2 += content + ""
    
    # Print and speak the collected response
    print(f"Weather Report: {response2.strip()}")
    tts_thread = threading.Thread(target=speak_response, args=(response2.strip(),))
    tts_thread.start()

def open_browser(prompt):
    genai.configure(api_key="")#Enter your api key
    generation_config = {"temperature":0.9, "top_p":1, "top_k":1, "max_output_tokens":2048}
    model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)

    response = model.generate_content([f"User has given this prompt in this prompt what do you think is the expected website name, only write the link so that i can directly paste in browser. Prompt: {prompt}"])

    web_name = response.text.strip()

    #Enter your chrome .exe directory and let %s be the suffix
    chrome_path = " %s"
    webbrowser.open(web_name)
    
def open_app(prompt):
    genai.configure(api_key="")#Enter your api key
    generation_config = {"temperature":0.9, "top_p":1, "top_k":1, "max_output_tokens":2048}
    model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)

    response = model.generate_content([f"User has given this prompt in this prompt what do you think is the expected app name, only write the app name also make sure that i need to pass this name in python subprocess module so give proper name, for example for ms word it is winword and for power point it is powerpnt, don't write anything else. Prompt: {prompt}"])

    app_name = response.text.strip()
    app_name = app_name + ".exe"
    print(f"Extracted app name: {app_name}")

    # Use subprocess to open the app
    try:
        subprocess.Popen([app_name])
    except FileNotFoundError:
        print(f"Error: {app_name} not found. Trying with full path.")
        # Enter Microsoft office apps directory
        app_path = f"C:\\Program Files\\Microsoft Office\\root\\Office16\\{app_name}"
        try:
            subprocess.Popen([app_path])
        except FileNotFoundError:
            print(f"Error: {app_path} not found.")

def extract_file_name_and_search(prompt):
    genai.configure(api_key="")#Enter your api key
    generation_config = {"temperature":0.9, "top_p":1, "top_k":1, "max_output_tokens":2048}

    model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)

    response = model.generate_content(["User has given this prompt in this prompt what do you think is the expected file name, only write the expected file name and nothing else: " + prompt])

    file_name = response.text.strip()
    print(f"Extracted file name: {file_name}")

    search_files_and_folders(file_name)

def search_files_and_folders(file_name):
    #Enter the directory path for which you want the model to search your files (Note that large directories require more processing time)
    directory = ""

    file_dict = {}

    for root, dirs, file_list in os.walk(directory):
        for file in file_list:
            file_dict[file] = os.path.join(root, file)
    print(file_dict)

    genai.configure(api_key="")#Enter your api key
    generation_config = {"temperature":0.9, "top_p":1, "top_k":1, "max_output_tokens":2048}

    model = genai.GenerativeModel("gemini-1.5-flash", generation_config=generation_config)

    response = model.generate_content(["This is what I am searching: " + file_name + ". Here is the list of file names: " + str(list(file_dict.keys())) + ". Only write the name of the closest match with file extension, nothing else."])

    closest_match = response.text.strip()
    print(f"Closest match: {closest_match}")

    # Ensure the closest match is in the dictionary
    if closest_match in file_dict:
        file_path = file_dict[closest_match]
        print(f"Opening file: {file_path}")
        try:
            os.startfile(file_path)
        except Exception as e:
            print(f"Failed to open file: {e}")

        tts_thread = threading.Thread(target=speak_response, args=(closest_match,))
        tts_thread.start()
        tts_thread.join()  # Wait for the TTS to finish before proceeding
    else:
        print(f"File {closest_match} not found.")

running = True
target_circle_size = 50
current_circle_size = 50

# Start the voice assistant in a separate thread
voice_assistant_thread = threading.Thread(target=listen_for_wake_word)
voice_assistant_thread.start()

while running:
    screen.fill(BLACK)  # Clear screen
    draw_gradient_background(screen, BLACK, BLUE, WIDTH, HEIGHT)

    # Smooth transition for circle size
    target_circle_size = int(50 + amplitude)
    current_circle_size += (target_circle_size - current_circle_size) * 0.1

    # Draw 3D vibrating sphere based on voice amplitude
    draw_3d_sphere(screen, WIDTH // 2, HEIGHT // 2, int(current_circle_size) * 2, amplitude / 10, WIDTH, HEIGHT, CYAN)  # Double the radius

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

    pygame.display.flip()  # Update screen

# Quit Pygame
pygame.quit()
import sys
sys.exit()
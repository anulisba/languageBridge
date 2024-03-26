from flask import Flask, render_template, jsonify, request
from transformers import MarianMTModel, MarianTokenizer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import random
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS
import os
import torch
from pymongo import MongoClient
import langid
import pygame
#from goto import with_goto
import json
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
# Replace these with your MongoDB connection details
mongo_host = "localhost"
mongo_port = 27017
database_name = "queryres"
collection_name_user = "userid"
collection_name_orders = "orders"

client = MongoClient(mongo_host, mongo_port)
db = client[database_name]
collection_user = db[collection_name_user]
collection_orders = db[collection_name_orders]
user_id = 60


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/process_message", methods=["POST"])
def process_message():
    data = json.loads(request.data)
    user_input = data.get("user_input", "")

    def record_audio(duration, filename):
        # Record audio for the specified duration
        print(f"Recording for {duration} seconds...")
        myrecording = sd.rec(int(duration * 44100), samplerate=44100, channels=2)
        sd.wait()
        sf.write(filename, myrecording, 44100)

    def translate_text(text):
        model_identifier = "Helsinki-NLP/opus-mt-ml-en"
        model = MarianMTModel.from_pretrained(model_identifier)
        tokenizer = AutoTokenizer.from_pretrained(model_identifier)
        input_text = text
        inputs = tokenizer(input_text, return_tensors="pt")
        # Generate output
        outputs = model.generate(**inputs)
        translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(translated_text)
        return translated_text
    def process_user_input(user_input):
        keywords = {
            "cancelling": ["cancel", "delete", "remove"],
            "booking": ["book", "buy", "reserve"]

            # Add more keywords as needed
        }

        for keyword, synonyms in keywords.items():
            if any(synonym in user_input.lower() for synonym in synonyms):
                return keyword

        return "enquiry"

    def book_order(order_details):
        existing_order = collection_orders.find_one({"user_id": order_details["user_id"]})

        if existing_order:
            return "Order already booked for this user ID. Thank you for using our service "
        else:
            db.orders.insert_one(order_details)
            return "Booking successful! Your order has been placed. Thank you for using our service"

    def cancel_order(user_id):
        existing_order = collection_orders.find_one({"user_id": user_id})

        if existing_order:
            collection_orders.delete_one({"user_id": user_id})
            return "Order cancellation successful. Thank you for using our service"
        else:
            return "No booking in this user ID. Thank you for using our service"

    def get_response(keyword):
        response = db.responses.find_one({"keyword": keyword})
        return (
            response["response"]
            if response
            else "Sorry, I couldn't find a suitable response. Please try again "
        )

    def user(userid,phone):
        if (userid != None):
            user1 = str(userid)
            l = ""
            for i in user1:
                l = l + " " + i
            response = "നിങ്ങളുടെ യൂസർ ഐഡി" + l + ".   നിങ്ങൾക്ക് എന്ത് സേവനങ്ങളാണ് വേണ്ടത്"
        else:
            response = "ക്ഷമിക്കണം ഈ ഫോൺ നമ്പറിൽ യൂസർ ഐഡി ഇല്ല. നിങ്ങളുടെ ഫോൺ നമ്പർ പുതുതായി രജിസ്റ്റർ ചെയ്തിട്ടുണ്ട്. കൂടുതൽ സേവനങ്ങൾക്കായി  വീണ്ടും വിളിക്കുക. "
            flag = False
            user123=random1(userid)
            user_data = {"phone_number": phone, "user_id": user123}
            db.userid.insert_one(user_data)
        return response

    def translate_to_malayalam(text):
        model_name = "Helsinki-NLP/opus-mt-en-ml"
        model = MarianMTModel.from_pretrained(model_name)
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        input_text= text
        inputs = tokenizer(input_text, return_tensors="pt")

        # Generate output
        outputs = model.generate(**inputs)
        translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(translated_text)
        return translated_text

    def text_to_speech(text, language='ml', output_file='output.mp3'):
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(output_file)

    def play_audio(file_path):
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():  # Wait for the playback to finish
            pygame.time.Clock().tick(10)  # Adjust the tick value as needed

        # After playback is complete, stop the mixer
        pygame.mixer.music.stop()
        pygame.mixer.quit()

    def check_user_phone_number(phone_number):
        user = collection_user.find_one({"phone_number": phone_number})
        if user:
            return user["user_id"]
        else:
            return None

    def random1(useri):
        id = random.randint(10, 9999)
        print(id)
        return id

    def main():
        flag = True
        filename = "recorded_audio.wav"
        duration = 3

        malayalam_text = "ലംഗ്വേജ് ബ്രിഡ്ജിലെക്ക് സ്വാഗതം.നിങ്ങളുടെ ഫോൺ നമ്പർ വ്യക്തമായി പറയുക"
        print("Malayalam Translation:", malayalam_text)
        text_to_speech(malayalam_text, language='ml', output_file='malayalam_output.mp3')
        pygame.mixer.init()
        pygame.mixer.music.load('malayalam_output.mp3')
        pygame.mixer.music.play()

        # Add a delay to allow the audio to play
        pygame.time.wait(5100)  # Adjust the delay as needed

        pygame.mixer.music.stop()
        rec = 9
        record_audio(rec, filename)
        print(f"Recording stopped. Audio saved as {filename}")
        r = sr.Recognizer()
        with sr.AudioFile(filename) as source:
            audio_data = r.record(source)
            try:
                malayalam_text = r.recognize_google(audio_data, language='ml-IN')
                print("Malayalam Text:", malayalam_text)
                phone_text = malayalam_text.split(" ")
                phone_no = "".join(phone_text)
                print(phone_no)

            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand the audio")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")
        user_id = check_user_phone_number(phone_no)
        response = user(user_id,phone_no)
        print(response)
        text_to_speech(response, language='ml', output_file='malayalam_output_new.mp3')
        play_audio('malayalam_output_new.mp3')
        if (user_id == None):
            return 0
        while flag:  # Introduce a loop to control the flow
            record_audio(duration, filename)
            print(f"Recording stopped. Audio saved as {filename}")

            r = sr.Recognizer()
            with sr.AudioFile(filename) as source:
                audio_data = r.record(source)
                try:
                    malayalam_text = r.recognize_google(audio_data, language='ml-IN')
                    print("Malayalam Text:", malayalam_text)
                    print("mal")
                    english_text = translate_text(malayalam_text)
                    print("English Translation:", english_text)
                    print("eng")
                except sr.UnknownValueError:
                    print("Google Speech Recognition could not understand the audio")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")

                response_keyword = process_user_input(english_text)

                if response_keyword == "booking":
                    order_details = {"user_id": user_id, "status": "booked"}
                    response = book_order(order_details)
                    print(response)
                    malayalam_text = translate_to_malayalam(response)
                    print("Malayalam Translation:", malayalam_text)
                    text_to_speech(malayalam_text, language='ml', output_file='malayalam_output_new.mp3')
                    play_audio('malayalam_output_new.mp3')  # Play the new audio
                    flag = False
                elif response_keyword == "cancelling":
                    user_id = user_id  # Replace with user identification logic
                    response = cancel_order(user_id)
                    print(response)  # Correct indentation

                    malayalam_text = translate_to_malayalam(response)
                    print("Malayalam Translation:", malayalam_text)
                    text_to_speech(malayalam_text, language='ml', output_file='malayalam_output_new.mp3')
                    play_audio('malayalam_output_new.mp3')  # Play the new audio
                    flag = False
                else:
                    response = get_response(response_keyword)
                    print(response)  # Correct indentation

                    malayalam_text = translate_to_malayalam(response)
                    print("Malayalam Translation:", malayalam_text)
                    text_to_speech(malayalam_text, language='ml', output_file='malayalam_output_new.mp3')
                    play_audio('malayalam_output_new.mp3')
                    # Set flag to exit the loop and continue from record_audio

    # Your existing logic for processing user input and generating a response goes here
    bot_response = main()
    return jsonify({'bot_response': bot_response})


if __name__ == "__main__":
    port = 60234  # Specify your desired port number
    app.run(debug=True, port=port)
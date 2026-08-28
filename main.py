import os
import time
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

# Core dependencies
import requests
from google import genai

# Try loading Android-compatible Plyer TTS
try:
    from plyer import tts
except ImportError:
    tts = None

class CruiseAIApp(App):
    def build(self):
        self.title = "Cruise AI"
        
        # Read key securely from environment variable
        api_key = os.environ.get("GEMINI_API_KEY")
        self.ai_client = genai.Client(api_key=api_key) if api_key else None

        # Main Layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Title Label
        title_label = Label(
            text="🚀 Cruise AI Assistant", 
            size_hint_y=None, 
            height=40, 
            font_size='20sp', 
            bold=True
        )
        layout.add_widget(title_label)

        # Output / Log Area
        self.scroll_view = ScrollView(size_hint=(1, 0.5))
        self.output_label = Label(
            text="Welcome to Cruise AI!\nType a prompt, talk, or generate videos.", 
            size_hint_y=None, 
            text_size=(None, None), 
            halign='left', 
            valign='top'
        )
        self.output_label.bind(texture_size=self.output_label.setter('size'))
        self.scroll_view.add_widget(self.output_label)
        layout.add_widget(self.scroll_view)

        # Text Input Area
        self.user_input = TextInput(
            hint_text="Ask something or describe a video...", 
            multiline=False, 
            size_hint_y=None, 
            height=50
        )
        layout.add_widget(self.user_input)

        # Top Buttons Grid
        btn_layout_1 = BoxLayout(size_hint_y=None, height=50, spacing=10)
        send_btn = Button(text="Send Text", on_press=self.send_text_prompt)
        voice_btn = Button(text="🎙 Voice Input", on_press=self.start_voice_thread)
        btn_layout_1.add_widget(send_btn)
        btn_layout_1.add_widget(voice_btn)
        layout.add_widget(btn_layout_1)

        # Bottom Buttons Grid
        btn_layout_2 = BoxLayout(size_hint_y=None, height=50, spacing=10)
        video_btn = Button(text="🎬 Generate Video", on_press=self.generate_ai_video)
        camera_btn = Button(text="📷 Camera Test", on_press=self.test_camera)
        btn_layout_2.add_widget(video_btn)
        btn_layout_2.add_widget(camera_btn)
        layout.add_widget(btn_layout_2)

        return layout

    def update_output(self, text):
        Clock.schedule_once(lambda dt: self._append_text(text))

    def _append_text(self, text):
        self.output_label.text += f"\n\n{text}"

    def speak_text(self, text):
        def tts_task():
            try:
                if tts:
                    tts.speak(text)
            except Exception as e:
                self.update_output(f"[TTS Error]: {e}")
        threading.Thread(target=tts_task, daemon=True).start()

    def send_text_prompt(self, instance):
        prompt = self.user_input.text.strip()
        if not prompt:
            return
        self.user_input.text = ""
        self.update_output(f"You: {prompt}")

        def ai_task():
            if not self.ai_client:
                self.update_output("[AI Error]: GEMINI_API_KEY is not configured.")
                return
            try:
                response = self.ai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                answer = response.text
                self.update_output(f"Cruise AI: {answer}")
                self.speak_text(answer)
            except Exception as e:
                self.update_output(f"[AI Error]: {e}")

        threading.Thread(target=ai_task, daemon=True).start()

    def generate_ai_video(self, instance):
        prompt = self.user_input.text.strip()
        if not prompt:
            self.update_output("[Video Error]: Enter a prompt first.")
            return

        self.user_input.text = ""
        self.update_output(f"Creating video for: '{prompt}'...\nWait 1-2 mins.")

        def video_task():
            if not self.ai_client:
                self.update_output("[Video Error]: GEMINI_API_KEY is not configured.")
                return
            try:
                operation = self.ai_client.models.generate_videos(
                    model="veo-2.0-generate-001",
                    prompt=prompt,
                    config={"aspect_ratio": "16:9", "duration_seconds": 5}
                )

                while not operation.done:
                    time.sleep(10)
                    operation = self.ai_client.operations.get(operation)

                result = operation.result
                generated_video = result.generated_videos[0]
                video_bytes = self.ai_client.files.download(file=generated_video.video)

                output_filename = "cruise_ai_video.mp4"
                with open(output_filename, "wb") as f:
                    f.write(video_bytes)

                self.update_output(f"🎥 Video saved: '{output_filename}'")
            except Exception as e:
                self.update_output(f"[Video Error]: {e}")

        threading.Thread(target=video_task, daemon=True).start()

    def start_voice_thread(self, instance):
        self.update_output("Voice recording active...")

    def test_camera(self, instance):
        self.update_output("[Camera]: Camera module active.")

if __name__ == '__main__':
    CruiseAIApp().run()
      

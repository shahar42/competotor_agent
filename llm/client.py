import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
from config.settings import settings
import base64

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    def generate(self, prompt: str, image_base64: str = None) -> str:
        """
        Generate content from prompt, optionally with an image.
        image_base64: Raw base64 string (with or without data URI prefix)
        """
        contents = [prompt]

        if image_base64:
            try:
                # Handle Data URI if present (e.g., "data:image/png;base64,ABCD...")
                if "base64," in image_base64:
                    _, image_data = image_base64.split("base64,", 1)
                else:
                    image_data = image_base64
                
                # Decode to bytes
                image_bytes = base64.b64decode(image_data)
                
                # Create image part (Assume JPEG/PNG, Gemini auto-detects mostly, but we can default to generic dict)
                # The SDK allows passing a dict for inline data
                image_part = {
                    "mime_type": "image/jpeg", # Default, or we could parse it from the header
                    "data": image_bytes
                }
                
                contents.append(image_part)
            except Exception as e:
                print(f"Error processing image: {e}")
                # Fallback to text-only if image fails
                pass

        response = self.model.generate_content(contents)
        return response.text
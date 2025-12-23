import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
from google.api_core.exceptions import ResourceExhausted
from config.settings import settings
import base64
import time
import re

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    def generate(self, prompt: str, image_base64: str = None) -> str:
        """
        Generate content from prompt, optionally with an image.
        image_base64: Raw base64 string (with or without data URI prefix)
        Handles 429 rate limit errors with automatic retry.
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

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(contents)
                return response.text
            except ResourceExhausted as e:
                # Extract retry delay from error message
                error_msg = str(e)
                retry_match = re.search(r'retry in ([\d.]+)s', error_msg)

                if retry_match:
                    retry_seconds = float(retry_match.group(1))
                else:
                    # Fallback: free tier = 5 req/min = 12s minimum
                    retry_seconds = 15

                if attempt < max_retries - 1:
                    print(f"Rate limit hit. Retrying in {retry_seconds:.1f}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(retry_seconds)
                else:
                    print(f"Rate limit hit. Max retries reached.")
                    raise
            except Exception as e:
                # Other errors - don't retry
                raise
# services/gemini_client.py

"""Service layer for Gemini API interactions.
Handles API key management (default vs user-provided), error handling (quota limits),
and provides a unified interface for content generation.
"""

import google.generativeai as genai
import streamlit as st
from google.api_core import exceptions

import google.generativeai as genai
import streamlit as st
from google.api_core import exceptions

class GeminiClient:
    def __init__(self, user_api_key=None):
        """Initialize with user key."""
        self.api_key = user_api_key
        self.is_default = False # No default key anymore
        if self.api_key:
            self._configure()

    def _configure(self):
        """Configure the genai library."""
        try:
            genai.configure(api_key=self.api_key)
        except Exception as e:
            # Configuration might fail if key is invalid format, but we handle calls later
            pass

    def generate_content(self, prompt, model_name="gemini-2.5-flash"):
        """Generate content with robust error handling."""
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text
        except exceptions.ResourceExhausted:
            return self._handle_quota_error()
        except Exception as e:
            # Catch-all for other errors, might be invalid key or other API issues
            if "429" in str(e) or "quota" in str(e).lower():
                return self._handle_quota_error()
            return f"❌ Error: {str(e)}"

    def _handle_quota_error(self):
        """Return the Bengali instruction message for quota limits."""
        return (
            "⚠️ **API Quota Limit Exceeded**\n\n"
            "The default API key has reached its usage limit. Please use your own API key.\n\n"
            "**Bengali Instruction:**\n"
            "আপনার ডিফল্ট API কী-এর সীমা শেষ হয়ে গেছে। অনুগ্রহ করে নিজের API কী ব্যবহার করুন।\n"
            "নতুন API কী পেতে ভিজিট করুন: [Google AI Studio](https://aistudio.google.com/)"
        )

    @staticmethod
    def get_active_key(st_session_state):
        """Helper to get the best available key from session state."""
        return st_session_state.get("api_key", None)

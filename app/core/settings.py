# app/core/settings.py

import os
from dotenv import load_dotenv

# Load variables from .env at project root
load_dotenv()

# Read Supabase environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")

class Settings:
	def __init__(self):
		self.SUPABASE_URL = SUPABASE_URL
		self.SUPABASE_ANON_KEY = SUPABASE_ANON_KEY
		self.SUPABASE_SERVICE_ROLE_KEY = SUPABASE_SERVICE_ROLE_KEY
		self.RAZORPAY_KEY_ID = RAZORPAY_KEY_ID
		self.RAZORPAY_KEY_SECRET = RAZORPAY_KEY_SECRET
		self.RAZORPAY_WEBHOOK_SECRET = RAZORPAY_WEBHOOK_SECRET

settings = Settings()
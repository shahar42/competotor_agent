import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "shaharisn1@gmail.com" # From your settings.py
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def test_smtp_auth():
    print(f"Testing auth for {SMTP_USER}...")
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("✅ SUCCESS: Authentication worked!")
        server.quit()
    except smtplib.SMTPAuthenticationError:
        print("❌ FAILED: Authentication error. Password incorrect or 2FA/App Password needed.")
    except Exception as e:
        print(f"❌ FAILED: Connection error: {e}")

if __name__ == "__main__":
    test_smtp_auth()

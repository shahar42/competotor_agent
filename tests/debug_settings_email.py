import sys
import os
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from config.settings import settings
import smtplib

def test_real_settings():
    print("--- DEBUG SETTINGS ---")
    print(f"User: '{settings.SMTP_USER}'")
    print(f"Pass Length: {len(settings.SMTP_PASSWORD)}")
    print(f"Pass Start: {settings.SMTP_PASSWORD[:3]}")
    print(f"Pass End: {settings.SMTP_PASSWORD[-3:]}")
    print("----------------------")

    try:
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.set_debuglevel(1)  # Show full SMTP conversation
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        print("✅ SUCCESS: Login accepted using app settings!")
        server.quit()
    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    test_real_settings()

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import settings

class EmailNotifier:
    def send_report(self, idea_description: str, competitors: list):
        """Send daily report with found competitors"""

        subject = f"🚨 New Competitors Found for Your Idea"

        body = f"""
<h2>Idea Monitoring Report</h2>
<p><strong>Your Idea:</strong> {idea_description}</p>

<h3>Similar Products Found:</h3>
<ul>
"""
        for comp in competitors:
            body += f"""
<li>
  <strong>{comp['name']}</strong> ({comp['similarity_score']}% similar)<br>
  Source: {comp['source']}<br>
  Price: ${comp['price'] or 'N/A'}<br>
  <a href="{comp['url']}">View Product</a><br>
  <em>Why similar:</em> {comp['reasoning']}
</li>
"""

        body += "</ul>"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = settings.RECIPIENT_EMAIL
        msg.attach(MIMEText(body, "html"))

        try:
            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            print("✓ Email sent successfully")
        except Exception as e:
            print(f"✗ Email error: {e}")

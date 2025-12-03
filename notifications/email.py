import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import settings

logger = logging.getLogger(__name__)

class EmailService:
    def send_alert(self, to_email: str, idea_title: str, competitors: list):
        """
        Send alert with found competitors.
        competitors: List of Competitor SQLAlchemy objects
        """
        subject = f"🚨 New Competitors Found for: {idea_title}"

        body = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Idea Validator Report</h2>
            <p>We found new potential competitors for your idea: <strong>{idea_title}</strong></p>
            <hr>
            <ul style="list-style: none; padding: 0;">
        """
        
        for comp in competitors:
            # Generate feedback links
            yes_link = f"{settings.API_BASE_URL}/webhooks/feedback?competitor_id={comp.id}&is_relevant=1"
            no_link = f"{settings.API_BASE_URL}/webhooks/feedback?competitor_id={comp.id}&is_relevant=0"
            
            price_display = f"${comp.price}" if comp.price else "N/A"
            
            body += f"""
            <li style="border: 1px solid #eee; margin-bottom: 15px; padding: 15px; border-radius: 8px;">
                <h3 style="margin-top: 0;">{comp.product_name}</h3>
                <p style="color: #666; font-size: 0.9em;">
                    <strong>Match:</strong> {comp.similarity_score}% | 
                    <strong>Source:</strong> {comp.source} | 
                    <strong>Price:</strong> {price_display}
                </p>
                <p><em>"{comp.reasoning}"</em></p>
                <p>
                    <a href="{comp.url}" style="background: #007bff; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px;">View Product</a>
                </p>
                <div style="margin-top: 10px; font-size: 0.85em; background: #f9f9f9; padding: 8px;">
                    <strong>Is this relevant?</strong> 
                    <a href="{yes_link}" style="color: green; margin-right: 10px;">✅ Yes (Correct)</a>
                    <a href="{no_link}" style="color: red;">❌ No (False Positive)</a>
                </div>
            </li>
            """

        body += """
            </ul>
            <p style="color: #999; font-size: 0.8em; text-align: center;">
                You are receiving this because you subscribed to Idea Validator.
            </p>
        </div>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = to_email
        msg.attach(MIMEText(body, "html"))

        try:
            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            logger.info(f"Email sent to {to_email}")
        except Exception as e:
            logger.error(f"Email error: {e}")
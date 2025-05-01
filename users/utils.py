from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings

def send_confirmation_email(user):
    # Génère un nouveau code à chaque envoi
    user.generate_confirmation_code()

    confirmation_link = f"http://localhost:8000/users/confirm_email/?token={user.confirmation_token}"

    subject = "Confirme ton adresse email ✉️"

    text_content = f"""
    Salut {user.username},

    Merci de t'être inscrit !
    
    Voici ton code de confirmation : {user.confirmation_code}

    Ou clique sur ce lien pour confirmer directement ton email :
    {confirmation_link}

    À très vite !
    """

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
        <div style="background-color: #ffffff; padding: 30px; border-radius: 10px; box-shadow: 0px 2px 8px rgba(0,0,0,0.05);">
            <h2 style="color: #333;">Bienvenue {user.username} 👋</h2>
            <p style="color: #555;">Merci de rejoindre notre aventure !</p>
            <p style="font-size: 16px; margin-top: 30px;">
                <strong>Ton code de confirmation :</strong><br>
                <span style="font-size: 24px; letter-spacing: 2px; color: #4CAF50;">{user.confirmation_code}</span>
            </p>
            <p style="margin-top: 40px;">
                Ou clique directement ici pour confirmer ton email :
            </p>
            <p>
                <a href="{confirmation_link}" style="display: inline-block; background-color: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none;">Confirmer mon email</a>
            </p>
            <p style="color: #888; font-size: 12px; margin-top: 50px;">Ce lien expirera dans 24 heures.</p>
        </div>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

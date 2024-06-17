import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class EmailSender:
    __slot__ = ('email', '__init', 'smtp_obj')
    def __init__(self, *, email: str, password: str, server: str, port: int = 587):
        self.email = email
        self.__init = False
        self.smtp_obj = None
        try:
            self.smtp_obj = smtplib.SMTP(server, port)
            self.smtp_obj.starttls()
            self.smtp_obj.login(self.email, password)
        except Exception as E:
            raise E
        self.__init = True
            
    def send_email_MIMEMultipart(self, msg: MIMEMultipart):
        if not self.__init:
            return 
        self.smtp_obj.sendmail(self.email, msg['To'], msg.as_string())
    
    def send_email(self, receiver: str, subject: str, body: str):
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = receiver
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        self.send_email_MIMEMultipart(msg)

    def generate_password_email(self, email_receiver, gen_password):
        self.send_email(
            email_receiver,
            "[DO NOT REPLY] Encore - Divert - Account Access Request",
            f"Thank you for signing up with Encore Services. Your Create Account request was accepted. \nPlease see below your randomly generated password.\nPassword: {gen_password}"
            )
        
if __name__ == "__main__":
    email_obj = EmailSender(
        email='dovertproject@outlook.com',
        password='Divert@Project123',
        server= 'smtp.office365.com',
    )
    email_obj.generate_password_email("samb@encore-environment.com","this_is_your_password")



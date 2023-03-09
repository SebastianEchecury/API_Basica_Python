import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart




def sendMail(to: str, passwordE: str):
    # Credenciales de Gmail
    email = 'employeesapi@gmail.com'
    password = 'bkmebvjsjdastjah'

    # Configuración del mensaje
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = to
    msg['Subject'] = 'New Password'
    body = 'Your password is ' + passwordE + '. \n Please change your temporary password.'
    msg.attach(MIMEText(body, 'plain'))

    # Enviar el correo electrónico
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email, password)
    text = msg.as_string()
    server.sendmail(email, to, text)
    server.quit()


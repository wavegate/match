from flask_mail import Message
msg = Message('test subject', sender=app.config['ADMINS'][0], recipients=['match0912@gmail.com'])
msg.body = 'text body'
msg.html = '<h1>HTML body</h1>'
mail.send(msg)
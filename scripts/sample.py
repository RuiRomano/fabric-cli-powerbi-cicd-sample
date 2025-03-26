from flask import Flask, request, jsonify
from flask_mail import Mail, Message

app = Flask(__name__)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@example.com'
app.config['MAIL_PASSWORD'] = 'your_password'
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@example.com'

mail = Mail(app)

@app.route('/send-email', methods=['POST'])
def send_email():
    data = request.get_json()
    if not data or 'to' not in data or 'subject' not in data or 'body' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    try:
        msg = Message(
            subject=data['subject'],
            recipients=[data['to']],
            body=data['body']
        )
        mail.send(msg)
        return jsonify({'message': 'Email sent successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
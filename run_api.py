from flask import Flask, render_template, request
import slack
app = Flask(__name__, template_folder="./frontend/build", static_folder="./frontend/build/static")

@app.route('/')
def serve_fronted():
    return render_template("index.html")

@app.route('/send-debug-message', methods=['POST'])
def send_debug_message():
    message = request.get_json().get("message")

    if message is None:
        return "VERY ERROR: No message received"

    response = slack.send_custom_to_active(message, debug=True)

    return response

@app.route('/send-real-message', methods=['POST'])
def send_real_message():
    message = request.get_json().get("message")

    if message is None:
        return "VERY ERROR: No message received"

    response = slack.send_custom_to_active(message, debug=False)

    return response

if __name__ == '__main__':
    app.run()

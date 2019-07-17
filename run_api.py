from flask import Flask, render_template, request
import slack
app = Flask(__name__, template_folder="./frontend/build", static_folder="./frontend/build/static")

@app.route('/')
def serve_fronted():
    return render_template("index.html")

@app.route('/send-debug-message', methods=['POST'])
def send_debug_message():
    message = request.get_json().get("message")

    if message is None or message == "":
        return "VERY ERROR: No message received"

    response = ""
    if "@against_user" in message:
        response = slack.send_match_messages(message, debug=True)
    else:
        response = slack.send_custom_messages(message, debug=True)

    if response is None or response == "":
        response = "No messages sent."
    
    return response

@app.route('/send-real-message', methods=['POST'])
def send_real_message():
    message = request.get_json().get("message")

    if message is None or message == "":
        return "VERY ERROR: No message received"
    
    response = ""
    if "@against_user" in message:
        response = slack.send_match_messages(message, debug=False)
    else:
        response = slack.send_custom_messages(message, debug=False)

    if response is None or response == "":
        response = "No messages sent."

    return response

if __name__ == '__main__':
    app.run()

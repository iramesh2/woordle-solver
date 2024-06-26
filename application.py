from flask import Flask, request, render_template, session, redirect, url_for
from flask_session import Session
from flask import send_from_directory
import woordle_methods

application = Flask(__name__)
application.config["SESSION_PERMANENT"] = False
application.config["SESSION_TYPE"] = "filesystem"
Session(application)

@application.route('/', methods=['GET', 'POST'])
def index():
    if 'history' not in session:
        session['history'] = []

    if 'possible_words' not in session or 'best_guess' not in session:
        session['possible_words'] = woordle_methods.read_in_file("possible_answers.txt")
        session['best_guess'] = woordle_methods.calculate_best_guess(session['possible_words'])
        session['win'] = False

    win_condition_met = False

    if request.method == 'POST':
        print(f"Form data received: {request.form}")
        print(request.form)  # Debug: print the form data received
        guess = request.form.get('guess', '').lower()
        feedback = request.form.get('feedback', '').lower()

        print(f"Before filtering, {len(session['possible_words'])} possible words.")
        session['possible_words'] = woordle_methods.filter_words(session['possible_words'], guess, feedback)
        print(f"After filtering, {len(session['possible_words'])} possible words.")

        if feedback == "ggggg":
            win_condition_met = True
            session['win'] = True
        else:
            session['win'] = False
            if guess and feedback:
                session['history'].append({'guess': guess, 'feedback': feedback})
                session['possible_words'] = woordle_methods.filter_words(session['possible_words'], guess, feedback)
                session['best_guess'] = woordle_methods.calculate_best_guess(session['possible_words'])

    if win_condition_met:
        message = "Congratulations! You've guessed the word correctly!"
    elif not session['possible_words']:
        message = "No possible words left. Start a new game."
        session.pop('possible_words', None)
        session.pop('best_guess', None)
        session['win'] = False
        session['history'] = []
    else:
        message = session['best_guess']

    session.modified = True
    return render_template('index.html', best_guess=message, win=session.get('win', False), history=len(session.get('history', [])))

@application.route('/undo', methods=['GET'])
def undo():
    if session.get('history'):
        session['history'].pop()
        session['possible_words'] = woordle_methods.read_in_file("possible_answers.txt")
        for action in session['history']:
            session['possible_words'] = woordle_methods.filter_words(session['possible_words'], action['guess'], action['feedback'])
        session['best_guess'] = woordle_methods.calculate_best_guess(session['possible_words'])
        session['win'] = False
    return redirect(url_for('index'))

@application.route('/restart', methods=['GET'])
def restart():
    session.pop('possible_words', None)
    session.pop('best_guess', None)
    session['win'] = False
    session['history'] = []
    return redirect(url_for('index'))

@application.route('/logo.png')
def logo():
    return send_from_directory(application.root_path, 'logo.png')

@application.errorhandler(400)
def bad_request(error):
    application.logger.error(f'Bad request: {request.url}, {request.data}, {error}')  # Log detailed error
    return f"Bad Request: {error}", 400

if __name__ == '__main__':
    application.run(debug=True)


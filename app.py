import os
import time
import helpers
from functools import wraps
from flask import ( Flask, flash, render_template, redirect,
                    request, session, url_for, abort)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

DEBUGGING = (os.environ.get("DEBUGGING").lower() == "true")
DEVELOPING = (os.environ.get("DEVELOPING").lower() == "true")

mongo = PyMongo(app)


def dev_only(func):
    """ Disables a wrapped route if not in development. """
    @wraps(func)
    def route(*args, **kwargs):
        if DEVELOPING:
            return func(*args, **kwargs)
        else:
            abort(404)
    return route


def game_time():
    """ Returns the length of a game in seconds """
    #Game length in seconds
    return 60;


def get_question():
    #Get the list of questions already asked
    question_list = helpers.get_question_list(session)

    #Get the first question
    question = list(mongo.db.questions.aggregate([
        #Excludes questions already asked
        { "$match" : { "_id" : {"$nin" : question_list} }},
        #Returns one random record
        { "$sample" : { "size" : 1 } }
    ]))

    #If we run out of questions, end the quiz
    if question == []:
        return redirect(url_for("gameover"))

    #Add the new question to the list
    helpers.add_question_to_list(session, question[0]["_id"])

    return question[0]


@app.route("/")
@app.route("/home")
def home():
    """ Homepage route. """
    helpers.clear_game_state(session)
    return render_template("home.html")


@app.route("/startgame", methods=["POST"])
def startgame():
    helpers.clear_game_state(session)

    if 'player_name' in request.form:
        session['player'] = request.form['player_name']
        session['player_score'] = 0
        session["game_start"] = time.time()

    else:
        return abort(400)

    return redirect(url_for("quiz"))


@app.route("/quiz")
def quiz():
    """ Quiz page route. """
    #Calculate game time remaining
    time_left = game_time() - (time.time() - session["game_start"])
    #If game time has expired, force gameover
    if time_left <= 0:
        redirect(url_for("gameover"))

    if 'sound' not in session:
        session['sound'] = True

    question = get_question()

    return render_template("quiz.html", question = question, time_left=time_left)


@app.route("/gameover")
@app.route("/leaderboard")
def gameover():
    """ Called when the game ends. """
    player = {}

    if 'player' in session and session['player']:
        if session['player_score'] > 0:
            #Store the player's score
            id = mongo.db.scores.insert_one({
                "player" : session["player"],
                "score" : session["player_score"],
                "time" : game_time()
            })
            #Where did the player place in the database?
            position = mongo.db.scores.count_documents({
                "score" : {"$gte":session["player_score"]}
            })
            player = {
                "name" : session['player'],
                "score" : session['player_score'],
                "place" : position,
                "id" : id.inserted_id
            }

    scores = mongo.db.scores.find().sort([
        ("score", -1),
        ("_id", 1)
    ]).limit(10)

    #clear session
    helpers.clear_game_state(session)

    return render_template("leaderboard.html", scores=scores, player=player)


@app.route("/AJAX_answer", methods=["POST"])
def AJAX_answer():
    """ Accepts an answer as an ajax request and returns if it is correct. """
    #Check that the game time hasn't elapsed
    time_left = game_time() - (time.time() - session["game_start"])
    if time_left <= 0:
        redirect(url_for("gameover"))

    response = {
        "correct_answer" : -1,
        "player_correct" : False,
        "player_score" : -1
    }
    correct = False

    question_list = helpers.get_question_list(session)
    if "answer" in request.json:
        question = mongo.db.questions.find_one( {"_id" : ObjectId(question_list[-1])} )
        #Did the player get the right answer?
        if (question['answer'] == int(request.json['answer'])):
            correct = True
            helpers.inc_score(session)
        response['correct_answer'] = question['answer']
        response['player_correct'] = correct
        response['player_score'] = session['player_score']

    #Get the next question
    question = get_question()

    response["next_question"] = {
        "question" : question["question"],
        "options" : [
            question["options"][0],
            question["options"][1],
            question["options"][2],
            question["options"][3]
        ]
    }

    return response


@app.route("/AJAX_sound", methods=["POST"])
def AJAX_sound():
    """ Toggles session sound on/off """
    if 'sound' not in session:
        session['sound'] = True

    session['sound'] = ('sound-toggle' in request.json)

    return {"sound-state" : session['sound']}


#
# Development only routes
#   These routes are to aid development and debugging and
#   will be switched off in production
#
@app.route("/add_question", methods=["GET", "POST"])
@dev_only
def add_question():
    """ Adds a single question to the database. """
    if request.method == "POST":
        new_question = {
            "question" : request.form["question"],
            "options" : [
                request.form["option_1"],
                request.form["option_2"],
                request.form["option_3"],
                request.form["option_4"]
            ],
            "answer" : int(request.form["answer"])
        }
        mongo.db.questions.insert_one(new_question)

    return render_template("add_question.html")


@app.route("/upload_questions")
@dev_only
def upload_questions():
    """ Bulk uploads questions in JSON format to the database. """
    """
    questions = [
    {
        "question" : "?",
        "options" : [
            "",
            "",
            "",
            ""
        ],
        "answer" :
    }]
    mongo.db.questions.insert(questions)
    """
    return "Uploaded questions"


@app.route("/all_questions")
@dev_only
def all_questions():
    """ Lists all the questions in the database. """
    questions = mongo.db.questions.find()
    return render_template("all_questions.html", questions=questions)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=DEBUGGING)

from bson.objectid import ObjectId

def get_question_list(session):
    """ Returns the list of questions already asked. """
    if "questions" not in session:
        session["questions"] = []

    id_list = []
    for id in session["questions"]:
        id_list.append(ObjectId(id))

    return id_list


def add_question_to_list(session,id):
    """ Adds a question to the list of asked questions. Takes ObjectId. """
    if "questions" not in session:
        session["questions"] = []

    tempList = session["questions"]
    tempList.append(str(id))
    session["questions"] = tempList


def get_score(session):
    """ Returns the player's current score """
    if "player_score" not in session:
        session["player_score"] = 0

    return session["player_score"]


def inc_score(session):
    """ Adds one to player score """
    if "player_score" not in session:
        session["player_score"] = 0

    session["player_score"] += 1


def clear_game_state(session):
    """ Clears persistent game state variables """
    session["player"] = ""
    session["player_score"] = 0
    session["game_start"] = 0
    session["questions"] = []

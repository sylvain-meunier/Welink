from flask import render_template, request, redirect, session, url_for as url_for_flask_ver
from requests_oauthlib import OAuth2Session
from code_team import *
import os


def url_for(url) :
    """ Raccourci pour la fonction url_for de flask """
    return url_for_flask_ver(url, _external=True, _scheme="https")

def update_session():
    """ Met à jour la session de l'utilisateur, puisque socketio refuse de la faire, même avec manage_session = False """
    try :
        for att, val in tempserversession[session['user_info']['_id']].items() :
            session['user_info'][att] = val
        session.modified = True
        tempserversession[session['user_info']['_id']] = {}
    except Exception as e :
        print("SERVER_ERROR", e) # for debugging purposes

tempserversession = {} # Permet de modifier la session Flask depuis les fonctions socket-io

# les variables app et socketio sont importées depuis code_team.py

# ================================== FLASK APP ================================== #

@app.route("/") # Création de la route pour la page d'accueil
def home() :
    """ Page principale qui redirige l'utilisateur vers le fil d'actualités dans la majorité des cas """
    if not "nextpage" in session :
        session['nextpage'] = "actu"
        session.modified = True
    if 'user_info' not in session :
        return redirect(url_for(".connection"))
    return redirect(url_for("."+session['nextpage']))

@app.route('/favicon.ico') # Création de la route pour l'icône à gauche du titre
def favicon():
    """ Permet d'afficher le magnifique icône de notre glorieuse application à côté du nom de la fenêtre """
    return app.send_static_file('favicon.ico')

@app.route("/connect") # Redirige vers la page de connexion à l'ent
def connection():
    """ User Authorization """
    ent = OAuth2Session(client_id, scope="userinfo", redirect_uri=app_url+"/callback")
    authorization_url, state = ent.authorization_url(authorization_base_url)

    # State is used to prevent CSRF, keep this for later.
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route("/callback", methods=["GET"])
def callback():
    """ Reçoit les informations de l'ent """
    if not 'oauth_state' in session :
        return redirect(url_for(".home"))
    ent = OAuth2Session(client_id, state=session['oauth_state'],  redirect_uri=app_url+"/callback")
    token = ent.fetch_token(token_url, client_id=client_id, client_secret=client_secret, code=request.args.get('code'))
    session['oauth_token'] = token

    return redirect(url_for('.checkuser')) # Vérifie si l'utilisateur est bien dans la BDD

@app.route("/checkuser")
def checkuser() :
    """ Gère la connexion de l'utilisateur """
    if not 'oauth_token' in session :
        return redirect(url_for(".home"))
    ent = OAuth2Session(client_id, token=session['oauth_token'])
    user_info_ent = ent.get('https://ent.iledefrance.fr/auth/oauth2/userinfo')
    try :
        user_info_ent = user_info_ent.json()
    except :
        return redirect(url_for(".home"))

    user_info = mongo.db.Users.find_one({'_id':user_info_ent['userId']}) # Récupère les infos sur l'utilisateur
    banned = False
    if user_info :
        banned = mongo.db.Banned.find_one({"_id" : user_info['_id']})

    else : # si aucune donnée n'est disponible
        session['ent_user_info'] = user_info_ent
        session.modified = True
        return redirect(url_for(".first_connection"))

    if banned :
        if 'user_info' in session :
            del session['user_info']
        end = datetime.strptime(banned['date'], fdate) + timedelta(days=banned["temps"])
        today = date(format1=fdate)
        today = datetime.strptime(today, fdate)
        if today - datetime.strptime(banned['date'], fdate) >= timedelta(days=banned["temps"]) :
            mongo.db.Banned.delete_one({"_id" : user_info['_id']})
            return redirect(url_for(".home"))
        return render_template('banned.html', end = date(date=end, format1=fdate), reason=banned["raison"])
    session['user_info'] = user_info
    try :
        user_info['selfinterets'] = user_info['interets'].copy() # permet de ne pas confondre les centres d'intérêts de l'utilisateur et ceux d'un autre utilisateur lorsqu'un autre profil est visité.
        user_info['selfinterets'].sort()
        user_info['convs'] = get_conv(user_info['_id'])
        for attribute in ['notifon', "autoscroll"] :
            if not attribute in user_info : # par défaut, ces attributs sont définies à True.
                user_info[attribute] = True
    except :
        return redirect(url_for(".home"))
    if not user_info['_id'] in tempserversession :
        tempserversession[user_info['_id']] = {}
    if 'nextpage' in session :
        nextpage = session['nextpage'] # Retient la page vers laquelle rediriger l'tuilisateur
        del session['nextpage'] # Evite de toujours rediriger par défaut l'utilisateur vers cette même page
        session.modified = True
        return redirect(url_for('.'+nextpage)) # si elle existe, ramène l'utilisateur à la première page à laquelle il a essayé d'accéder (fil d'actualités par défaut)
    return redirect(url_for('.actu'))

@app.route("/profil", methods=["GET", "POST"])
@app.route("/profil/", methods=["GET", "POST"])
@app.route("/profil/<user_id>", methods=["GET", "POST"]) # Affiche le profil de l'utilisateur
def profile(user_id="none"):
    """ Affiche le profil d'un utilisateur """
    if not 'user_info' in session : # Teste si l'utilisateur est connecté
        session['nextpage'] = "profile" # permet de se rappeller de la page initiale
        session.modified = True
        return redirect(url_for('.home'))

    update_session()

    if user_id == "none" :
        return redirect(app_url + "/profil/" + session['user_info']['_id'])

    tprofil, user, blocked = "son_profile 3.0.html", session['user_info'], None
    if session['user_info']['_id'] != user_id :
        user = mongo.db.Users.find_one({'_id':user_id})
        if not user :
            return render_template("no_user.html", convcolor=convcolor, user=session['user_info'])
        tprofil = "autre profile 3.0.html"
        if 'convs' in session['user_info'] :
            user['convs'] = session['user_info']['convs'] # Permet d'afficher ses propres conversations privées et non celles de l'utilisateur
        user['selfinterets'] = session['user_info']['interets'] # de même pour les centres d'intérêt
        if 'notifs' in session['user_info'] :
            user['notifs'] = session['user_info']['notifs'] # idem pour les notifications
        if 'blocked' in session['user_info'] :
            blocked = user['_id'] in session['user_info']['blocked'] # Détermine si l'utilisateur a été bloqué ou non
    user['nbpost'] = mongo.db.Messages.count_documents({"userid":user['_id']})
    return render_template(tprofil, user = user, convcolor = convcolor, etat='actu', navbar="Fil d'actualités", birth=check_birthday(user['naissance']), blocked = blocked, gl_interets = gl_interets)

@app.route("/actu/", methods=['GET', 'POST'])
@app.route("/actu", methods=['GET', 'POST']) # Affiche le fil d'actualités
def actu():
    """ Affiche le fil d'actualités """
    if not 'user_info' in session : # Teste si l'utilisateur est connecté
        session['nextpage'] = "actu"
        session.modified = True
        return redirect(url_for('.home'))

    update_session()

    msgs = get_msg(session['user_info'], {"interets": {"$in": session['user_info']['interets']}})[::-1]
    return render_template("actu.html", user=session['user_info'], convcolor = convcolor, msgs=msgs, etat='profil', navbar="Mon profil", previous=None, maxtitre=limite_titre, maxcontenu=limite_contenu)

@app.route("/post", methods=["GET", "POST"])
@app.route("/post/<string:statut>", methods=["GET", "POST"])
@app.route("/post/<string:statut>/<string:msgid>", methods=["GET", "POST"])
def post_msg(statut='msg', msgid=None) :
    """ Permet de post un message ou un commentaire """
    if not 'user_info' in session : # Teste si l'utilisateur est connecté
        session['nextpage'] = "post_msg"
        session.modified = True
        return redirect(url_for('.home'))

    update_session()

    if not statut in ['com', 'msg'] :
        return redirect(url_for(".actu"))

    if request.method == "POST" :
        req = request.form
        infos = {}
        if statut =="msg" :
            for i in ['titre', 'contenu'] :
                infos[i] = req[i]
            infos['img'] = None
            infos['userid'] = session['user_info']['_id']
        elif statut == "com" and msgid :
            infos['contenu'] = req['contenu']
            infos['img'] = None
            infos['msgid'] = ObjectId(str(msgid))
            infos['userid'] = session['user_info']['_id']
        if infos :
            send_msg(statut, infos)
            # ATTENTION : envoyer notifications à toutes les personnes concernées
            # socketio => envoyer immédiatement la notif
            # update BDD pour afficher la notif à la prochaine maj (Fil d'actius (len(NOTIFS)))
        return redirect(url_for(".actu"))

    return render_template("post_creation.html", convcolor = convcolor, user=session['user_info'], previous=None, etat="actu", navbar="Fil d'actualités", check_birthday=check_birthday)

@app.route('/update/<string:vatype>/<string:value>', methods=['GET', "POST"])
def update_value(vatype, value) :
    """ Met à jour un message ou un utilisateur """
    if 'user_info' in session : # Teste si l'utilisateur est connecté
        update_session()
        if value == "undefined" :
            emit("alert_user", "Impossible de modifier ce message.\nEssayez de rafraîchir la page", namespace="/", room=session['user_info']['_id'])
            return redirect(url_for('.home'))
        if request.method == "POST" :
            req, updata = request.form, {}
            if vatype == "user" :
                if value == "interets" :
                    newinter = req['hidTest'].split(",")
                    if req['hidTest'] :
                        session['user_info']['interets'] = session['user_info']['selfinterets'] = updata['interets'] = newinter
                else :
                    session['user_info'][value] = updata[value] = req[value]

                session.modified = True
                if updata :
                    mongo.db.Users.update_one({'_id':session['user_info']['_id']}, { "$set": updata})
                return redirect(url_for('.profile'))
            else :
                session['nextpage'] = "actu"
                session.modified = True
                msg = mongo.db.Messages.find_one({'_id':ObjectId(str(value))})
                if vatype == "msg" :
                    updata = {}
                    newinter = req['hidTest'].split(",")
                    if newinter[0] :
                        updata['interets'] = newinter
                    updata['titre'] = req["titre"]
                    updata['contenu'] = req["contenu"]
                    mongo.db.Messages.update_one({'_id':ObjectId(str(value))}, { "$set": updata})
                elif vatype == "com" :
                    updata = {}
                    updata['contenu'] = req["contenu"]
                    mongo.db.Messages.update_one({'_id':ObjectId(str(value))}, { "$set": updata})
                return redirect(url_for('.home'))
        elif vatype in ('msg', 'com') :
            session['nextpage'] = "actu"
            session.modified = True
            msg = mongo.db.Messages.find_one({'_id':ObjectId(str(value))})
            if msg['userid'] == session['user_info']['_id'] :
                tmsg = 'com_creation.html'
                if vatype == 'msg' :
                    tmsg = 'post_creation.html'
                return render_template(tmsg, convcolor=convcolor, user=session['user_info'], previous=msg, etat="actu", navbar="Fil d'actualités", check_birthday=check_birthday)
    else :
        session['nextpage'] = "actu"
        session.modified = True
    return redirect(url_for('.home'))

@app.route("/interet/<value>", methods=['GET', 'POST'])
def interet(value):
    """ Filtre le fil d'actualités avec un seul centre d'intérêt """
    if not 'user_info' in session : # Teste si l'utilisateur est connecté
        if value == "undefined" :
            emit("alert_user", "Impossible d'accéder à cette page.\nEssayez de rafraîchir la page", namespace="/", room=session['user_info']['_id'])
            return redirect(url_for('.home'))
        session['nextpage'] = "actu"
        session.modified = True
        return redirect(url_for('.home'))
    update_session()
    msgs = get_msg(session['user_info'], {"interets": {"$in": [value]}})[::-1]
    if not msgs :
        return render_template("no_msg.html", user = session['user_info'], convcolor = convcolor)
    return render_template("actu.html", convcolor = convcolor, user=session['user_info'], msgs=msgs, etat='profil', navbar="Mon profil", previous=None, maxtitre=limite_titre, maxcontenu=limite_contenu)

@app.route("/contact", methods=["GET", "POST"])
@app.route("/contact/", methods=["GET", "POST"])
def contact() :
    """ Permet de contacter notre équipe """
    if not 'user_info' in session : # Teste si l'utilisateur est connecté
        session['nextpage'] = "actu"
        session.modified = True
        return redirect(url_for('.home'))

    update_session()

    if request.method == "POST" :
            req = request.form
            contactus(req["sujet"], req["contenu"], session['user_info']['prenom'], session['user_info']['nom'], session['user_info']['_id'])
            return redirect(url_for('.actu'))

    return render_template("post_creation.html", convcolor = convcolor, previous=None, user=session['user_info'], contact=True, etat="actu", navbar="Fil d'actualités", check_birthday=check_birthday)

@app.route("/report/<userid>", methods=["GET", "POST"])
def report(userid) :
    """ Permet de reporter un utilisateur """
    if not 'user_info' in session : # Teste si l'utilisateur est connecté
        session['nextpage'] = "actu"
        session.modified = True
        return redirect(url_for('.home'))

    update_session()

    user = mongo.db.Users.find_one({"_id" : userid})
    if not user :
        return render_template("no_user.html", convcolor=convcolor, user=session['user_info'])

    if request.method == "POST" :
            req = request.form
            contactus("Report : " + req["sujet"], "Infos Report : " + user['prenom']  + " " + user['nom'] + " (" + userid + ")\n\n" + req["contenu"], session['user_info']['prenom'], session['user_info']['nom'], session['user_info']['_id'])
            return redirect(url_for('.actu'))

    return render_template("post_creation.html", convcolor = convcolor, previous="Report de " + user['prenom'] + " " + user['nom'], user=session['user_info'], contact=True, etat="actu", navbar="Fil d'actualités", reportid = user['_id'], check_birthday=check_birthday)

@app.route("/mp/<namespace>", methods=['GET', 'POST'])
def private_msg(namespace) :
    """ Permet d'afficher une conversation """
    skip = 0

    if request.method == 'POST' and 'skip' in request.form:
        skip = int(request.form['skip'])

    if 'user_info' in session : # Teste si l'utilisateur est connecté
        if namespace == "undefined" :
            emit("alert_user", "Impossible de se connecter à cette conversation.\nEssayez de rafraîchir la page", namespace="/", room=session['user_info']['_id'])
            return redirect(url_for('.home'))

        try :
            conv = mongo.db.Conversations.find_one({'_id' : ObjectId(namespace)})
        except :
            conv = None

        if not conv :
            return redirect(url_for('.actu'))

        update_session() # TONARI NO TO TO RO TOTORO TO TO RO TOTORO

        other_user = mongo.db.Users.find_one({"_id" : conv['users'][conv['users'][0]==session['user_info']['_id']]})

        if 'blocked' in other_user and session['user_info']['_id'] in other_user['blocked'] :
            return render_template("alert_user.html", msg = "Cet utilisateur vous a bloqué, vous ne pouvez plus lui envoyer de messages privés.", user = session['user_info'])

        if not conv["nom"] :
            nom = other_user["prenom"] + " " + other_user['nom']

        if conv and session['user_info']['_id'] in conv["users"] : # S'assure que seules les personnes dans la conversion y ont accès (et pas n'importe qui possédant l'identifiant)
            messages = get_privates(ObjectId(namespace), session['user_info'], skip=skip)

            try :
                del session['user_info']['notifs']['privs'][namespace] # Annule la notification pour cette conversation, si elle existe
                session.modified = True
            except : pass

            try :
                user = mongo.db.Users.find_one({'_id' : session['user_info']['_id']}) # De même dans la BDD
                del user['notifs']['privs'][namespace]
                mongo.db.Users.update_one({'_id' : user['_id']}, {"$set" : {"notifs" : user["notifs"]}})
            except : pass

            userid = mongo.db.Users.find_one({"_id" : conv['users'][conv['users'][0]==session['user_info']['_id']]})

            if skip > 0:
                return json.dumps(messages)

            return render_template("privconv.html", convcolor=convcolor, user=session['user_info'], msgs=messages, etat='actu', navbar="Fil d'actualités", maxcontenu=limite_contenu, var_namespace=namespace, convname=conv['nom'], convid=conv['_id'], useridpdp=userid)

    session['nextpage'] = "actu"
    session.modified = True
    return redirect(url_for('.home'))

@app.route("/firstconnection", methods=['GET', 'POST'])
def first_connection():
    """ Route de la première connexion """

    if not 'ent_user_info' in session :
        return redirect(url_for(".home"))

    if request.method == "POST" and request.form['hidTest'] :
        req = request.form
        user_info = {
            "interets" : req['hidTest'].split(','),
            'biographie':"Bonjour, c'est une belle journée dehors, non ?",
            'reseaux' : {"Discord":"Me#123", 'Twitter':'@Coucou'}
        }
        session['user_info'] = user_update(session['ent_user_info'], user_info) # Enregistre l'utilisateur
        session['user_info']['selfinterets'] = session['user_info']['interets'].copy()
        session['user_info']['selfinterets'].sort()
        session['user_info']['convs'] = [] # Initialise un tableau vide pour contenir les conversations de l'utilisateur
        session.modified = True
        tempserversession[session['user_info']['_id']] = {}
        del session['ent_user_info']
        return redirect(url_for('.actu')) # L'enregistrement est complété, l'utilisateur est redirigé vers son fil d'actualités

    return render_template('firstime.html', convcolor = convcolor, user=session['ent_user_info'], gl_interets = gl_interets) # L'utilisateur peut rentrer ses informations

@app.route("/create/conversation/<userid>/<convname>")
def create_conversations(userid, convname) :
    """ Permet de créer une conversation """
    if not 'user_info' in session or not mongo.db.Users.find_one({"_id" : userid}) : # Teste si l'utilisateur est connecté
        session['nextpage'] = "actu"
        session.modified = True
        return redirect(url_for('.home'))

    update_session()

    convid, new = create_conv([session['user_info']['_id'], userid])
    convid = str(convid)
    if new :
        if 'convs' in session['user_info'] :
            session['user_info']['convs'].append([convname, convid])
        else:
            session['user_info']['convs'] = [[convname, convid]]
        session['user_info']['convs'].sort()
        session.modified = True
        convname = session['user_info']['prenom'] + " " + session['user_info']['nom']
        for i in [userid] : # For now, we only have conversations with 2 users available
            emit("specificuserinfo", {"kind" : "conv", "convid" : convid, "convname" : convname}, namespace = "/", room = i, broadcast=True)
    return redirect(app_url + "/mp/" + convid)

# ================================== SOCKET-IO ================================== #

@socketio.on("connect")
def handle_connection(auth) :
    """ Fonction de connexion avec socketio """
    session['socketioconnected'] = True
    session.modified = True
    if 'user_info' in session :
        join_privates(session["user_info"], True)
        emit("senduserinfo", {"user" : session['user_info'], "maxcontenu" : limite_contenu, "maxtitre" : limite_titre, "colors" : colors, "convcolor" : convcolor, "maxnotifs" : maxnotifs})
        join_room(session['user_info']['_id'])

@socketio.on("disconnect")
def handle_disconnection() :
    """ Fonction de déconnexion avec socketio """
    if 'socketioconnected' in session :
        del session['socketioconnected']

@socketio.on('like')
def handle_like(id) :
    """ Permet de liker un message """
    likes, cond = pylike(id, session['user_info'])
    return id, str(likes), cond

@socketio.on('msginfo')
def handle_msginfo(id) :
    """ Renvoie les informations du message """
    msg = mongo.db.Messages.find_one({'_id':ObjectId(id)})
    user = mongo.db.Users.find_one({'_id' : msg['userid']})
    nom, prenom, profil = user['nom'], user['prenom'], user['profil']
    date = msg['date']
    img = msg['img']

    nbcomment = mongo.db.Messages.count_documents({"statut":"com", "msgid":ObjectId(id)})
    return id, nom, prenom, profil, nbcomment, img, date

@socketio.on("private_msg_send")
def handle_send_msgprv(content, namespace, img=None) :
    """ Permet d'envoyer un message privé """
    while content and content[-1] in ["\n", " "] :
        content = content[:-1]
    if content :
        infos = {
            'img' : img,
            'contenu' : content,
        }
        conv = mongo.db.Conversations.find_one({"_id" : ObjectId(namespace)})
        if not conv :
            return None
        for userid in conv['users'] :
            if userid != session['user_info']['_id'] : # Exclut l'utilisateur qui a envoyé le message
                user = mongo.db.Users.find_one({"_id":userid})
                if not "notifs" in user :
                    user['notifs'] = {}
                if not "privs" in user['notifs'] :
                    user['notifs']['privs'] = {namespace : 1}
                else :
                    if not namespace in user['notifs']['privs'] :
                        user['notifs']['privs'][namespace] = 1
                    elif user['notifs']['privs'][namespace] < maxnotifs :
                        user['notifs']['privs'][namespace] += 1
                mongo.db.Users.update_one({'_id' : userid}, {'$set' : {"notifs" : user['notifs']}})
        emit('private_msg_received', {'prenom' : session['user_info']['prenom'], 'nom' : session['user_info']['nom'], 'userid' : session['user_info']['_id'], 'contenu' : content, 'img' : img, 'namespace':namespace, "date" : "Maintenant"}, broadcast=True, to=namespace)
        pysend_private_msg(infos, namespace, session['user_info']['_id'])
    return namespace

@socketio.on("private_msg_deleted")
def handle_deleted_msgprv(id, namespace) :
    """ Permet de supprimer un message privé """
    id = ObjectId(id)
    msg = mongo.db.Privates.find_one({'_id' : id})
    if session["user_info"]['_id'] == msg["userid"] :
        pydelete_private_msg(id, namespace)

@socketio.on("askcomments")
def handle_askcomments(msgid, _id, color) :
    """ Renvoie les commentaires d'un message """
    comms = get_comm(ObjectId(msgid), session['user_info'])[::-1]
    color = colors[color==colors[0]] # alterne les couleurs de fond des commentaires
    return _id, comms, color, msgid, len(comms)

@socketio.on("send_comment")
def handle_send_comment(id, content) :
    """ Ajoute le commentaire dans la base de donnée """
    msg = mongo.db.Messages.find_one({"_id" : ObjectId(id)})
    if not msg :
        emit("when_msg_deleted", {"text" : "Le message que vous essayez de commenter a été supprimé.", "msgid" : id})
        return None, None, None
    user = mongo.db.Users.find_one({'_id' : msg['userid']})
    if 'blocked' in user and session['user_info']['_id'] in user['blocked'] :
        return 0, "blocked", 0
    com = False
    while content and content[-1] in ["\n", " "] :
        content = content[:-1]
    change = nb = False
    if content :
        nb = mongo.db.Messages.count_documents({'statut':"com", "msgid" : ObjectId(id)}) + 1
        change = 1
        infos = {
            'contenu' : content,
            "img" : None,
            "msgid" : ObjectId(id),
            "userid" : session['user_info']['_id']
        }
        com = send_msg("com", infos)
        for att in ['_id', 'msgid', 'like'] :
            com[att] = str(com[att])
            user = session["user_info"]
        com['prenom'] = check_birthday(user['naissance']) + user['prenom']
        com["nom"] = user['nom']
        com['date'] = current_date(com["date"])
        com["comms"] = "0"
    return com, change, nb

@socketio.on("delete_comment")
def handle_delete_comment(id, msgid) :
    """ Permet de supprimer un commentaire """
    msg = mongo.db.Messages.find_one({"_id" : ObjectId(id)})
    if not msg :
        emit("when_msg_deleted", {"text" : "Ce message a déjà été supprimé.", "msgid" : id})
        return None, None, None
    change = nb = False
    if msg and msg['userid'] == session['user_info']["_id"] :
        nb = mongo.db.Messages.count_documents({'statut':'com', 'msgid' : ObjectId(msgid)}) - 1
        change = 1
        mongo.db.Messages.delete_one({"_id" : ObjectId(id)})
    return msgid, change, max(nb, 0)

@socketio.on("postmsg")
def handle_postmsg(titre, contenu, interets) :
    """ Permet de poster un message """
    infos = {}
    infos['titre'] = titre
    infos['contenu'] = contenu
    infos['img'] = None
    infos['interets'] = interets
    infos['userid'] = session['user_info']['_id']
    send_msg("msg", infos)

@socketio.on("delete_msg")
def handle_delete_msg(msgid) :
    """ Permet de supprimer un post """
    strmsgid = msgid
    msgid = ObjectId(str(msgid))
    msg = mongo.db.Messages.find_one({'_id' : msgid})
    if not msg :
        emit("when_msg_deleted", {"text" : "Ce message a déjà été supprimé.", "msgid" : strmsgid})
        return
    if msg["userid"] == session['user_info']['_id'] : # S'assure que seul le créateur du message peut le supprimer
        delete_msg(msgid)

@socketio.on('removenotifs')
def handle_removenotifs(kind, id) :
    """ Supprime une notification (par exemple lorsque l'utilisateur a cliqué sur une conversation) """
    user = mongo.db.Users.find_one({'_id' : session['user_info']['_id']})
    try :
        del user["notifs"][kind][id]
        mongo.db.Users.update_one({"_id" : user["_id"]}, {"$set" : {"notifs" : user['notifs']}})
    except :
        pass
    if 'notifs' in user :
        tempserversession[user['_id']]['notifs'] = user['notifs']

@socketio.on("leave_conv")
def handle_leave_conv(convid) :
    """ Permet de quitter une conversation """
    lastuser = leave_conv(ObjectId(convid), session['user_info']['_id'])
    if lastuser :
        emit("conv_deleted", {"convname" : session['user_info']['prenom'] + " " + session['user_info']['nom'], "convid" : convid}, namespace="/", room=lastuser, broadcast=True)

    conv_remove(session['user_info']['convs'], convid)
    tempserversession[session['user_info']['_id']]['convs'] = session['user_info']['convs']

    return "/profil", convid # redirige l'utilisateur vers son profil

@socketio.on("conv_disapeared")
def handle_disapeared_conv(convid) :
    """ L'utilisateur n'est pas à l'origine de la disparition de la conversation """
    conv_remove(session['user_info']['convs'], convid)
    tempserversession[session['user_info']['_id']]['convs'] = session['user_info']['convs']

@socketio.on("autoscroll_upd")
def handle_auto_scroll_udate(value) :
    """ Permet de retenir les paramètres d'auto-scroll ou non de l'utilisateur dans les messages privés """
    tempserversession[session['user_info']['_id']]['autoscroll'] = value
    mongo.db.Users.update_one({"_id" : session['user_info']['_id']}, {"$set" : {"autoscroll" : value}})

@socketio.on("setnotifoptions")
def handle_set_notif_options(value) :
    """ Permet d'activer ou non les notifications """
    tempserversession[session['user_info']['_id']]['notifon'] = value
    mongo.db.Users.update_one({"_id" : session['user_info']['_id']}, {"$set" : {"notifon" : value}})

@socketio.on('blockuser')
def handle_block_user(userid, value) :
    """ Permet de (dé)bloquer un utilisateur """
    if value :
        if not 'blocked' in session['user_info'] :
            tempserversession[session['user_info']['_id']]['blocked'] = [userid]
            mongo.db.Users.update_one({'_id' : session['user_info']['_id']}, {"$set" : {"blocked" : [userid]}}) # l'utilisateur est désormais bloqué
        else :
            tempserversession[session['user_info']['_id']]['blocked'] = [userid] + session['user_info']['blocked']
            mongo.db.Users.update_one({'_id' : session['user_info']['_id']}, {"$addToSet" : {"blocked" : userid}}) # l'utilisateur est désormais bloqué
    else :
        if 'blocked' in session['user_info'] :
            try :
                if userid in session['user_info']['blocked'] :
                    session['user_info']['blocked'].remove(userid)
                    tempserversession[session['user_info']['_id']]['blocked'] = session['user_info']['blocked']
                if 'blocked' in tempserversession[session['user_info']['_id']] and userid in tempserversession[session['user_info']['_id']]['blocked'] :
                    tempserversession[session['user_info']['_id']]['blocked'].remove(userid)
            except : pass
        mongo.db.Users.update_one({'_id' : session['user_info']['_id']}, {"$pull" : {"blocked" : userid}}) # l'utilisateur n'est plus bloqué

@socketio.on("newconv")
def handle_new_conv(convid, convname) :
    """ Permet de rejoindre une nouvelle conversation """
    join_room(convid)
    if 'convs' in tempserversession[session['user_info']['_id']] : # assez illisible...
        tempserversession[session['user_info']['_id']]['convs'].append((convname, convid))
    else :
        if not 'convs' in session['user_info'] :
            tempserversession[session['user_info']['_id']]['convs'] = [(convname, convid)]
        else :
            tempserversession[session['user_info']['_id']]['convs'] = [(convname, convid)] + session['user_info']['convs'] # permet de ne pas oublier d'autres conversations en passant

@socketio.on('asksearch')
def handle_ask_search(contenu, kind, lastSeen) :
    """ Naive request on DB  """
    if kind in ['Aimé', "Commenté"] :
        sortie = []
        user = mongo.db.Users.find_one({'_id' : session['user_info']['_id']})
        if kind == "Aimé" :
            for _id in user['like'] :
                msg = mongo.db.Messages.find_one({'_id' : ObjectId(_id)})
                if msg and not msg in sortie :
                    for att in ['_id', 'msgid'] :
                        if att in msg :
                            msg[att] = str(msg[att]) # convertit les valeurs en str
                    sortie.append(msg)

        sortie.sort(key=lambda x: x['date'])
        return sortie[::-1], "Post"

    if not contenu :
        return ""

    sortie = []

    filtre = "nom"

    if kind == "Utilisateur" :
        bdd = mongo.db.Users
        attributes = ["nom", "prenom", "lycee", "niveau", '_id']
        att1 = None
        # att1 = "lycee"
        # statut = session['user_info'][att1] # Pour l'heure, ne recherche que les utilisateurs du même lycée

    else :
        bdd = mongo.db.Messages
        attributes = ["contenu", 'userid']
        filtre = "date"
        statut = "com"
        att1 = 'statut'

        if kind == "Message" :
            statut = "msg"
            attributes.append('titre')

    for k in attributes :
        if att1 :
            query = bdd.find({att1 : statut, k : {"$regex" : contenu, "$options" : "i"}})
        else :
            query = bdd.find({k : {"$regex" : contenu, "$options" : "i"}})
        try :
            for i in query :
                for att in ['_id', 'msgid'] :
                    if att in i :
                        i[att] = str(i[att]) # convertit les valeurs en str
                if 'prenom' in i :
                    i['prenom'] = check_birthday(i['naissance']) + i['prenom']
                if not i in sortie :
                    sortie.append(i)
        except :
            pass
    sortie.sort(key=lambda x: x[filtre])
    return sortie[::-1], kind

# ================================== LAUNCHING APP ================================== #

if __name__ == "__main__" :
    # This allows us to use a plain HTTP callback
    # os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = "1"

    app.secret_key = os.urandom(24)
    socketio.run(app, host='127.0.0.1', port=os.environ.get("PORT", 5000))

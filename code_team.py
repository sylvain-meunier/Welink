from flask_socketio import SocketIO, emit, join_room
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from flask_pymongo import PyMongo
from bson import ObjectId
from flask import Flask
import certifi
import pytz
import time

# Database, see : https://dbdiagram.io/d/60a3fa77b29a09603d15723b

# Useful variables
limite_mp = 100 # nombre limite de message privé par conversation
limite_titre = 115 # nombre limite de caractères pour le titre des posts
limite_contenu = 630 # nombre limite de caractères pour le contenu du message
contact_mail = "welink.ctl@gmail.com"
timezone = pytz.timezone("Europe/Paris")
colors = ["218, 207, 247", "222, 231, 142"] # couleurs alternées des commentaires
convcolor = "#adfff3" # Couleur des notifications dans la liste des conversations

with open("static/interests.array", 'r', encoding="utf-8") as file :
    gl_interets = file.read().splitlines() # Récupère les centres d'intérêt depuis le fichier interests.array

# App
app = Flask("Welink")
socketio = SocketIO(app)
app.config["MONGO_URI"] = 'secret'
mongo = PyMongo(app, tlsCAFile=certifi.where())

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": contact_mail,
    "MAIL_PASSWORD": "secret"
}

app.config.update(mail_settings)
mail = Mail(app)

app_url = "https://we-link.herokuapp.com"

client_id = 'secret'
client_secret = 'secret'
authorization_base_url = 'https://ent.iledefrance.fr/auth/oauth2/auth'
token_url = 'https://ent.iledefrance.fr/auth/oauth2/token'

# time
fdate = '%d/%m/%y'
fheure = '%H:%M:%S'
format = fdate + " " + fheure # format de la date

def date(date = None, format1 = format, stringified=True) :
    """ Renvoie la date du jour
    """
    if date :
        return date.strftime(format1)
    date = datetime.now(timezone)
    if stringified :
        date = date.strftime(format1)
    return date

def date_to_obj(date, format1 = format) :
    """ Renvoie un objet date à la place du str
    """
    return time.strptime(date, format1)

def cut_date(date, fdate=fdate, fheure=fheure) :
    """ Renvoie la date et l'heure séparément """
    date = date_to_obj(date)
    return time.strftime(fdate, date), time.strftime(fheure, date)

def current_date(msgdate) : # Fait par le KAMARAD au sapin (L'Homme à l'arbre), et l'homme au perceptron
    """ Renvoie la date selon un format plus 'humain' : "Aujourd'hui", 'Hier', ou la date elle-même en fonction de la date du jour """
    hoy = date(stringified=False)
    gestern = date(date = hoy - timedelta(days=1), format1=fdate)
    hoy = date(date=hoy, format1=fdate)
    tempmsgdate = msgdate
    msgdate, hour = cut_date(date=msgdate)
    if msgdate == hoy : return "Aujourd'hui à " + hour
    elif msgdate == gestern : return "Hier à " + hour
    return tempmsgdate

def check_birthday(naissance, format_naiss="%d-%m"):
    """ Renvoie un petit gâteau s'il s'agit du jour d'anniversaire de l'utilisateur, et une chaîne vide sinon """
    if naissance :
        today = date(format1=format_naiss)
        if today == naissance[:5] :
            return "\U0001f382 "
    return ""

def get_msg(user, filtre) :
    """ Filtre les données du l'utilisateur pour renvoyer les messages de son fil d'actualité """
    l = []
    filtre['statut'] = "msg"
    msg = mongo.db.Messages.find(filtre)
    for i in msg :
        author = mongo.db.Users.find_one({'_id' : i['userid']}) # trouve l'auteur du message
        i['nom'] = author['nom']
        i['prenom'] = check_birthday(author['naissance']) + author['prenom']
        if i['img'] : # Si le message contient une image, met à jour le chemin vers celle-ci
            i['img'] = i['userid'] + "/" + i['_id'] + "/" + i['img'] # sous la forme : static/id_utilisateur/id_message/nom_du_fichier
        i['date'] = current_date(i['date'])
        i['liked'] = liked(i['_id'], user)
        i["comms"] = mongo.db.Messages.count_documents({'statut':'com', 'msgid':i['_id']}) # compte le nombre de commentaires du post
        l.append(i)
    return l

def get_conv(userid) :
    """ Renvoie l'ensemble des conversations dont l'utilisateur fait partie """
    convs = []
    conv = mongo.db.Conversations.find({"users": {"$in" : [userid]}})
    for i in conv :
        nom = i['nom']
        if not nom : # si la conversation est privée
            user = mongo.db.Users.find_one({"_id" : i['users'][i['users'][0]==userid]})
            nom = user["prenom"] + " " + user['nom']
        convs.append([nom, str(i['_id'])])
    return convs

def get_comm(msgid, user) :
    """ Renvoie tous les commentaires associés au message """
    sortie = []
    comms = mongo.db.Messages.find({'statut':'com', 'msgid' : msgid}) # trouve les commentaires
    for k in comms :
        author = mongo.db.Users.find_one({'_id' : k['userid']}) # trouve l'auteur du message
        k['nom'] = author['nom']
        k['prenom'] = check_birthday(author['naissance']) + author['prenom']
        k['date'] = current_date(k['date'])
        k['comms'] = str(mongo.db.Messages.count_documents({'statut':'com', 'msgid':k['_id']})) # compte le nombre de messages
        for att in ["_id", "msgid"] : # transforme les objets ObjectId en str
            k[att] = str(k[att])
        if k['img'] : # Si le message contient une image, met à jour le chemin vers celle-ci
            k['img'] = k['userid'] + "/" + k['_id'] + "/" + k['img'] # sous la forme : static/id_utilisateur/id_message/nom_du_fichier
        k['liked'] = liked(k['_id'], user)
        sortie.append(k)
    return sortie

def join_privates(user, cond) :
    """ Permet à l'utilisateur de recevoir des informations du serveur à propos de ses conversations privés """
    if not cond :
        return
    conversations = mongo.db.Conversations.find({"users": {"$in": [user['_id']]}})
    for conv in conversations :
        join_room(str(conv['_id'])) # rejoint les groupes des conversations

def get_privates(namespace, user) :
    ''' Renvoie les messages privés associés à la conversation passée en argument '''
    sortie = []
    messages = mongo.db.Privates.find({'namespace' : namespace})
    for msg in messages :
        author = user
        if msg['userid'] != user["_id"] :
            author = mongo.db.Users.find_one({'_id' : msg["userid"]})
        msg['nom'] = author['nom']
        msg['prenom'] = check_birthday(author["naissance"]) + author['prenom']
        msg['date'] = current_date(msg['date'])
        sortie.append(msg)
    return sortie

def register(user_info) :
    """ Permet l'enregistrement de nouveaux utilisateurs
    DEPRECATED, see user_update
    """
    infos = {'biographie':"Bonjour, c'est une belle journée dehors, non ?", 'reseaux' : {"Discord":"Me#123", 'Twitter':'@Coucou'}}
    return user_update(user_info, infos) # Met à jour la BDD avec ces informations

def user_update(ent, infos) : # ent vient de l'ent, infos vient de la page d'inscription
    """ Met à jour la base de donnée des utilisateurs
    """
    if not 'birthDate' in ent or not ent['birthDate'] :
        ent['birthDate'] = "2021-07-05"
    for att in ['lastName', 'firstName', 'schoolName', 'level'] :
        if att not in ent or not ent[att] :
            ent[att] = ''
    user = {a:b for a, b in infos.items()}
    user['_id'] = ent['userId']
    user['nom'] = ent['lastName']
    user['prenom'] = ent['firstName']
    user['lycee'] = ent['schoolName']
    user['naissance'] = ent['birthDate'][8:] + ent['birthDate'][4:8] + ent['birthDate'][:4]
    user['niveau'] = ent['level']
    user['like'] = []
    user["notifs"] = {}
    user['autoscroll'] = user['notifon'] = True
    mongo.db.Users.insert_one(user)
    return user

def send_msg(statut, infos) :
    ''' Envoie un message ou commentaire '''
    msg = { a:b for a, b in list(infos.items()) + [('date', date()), ('statut', statut), ('like', 0)] } # intègre les informations au message
    mongo.db.Messages.insert_one(msg)
    return msg

def delete_msg(id) :
    ''' Supprime un message et les commentaires associés '''
    coms = mongo.db.Messages.find({"statut":"com", "msgid":id})
    for i in coms :
        delete_msg(i['_id'])
    mongo.db.Messages.delete_one({'_id' : id})

def pysend_private_msg(infos, convid, userid) :
    ''' Envoie un message privé '''
    convid = ObjectId(convid)
    msg = { a:b for a, b in list(infos.items()) + [('date', date()), ("namespace", convid), ('userid', userid)] } # intègre les informations au message
    mongo.db.Privates.insert_one(msg)
    msgs = mongo.db.Conversations.find_one({'_id' : convid})["msgs"] # récupère le nombre de messages dans la conversation
    if msgs >= limite_mp :
        mongo.db.Privates.delete_one({'namespace' : convid}) # supprime le message le plus ancien de la conversation (renvoyé en premier par Mongodb)
    else :
        mongo.db.Conversations.update_one({'_id' : convid}, { "$set": {'msgs' : msgs+1}})

def pydelete_private_msg(id, convid) :
    ''' DEPRECATED Supprime un message privé '''
    mongo.db.Privates.delete_one({'_id' : id})
    msgs = mongo.db.Conversations.find_one({'_id' : convid})["msgs"]
    mongo.db.Conversations.update_one({'_id' : convid}, { "$set": {'msgs' : max(msgs-1, 0)}})

def create_conv(users, name="") :
    """ Crée une conversation entre 2 utilisateurs et en renvoie l'identifiant """
    conv = mongo.db.Conversations.find_one({"users": {"$size" : 2, "$all" : users}})
    if conv : # si la conversation existe déjà
        return conv['_id'], 0
    return mongo.db.Conversations.insert_one({'nom' : "", "users" : users, 'msgs' : 0}).inserted_id, 1

def leave_conv(convid, userid) :
    """ Permet de quitter une conversation """
    conv = mongo.db.Conversations.find_one({'_id' : convid})
    if not conv :
        return
    if len(conv['users']) <= 2 : # Une conversation avec un seul utilisateur ne peut plus exister
        msgs = mongo.db.Privates.find({'namespace' : convid})
        for msg in msgs :
            mongo.db.Privates.delete_one({'_id' : msg['_id']}) # Supprime les messages de la conversation
        mongo.db.Conversations.delete_one({'_id' : convid}) # POOOONYO POOOONYO POOONYO SAKANA NO KO
        return conv['users'][conv['users'][0] == userid] # renvoie l'identifiant du dernier utilisateur dans la conversation
    else : # Pour l'heure, jamais utilisé
        conv['users'].remove(userid) # Retire l'utilisateur de la liste des participants...
        mongo.db.Conversations.update_one({'_id' : convid}, {"$set" : {"users" : conv['users']}}) # ... et met à jour la BDD
        # envoyer un message indiquant que l'utilisateur est parti

def conv_remove(convlist, convid) :
    """ Trouve et supprime la conversation parmi la liste passé en argument """
    if not convlist : return
    a = 0
    while a < len(convlist) and convlist[a][1] != convid :
        a += 1

    if a < len(convlist) :
        convlist.pop(a)

def pylike(id, user) :
    """ Met à jour la BDD lors d'un like """
    msg = mongo.db.Messages.find_one({'_id':ObjectId(id)})
    if not msg :
        return None, None
    user = mongo.db.Users.find_one({'_id':user['_id']}) # session.modified = True ne semble pas fonctionner...
    likes = msg['like']
    cond = True
    if id not in user['like'] :
        user['like'].append(id)
        likes += 1
    else :
        user['like'].remove(id)
        likes = max(0, likes-1)
        cond = False
    mongo.db.Users.update_one({'_id':user['_id']}, { "$set": {'like' : user['like']}})
    mongo.db.Messages.update_one({'_id':ObjectId(id)}, {"$set" : {"like" : likes}})
    return likes, cond

def liked(msgid, user) :
    """ Détermine si le message a été apprécié par l'utilisateur """
    user = mongo.db.Users.find_one({'_id':user['_id']})
    return str(msgid) in user['like']

def contactus(sujet, contenu, prenom, nom, id) :
    """ Envoie un mail à l'adresse : welink.ctl@gmail.com """
    nom = prenom + " " + nom
    msg = Message(subject=sujet, sender=(nom, contact_mail), recipients=[contact_mail], body="Message de " + nom + " (" + id + ")\n\n" + contenu)
    mail.send(msg)

def ban(userid, reason, time=15) :
    """ Ajoute l'ex-utilisateur à la table des Bannis """
    banned = {'_id' : userid, 'raison' : reason, 'temps' : time, 'date':date(format1=fdate)}
    try :
        mongo.db.Banned.insert_one(banned)
    except :
        mongo.db.Banned.update({"_id" : userid}, {"$set" : {'temps':time, "raison" : reason, "date":date(format1=fdate)}})

def delete_user(userid, tempserversession) :
    """ Supprime toute trace de l'utilisateur dans la BDD """
    msgs = mongo.db.Messages.find({"userid" : userid})
    for msg in msgs :
        delete_msg(msg['_id']) # Supprime les posts et commentaires
    convs = mongo.db.Conversations.find({"users": {"$in" : [userid]}})
    for conv in convs :
        leave_conv(conv['_id'], userid) # Supprime les conversations
    mongo.db.Privates.delete_many({"userid" : userid}) # Supprime les messages privés, si jamais il en restait
    mongo.db.Banned.delete_one({'_id' : userid}) # Supprime l'utilisateur de la table des Bannis
    mongo.db.Users.delete_one({'_id' : userid}) # Supprime l'utilisateur
    if userid in tempserversession :
        del tempserversession[userid]

# dummy msg
# msg_update("ec0ff54c-6e1a-44ef-9121-ce42ce810250", ['Art', 'Peinture'], "Aquarelle", "J'aime l'aquarelle.")

# dummy com
# send_msg("com", {"userid":"ec0ff54c-6e1a-44ef-9121-ce42ce810250", "msgid":ObjectId("60bbb9b570d0dcc13d5b938a"), "contenu":"Moi aussi !"})

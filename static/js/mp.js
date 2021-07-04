// import {templateMp} from "./jstemplates/templates.js"; // Not working :(

function templateMp(msg) {
    // Permet d'afficher un message privé
    var __result = "<div class=\"columns\" style=\"padding-bottom: 0px;\">\n            <div class=\"column\" style=\"padding-bottom: 0px;\">\n                <div class=\"media\" style=\"padding-bottom: 0px;\">\n                    <div class=\"media-content\" style=\"padding-bottom: 0px;\">\n                        <p class=\"is-size-6\" style=\"padding-bottom: 0px; word-break: break-word;\">";__result += "" + msg["date"];__result += " ";__result += "" + msg["prenom"];__result += " " + msg["nom"];__result += " :</p>\n                    </div>\n                </div>\n            </div>\n        </div>\n        <div class=\"block\" style=\"word-break: break-word;\">\n            ";__result += sanitize(msg["contenu"]);__result += "\n        </div>";
    return __result;
};

function update_btn_private(id){
    // S'assure que l'utilisateur peut toujours cliquer sur Entrée pour envoyer un message
    if (id){
        input = document.getElementById("textmp" + id)
        input.addEventListener("keyup", function(event) {
            if (event.keyCode === 13 && !event.shiftKey) {
                event.preventDefault();
                btn.click();
                }
            }
        );
        btn = document.getElementById("buttmp"+id)
        unloading(btn);
    }else{
        new AWN().confirm("Cette conversation a été supprimée", () => window.location.href = "/profil", false, {
            labels: {
                confirm : "Information"
            }
        })
    }
};

function add_msg_to_screen(data, userid){
    // Affiche un message privé dans la conversation
    if (data['userid'] === userid){
    update_btn_private(data['namespace']) // seulement si le message provient bien de l'utilisateur
    };
    span = document.createElement("div");
    span.innerHTML = templateMp(data);
    btn = document.getElementById("Answer24Priv")
    document.getElementById("privmsgbox").appendChild(span);
    if (window.scroll_var){
        btn.scrollIntoView();
    }
};

function send_private_msg(namespace){
    // Envoie un message privé
    var texteare = document.getElementById("textmp"+namespace);
    var btn = document.getElementById('buttmp' + namespace)
    loading(btn); // for some reason makes everything work
    socket.emit('private_msg_send', texteare.value, namespace, callback=update_btn_private)
    texteare.value = ""
};

function delete_priv_msg(btn, id, namespace){
    // Supprime un message privé
    btn.parentNode.parentNode.parentNode.remove();
    socket.emit("private_msg_deleted", id, namespace);
};

function auto_scroll(){
    // Active ou non l'auto-scroll
    window.scroll_var = !window.scroll_var;
    socket.emit("autoscroll_upd", scroll_var);
    return scroll_var;
};

function update_auto_scroll(btn){
    // Met à jour le texte du bouton
    if(auto_scroll()){
        btn.innerHTML = "Désactiver l'auto-scroll";
    }else{
        btn.innerHTML = "Activer l'auto-scroll";
    }
};
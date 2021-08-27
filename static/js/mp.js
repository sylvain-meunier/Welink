// import {templateMp} from "./jstemplates/templates.js"; // Not working :(

function templateMp(msg) {
    // Permet d'afficher un message privé
    var __result = "<div class=\"columns\" style=\"padding-bottom: 0px;\">\n            <div class=\"column\" style=\"padding-bottom: 0px;\">\n                <div class=\"media\" style=\"padding-bottom: 0px;\">\n                    <div class=\"media-content\" style=\"padding-bottom: 0px;\">\n                        <p class=\"is-size-6\" style=\"padding-bottom: 0px; word-break: break-word;\">";__result += "" + msg["date"];__result += " ";__result += "" + msg["prenom"];__result += " " + msg["nom"];__result += " :</p>\n                    </div>\n                </div>\n            </div>\n        </div>\n        <div class=\"block\" style=\"word-break: break-word;\">\n            ";__result += sanitize(msg["contenu"]);__result += "\n        </div>";
    return __result;
};

function update_btn_private(id){
    // S'assure que l'utilisateur peut toujours cliquer sur Entrée pour envoyer un message
    if (id){
        input = document.getElementById("new_pm_textarea")
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
    let msgbox = document.getElementById("temporary-pmsgbox")
    if (msgbox){
        msgbox.remove()
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
    var texteare = document.getElementById("new_pm_textarea");
    var btn = document.getElementById('buttmp' + namespace)
    loading(btn); // for some reason makes everything work
    socket.emit('private_msg_send', texteare.innerText, namespace, callback=update_btn_private)
    texteare.innerText = ""
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


/**
 * Permet de changer la taille d'une div en fonction de la taille des autres éléments
 * @param {Document}textarea
 * @param {Object[]}pm_container
 * @param {string}margin
 */
function resize_privmsgbox(element_to_change_height, elements_relative, margin="0px"){
    let height = 0
    elements_relative.forEach((element)=>{
        let style = window.getComputedStyle(element)
        height += parseInt(element.offsetHeight) + parseInt(style['margin-bottom'].replace('px', '')) + parseInt(style['margin-top'].replace('px', ''))
    })
    let element_to_change_height_style = window.getComputedStyle(element_to_change_height)
    element_to_change_height.style.height = 'calc(100vh - ' + height + 'px - ' + margin + ' - ' + (parseInt(element_to_change_height_style['margin-bottom'].replace('px', '')) + parseInt(element_to_change_height_style['margin-top'].replace('px', ''))) + 'px)'
}

/**
 * Rajoute des messages en fonctions d'une liste js de message
 * @param {Object[]}list
 * @param {Document}container
 */
function post_more_mp(list, container){
    list.forEach((element=>{
        let message_container = document.createElement('div')
        message_container.classList.add('message', element['class'])

        // On créer la partie haute du message
        let message_title_container = document.createElement('div')
        message_title_container.classList.add('columns')
        message_title_container.style.paddingBottom = '0px'

        let message_title = document.createElement('div')
        message_title.classList.add('column')
        message_title.style.paddingBottom = "Opx"

        let message_title_media_container = document.createElement('div')
        message_title_media_container.classList.add('media')
        message_title_media_container.style.paddingBottom = "Opx"

        let message_title_media = document.createElement('div')
        message_title_media.classList.add('media-content')
        message_title_media.style.paddingBottom = "Opx"

        let message_title_content = document.createElement('p')
        message_title_content.classList.add('is-size-6')
        message_title_content.style.paddingBottom = 'Opx'
        message_title_content.style.wordBreak = 'break-word'
        message_title_content.innerHTML = element['date'] + ' ' + element['nom'] + ' ' + element['prenom']

        message_title_media.appendChild(message_title_content)
        message_title_media_container.appendChild(message_title_media)
        message_title.appendChild(message_title_media_container)
        message_title_container.appendChild(message_title)
        message_container.appendChild(message_title_container)

        // On crée ensuite la partie basse du message
        let message_content = document.createElement('div')
        message_content.classList.add('block')
        message_content.style.wordBreak = 'break-word'
        message_content.innerHTML = element['contenu']

        message_container.appendChild(message_content)

        container.insertBefore(message_container, container.firstChild)

    }))
}

/**
 * @class
 * @classdesc Gestionnaire d'affichage de chargement sur à un utilisateur
 */
class loader{
    constructor() {
        this.chargement_container = document.createElement('div')
        this.chargement_container.classList.add('chargement')
    }
    /*Affiche un chargement*/
    start(){
        document.querySelector('html').appendChild(this.chargement_container)
        document.querySelector('body').style.pointerEvents = false
        document.querySelector('body').style.opacity = '0.5'
    }
    /*Supprime un chargement*/
    stop(){
        this.chargement_container.remove()
        document.querySelector('body').style.pointerEvents = true
        document.querySelector('body').style.opacity = '1'
    }
}
const client_loading = new loader()


window.onload = ()=>{
    const new_pm_textarea = document.getElementById('new_pm_textarea')
    const pm_container = document.getElementById('privmsgbox')
    const headband = document.getElementById('headband')
    const new_pm_container = document.getElementById('Answer24Priv')
    let observer = new MutationObserver(()=>{resize_privmsgbox(pm_container, [headband, new_pm_container])})
    observer.observe(new_pm_textarea, {childList: true, attributes: true})
    resize_privmsgbox(pm_container, [headband, new_pm_container])

    const pagemaincontent = document.getElementById('pagemaincontent')
    pm_container.style.display = 'flex'
    pm_container.style.flexDirection = 'column-reverse'
    pagemaincontent.style.overflow = 'hidden'

    let loading = false
    pm_container.addEventListener('scroll', ()=>{
        if((pm_container.scrollHeight - pm_container.offsetHeight + pm_container.scrollTop) === 0 && !loading){
            // On empêche de charger les messages pendant qu'on les charge
            loading = true

            // On montre à l'utilisateur qu'on est en train de charger
            client_loading.start()

            let xhr = new XMLHttpRequest()
            let data = new FormData()
            xhr.onreadystatechange = ()=>{
                if(xhr.readyState === 4 && xhr.status === 200){
                    client_loading.stop()
                    post_more_mp(JSON.parse(xhr.responseText), pm_container)
                }
            }
            data.append('skip', pm_container.childElementCount)
            xhr.open('POST', '/mp/' + window.location.pathname.replace('/mp/', ''))
            xhr.send(data)
        }
    })
}
function set_globals(data){
    // Permet de définir les variables globales envoyées par le serveur
    window.user = data['user'] ;
    window.maxcontenu = data['maxcontenu'] ;
    window.maxtitre = data['maxtitre'] ;
    window.colors = data['colors'] ;
    window.convcolor = data["convcolor"] ;
    window.scroll_var = data['user']['autoscroll'] ;
    window.notifon = data['user']['notifon'] ;
    window.maxnotifs = data['maxnotifs']
}

function loading(btn){
    // Marque l'élément comme étant en train de charger
    if (btn){
        btn.classList.add("is-loading");
        btn.classList.add("is-static");
    }
};

function unloading(btn){
    // Réaffiche l'élément sans le chargement
    if (btn){
        btn.classList.remove("is-loading");
        btn.classList.remove("is-static");
    }
};

function replace_convs(){
    // Place les dernières conversations qui ont reçu un message en haut de la liste
    // notification({'namespace':'60e33e5349bc95d6253d6dd4'})
    const userlist = document.getElementById("userconversationslist");
    let ind = 0, curind = 0, maxi = userlist.children.length;
    while (curind < maxi) {
        if (ind < maxi && userlist.children[curind].firstChild.style.backgroundColor){
            userlist.insertBefore(userlist.children[curind], userlist.children[ind]);
            ind++;
        };
        curind++;
    };
};

function notification(data){
    // Gère les notification
    if (data['namespace']){
        var conv = document.getElementById("listebandeauconv" + data['namespace']);
        conv.style.backgroundColor = convcolor;
        amount = conv.getAttribute("data-amount")
        if (!amount){
            conv.setAttribute("data-amount", "1");
        }else{
            amount = parseInt(amount)
            if(amount === maxnotifs || amount === maxnotifs.toString() + "+"){
                conv.setAttribute("data-amount", maxnotifs.toString() + "+");
            }else{
                amount++;
                conv.setAttribute("data-amount", amount.toString());
            }
        };
        replace_convs()
        if (window.notifon){
            var notif = new AWN();
            var contenu = sanitize(data['contenu']).slice(0, 40)
            var titre = sanitize(data['prenom'] + " " + data['nom'])
            notif.info(contenu, {
                labels : {
                    info : titre,
                },
                icons : {
                    prefix : "<i class='far fa-bell fa-3x",
                    info : "",
                }
            });
            /*
            var div = document.createElement("div")
            div.classList.add("dropdown-item")
            div.innerHTML = titre
            var butt1 = document.createElement("button")
            butt1.innerHTML = contenu
            div.appendChild(butt1)
            var butt1 = document.createElement("button")
            butt1.classList.add("delete")
            butt1.onclick = function(){ delete_notification(this.parentElement); }
            div.appendChild(butt1)
            document.getElementById("dropdownlistnotifications").appendChild(div)
            */
        }
    };
};

function received_private_msg(data){
    // Affiche le message privé ou envoie une notification selon la page que consulte l'utilisateur
    writemsg = document.getElementById("new_pm_textarea");
    if (writemsg && writemsg.getAttribute("namespace") === data['namespace']){
        add_msg_to_screen(data) // affiche le message
        socket.emit("removenotifs", "privs", data['namespace'])
    }else{
        notification(data);
    }
};

function insertAfter(newNode, existingNode) {
    // Permet d'insérer un élément après un autre (USELESS ?)
    existingNode.parentNode.insertBefore(newNode, existingNode.nextSibling);
};

function alert_user(text){
    // Permet de transmettre un message à l'utilisateur
    new AWN().confirm(text, false, false, {
        labels: {
            confirm : "Information"
        }
    })
};

function sanitize(string) {
    // Retire les éventuels éléments du string qui pourraient contenir du HTML
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": "’",
        "/": '&#47;',
    };
    const reg = /[&<>"'/]/ig;
    return string.replace(/[<]br[^>]*[>]/gi, '\n').replace(reg, (match)=>(map[match])).replace(/(?:\r\n|\r|\n)/g, '<br>');
};

function redirect_user(url, convid){
    // Redirige l'utilisateur vers une autre page
    window.location.href = url
    if (convid){ // Permet aussi de supprimer une conversation côté client lorsque celle-ci n'existe plus côté serveur
        document.getElementById("listebandeauconv"+convid).remove()
    }
};

function leave_conv(convid, convname){
    // Permet de quitter une conversation
    notifier.confirm("Voulez-vous vraiment quitter la conversation : '" + convname + "' ?",
    () => {
      socket.emit("leave_conv", convid, callback=redirect_user);
      // mettre un écran de chargement
    }, function(){
    }, {
      labels: {
        confirm: 'Attention !',
        confirmCancel : "Annuler",
        confirmOk: "Supprimer"
      },
      icons : {
        confirm: "exclamation-triangle"
      }
    }
  )
};

function bandeausearch(){
    // Fonction de recherche depuis le bandeau
    loading(document.getElementById("bandeauresearchbutton"));
    select = document.getElementById("selectfiltermsg")
    entry = document.getElementById("bandeauresearchbar");
    try{
        if (entry.value === msgfilters && select.value === searchkind){
            unloading(document.getElementById("bandeauresearchbutton"));
            return false; // Evite que les résultats ne soient affichés plusieurs fois
        }
    }catch{};
    window.searchkind = select.value
    socket.emit("asksearch", entry.value, searchkind, null, callback=set_result_search);
    window.msgfilters = entry.value;
    window.lastsearchid = null
    document.getElementById("pagemaincontent").innerHTML = '<title>Welink | Recherche</title><div id="searchresultdiv" class="box"></div>'
};

function search_template_msg(data){
    // Template de post pour les recherches
    return "<p><figure class=\"image is-64x64\"><a href=\"/profil/" + data["userid"] + "\"><img class=\"is-rounded\" src=\"https://ent.iledefrance.fr/userbook/avatar/" + data["userid"] + "?thumbnail=100x100\" title=\"Voir le profil\"></a></figure>" + sanitize(data['titre']) + "</p>" + "<p>" + sanitize(data['contenu']) + "</p>"
};

function search_template_com(data){
    // Template de commentaire pour les recherches
    return "<p><figure class=\"image is-64x64\"><a href=\"/profil/" + data["userid"] + "\"><img class=\"is-rounded\" src=\"https://ent.iledefrance.fr/userbook/avatar/" + data["userid"] + "?thumbnail=100x100\" title=\"Voir le profil\"></a></figure>" + sanitize(data['contenu']) + "</p>"
};

function search_template_user(data){
    // Template d'utilisateur pour les recherches
    data['prenom'] += " ";
    return "<a href=\"/profil/" + data["_id"] + "\"><div><p><figure class=\"image is-64x64\"><img class=\"is-rounded\" src=\"https://ent.iledefrance.fr/userbook/avatar/" + data["_id"] + "?thumbnail=100x100\" title=\"Voir le profil\"></figure>" + data['prenom'] + data['nom'] + "</p>" + "<p>" + sanitize(data['lycee']) + "</p></div></a>"
};

function set_result_search(results, kind){
    // Affiche les résultats de la recherche
    if (!(typeof results !== 'undefined' && results.length > 0)){
        var div = document.createElement("div")
        div.innerHTML = "Votre recherche n'a retourné aucun résultat."
        document.getElementById("searchresultdiv").appendChild(div)
    }else{
        for (const result of results){
            var div = document.createElement("div")
            if (kind === "Utilisateur"){
                div.innerHTML = search_template_user(result)
            }else if('titre' in result){
                div.innerHTML = search_template_msg(result)
            }else{
                div.innerHTML = search_template_com(result)
            }
            window.lastsearchid = result['_id']
            div.id = result['_id']
            div.classList.add('search_result')
            document.getElementById("searchresultdiv").append(div, document.createElement('hr'))
        }
    };
    unloading(document.getElementById("bandeauresearchbutton"))
};

function delete_notification(div){
    // Supprime une notification
    div.remove();
};

function setnotifoptions(){
    // Active ou non les notifications
    window.notifon = !window.notifon
    socket.emit("setnotifoptions", window.notifon)
    return window.notifon
};

function update_notif_opt(btn){
    // Met à jour l'affichage du bouton
    if (setnotifoptions()){
        btn.firstChild.classList.remove("fa-bell-slash")
        btn.firstChild.classList.add("fa-bell")
        new AWN().info("Les notifications ont été réactivées", {
            labels : {
                info : "Information"
            }
        })
    }else{
        btn.firstChild.classList.remove("fa-bell")
        btn.firstChild.classList.add("fa-bell-slash")
        new AWN().info("Les notifications ont été désactivées", {
            labels : {
                info : "Information"
            }
        })
    }
};

function update_interets(array){
    // Met à jour les centres d'intérêt de l'utilisateur
    document.getElementById("hidTest").value = array
    if (array.length === 0){
        let notifier = new AWN();
        notifier.warning("Vous devez sélectionner au moins un centre d'intérêt")
        return false;
    }else{
        return true;
    }
};

function conv_deleted(data){
    // Informe l'utilisateur qu'une conversation a été supprimée
    var convid = data['convid']
    var username = data['convname']
    socket.emit("conv_disapeared", convid)
    const temp1 = document.getElementById("new_pm_textarea")
    if (temp1 && temp1.getAttribute("namespace")){ // L'utilisateur est dans la conversation...
        new AWN().confirm("Cette conversation a été supprimée car " + username + " l'a quittée.", () => redirect_user("/profil", convid), false, {
            labels: {
                confirm : "Information"
            }
        })
    }else{ // ... ou pas
        document.getElementById("listebandeauconv"+convid).remove()
    }
};

function when_msg_deleted(data){
    // Si l'utilisateur tente de commenter un message qui n'existe plus, supprime ce message et prévient l'utilisateur
    alert_user(data['text']);
    msgid = data['msgid']
    var com = document.getElementById("msgdiv" + msgid);
    if (!com){
        com = document.getElementById("commentdiv" + msgid);
    };
    if (com){
        com.remove()
    }
}

function serverspeaking(data){
    // Reçoit des informations du serveur
    if (data['kind'] === "conv"){
        socket.emit("newconv", data['convid'], data['convname']) ;
        var li = document.createElement("li") ;
        li.innerHTML = '<a id="listebandeauconv' + data['convid'] + '" href="/mp/' + data['convid'] +'">' + data['convname'] + "</a>" ;
        document.getElementById("userconversationslist").appendChild(li) ;
    }
};

if (!window.socket){
    window.socket = io(); // Global connection with server
};

socket.on('private_msg_received', received_private_msg) ;
socket.on('senduserinfo', set_globals) ;
socket.on("alert_user", alert_user) ;
socket.on("specificuserinfo", serverspeaking) ;
socket.on("conv_deleted", conv_deleted) ;
socket.on("when_msg_deleted", when_msg_deleted)

window.onload = replace_convs ;

if (!window.convcolor){
    window.convcolor = "#adfff3";
}

let notifier = new AWN({});
let currentCallOptions = {}
function upd_msg(){
    // Met à jour les centres d'intérêt d'un message
    interets = dropdown.selected()
    if (interets.length === 0){
        let notifier = new AWN();
        notifier.warning("Vous devez sélectionner au moins un centre d'intérêt, ou bien votre message sera invisible")
        return false;
    }else{
        document.getElementById("hidTest").value = interets
        notifier.success("Votre message a bien été modifié", {
            labels : {
                success : "Succès !"
            },
            icons : {
                info : "check-circle fa-3x"
            }
        })
        return true;
    }
};

function post_msg(){
    // Permet de poster un message
    texteraea = document.getElementById("contenu")
    entry = document.getElementById("titre")
    interets = dropdown.selected()
    if (interets.length  === 0){
        let notifier = new AWN();
        notifier.warning("Vous devez sélectionner au moins un centre d'intérêt, ou bien votre message sera invisible")
    }else{
        notifier.confirm("Êtes-vous prêts à poster ?",
        function() {socket.emit("postmsg", entry.value, texteraea.value, interets, callback=post_redirect)},
        false,
        {
            labels: {
              confirm: 'Poster un message',
              confirmCancel : "Annuler",
              confirmOk: "Poster"
            },
          }
        )
    }
};

function post_redirect(){
    // Redirige l'utilisateur vers le fil d'actualités après avoir posté un message
    let notifier = new AWN();
    notifier.success("Votre message a bien été envoyé", {
        labels : {
            success : "Succès !"
        },
        icons : {
            info : "check-circle fa-3x"
        }
    });
    window.location.href = "/actu";
};
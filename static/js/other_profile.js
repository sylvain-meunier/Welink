function privconvget(btn, userid, convname){
  // Affiche la conversation ou la crée si elle n'existe pas
  loading(btn) // unloading btn is useless since user leaves the page
  window.location.href = "/create/conversation/" + userid + "/" + convname
};

function blockuser(btn, userid){
  // Permet de bloquer ou débloquer un utilisateur
    var confirmtext = 'Voulez-vous vraiment bloquer cette personne ?\nElle ne sera plus en mesure de vous envoyer de messages ou de commenter vos posts.'
    if (btn.innerHTML === "Débloquer cet utilisateur"){
        confirmtext = 'Voulez-vous débloquer cette personne ?'
    };
    notifier.confirm(confirmtext,
      () => {
        truly_blockuser(btn, userid);
      }, function(){
      return false;
      }, {
        labels: {
          confirm: 'Attention !',
          confirmCancel : "Annuler",
          confirmOk: "Confirmer"
        },
        icons : {
          confirm: "exclamation-triangle"
        }
      }
    )
};

function truly_blockuser(btn, userid){
  // Bloque ou débloque vraiment un utilisateur
    if (btn.firstChild.nodeValue === "Débloquer cet utilisateur"){
        btn.innerHTML = "Bloquer cet utilisateur";
        socket.emit("blockuser", userid, false)
    }else{
        btn.innerHTML = "Débloquer cet utilisateur";
        socket.emit("blockuser", userid, true)
    }
};
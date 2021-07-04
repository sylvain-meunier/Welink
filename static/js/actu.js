// import {comtemplate} from "templates"; // Still not working :(
// By the way, I dunno what a JS is

function comtemplate(com, color) {
  // Renvoie la mise en forme HTML d'un commentaire
  const rtext = sanitize(com["contenu"].slice(0,maxcontenu))
  const ftext = sanitize(com["contenu"].slice(maxcontenu))
  com['contenu'] = sanitize(com['contenu']);
  var __result = "<div class=\"box\" style=\"background-color: rgb(";__result += color;__result += ");\">\n  <div class=\"columns\">\n    <div class=\"column\">\n      <div class=\"media\">\n        <div class=\"media-left\">\n          <figure class=\"image is-64x64\">\n            <a href=\"/profil/";__result += "" + com["userid"];__result += "\">\n              <img class=\"is-rounded\" src=\"https://ent.iledefrance.fr/userbook/avatar/";__result += "" + com["userid"];__result += "?thumbnail=100x100\" title=\"Voir le profil\">\n            </a>\n          </figure>\n        </div>\n        <div class=\"media-content\">\n          <p class=\"is-size-5\">";__result += "" + com["prenom"];__result += " ";__result += "" + com["nom"];__result += "</p>\n          <p class=\"is-size-6\">";__result += "" + com["date"];__result += "</p>\n        </div>\n      </div>\n    </div>\n    <div class=\"column\">\n      <div class=\"columns\"> \n        <div class=\"column\">\n          <div class=\"is-pulled-right\">\n          </div>\n        </div>\n      </div>\n    </div>\n  </div>\n  <div class=\"box is-shadowless\">\n    ";if(com["img"]){__result += "\n    <div class=\"card-image\" style=\"padding-bottom: 5px; padding-top: 5px;\">\n      <figure class=\"photo du post\"> <!-- s'il y en a une -->\n        <img src=";__result += url_for("static");__result += " alt=\"Photo du post\">\n      </figure>\n    </div>\n    ";}__result += "\n    <div class=\"block\">\n      ";__result += "" + rtext;if(ftext){__result += "<a onclick=\"show_msg(this, '";__result += com["contenu"];__result += "', '";__result += rtext ;__result += "')\">...</a>";}__result += "\n    </div>\n    ";if(com["userid"] === user["_id"]){__result += "\n    <button class=\"button is-rounded is-static is-ghost\" disabled>\n      ";__result += "" + com["like"];__result += " <i class=\"fas fa-heart\" style=\"margin-left: 5px;\"></i>\n    ";} else if(com["liked"]){__result += "\n    <button class=\"button is-rounded is-ghost\" id=\"";__result += "" + com["_id"];__result += "\" onclick=\"jslike(this.id)\">\n      ";__result += "" + com["like"];__result += " <i class='fas fa-heart' style=\"color: #ffc162; margin-left: 5px;\"></i>\n    ";} else {__result += "\n    <button class=\"button is-rounded is-ghost\" id=\"";__result += "" + com["_id"];__result += "\" onclick=\"jslike(this.id)\">\n      ";__result += "" + com["like"];__result += " <i class=\"far fa-heart\" style=\"margin-left: 5px;\"></i>\n    ";}__result += "\n    </button>\n    <button class=\"button is-rounded is-ghost\" id=\"COMMENTAIRE";__result += "" + com["_id"];__result += "\" onclick=\"show_comment(this, '";__result += com["_id"];__result += "', this.id, '" + color + "')\">\n      ";__result += "" + com["comms"];__result += " <i class=\"fas fa-comments\" style=\"margin-left: 5px;\"></i>\n    </button>\n    <button class=\"button is-rounded is-ghost\" onclick=\"answer(this, '";__result += "" + com["_id"];__result += "', '" + color +"')\">\n      <i class=\"fas fa-comment-medical\"></i>\n    </button>\n    ";if(com["userid"] === user["_id"]){__result += "\n    <a href=\"/update/com/";__result += "" + com["_id"];__result += "\">\n      <button class=\"button is-rounded\">\n        Modifier\n      </button>\n    </a>\n    <form onsubmit=\"delete_comment('";__result += "" + com["_id"];__result += "', '" + com['msgid'] + "') ; return false;\" style=\"display: inline;\">\n      <button type=\"submit\" class=\"button is-danger\">\n        Supprimer\n      </button>\n    </form>\n    ";}__result += "\n  </div>\n</div>";
  return __result;
};

function update_amount_comment(msgid, change, value){
  // Met à jour le nombre de commentaires d'un message
  if (change){
    var btn = document.getElementById("COMMENTAIRE"+msgid)
    btn.innerHTML = value.toString() + "<i class='fas fa-comments' style='margin-left: 5px;'></i>"
  };
};

function delete_comment(id, msgid){
  // Demande à l'utilisateur s'il veut supprimer un commentaire
  notifier.confirm('Voulez-vous vraiment supprimer ce commentaire ?\nCela supprimera également tous les commentaires associés.',
    () => {
      truly_delete_comment(id, msgid);
    }, function(){
    return false;
  }, {
    labels: {
      confirm: 'Attention !',
      confirmCancel : "Annuler",
      confirmOk: "Supprimer"
    },
    icons : {
      confirm: "exclamation-triangle"
    }
  })
};

function truly_delete_comment(id, msgid){
  // Supprime un commentaire
  span = document.getElementById("commentdiv" + id)
  if (span){
    span.remove();
    socket.emit("delete_comment", id, msgid, callback=update_amount_comment);
  }
};

function update_com_btn(com, change, nb){
  // Reçoit le commentaire après l'avoir envoyé
  var btn = document.getElementById("Answer42btn") ;
  unloading(btn)
  if (com){
    div2 = document.getElementById("msg-commentaire" + com['msgid'])
    if (div2){ // Si les commentaire sont déjà affichés
      // Affiche le commentaire
      if (div.comcolor===colors[0]){
        var color = colors[1]
      }else{
        var color = colors[0]
      };
      var span = document.createElement("span");
      span.style.padding = "0px 0px 0px 10px"
      span.id = "commentdiv" + com['_id']
      span.innerHTML = comtemplate(com, color)
      div2.insertBefore(span, div2.firstChild)
      if (div2.style.display === "none"){
        div2.style.display = "block";
      }
    }else{
      document.getElementById('COMMENTAIRE' + com['msgid']).click();
    }
      update_amount_comment(com['msgid'], change, nb) // Met à jour l'affichage du nombre de commentaires
  }else if (change === "blocked"){
    alert_user("Vous ne pouvez pas commenter ce message car l'utilisateur qui l'a posté vous a bloqué.")
  }
};

function send_comment(btnid){
  // Permet d'envoyer un commentaire
  btn = document.getElementById(btnid)
  textarea = document.getElementById("Answer42contenu")
  loading(btn)
  div = document.getElementById("Answer42")
  if (textarea.value){
    socket.emit('send_comment', div.msgid, textarea.value, callback=update_com_btn);
    textarea.value = "";
  }else{
    unloading(btn)
  }
};

function show_comment(btn, msgid, id, color){
  // Affiche ou cache les commentaires sous le message
  var div = document.getElementById("msg-commentaire" + msgid);
  if (!div){
    div = document.createElement("div");
    div.id = "msg-commentaire" + msgid;
    var msg = document.getElementById("msgdiv" + msgid);
    if (!msg){
      msg = document.getElementById("commentdiv" + msgid);
    };
    msg.appendChild(div);
  }else{
    if (div.style.display === "none"){
      div.style.display = "block";
    }else{
      div.style.display = "none";
      return false; // fin de la fonction dans ce cas
    }
  }
  loading(btn);
  socket.emit("askcomments", msgid, id, color, callback=upd_comments);
};

function answer(btn, msgid, color){
  // Affiche le formulaire permettant d'écrire un commentaire
  comm = document.getElementById("Answer42");
  var msg = document.getElementById("msgdiv" + msgid);
    if (!msg){
      msg = document.getElementById("commentdiv" + msgid)
    };
  if (comm.parentNode === msg){
    if (comm.style.display === "none"){
      comm.style.display = 'block';
    }else{
      comm.style.display = 'none';
    }
  }else{
    const comentdiv = document.getElementById("msg-commentaire" + msgid);
    if (comentdiv){
      msg.insertBefore(comm, comentdiv.previousSibling)
    }else{
      msg.appendChild(comm)
    }
    comm.style.display = 'block';
    comm.msgid = msgid
    comm.comcolor = color
    document.getElementById("Answer42contenu").focus() // Donne le focus à l'entrée de texte
  }
};

function upd_comments(id, array, color, msgid, nb){
  // Cherche et affiche les commentaires d'un message
  btn = document.getElementById(id);
  unloading(btn);
  var div = document.getElementById("msg-commentaire"+msgid)
  update_amount_comment(msgid, true, nb)
  if (!div && array.length){ // Si aucun commentaire n'est affiché, mais que certains existent
    var div = document.createElement("div"); // Les commentaires n'ont pas encore été affichés pour ce message
    div.id = "msg-commentaire"+msgid;
    btn.parentNode.appendChild(div)
  };

  for (let i = 0; i < array.length; i++){ // Affiche les commentaires
    already_com = document.getElementById("commentdiv" + array[i]['_id'])
    if (already_com){
      already_com.remove()
    };
    var com = document.createElement("span");
    com.style.padding = "0px 0px 0px 10px";
    com.id = "commentdiv" + array[i]['_id'];
    div.appendChild(com);
    com.innerHTML = comtemplate(array[i], color);
  };
  if (!array.length && div){ // Si aucun commentaire n'existe
    div.remove()
  }
};

function update_like(id, likes, cond){
  // Met à jour le nombre de likes
  var btn = document.getElementById(id);
  unloading(btn);
  if (cond){
    btn.innerHTML = likes + " <i class='fas fa-heart' style='color: #ffc162; margin-left: 5px;'></i>";
  }else{
    btn.innerHTML = likes + " <i class='far fa-heart' style='margin-left: 5px;'></i>";
  }
};

function jslike(id){
  // Indique au serveur que l'utilisateur a cliqué sur le bouton Like
  var btn = document.getElementById(id);
  loading(btn);
  socket.emit('like', id, callback=update_like);
};

function show_msg(btn, fulltext, reducedtext){
  // Montre tout le texte du message (s'il est trop long)
  btn.parentNode.innerHTML = sanitize(fulltext) + "<a onclick=" + '"hide_msg(this, ' + "'" + sanitize(fulltext) + "'" + ", '" + sanitize(reducedtext) + "')" + '"> Réduire</a>'
};

function hide_msg(btn, fulltext, reducedtext){
  // Réduit le texte du message (s'il est trop long)
  var msg = btn.parentNode;
  msg.innerHTML = sanitize(reducedtext) + "<a onclick=" + '"show_msg(this, ' + "'" + sanitize(fulltext) + "'" + ", '" + sanitize(reducedtext) + "')" + '">...</a>'
  msg.parentNode.children[0].scrollIntoView({ behavior: 'smooth' })
};

function update_msginfo(id, nb){
  // Met à jour le nombre de commentaires
  var btn = document.getElementById("msginfo" + id + "comm");
  btn.firstChild.innerHTML = "<i class='fas fa-comment'></i> (" + nb + ")";
};

function jsmsginfo(id){
  // Useless ?
  socket.emit('msginfo', id, callback=update_msginfo);
};

function delete_msg(msgid){
  // Demande à l'utilisateur s'il souhaite supprimer un post
  notifier.confirm('Voulez-vous vraiment supprimer ce post ?\nCela supprimera également tous les commentaires associés.',
    () => {
      truly_delete_msg(msgid);
    }, function(){
    return false;
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
  
function truly_delete_msg(msgid){
  // Supprime un post
  span = document.getElementById("msgdiv" + msgid);
  if (span){
    span.remove();
    socket.emit("delete_msg", msgid);
    document.getElementById("separationmsg" + msgid).remove()
  }
};
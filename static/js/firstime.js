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

let notifier = new AWN({});
let currentCallOptions = {}
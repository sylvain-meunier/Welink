function update_interets(array){
    // Définit les centres d'intérêt de l'utilisateur
    if (!(array === "")){
        document.getElementById("hidTest").value = array
        return array;
    }else{
        return false;
    }
};

let notifier = new AWN({});
let currentCallOptions = {}
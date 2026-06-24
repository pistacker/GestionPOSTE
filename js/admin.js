import { addActivity } from "./api.js";

window.add = async function () {
  const data = {
    asso: document.getElementById("asso").value,
    date: document.getElementById("date").value,
    activite: document.getElementById("activite").value,
    lieu: document.getElementById("lieu").value,
    horaire: document.getElementById("horaire").value,
    rdv: document.getElementById("rdv").value,
    inscrit: document.getElementById("inscrit").checked,
    note: document.getElementById("note").value,
  };

  await addActivity(data);

  alert("Activité ajoutée !");
};

import { getGristAuthInfo, gristApiRequest } from './grist-client.js';


const TYPE_INDEX_AUTHORIZE = ['Numeric','Text']

/**
 * Récupère les colonnes de la table.
 * @returns 
 */
async function getTableInfo() {
  const tableId = await grist.getTable().getTableId();
  return await gristApiRequest(`tables/${tableId}/columns?hidden=false`)
}


function completeColumnIndex(columns) {
  const select = document.getElementById("column-select");
  let count = 0;
  columns.forEach(col => {
    const type = col.fields.type;
    if (TYPE_INDEX_AUTHORIZE.includes(type) ) {
      const opt = document.createElement("option");
      opt.value = col.id;
      opt.textContent = col.fields.label;
      select.append(opt);
      count++;
    }
  });

  if (count === 0) {
      const messageGroup = document.getElementById("column-select-messages");
      messageGroup.innerHTML = `<p class="fr-message fr-message--error">
      Aucune colonne disponible pour créer un index. Il faut une colonne de type Numeric ou Text.
      </p>`;
      // Désactive le bouton de validation
      const submitBtn = document.getElementById("submit-btn");
      if (submitBtn) submitBtn.setAttribute("disabled", "true");
  }
}

async function initGrist() {
    grist.ready({
        requiredAccess: 'full'
    });
    const select = document.getElementById("column-select");
    const submitBtn = document.getElementById("submit-btn");


    // 🔹 Activer le bouton uniquement si une colonne est choisie
    select.addEventListener("change", () => {
      if (select.value) {
        submitBtn.removeAttribute("disabled");
        clearMessages();
      } else {
        submitBtn.setAttribute("disabled", "true");
      }
    });

     try {
        const tableInfo = await getTableInfo();
        completeColumnIndex(tableInfo.columns); 
      } catch (err) {
        console.error("Erreur :", err);
      } finally {
      }


    // grist.onRecords( function(records) {      
    //   dataRecord = records;
    // });

}


document.addEventListener('DOMContentLoaded', initGrist);
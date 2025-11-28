import { publishDataGrist } from './modules/dataEtat.js';
import { login } from './modules/login.js';
import { getColumnTable } from './grist-client.js';

const oidcConfig = window.OIDC_CONFIG;

const TYPE_INDEX_AUTHORIZE = ['Numeric', 'Text'];

function completeColumnIndex(columns) {
  const select = document.getElementById("column");
  let count = 0;
  columns.forEach(col => {
    const type = col.fields.type;
    if (TYPE_INDEX_AUTHORIZE.includes(type)) {
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
    const submitBtn = document.getElementById("submit-btn");
    if (submitBtn) submitBtn.setAttribute("disabled", "true");
  }
}

function displayErrorFeedback(message) {
  const feedBack = document.getElementById("feedback");
  const infos = document.getElementById("infos");
  if (feedBack) {
    infos.classList.add("fr-hidden"); // on efface les infos du plugins
    feedBack.classList.remove("fr-hidden");
    feedBack.classList.add("fr-alert--error");
    feedBack.innerHTML = `
      <p>${message}</p>
      <button title="Masquer le message" onclick="const alert = this.parentNode; alert.parentNode.removeChild(alert)" type="button" class="fr-btn--close fr-btn">Masquer le message</button>
    `;
  }
}

function hidePart(id) {
  const loadingDiv = document.getElementById(id);
  if (loadingDiv) {
    loadingDiv.classList.add("fr-hidden");
  }
}

function showPart(divId) {
  const div = document.getElementById(divId);
  if (div) {
    div.classList.remove("fr-hidden");
  }
}


async function initGrist() {
  grist.ready({
    requiredAccess: 'full'
  });
  

  const select = document.getElementById("column");
  const submitBtn = document.getElementById("submit-btn");
  const label = document.getElementById("column-select-label");
  const form = document.getElementById("columns-form");

  // Récupère une seule fois l'id de la table
  let tableId;
  try {
    tableId = await grist.getSelectedTableId();
    // Utilise l'identifiant de la table dans le label
    if (label && tableId) {
      label.textContent = `Sélectionner un index pour la table « ${tableId} »`;
    }
    const tableInfo = await getColumnTable(tableId);
    completeColumnIndex(tableInfo.columns);
    hidePart("loading-plugins");
    showPart("form-publish");
  } catch (err) {
    displayErrorFeedback("Erreur sur la récupération de la table sélectionnée : " + err.message);
  }

  // 🔹 Activer le bouton uniquement si une colonne est choisie
  select.addEventListener("change", () => {
    if (select.value) {
      submitBtn.removeAttribute("disabled");
    } else {
      submitBtn.setAttribute("disabled", "true");
    }
  });

  // 🔹 Sur submit, appelle publishDataGrist et empêche le submit classique
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    submitBtn.disabled = true;
    showPart("loading-publish");

    const token = await login( oidcConfig.url, oidcConfig.realm, oidcConfig.clientId );

    hidePart("form-publish");
    const data = new FormData(form);
    const indexCol = data.get("column");
    if (tableId && indexCol) {
      try {
        await publishDataGrist(tableId, indexCol, token);
        hidePart("loading-publish");
        showPart("success-publish");
      } catch(err) {
        submitBtn.disabled = false;
        displayErrorFeedback(err.message);
        showPart("form-publish");
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', initGrist);
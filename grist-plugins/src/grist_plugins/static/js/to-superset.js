import { publishDataGrist, linkWithSuperset } from './modules/dataEtat.js';
import { login } from './modules/login.js';
import { getColumnTable, getGristDocId } from './grist-client.js';

const oidcConfig = window.OIDC_CONFIG;

const TYPE_INDEX_AUTHORIZE = ['Numeric', 'Text', 'Int'];

// La table publiée s'appelle <tableId>_<docId> : 63 caractères au plus (limite PostgreSQL)
const PUBLISHED_TABLE_NAME_MAX_LENGTH = 63;

/**
 * Renvoie le message expliquant pourquoi la table ne peut pas être publiée, ou null si elle peut l'être.
 */
function checkPublishable(docId, tableId) {
  const maxTableIdLength = PUBLISHED_TABLE_NAME_MAX_LENGTH - docId.length - 1;
  if (tableId.length > maxTableIdLength) {
    return `Le nom de la table « ${tableId} » est trop long pour être publié depuis ce document `
      + `(${maxTableIdLength} caractères au plus). Renommez la table pour la publier.`;
  }
  return null;
}

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
  }
}

function displayErrorFeedback(message) {
  const errorDiv = document.getElementById("error-message");
  const feedBack = document.getElementById("error-feedback");
  const infos = document.getElementById("infos");
  if (feedBack) {
    infos.classList.add("fr-hidden"); // on efface les infos du plugins
    feedBack.classList.remove("fr-hidden");
    errorDiv.classList.add("fr-alert--error");
    errorDiv.innerHTML = `
      <p>${message}</p>
    `;
  }
}

function resetError() {
  const feedBack = document.getElementById("error-feedback");
  const form = document.getElementById("form-publish");
  if (feedBack) {
    feedBack.classList.add("fr-hidden");
    form.classList.remove("fr-hidden");
  }
  showPart("form-publish");
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

function publishInProgress() {
  const loadingDiv = document.getElementById('loading');
  const icon = loadingDiv.querySelector('span');
  loadingDiv.textContent = ''; // Vide la div
  loadingDiv.appendChild(icon); // Remet l'icône
  loadingDiv.appendChild(document.createTextNode('Publication en cours...'));
  showPart('loading');
}

function linkToSupersetInProgress() {
  const loadingDiv = document.getElementById('loading');
  const icon = loadingDiv.querySelector('span');
  loadingDiv.textContent = ''; // Vide la div
  loadingDiv.appendChild(icon); // Remet l'icône
  loadingDiv.appendChild(document.createTextNode('Liaison avec Superset ...'));
  showPart('loading');
}


async function initGrist() {
  grist.ready({
    requiredAccess: 'full'
  });
  

  const select = document.getElementById("column");
  const submitBtn = document.getElementById("submit-btn");
  const submitContainer = document.getElementById("submit-container");
  const label = document.getElementById("column-select-label");
  const form = document.getElementById("columns-form");
  const colSelectGroup = document.getElementById("col-select-group");
  const hasIndexYes = document.getElementById("has-index-yes");
  const hasIndexNo = document.getElementById("has-index-no");

  // Récupère une seule fois l'id du document et de la table
  let docId;
  let tableId;
  try {
    docId = await getGristDocId();
    tableId = await grist.getSelectedTableId();
    const blockingReason = checkPublishable(docId, tableId);
    if (blockingReason) {
      displayErrorFeedback(blockingReason);
      hidePart("loading-plugins");
      hidePart("back-btn"); // rien à corriger dans le formulaire : il faut renommer la table dans Grist
      return;
    }
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

  // Gérer l'affichage conditionnel du select d'index et du bouton submit
  hasIndexYes.addEventListener("change", () => {
    if (hasIndexYes.checked) {
      colSelectGroup.classList.remove("fr-hidden");
      submitContainer.classList.remove("fr-hidden");
    }
  });

  hasIndexNo.addEventListener("change", () => {
    if (hasIndexNo.checked) {
      colSelectGroup.classList.add("fr-hidden");
      submitContainer.classList.remove("fr-hidden");
      select.value = ""; // Réinitialiser la sélection
    }
  });

  // 🔹 Sur submit, appelle publishDataGrist et empêche le submit classique
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    publishInProgress()

    const token = await login( oidcConfig.url, oidcConfig.realm, oidcConfig.clientId );

    hidePart("form-publish");
    const data = new FormData(form);
    const indexCol = data.get("column") || null; // Index optionnel
    
    if (tableId) {
      try {
        await publishDataGrist(docId, tableId, indexCol, token);
        linkToSupersetInProgress()
        await linkWithSuperset(docId, tableId, token);
        hidePart("loading");
        showPart("success");
      } catch(err) {
        displayErrorFeedback(err.message);
        hidePart("loading");
        showPart("error-message");
      }
    }
  });

  const backBtn = document.getElementById("back-btn");
  if (backBtn) {
    backBtn.addEventListener("click", resetError);
  }
}

document.addEventListener('DOMContentLoaded', initGrist);
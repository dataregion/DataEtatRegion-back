import Papa from 'papaparse';
import { getColumnTable } from '../grist-client.js';


/**
 * Nettoie la valeur issue d'un enregistrement Grist.
 * Si la valeur est un tableau :
 * 1. Retire éventuellement le préfixe "L"
 * 2. Transforme le tableau en chaîne pour le CSV.
 */
function sanitizeValue(value) {
  if (!Array.isArray(value)) {
    return value;
  }
  let sanitizedValue = value;
  if (sanitizedValue[0] === "L") {
    sanitizedValue = sanitizedValue.slice(1);
  }
  return sanitizedValue.join(",");
}

export async function fetchTableRows(tableRef, colsToKeep) {
  if (!tableRef) {
    return [];
  }

  const tableData = await grist.docApi.fetchTable(tableRef);
  const colInfoMap = new Map(colsToKeep.map(c => [c.id, c]));
  const availableCols = Object.keys(tableData).filter(col =>
    colInfoMap.has(col)
  );
  const rowCount = availableCols.length
    ? (tableData[availableCols[0]]).length
    : 0;

  const rows = [];
  for (let i = 0; i < rowCount; i++) {
    const row = {};
    for (const col of availableCols) {
      const colInfo = colInfoMap.get(col);
      const displayCol = colInfo && colInfo.displayColId;
      const value = (tableData[displayCol || col])[i];
      row[col] = sanitizeValue(value);
    }
    rows.push(row);
  }

  return rows;
}

function filterColumns(columns) {
  // Filtrer les colonnes pour exclure les références
  return columns.filter(col => !col.fields.type.startsWith('Ref:'));
}

async function _parseError(response) {
  let errorMessage = `Erreur HTTP ${response.status}`;
  try {
    // Tenter de parser la réponse JSON
    const errorData = await response.json();

    // Vérifier si un message custom existe
    if (errorData.message) {
      errorMessage = errorData.message;
    } else if (errorData.detail) {
      // FastAPI renvoie souvent "detail"
      errorMessage = typeof errorData.detail === 'string'
        ? errorData.detail
        : JSON.stringify(errorData.detail);
    } else if (errorData.error) {
      errorMessage = errorData.error;
    }
  } catch (parseError) {
    // Si le parsing JSON échoue, utiliser le statut HTTP
    console.warn('Impossible de parser la réponse d\'erreur:', parseError);
  }
  throw new Error(errorMessage);
}

export async function publishDataGrist(tableId, colIndex, token) {
  // récupérer les colonnes
  const tableInfo = await getColumnTable(tableId);
  const columns = filterColumns(tableInfo.columns);

  const rows = await fetchTableRows(tableId, columns);

  // Générer le CSV avec PapaParse
  const csv = Papa.unparse({
    fields: columns.map(c => c.id),
    data: rows.map(row => columns.map(c => row[c.id]))
  });
  // Créer un File
  const file = new File([csv], `${tableId}.csv`, { type: 'text/csv' });
  
  // Normaliser les types et extraire la timezone pour les DateTime
  const colsClean = columns.map(c => {
    const rawType = c.fields.type;
    let type = rawType;
    let timezone = null;
    
    // Si c'est un DateTime avec timezone (ex: "DateTime:Europe/Madrid")
    if (rawType.startsWith('DateTime:')) {
      const parts = rawType.split(':', 2);
      type = parts[0];  // "DateTime"
      timezone = parts[1];  // TimeZone
    }
    
    return {
      id: c.id,
      type: type,
      is_index: c.id === colIndex,
      timezone: timezone
    };
  });

  // Préparer FormData
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tableId', tableId);
  formData.append('columns', JSON.stringify(colsClean));

  // Envoyer à l'endpoint
  try {
    const response = await fetch('/to-superset/publish', {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      await _parseError(response);
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Erreur lors de la publication:', error);

    // Vérifier si c'est une erreur réseau
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Erreur de connexion au serveur');
    }

    // Propager l'erreur
    throw error;
  }
}


export async function linkWithSuperset(tableId, token) {
  // Envoyer à l'endpoint
  try {
    const formData = new FormData();
    formData.append('tableId', tableId);
    const response = await fetch('/to-superset/link', {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      await _parseError(response);
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Erreur lors du liens avec Superset:', error);

    // Vérifier si c'est une erreur réseau
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Erreur de connexion au serveur');
    }
    throw error;
  }
}
import { getGristAuthInfo, gristApiRequest } from './grist-client.js';



async function getTableInfo() {
  const tableId = await grist.getTable().getTableId();
  return await gristApiRequest(`tables/${tableId}/columns?hidden=false`)
}


function createTableFromColumns(columns) {
  const table = document.createElement('table');
  table.style.borderCollapse = 'collapse';
  table.style.width = '100%';

  // Header
  const thead = table.createTHead();
  const headerRow = thead.insertRow();
  ['ID', 'Label', 'Type'].forEach(text => {
    const th = document.createElement('th');
    th.textContent = text;
    th.style.border = '1px solid #ccc';
    th.style.padding = '6px';
    th.style.backgroundColor = '#eee';
    headerRow.appendChild(th);
  });

  // Body
  const tbody = table.createTBody();
  columns.forEach(col => {
    const row = tbody.insertRow();
    const idCell = row.insertCell();
    idCell.textContent = col.id || '';
    idCell.style.border = '1px solid #ccc';
    idCell.style.padding = '6px';

    const labelCell = row.insertCell();
    labelCell.textContent = (col.fields && col.fields.label) || '';
    labelCell.style.border = '1px solid #ccc';
    labelCell.style.padding = '6px';

    const typeCell = row.insertCell();
    typeCell.textContent = (col.fields && col.fields.type) || '';
    typeCell.style.border = '1px solid #ccc';
    typeCell.style.padding = '6px';
  });

  return table;
}

async function initGrist() {
    grist.ready({
        requiredAccess: 'full'
    });

    let dataRecord = {}

    grist.onRecords( function(records) {      
      dataRecord = records;
    });


    const form = document.getElementById("supersetForm");
    const resultBloc = document.getElementById("resultBloc");
    const resultArea = document.getElementById("resultArea"); 



    form.addEventListener("submit", async function (event) {
      console.log("click bouton go to grist")
      event.preventDefault();

      try {
        const tableInfo = await getTableInfo();
        // Vide l'ancien contenu
        resultArea.innerHTML = '';
        // Génère le tableau HTML
        const table = createTableFromColumns(tableInfo.columns);
        resultArea.appendChild(table);
       
      } catch (err) {
        console.error("Erreur :", err);
        resultArea.textContent = `Erreur : ${err.message}`;
      } finally {
        resultBloc.style.display = "block";
      }
    });
}


document.addEventListener('DOMContentLoaded', initGrist);
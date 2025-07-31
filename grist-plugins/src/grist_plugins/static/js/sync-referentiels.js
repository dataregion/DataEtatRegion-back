async function getDocId() {
  return await grist.docApi.getDocName()
}

async function getTableId() {
  return await grist.getTable().getTableId();
}


async function initGrist() {
    grist.ready({
        requiredAccess: 'full'
    });

    const form = document.getElementById("syncForm");
    const button = document.getElementById("submitBtn");

    const docId = await getDocId();
    const tableId = await getTableId();
    const tableName = window.tableNameFromServer;
    console.log("tableName from server:", tableName);

    // form.addEventListener("submit", async function (event) {
    //   event.preventDefault();
    //   button.disabled = true
    //   button.replaceChildren("Synchronisation")
    //   try {
    //     const response = await fetch(`/launch-sync?docId=${docId}&tableId=${tableId}&tableName=${tableName}`, {
    //       method: 'POST'
    //     });
    //     if (!response.ok) {
    //       const errorText = await response.text();
    //     } else {
    //       button.replaceChildren("Synchroniser")
    //       button.disabled = false
    //     }
    //   } catch (err) {
    //     console.error("Erreur :", err);
    //     resultArea.textContent = `Erreur : ${err.message}`;
    //   } finally {
    //     resultBloc.style.display = "block";
    //   }
    // });
}

document.addEventListener('DOMContentLoaded', initGrist);
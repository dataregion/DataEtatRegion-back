async function initGrist() {
    grist.ready({
        requiredAccess: 'full'
    });

    const form = document.getElementById("syncForm");
    const button = document.getElementById("submitBtn");

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      button.disabled = true
      button.replaceChildren("Synchronisation")
      try {
        const response = await fetch("http://localhost:8000/launch-sync", {
          method: 'POST'
        });
        if (!response.ok) {
          const errorText = await response.text();
        } else {
          button.replaceChildren("Synchroniser")
          button.disabled = false
        }
      } catch (err) {
        console.error("Erreur :", err);
        resultArea.textContent = `Erreur : ${err.message}`;
      } finally {
        resultBloc.style.display = "block";
      }
    });
}

document.addEventListener('DOMContentLoaded', initGrist);
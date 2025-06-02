// Récupère le token d'accès et l'URL de base
async function getGristAuthInfo() {
  try {
    const tokenInfo = await grist.docApi.getAccessToken({ readOnly: true });

    return {
      baseUrl: tokenInfo.baseUrl,
      token: tokenInfo.token
    };
  } catch (error) {
    console.error('Erreur lors de la récupération du token Grist:', error);
    throw error;
  }
}

// Fait une requête HTTP vers l'API REST de Grist
async function gristApiRequest(endpoint, method = 'GET', body = null) {
  const { baseUrl, token } = await getGristAuthInfo();
  const [path, queryString] = endpoint.split('?');
  const url = new URL(`${baseUrl}/${path}`);

  // Ajoute les query params de l'endpoint initial
  if (queryString) {
    const params = new URLSearchParams(queryString);
    for (const [key, value] of params.entries()) {
      url.searchParams.set(key, value);
    }
  }
  url.searchParams.set('auth', token);

  const options = {
    method,
    headers: {
      'Content-Type': 'application/json'
    }
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(url.toString(), options);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Erreur API Grist: ${response.status} ${response.statusText}\n${errorText}`);
  }

  return response.json();
}

// Exporte la fonction pour l'utiliser ailleurs
export { getGristAuthInfo, gristApiRequest };
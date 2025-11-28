
// Générer un state aléatoire pour sécurité CSRF
function generateState() {
  return Math.random().toString(36).substring(2, 15);
}

// Générer le code verifier et challenge pour PKCE
async function generatePKCE() {
  const verifier = generateRandomString(128);
  const challenge = await generateCodeChallenge(verifier);
  return { verifier, challenge };
}

function generateRandomString(length) {
  const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
  let text = '';
  for (let i = 0; i < length; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
}

async function generateCodeChallenge(verifier) {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return base64urlEncode(hash);
}

function base64urlEncode(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

// Construire l'URL d'autorisation
async function buildAuthUrl(url, realm, clientId) {
  const state = generateState();
  const { verifier, challenge } = await generatePKCE();
  
  // Stocker le state et verifier pour validation ultérieure
  sessionStorage.setItem('oidc_state', state);
  sessionStorage.setItem('oidc_verifier', verifier);
  
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: `${window.location.origin}/callback`,
    response_type: 'token',
    scope: 'openid profile email',
    state: state,
    code_challenge: challenge,
    code_challenge_method: 'S256',
  });
  return `${url}/realms/${realm}/protocol/openid-connect/auth?${params}`;
}

// Gérer le callback de la popup
function handleCallback(event) {
  // Vérifier l'origine pour sécurité
  if (event.origin !== window.location.origin) return;
  
  const { type, data } = event.data;
  console.log("Réception du message de callback OIDC :", event.data);
  
  if (type === 'oidc-callback') {
    const { resolve, reject, timeout } = window._oidcCallbacks;
    clearTimeout(timeout);
    
    // Vérifier le state
    const savedState = sessionStorage.getItem('oidc_state');
    if (data.state !== savedState) {
      reject(new Error('State invalide - possible attaque CSRF'));
      return;
    }
    
    if (data.error) {
      reject(new Error(data.error));
    } else if (data.token) {
      // Implicit flow - token directement
      resolve(data.token);
    }
    
    // Nettoyer
    sessionStorage.removeItem('oidc_state');
    window.removeEventListener('message', handleCallback);
  }
}


// Ouvrir la popup de connexion
export async function login(url, realm, clientId) {
  const authUrl = await buildAuthUrl(url, realm, clientId);
  
  // Alternative : ouvrir dans un nouvel onglet
  console.log("Ouverture de l'URL d'authentification :", authUrl);
  window.open(authUrl, '_blank');
  
  // Écouter le message de la page de callback
  window.addEventListener('message', handleCallback);
  
  return new Promise((resolve, reject) => {
    // Timeout après 1 minute
    const timeout = setTimeout(() => {
      reject(new Error('Authentification expirée'));
    }, 1 * 60 * 1000);
    
    // Stocker les callbacks pour les utiliser dans handleCallback
    window._oidcCallbacks = { resolve, reject, timeout };
  });
}
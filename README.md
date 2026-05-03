# J.A.R.V.I.S — Interface Mobile

Interface vocale mobile connectée au backend Python via WebSocket.

## Backend
- HTTP : `http://frvill.duckdns.org:8080/`
- WebSocket : `ws://frvill.duckdns.org:8765`

## Déploiement GitHub Pages

1. Pousser les fichiers à la racine du repo `xfville-art/Jarvs`
2. Dans **Settings → Pages**, sélectionner `main` branch, dossier `/` (root)
3. L'app sera accessible sur `https://xfville-art.github.io/Jarvs/`

## ⚠️ Problème WebSocket depuis GitHub Pages (HTTPS)

GitHub Pages force HTTPS. Or le backend utilise `ws://` (non-sécurisé).  
Les navigateurs bloquent les connexions `ws://` depuis une page `https://` (mixed content).

### Solution A — Chrome (recommandée pour usage perso)
1. Ouvre `chrome://flags` sur le téléphone
2. Cherche **Insecure origins treated as secure**
3. Ajoute `http://frvill.duckdns.org:8080`
4. Relance Chrome

### Solution B — Nginx reverse proxy `wss://` (pérenne)
Sur le serveur, configurer nginx pour terminer SSL et rediriger vers le WebSocket local :
```nginx
server {
    listen 8766 ssl;
    ssl_certificate     /chemin/cert.pem;
    ssl_certificate_key /chemin/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```
Puis changer `BACKEND_WS_PORT` dans `app.js` à `8766`.

## Fichiers
| Fichier | Rôle |
|---------|------|
| `index.html` | Structure HTML |
| `app.js` | Logique WebSocket, STT, TTS, états |
| `orb.js` | Visualisation 3D Three.js |
| `style.css` | Styles glassmorphism |

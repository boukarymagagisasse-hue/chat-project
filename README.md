# Chat Project — première version

Application de chat inspirée de Telegram : canaux, messages enregistrés et mise à jour en direct dans le navigateur.

## Prérequis
- Windows 10/11
- Python 3.10 ou plus récent
- Une connexion Internet est utile uniquement pour installer les dépendances la première fois.

## Démarrage facile sous Windows
1. Décompressez le dossier `chat-project` sur le Bureau.
2. Ouvrez le dossier `chat-project`, puis double-cliquez sur `DEMARRER_WINDOWS.bat`.
3. La première exécution crée un environnement Python et installe les dépendances. Cela peut prendre quelques minutes.
4. Une fois le serveur démarré, ouvrez votre navigateur à l'adresse : http://127.0.0.1:8000
5. Pour arrêter le serveur, revenez à la fenêtre noire et appuyez sur `Ctrl + C`.

Si Windows affiche un avertissement, vérifiez que le fichier provient bien de votre propre dossier de projet avant de l'exécuter.

## Fonctions incluses
- Liste de canaux (Général, Annonces, Questions)
- Création de canaux
- Envoi de messages avec nom d'utilisateur
- Messages enregistrés dans une base SQLite locale (`backend/chat.db`)
- Actualisation en direct avec WebSocket lorsque plusieurs navigateurs sont connectés
- Interface adaptée aux écrans étroits et larges
- API REST de base et documentation interactive à `/docs`

## Structure
```text
chat-project/
├── DEMARRER_WINDOWS.bat
├── README.md
└── backend/
    ├── requirements.txt
    ├── app/
    │   └── main.py
    └── static/
        └── index.html
```

## Notes importantes
C'est une première version pédagogique fonctionnelle du **chat web**. Elle n'inclut pas encore l'authentification, les conversations privées, ni les applications mobiles et de bureau natives. Ces éléments pourront être ajoutés ensuite. La base SQLite permet de démarrer facilement ; PostgreSQL pourra remplacer SQLite pour le déploiement. Ne publiez pas ce serveur sur Internet sans ajouter une authentification et des protections adaptées.

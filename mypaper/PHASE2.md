# My Paper Phase 2 — Google sign-in (not live yet)

Front-end code is already wired behind `firebase-config.js` (`enabled: false`).
No Firebase project was created. No keys were invented.

## What the user needs to switch it on

1. A Google account that will own the Firebase project (ideally the Earth5R / Yes Bro org account).
2. Create a Firebase project in the Firebase console (Blaze not required for Auth + Firestore light use).
3. Enable Authentication → Sign-in method → Google.
4. Add authorized domain: `yesbrohq.com` (and `localhost` for tests).
5. Create a Web app in Project settings and copy the web config.
6. Create a Firestore database (production mode), then paste the rules from `firestore.rules` in this folder.
7. Edit `/mypaper/firebase-config.js` on the site:
   - set `enabled: true`
   - fill `apiKey`, `authDomain`, `projectId`, `storageBucket`, `messagingSenderId`, `appId`
8. Redeploy / commit that one file. The Sign in with Google button appears on its own.

## Data shape

Collection `users`, document id = Firebase Auth `uid`:

```
{ email, name, picks: ["auto.india-auto", "daily.india-politics", ...], created, last_seen }
```

Picks still also live in `localStorage` and the `?t=` URL so anonymous readers keep working.

# My Paper Phase 2 — Google sign-in + whole-paper picks

Live for project **Yes Bro** (`yes-bro-5c2dd`), Spark plan.
Web config lives in `firebase-config.js` with `enabled: true`.

## Whole-paper picks

Paper-level picks look like `ux.*`. Adding a whole paper includes every section, jobs, events, research and talks for that edition, including sections that land on future days.

Section picks look like `daily.india-politics`. They sit under **Or pick sections** in the picker.

Shareable URL example:

`https://yesbrohq.com/mypaper/?t=ux.*,arch.*,startups.*`

Reader view shows each added paper as its own block with the paper name as a heading.

## Console links

- Auth users: https://console.firebase.google.com/project/yes-bro-5c2dd/authentication/users
- Firestore `users` collection: https://console.firebase.google.com/project/yes-bro-5c2dd/firestore/databases/-default-/data/~2Fusers
- Rules editor: https://console.firebase.google.com/project/yes-bro-5c2dd/firestore/databases/-default-/rules

Paste `firestore.rules` from this folder into the Rules editor and publish. The live rules must allow `uid`, `email`, `name`, `photo`, `picks`, `created`, `last_seen` or sign-in merge writes will fail.

## Doc shape

`users/{uid}` = `{ uid, email, name, photo, picks, created, last_seen }`

On Google sign-in the client merges local picks with cloud picks (union), writes the merged list, then keeps localStorage as a fallback when signed out or offline.

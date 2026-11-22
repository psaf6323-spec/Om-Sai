# Om Sai

A shop-management web app for Om Sai (stock, sales, expenses, profit, parties, orders, rate comparison with
price-rise alerts, staff logins, voice assistant, backup/restore). English and Nepali.
The whole app is one file, `index.html`; a tiny Node server (`server.js`) serves it. No build step, no npm install.

## Run locally (2 steps)
Requirements: **Node 18+** (https://nodejs.org). Nothing to install.

```bash
cd om-sai
npm start            # or: node server.js
# open http://localhost:8080  (use a browser, Chrome/Edge recommended)
```
- Change port: `PORT=3000 npm start`. Allow other devices on your Wi-Fi: `HOST=0.0.0.0 npm start`
  (other devices must use `http://<your-pc-ip>:8080`; microphone/camera and password hashing need `localhost` or HTTPS,
  so for phones deploy to HTTPS, see "Putting it online").
- Do not open `index.html` by double-clicking (file://): the browser blocks the secure-crypto features used for logins.
- `npm run check` verifies the app script parses.

## First login
- Admin ID `admin`, password `admin123` -> the app **forces you to set a new password** immediately (min 8 characters).
- The old default staff account is disabled. Add real staff in **Settings** (name, Staff ID, password; or leave the password blank to generate one).
- A **recovery code** is shown once after you set your password. Write it on paper. **Forgot password?** on the login screen resets the admin password with that code (this also turns off two-step verification and issues a new code). Create a new code any time in Settings.
- If no recovery code was ever created (older installs): Forgot password? → type `RESET`, wait 60 seconds, tap it again, set a new password. Data is kept and the admin sees a notice about the reset on next login.
- Staff who forget their password: the admin sets a new one in Settings.
- Turn on **two-step verification** (Authenticator app) in Settings.

## Features (nothing removed)
- Menus: Home, New Entry, Daily Collection, Stock, Sold Out Items, Sales, Compare & Graphs, Expenses, Profit Report,
  Parties to Pay, Ordered Items, To Be Ordered, **Rate Compare**, Shop Hours, Chat, Settings.
- Optional logo; app name "Om Sai"; colourful theme (light/dark follows the device).
- Camera/gallery photos are shrunk to **10 KB or less**. Photos live in IndexedDB so 1000+ items fit.
- **Rate Compare** (admin): search an item, see 1 year of purchases (item, rate per packet, rate per piece, supplier, date),
  min/max/average, chart, cheapest supplier, and **price-rise alerts** (default 5%, adjustable); alert count on Home.
- **Voice assistant**: say "hello" (it listens after login; needs mic permission). It greets by time of day, asks what it can do,
  opens menus, fills the entry form, saves, compares ("compare lip gloss"), "price alerts", and sleeps on "thank you".
- **Staff**: admin creates Staff ID + password; staff see a limited menu; admin-only functions are guarded.
- **Backup / restore** (Settings): download all data as `.json` (optional passphrase encryption, AES-GCM); restore by choosing
  the file and typing `RESTORE`. Backups exclude passwords, MFA secrets and logins.
- Security hardening in the app: passwords hashed with PBKDF2-SHA256 (150k iterations, salted); login lockout after 5 wrong tries;
  TOTP two-step verification; input sanitising (XSS); image upload validation (real JPG/PNG/WebP only, max 12 MB, re-encoded);
  no auth token stored; hostile-backup rejection.

## Install as an app (PWA) and put it online
The project is an installable web app (manifest + service worker + icons). Installing needs **HTTPS** (or `localhost`).
1. **Host it** (free, static files only) - pick one:
   - **GitHub Pages:** push this folder to a GitHub repo -> Settings -> Pages -> Deploy from branch `main` / root. Your app is at `https://<user>.github.io/<repo>/`.
   - **Firebase Hosting:** `npm i -g firebase-tools && firebase login && firebase init hosting` (public directory: `.`, single-page app: No), then `firebase deploy`.
   (Do not host the `tests/` folder publicly if you prefer; it is harmless but unnecessary.)
2. **Install on each phone:** open the HTTPS link in Chrome -> menu -> *Install app* / *Add to Home screen*. iPhone (Safari): Share -> *Add to Home Screen*.
   Settings -> *App & data safety* shows install state and storage status.
3. **Keep data safe:** in Settings tap *Protect my data* (asks the browser not to auto-clear storage), and download a backup weekly.
   The installed app opens offline. Data is stored on that phone only; two phones do not share data until a shared database (Firebase) is added.
Files involved: `manifest.webmanifest`, `sw.js`, `icons/`.

## Where data is stored
In the browser (localStorage + IndexedDB) of the device you use. **Each browser has its own data**, so two phones do not share stock.
Take regular backups. Clearing browser data deletes the data.

## External dependency
- `qrcodejs 1.0.0` loaded from cdnjs (used for QR codes). Offline, QR codes will not draw; everything else works.
  To vendor it, download `qrcode.min.js` into this folder and change the `<script src=...>` in `index.html`.
- No npm packages are required to run. Tests need Python + Playwright (see below).

## Differences outside claude.ai
The app was built on claude.ai and uses three optional claude.ai features: shared chat database, dictation and file-save prompt.
Run locally, these fall back automatically: chat is stored locally, voice uses the browser's speech recognition (Chrome/Edge),
and backups download as a normal file.

## Tests
```bash
pip install -r tests/requirements.txt && playwright install chromium
python3 tests/run_all.py            # PWA/offline + unit + integration + break-it + security + backup/alerts
python3 tests/run_all.py --full     # also 1000 items with photos
```
Tests run in a headless browser against `index.html` (the QR library is stubbed, so no internet is needed). Linux/macOS.
They cover: calculations, 1000-item entry, staff IDs/passwords, sales/stock, voice commands, hostile input (XSS, quotes,
bad numbers), password hashing, lockout, MFA (RFC 6238 vectors), upload validation, backup/restore, price alerts.

## Not included (needs a server)
CSRF, JWT, CORS, server-side permissions, row-level security, webhooks, SSRF checks and sharing one dataset between
phones need a backend. Planned path: host `index.html` on GitHub Pages / Firebase Hosting and add Firebase Authentication +
Firestore with security rules. **Firebase and GitHub are not connected in this ZIP.**

## Project layout
```
om-sai/
  index.html     the app (all features)
  server.js      zero-dependency static server (npm start)
  manifest.webmanifest, sw.js, icons/   install-as-app + offline files
  package.json   scripts: start, check, test (no dependencies)
  tests/         Playwright test suite (Python)
  README.md
```

# CreditX

Carbon credit management platform built with Flask, Firebase Authentication, SQLite, and a single-page frontend.

## Overview

CreditX helps a user:

- sign in with Google or mobile OTP
- complete a company profile and upload verification documents
- calculate emissions and estimated carbon credits
- view a marketplace, blockchain-style ledger, portfolio, and reports

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Flask
- Auth: Firebase Authentication
- Database: SQLite
- Local file storage: encrypted document storage on disk

## Key Features

- Google sign-in with Firebase
- OTP sign-in flow for local testing
- multi-step company onboarding
- encrypted-at-rest profile fields and uploaded documents
- emissions calculator and report generator
- marketplace, portfolio, and ledger views

## Local Setup

1. Clone or open the project folder.
2. Create your Firebase env file from the example.
3. Add your Firebase web app values.
4. Start the Flask app.

```bash
cd /Users/deepalisingh/Downloads/creditx_project_fixed
cp firebase.local.env.example firebase.local.env
bash start.sh
```

Open: [http://localhost:8080](http://localhost:8080)

## Manual Run

```bash
cd /Users/deepalisingh/Downloads/creditx_project_fixed
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
set -a
source firebase.local.env
set +a
python3 app.py
```

## Firebase Setup

In Firebase Console:

1. Create a project.
2. Add a Web App.
3. Copy the Firebase config into `firebase.local.env`.
4. Enable `Authentication -> Sign-in method -> Google`.
5. Add `localhost` and `127.0.0.1` to authorized domains if needed.

## Security Notes

- `firebase.local.env` is excluded from Git.
- uploaded documents are stored encrypted on disk
- sensitive profile fields are stored encrypted in SQLite
- encryption key is stored locally in `secrets/fernet.key` and excluded from Git

This is strong server-side encryption at rest, not full end-to-end encryption.

## Repository Hygiene

Ignored from version control:

- `.venv/`
- `firebase.local.env`
- `creditx.db`
- `uploads/`
- `secrets/`

## Helpful Files

- [app.py](/Users/deepalisingh/Downloads/creditx_project_fixed/app.py)
- [static/index.html](/Users/deepalisingh/Downloads/creditx_project_fixed/static/index.html)
- [start.sh](/Users/deepalisingh/Downloads/creditx_project_fixed/start.sh)
- [firebase.local.env.example](/Users/deepalisingh/Downloads/creditx_project_fixed/firebase.local.env.example)
- [teaminfinique](/Users/deepalisingh/Downloads/creditx_project_fixed/teaminfinique)

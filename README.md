# CreditX

AI-powered carbon intelligence platform for Indian MSMEs  built with Flask, Firebase Authentication, SQLite, and a single-page frontend.


## Problem
Indian MSMEs often track emissions using manual bills, spreadsheets, and non-auditable records.

## Solution
CreditX helps MSMEs track emissions, view analytics, receive AI-based reduction suggestions, and prepare for future carbon credit participation.

## Overview

CreditX helps a business user:

- sign in with Google or mobile OTP
- complete a company profile and upload verification documents
- calculate emissions and estimated carbon credits
- review marketplace, portfolio, blockchain-style ledger, and reports

## Demo Flow

1. Sign in with Google or OTP.
2. Complete company onboarding.
3. Upload or verify documents.
4. Calculate emissions and view credits.
5. Explore marketplace, reports, and dashboard pages.

## Features

- Google sign-in with Firebase Authentication
- OTP sign-in flow for local testing
- multi-step onboarding and profile verification
- encrypted-at-rest profile fields and uploaded documents
- emissions calculator and report generator
- marketplace, portfolio, and blockchain-style ledger views

## Screenshots

Add screenshots to a `docs/` folder and reference them here.

```md
![Sign in](docs/signin.png)
![Dashboard](docs/dashboard.png)
![Marketplace](docs/marketplace.png)
```

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Flask
- Auth: Firebase Authentication
- Database: SQLite
- File security: encrypted local document storage

## Quick Start

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

1. Create or open a Firebase project.
2. Add a Web App.
3. Copy Firebase web config into `firebase.local.env`.
4. Enable `Authentication -> Sign-in method -> Google`.
5. Add `localhost` and `127.0.0.1` to authorized domains when needed.

## Security Notes

- `firebase.local.env` is excluded from Git
- uploaded documents are encrypted before being stored on disk
- sensitive profile fields are encrypted before being stored in SQLite
- encryption key is stored locally in `secrets/fernet.key` and excluded from Git

This is strong server-side encryption at rest, not full end-to-end encryption.

## Repository Hygiene

Ignored from version control:

- `.venv/`
- `firebase.local.env`
- `creditx.db`
- `uploads/`
- `secrets/`

## Project Files

- `app.py` - Flask backend and API routes
- `static/index.html` - frontend UI and logic
- `start.sh` - local startup script
- `firebase.local.env.example` - Firebase env template
- `teaminfinique` - quick local setup guide

## License

This project is licensed under the MIT License.

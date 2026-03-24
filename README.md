# CreditX

Local Flask + Firebase carbon credit platform.

## What changed

- Fixed the post-sign-in/profile flow so the app can reliably enter the main platform.
- Fixed profile persistence so DigiLocker verification is not lost during save.
- Switched Firebase setup to a Flask-served runtime config using local environment variables.
- Added local session restore, better page navigation, and safer startup steps for macOS.

## Quick start

```bash
cd /Users/deepalisingh/Downloads/creditx_project_fixed
cp firebase.local.env.example firebase.local.env
```

Edit `firebase.local.env` with your Firebase Web App config, then run:

```bash
bash start.sh
```

Open [http://localhost:8080](http://localhost:8080).

## Firebase setup

In Firebase Console:

1. Create or open your project.
2. Enable `Authentication -> Sign-in method -> Google`.
3. Add a Web App and copy its config values into `firebase.local.env`.
4. Make sure `localhost` is allowed in authorized domains.

## Manual run

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

## GitHub push

```bash
cd /Users/deepalisingh/Downloads/creditx_project_fixed
git init
git add .
git commit -m "Fix CreditX local Firebase + Flask workflow"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

## Notes

- The OTP flow works locally through Flask and returns a demo OTP for testing.
- Firebase config is optional for OTP login, but required for Google sign-in.
- See `/Users/deepalisingh/Downloads/creditx_project_fixed/teaminfinique` for the exact command list.

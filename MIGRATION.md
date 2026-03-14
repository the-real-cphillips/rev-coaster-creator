# Migrating to Reverie Brewing Co. Google Workspace

This document covers handing the Coaster Club system off to the brewery's Google Workspace account.

---

## Overview

There are three components to migrate:

| Component | Currently | After Migration |
|---|---|---|
| Google Sheet | Your personal Google account | Reverie's Workspace |
| Apps Script Web App | Your personal Google account | Reverie's Workspace |
| GitHub Secrets | Pointing at your accounts | Updated to point at Reverie's |

The GitHub repo, Actions pipeline, and the site itself on GitHub Pages don't need to change at all.

---

## Step 1 — Copy the Google Sheet to Reverie's Drive

1. Open the **Reverie Coaster Club** sheet in your Google Drive
2. **File → Make a copy**
3. In the dialog, check **"Share it with the same people"** if desired
4. Click the **folder icon** and navigate to a shared Reverie Workspace drive
5. Click **Make a copy**
6. Open the new copy and grab the **Sheet ID** from the URL:
   `https://docs.google.com/spreadsheets/d/`**`THIS_IS_THE_NEW_SHEET_ID`**`/edit`

---

## Step 2 — Create a new Apps Script project under Reverie's account

> This step must be done while logged into Reverie's Google Workspace account.

1. Go to [script.google.com](https://script.google.com) → **New Project**
2. Paste in the contents of `src/Code.gs` from the repo
3. Replace `YOUR_SPREADSHEET_ID_HERE` with the new Sheet ID from Step 1
4. Save the project (name it something like **Reverie Coaster Club API**)

---

## Step 3 — Deploy the new Apps Script as a Web App

Still in the new Apps Script project:

1. Click **Deploy → New Deployment**
2. Click the **gear icon** → select **Web App**
3. Configure:
   - **Description:** Coaster Club v1
   - **Execute as:** Me (Reverie's account)
   - **Who has access:** Anyone
4. Click **Deploy**
5. **Copy the Web App URL** — it ends in `/exec` and looks like:
   `https://script.google.com/macros/s/AKfycb.../exec`

---

## Step 4 — Update GitHub Secrets

In the GitHub repo → **Settings → Secrets and variables → Actions**:

| Secret | Action |
|---|---|
| `APPS_SCRIPT_URL` | Replace with the new Web App URL from Step 3 |
| `CLASP_CREDENTIALS` | Replace with credentials from Reverie's account (see below) |
| `CLASP_JSON` | Replace with new Script ID from Reverie's project (see below) |
| `DEPLOYMENT_ID` | Replace with new Deployment ID from Reverie's project (see below) |

### Getting new CLASP_CREDENTIALS
On a machine logged into Reverie's Google account:
```bash
npm install -g @google/clasp
clasp login
cat ~/.clasprc.json
```
Copy the full JSON contents into the `CLASP_CREDENTIALS` secret.

### Getting new CLASP_JSON
In the new Apps Script project URL:
`https://script.google.com/home/projects/`**`SCRIPT_ID`**`/edit`

The secret value should be:
```json
{"scriptId":"YOUR_NEW_SCRIPT_ID","rootDir":"./src"}
```

### Getting new DEPLOYMENT_ID
In the Apps Script editor → **Deploy → Manage Deployments** → copy the Deployment ID (not the Web App URL — it looks like `AKfycb...` without `/exec`).

---

## Step 5 — Trigger a new build

Once all secrets are updated:

1. Go to **Actions → Build & Deploy → Run workflow**
2. Confirm the build succeeds and the site deploys
3. Test a form submission and verify it lands in Reverie's Sheet

---

## Step 6 — Verify notifications

The Google Sheets notification (Tools → Notification settings) is tied to the Sheet, not the script. You'll need to set it up again on the new copy:

1. Open the new Reverie Sheet
2. **Tools → Notification settings → Edit notifications**
3. Set: **Any changes are made** → **Email — right away**
4. Enter the email address that should receive notifications

---

## Step 7 — Clean up (optional)

Once everything is confirmed working under Reverie's account:

- You can delete the original Sheet from your personal Drive
- You can delete the original Apps Script project from your account
- Remove yourself from any shared access if appropriate

---

## Rollback

If anything goes wrong, the old secrets are still in your password manager / `.clasprc.json`. Just revert the GitHub Secrets to the previous values and re-run the workflow — the site will be back on your account within minutes.

---

## Summary Checklist

- [ ] Sheet copied to Reverie's Drive
- [ ] New Sheet ID noted
- [ ] New Apps Script project created under Reverie's account
- [ ] `SPREADSHEET_ID` updated in Code.gs
- [ ] New Web App deployed, URL copied
- [ ] `APPS_SCRIPT_URL` secret updated in GitHub
- [ ] `CLASP_CREDENTIALS` secret updated with Reverie's credentials
- [ ] `CLASP_JSON` secret updated with new Script ID
- [ ] `DEPLOYMENT_ID` secret updated
- [ ] Build & Deploy Action triggered and successful
- [ ] Test submission verified in Reverie's Sheet
- [ ] Email notifications configured on new Sheet
- [ ] Old resources cleaned up (optional)

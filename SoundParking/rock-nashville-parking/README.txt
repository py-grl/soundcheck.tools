# Rock Nashville Parking — Deployment Guide
# ==========================================
# READ THIS TOP TO BOTTOM. Every command is explained.
# Do not skip steps.


# ── STEP 1: Connect to your VPS ───────────────────────────────────────────────
#
# On your local Windows machine:
#   1. Press Windows key + R
#   2. Type: mstsc
#   3. Hit Enter
#   4. In the "Computer" box, type your VPS IP address (e.g. 123.456.78.9)
#   5. Click Connect
#   6. Log in with your username (usually "Administrator") and your VPS password
#
# You're now looking at your VPS desktop. Everything below happens IN there.


# ── STEP 2: Install Node.js ───────────────────────────────────────────────────
#
# Node.js is the engine that runs your server.
#
#   1. Open a browser ON THE VPS (not your laptop)
#   2. Go to: https://nodejs.org
#   3. Download the LTS version (the one that says "Recommended For Most Users")
#   4. Run the installer — click Next through everything, keep all defaults
#   5. When it finishes, open Command Prompt (search "cmd" in the Start menu)
#   6. Type this and hit Enter:
#
#        node --version
#
#   You should see something like: v20.11.0
#   If you do, Node is installed. If not, restart and try again.


# ── STEP 3: Copy the project to your VPS ─────────────────────────────────────
#
# Option A — GitHub (recommended since you have an account):
#
#   First, push this project to a GitHub repo on your laptop.
#   Then on the VPS, install Git: https://git-scm.com/download/win
#
#   In Command Prompt on the VPS:
#
#        git clone https://github.com/YOUR_USERNAME/rock-nashville-parking.git
#        cd rock-nashville-parking
#
# Option B — Manual copy:
#
#   Use Windows File Explorer or a tool like WinSCP to drag the project folder
#   onto the VPS. Then open Command Prompt, navigate to it:
#
#        cd C:\path\to\rock-nashville-parking


# ── STEP 4: Install dependencies ─────────────────────────────────────────────
#
# Remember package.json lists the libraries the project needs.
# This command reads that list and downloads them all:
#
#      npm install
#
# npm = Node Package Manager. It fetches code libraries from the internet
# and puts them in a folder called node_modules. You'll see it appear.
# This only needs to happen once (or when dependencies change).


# ── STEP 5: Start the server ──────────────────────────────────────────────────
#
#      npm start
#
# You should see:
#   Database ready.
#   Rock Nashville Parking running at http://localhost:3000
#
# Test it on the VPS by opening a browser and going to: http://localhost:3000
# The parking app should load. Add a test reservation.


# ── STEP 6: Open the firewall port ───────────────────────────────────────────
#
# Right now port 3000 is blocked to the outside world.
# A "port" is like a numbered door on your server. We need to open door 3000.
#
# On Windows VPS:
#   1. Search "Windows Defender Firewall" in the Start menu
#   2. Click "Advanced settings"
#   3. Click "Inbound Rules" on the left
#   4. Click "New Rule..." on the right
#   5. Select "Port" → Next
#   6. Select "TCP", type 3000 → Next
#   7. Select "Allow the connection" → Next → Next
#   8. Name it "Node Parking App" → Finish
#
# Also check your VPS provider's dashboard — some have a separate firewall
# (called a "Security Group" on some platforms) where you also need to allow
# port 3000 for TCP traffic.


# ── STEP 7: Access from any browser ──────────────────────────────────────────
#
# On any computer, phone, or browser — go to:
#
#      http://YOUR_VPS_IP:3000
#
# Example: http://123.456.78.9:3000
#
# Share that URL with your team and everyone is reading/writing the same data.


# ── STEP 8: Keep it running after you close the terminal ─────────────────────
#
# Right now if you close Command Prompt, the server stops.
# To keep it running permanently, install PM2 — a process manager:
#
#      npm install -g pm2
#      pm2 start server.js --name "parking"
#      pm2 save
#      pm2 startup
#
# PM2 keeps your app alive 24/7 and restarts it automatically if it crashes
# or if the VPS reboots. This is what "production" servers use.
#
# To check if it's running:   pm2 status
# To see logs:                pm2 logs parking
# To stop it:                 pm2 stop parking
# To restart it:              pm2 restart parking


# ── LATER: Attach a domain name ──────────────────────────────────────────────
#
# When Rock Nashville gets a domain (e.g. parking.rocknashville.com):
#   1. In your domain registrar's DNS settings, add an A record
#      pointing the subdomain to your VPS IP address
#   2. Install nginx as a reverse proxy to forward port 80 → 3000
#      so people don't have to type :3000 in the URL
#   3. Install a free SSL certificate via Let's Encrypt (certbot)
#      so it's https:// not http://
#
# That's a separate guide — ask Claude when you're ready for it.


# ── TROUBLESHOOTING ───────────────────────────────────────────────────────────
#
# "npm is not recognized"
#   → Node.js didn't install correctly. Restart the VPS and try again.
#
# "Cannot find module 'better-sqlite3'"
#   → You skipped npm install. Run it.
#
# "Port 3000 refused / can't connect from outside"
#   → Firewall isn't open. Re-do Step 6.
#
# "Database error"
#   → Make sure you're running the server FROM inside the project folder.
#     cd rock-nashville-parking && npm start

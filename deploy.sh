#!/bin/bash

# Configuration
REPO_PATH="/root/nexhacks-2026"
LOG_FILE="${REPO_PATH}/deploy.log"
DISCORD_WEBHOOK="${DISCORD_WEBHOOK_URL}"  
GITHUB_REPO="nexhacks-2026"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Function to send Discord webhook
send_discord() {
    local status=$1
    local message=$2
    local color=$3

    if [ -z "$DISCORD_WEBHOOK" ]; then
        log "WARNING: DISCORD_WEBHOOK_URL not set, skipping Discord notification"
        return
    fi

    local title="Deployment Successful"
    [ "$status" = "failure" ] && title="Deployment Failed"

    local commit=$(git rev-parse --short HEAD 2>/dev/null || echo "N/A")

    local payload=$(cat <<EOF
{
    "content": "$ **$title** - $GITHUB_REPO",
    "embeds": [
        {
            "title": "$title",
            "color": $color,
            "fields": [
                {
                    "name": "Repository",
                    "value": "$GITHUB_REPO",
                    "inline": true
                },
                {
                    "name": "Branch",
                    "value": "main",
                    "inline": true
                },
                {
                    "name": "Commit",
                    "value": "\`$commit\`",
                    "inline": true
                },
                {
                    "name": "Server",
                    "value": "$(hostname)",
                    "inline": true
                },
                {
                    "name": "Status",
                    "value": "$message",
                    "inline": false
                },
                {
                    "name": "Timestamp",
                    "value": "$(date '+%Y-%m-%d %H:%M:%S %Z')",
                    "inline": false
                }
            ]
        }
    ]
}
EOF
)

    curl -X POST "$DISCORD_WEBHOOK" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        2>/dev/null || log "WARNING: Failed to send Discord notification"
}

# Check if deployment already in progress
if [ -f "${REPO_PATH}/.deploy.lock" ]; then
    log "Deployment already in progress, skipping"
    exit 0
fi

# Create lock file
touch "${REPO_PATH}/.deploy.lock"
trap "rm -f ${REPO_PATH}/.deploy.lock" EXIT

# Navigate to the repository
cd "$REPO_PATH" || exit 1

log "Checking git status for $REPO_PATH"

# Fetch latest changes from remote
git fetch origin main || {
    log "ERROR: Failed to fetch from origin"
    send_discord "failure" "Failed to fetch from origin" "15158332"
    exit 1
}

# Check if local main is behind remote main
LOCAL=$(git rev-parse main)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    log "New changes detected on main branch"

    # Pull the latest changes
    log "Pulling latest changes..."
    git pull origin main || {
        log "ERROR: Failed to pull changes"
        send_discord "failure" "Failed to pull changes" "15158332"
        exit 1
    }

    # Stop and remove containers
    log "Running docker compose down..."
    docker compose down || {
        log "ERROR: docker compose down failed"
        send_discord "failure" "docker compose down failed" "15158332"
        exit 1
    }

    # Build and start containers
    log "Running docker compose up -d --build..."
    docker compose up -d --build || {
        log "ERROR: docker compose up -d --build failed"
        send_discord "failure" "docker compose up -d --build failed" "15158332"
        exit 1
    }

    log "Deployment completed successfully"
    send_discord "success" "Docker containers rebuilt and running" "3066993"
else
    log "No new changes on main branch"
fi

exit 0
#!/bin/bash

# Store the root directory path
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Setting up RepoScout..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed. Please install Python from https://www.python.org/downloads/"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip is not installed. Please install pip from https://pip.pypa.io/en/stable/installation/"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js from https://nodejs.org/en/download/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install npm from https://docs.npmjs.com/downloading-and-installing-node-js-and-npm"
    exit 1
fi

# Setup backend
echo "Setting up backend..."
cd "$ROOT_DIR/backend"
pip3 install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "GITHUB_TOKEN=\"ENTER YOUR GITHUB Personal Access Token\"" > .env
    echo "Please update the GITHUB_TOKEN in backend/.env with your GitHub Personal Access Token"
fi

# Setup frontend
echo "Setting up frontend..."
cd "$ROOT_DIR/frontend"
npm install

echo "Setup complete!"
echo "Starting the application..."

# Function to detect the terminal emulator
detect_terminal() {
    if [ -n "$TERM_PROGRAM" ]; then
        case "$TERM_PROGRAM" in
            "iTerm.app") echo "iterm" ;;
            "Apple_Terminal") echo "osx" ;;
            *) echo "xterm" ;;
        esac
    else
        echo "xterm"
    fi
}

# Get the terminal type
TERM_TYPE=$(detect_terminal)

# Start backend server
case "$TERM_TYPE" in
    "iterm")
        osascript -e "tell application \"iTerm\"
            create window with default profile
            tell current session
                write text \"cd '$ROOT_DIR/backend' && python3 app.py\"
            end tell
        end tell"
        ;;
    "osx")
        osascript -e "tell application \"Terminal\"
            do script \"cd '$ROOT_DIR/backend' && python3 app.py\"
        end tell"
        ;;
    *)
        xterm -e "cd '$ROOT_DIR/backend' && python3 app.py" &
        ;;
esac

# Start frontend server
case "$TERM_TYPE" in
    "iterm")
        osascript -e "tell application \"iTerm\"
            create window with default profile
            tell current session
                write text \"cd '$ROOT_DIR/frontend' && npm start\"
            end tell
        end tell"
        ;;
    "osx")
        osascript -e "tell application \"Terminal\"
            do script \"cd '$ROOT_DIR/frontend' && npm start\"
        end tell"
        ;;
    *)
        xterm -e "cd '$ROOT_DIR/frontend' && npm start" &
        ;;
esac

echo "Both servers are starting in new windows."
echo "Please make sure to update your GitHub token in backend/.env if you haven't already." 
# RepoScout

RepoScout is an application that helps you find GitHub repositories that match your specific needs and requirements.

## Prerequisites

Before running the application, make sure you have the following installed:
- Node.js and npm
  - [Download Node.js and npm](https://nodejs.org/en/download/)
  - [Node.js Installation Guide](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)
- Python and pip
  - [Download Python](https://www.python.org/downloads/)
  - [Python Installation Guide](https://docs.python.org/3/using/index.html)
  - [pip Installation Guide](https://pip.pypa.io/en/stable/installation/)

## Quick Setup

We provide setup scripts to automate the installation process:

### For Windows Users
```powershell
.\setup.ps1
```

### For Unix-like Systems (Linux/macOS)
```bash
chmod +x setup.sh
./setup.sh
```

The setup scripts will:
1. Check if all prerequisites are installed
2. Install Python dependencies
3. Create the `.env` file for GitHub token
4. Install Node.js dependencies

## Manual Setup Instructions

1. **Backend Setup**
   - Navigate to the backend directory:
     ```bash
     cd backend
     ```
   - Install Python dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Create a `.env` file in the backend directory with your GitHub token:
     ```
     GITHUB_TOKEN="ENTER YOUR GITHUB Personal Access Token"
     ```
     > Note: A GitHub Personal Access Token is required to avoid rate limiting when fetching repositories.

2. **Frontend Setup**
   - Navigate to the frontend directory:
     ```bash
     cd frontend
     ```
   - Install Node.js dependencies:
     ```bash
     npm install
     ```

## Running the Application

1. **Start the Backend Server**
   - In the backend directory:
     ```bash
     python app.py
     ```

2. **Start the Frontend Development Server**
   - In the frontend directory:
     ```bash
     npm start
     ```

The application should now be running with the backend server and frontend development server active.
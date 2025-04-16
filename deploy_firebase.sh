#!/bin/bash

# 24/7 Stock Dashboard - Firebase Deployment Script
# This script automates the deployment of the stock dashboard to Firebase

# Text styling
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

echo -e "${BOLD}24/7 Stock Dashboard - Firebase Deployment${NC}\n"

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo -e "${RED}Firebase CLI not found!${NC}"
    echo -e "Installing Firebase CLI globally..."
    npm install -g firebase-tools
fi

# Login to Firebase
echo -e "\n${YELLOW}Step 1: Login to Firebase${NC}"
firebase login

# Check if the Firebase project is set up
echo -e "\n${YELLOW}Step 2: Initializing Firebase project${NC}"
echo -e "If this is your first time deploying, you'll need to set up a Firebase project."
echo -e "Otherwise, select the existing project when prompted."

# Install dependencies for functions
echo -e "\n${YELLOW}Step 3: Installing dependencies for Cloud Functions${NC}"
cd functions
echo -e "Installing npm packages..."
npm install
cd ..

# Deploy Firebase resources
echo -e "\n${YELLOW}Step 4: Deploying to Firebase${NC}"
echo -e "This will deploy your Firebase Hosting, Functions, and Realtime Database."
read -p "Continue with deployment? (y/n): " confirm

if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
    echo -e "Deploying..."
    firebase deploy
    
    echo -e "\n${GREEN}Deployment completed!${NC}"
    echo -e "Your app is now available at the Firebase hosting URL above."
    
    # Get Firebase hosting URL
    PROJECT_ID=$(grep "default" .firebaserc | cut -d '"' -f 4)
    if [[ ! -z "$PROJECT_ID" && "$PROJECT_ID" != "YOUR_FIREBASE_PROJECT_ID" ]]; then
        echo -e "\nAccess your app at: ${BOLD}https://$PROJECT_ID.web.app${NC}"
    fi
    
    echo -e "\n${YELLOW}Important:${NC}"
    echo -e "1. Make sure to update public/firebase-config.js with your actual Firebase configuration."
    echo -e "2. If you encounter any issues, check the Firebase console for error logs."
    echo -e "3. The first stock data update may take a few minutes to complete."
else
    echo -e "\n${YELLOW}Deployment cancelled.${NC}"
fi

echo -e "\n${BOLD}Deployment process finished.${NC}" 
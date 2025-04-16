# 24/7 Stock Dashboard - Firebase Setup and Deployment Guide

This guide will walk you through setting up and deploying the 24/7 Stock Dashboard application on Firebase.

## Prerequisites

1. [Node.js](https://nodejs.org/) installed (v14 or newer)
2. [Firebase CLI](https://firebase.google.com/docs/cli) installed
   ```
   npm install -g firebase-tools
   ```
3. A Firebase account (create one at [firebase.google.com](https://firebase.google.com/))

## Setup Steps

### 1. Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Enter a project name (e.g., "stock-dashboard")
4. Follow the prompts to complete project creation

### 2. Configure Firebase Features

#### Enable Authentication:
1. In Firebase Console, go to your project
2. Select "Authentication" from the left menu
3. Click "Get Started"
4. In the "Sign-in method" tab, enable "Email/Password"

#### Set up Realtime Database:
1. In Firebase Console, go to "Realtime Database"
2. Click "Create Database"
3. Choose a location (usually closest to your users)
4. Start in "test mode" for now (we'll secure it later)

### 3. Get Your Firebase Configuration

1. In Firebase Console, go to Project Settings (gear icon)
2. Scroll down to "Your apps" section
3. Click on the Web App icon (</>) to add a web app
4. Register your app with a nickname (e.g., "stock-dashboard-web")
5. Copy the Firebase configuration object

### 4. Update Project Files

1. Edit `public/firebase-config.js` and replace the placeholder values with your actual Firebase configuration
2. Edit `.firebaserc` and replace "YOUR_FIREBASE_PROJECT_ID" with your actual Firebase project ID

### 5. Deploy to Firebase

```bash
# Login to Firebase
firebase login

# Initialize project (if not already done)
# When prompted, select the features you want to use:
# - Hosting (for frontend)
# - Functions (for backend)
# - Realtime Database
firebase init

# Deploy everything
firebase deploy

# Or deploy specific services
firebase deploy --only hosting
firebase deploy --only functions
```

### 6. Access Your Deployed App

After successful deployment, Firebase will provide a hosting URL where your app is accessible (usually `https://YOUR-PROJECT-ID.web.app`).

## Troubleshooting

### Database Security Rules
If you encounter issues with accessing or writing to the database, check your security rules in `database.rules.json` and ensure they match your application's needs.

### Functions Deployment Issues
If functions fail to deploy:
1. Make sure you're on the Blaze (pay as you go) plan as functions require this
2. Check that your Node.js version matches the one specified in `functions/package.json`
3. Run `cd functions && npm install` before deploying

### Authentication Issues
If users can't sign in:
1. Ensure Authentication is enabled in Firebase console
2. Verify that the credentials in firebase-config.js are correct
3. Check browser console for specific error messages

## Maintaining Your Deployment

### Updating Your App
After making changes to your code:

```bash
# Deploy changes
firebase deploy
```

### Monitoring
Firebase Console provides monitoring for:
- Authentication users and sign-in methods
- Realtime Database content and usage
- Function executions and errors
- Hosting traffic and performance

## Extra Resources

- [Firebase Documentation](https://firebase.google.com/docs)
- [Firebase CLI Reference](https://firebase.google.com/docs/cli)
- [Firebase Hosting Guide](https://firebase.google.com/docs/hosting)
- [Firebase Functions Guide](https://firebase.google.com/docs/functions)
- [Firebase Authentication Guide](https://firebase.google.com/docs/auth)
- [Firebase Realtime Database Guide](https://firebase.google.com/docs/database) 
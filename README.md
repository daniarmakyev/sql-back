# Project Setup for Render Deployment

This document provides instructions for deploying the SQL Challenge Backend project to Render using Docker.

## Files Created

- **`Dockerfile`**: This file contains the instructions for building the Docker image for the application. It installs dependencies, copies the application code, and specifies the command to run the application.

- **`.dockerignore`**: This file lists files and directories that should be excluded from the Docker build context. This helps to reduce the size of the Docker image and speed up the build process.

## Deployment to Render

1. **Push to GitHub**: Make sure your project, including the `Dockerfile` and `.dockerignore` files, is pushed to a GitHub repository.

2. **Create a New Web Service on Render**:
   - Go to the Render dashboard and create a new "Web Service".
   - Connect your GitHub repository.
   - On the settings page:
     - **Name**: Give your service a name (e.g., `sql-challenge-api`).
     - **Region**: Choose a region close to your users.
     - **Branch**: Select the branch you want to deploy (e.g., `main`).
     - **Runtime**: Select `Docker`.
     - **Build Command**: You can leave this blank. Render will use the `Dockerfile` to build the image.
     - **Start Command**: This is defined by the `CMD` in your `Dockerfile`, so you can leave this blank or use the default.
     - **Port**: Set to `8000`.

3. **Add Environment Variables**:
   - You will need to add the environment variables from your `.env` file to the Render service. Go to the "Environment" tab for your service and add them as key-value pairs.

4. **Deploy**:
   - Click "Create Web Service". Render will automatically start the build and deployment process.

## Local Docker Build (Optional)

To build and run the Docker image locally for testing:

1. **Build the image**:
   ```bash
   docker build -t sql-challenge-api .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 --env-file .env sql-challenge-api
   ```
   This command assumes you have a `.env` file with the necessary environment variables.

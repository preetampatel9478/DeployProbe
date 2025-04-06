# DeployProbe

DeployProbe is a web application that tests if deployed websites can handle traffic storms and analyzes code quality for scalability.

## Deploying to Render

### Option 1: One-Click Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Option 2: Manual Deployment

1. Fork or clone this repository
2. Create a new Web Service in the Render Dashboard
3. Connect your GitHub/GitLab repository
4. Use the following settings:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Click "Create Web Service"

## Environment Variables

The following environment variables can be set in your Render dashboard:

- `FLASK_DEBUG`: Set to "true" to enable debug mode (default: "false")
- `PORT`: The port on which the application will run (default: 5000, but Render will set this automatically)

## Features

- Load testing simulation with customizable user capacity
- Code quality analysis focused on scalability
- Mobile responsiveness checking
- Page speed measurement
- Content assessment

## Getting Started

### Prerequisites

- Python 3.7+
- pip

### Installation

1. Clone the repository

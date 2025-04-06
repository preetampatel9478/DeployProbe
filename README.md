# DeployProbe

DeployProbe is a web application that tests if deployed websites can handle traffic storms and analyzes code quality for scalability.

## Overview

DeployProbe helps you understand if your website is ready for high traffic situations by simulating load, analyzing code quality, and providing actionable insights. Perfect for developers preparing for product launches or marketing campaigns that might drive sudden traffic spikes.

## Features

- **Load testing simulation** with customizable user capacity
- **Traffic storm handling** assessment (5,000-10,000+ users)
- **Code quality analysis** focused on scalability
- **Mobile responsiveness** checking
- **Page speed measurement**
- **Content assessment**
- **High concurrency testing**
- **Scalability recommendations**

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

## Getting Started

### Prerequisites

- Python 3.7+
- pip

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/DeployProbe.git
   cd DeployProbe
   ```

2. Create a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application
   ```bash
   python app.py
   ```

5. Navigate to `http://localhost:5000` in your browser

## How to Use DeployProbe

1. Enter the URL of the website you want to test
2. Specify the target user capacity (e.g., 5000 users)
3. Click "Launch Test" to begin the analysis
4. View the comprehensive report that includes:
   - Basic site accessibility
   - Code quality score
   - Mobile responsiveness
   - Page load speed
   - Estimated user capacity
   - High traffic readiness assessment
   - Scalability recommendations

## Understanding Your Results

The test results include multiple sections:

- **Site Status**: Confirms if your site is accessible
- **Load Test**: Shows how your site performs under simulated traffic
- **Scalability Analysis**: Estimates how many concurrent users your site can handle
- **Code Quality**: Analyzes implementation best practices for high-traffic sites
- **Mobile Responsiveness**: Checks if your site is optimized for mobile devices
- **Page Speed**: Measures load time and performance

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Flask
- Uses Beautiful Soup for HTML parsing
- Concurrent testing implemented with ThreadPoolExecutor

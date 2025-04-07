# Coupon Chatbot Web Interface

A modern web interface for the Coupon Chatbot that helps users find amazing deals and coupons across various platforms.

## Features

- Modern and responsive web interface
- Real-time chat interaction
- Quick suggestion chips for common queries
- Beautiful coupon code display
- Support for multiple platforms (Amazon, Flipkart, Food delivery, etc.)
- Powered by Google Gemini AI

## Prerequisites

- Python 3.8 or higher
- Google Gemini API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory and add your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

## Running the Application

1. Make sure your virtual environment is activated.

2. Run the Flask application:
```bash
python app.py
```

3. Open your web browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
├── app.py              # Flask application
├── coupon_chatbot.py   # Chatbot logic
├── requirements.txt    # Python dependencies
├── static/            # Static files
│   ├── css/
│   │   └── style.css  # Styles
│   └── js/
│       └── script.js  # Frontend logic
└── templates/
    └── index.html     # Main template
```

## Usage

1. Type your message in the input field or click on suggestion chips
2. The chatbot will respond with relevant coupon codes and deals
3. Coupon codes are displayed in a special format with all relevant details
4. You can ask for deals from specific platforms or categories

## Deployment

### Option 1: Render (Recommended for Beginners)

1. Sign up for a free account at [Render](https://render.com/)
2. From your dashboard, click "New" and select "Web Service"
3. Connect your GitHub repository or upload your code directly
4. Configure your web service:
   - Name: `jugaad-coupon-chatbot` (or any name you prefer)
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:app`
5. Add your environment variables (GOOGLE_API_KEY) in the "Environment" section
6. Click "Create Web Service"

### Option 2: Heroku

1. Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Login to Heroku: `heroku login`
3. Create a new Heroku app: `heroku create jugaad-coupon-bot`
4. Push your code to Heroku: `git push heroku main`
5. Set your environment variables: `heroku config:set GOOGLE_API_KEY=your_api_key_here`
6. Open your app: `heroku open`

### Option 3: PythonAnywhere

1. Sign up for a [PythonAnywhere](https://www.pythonanywhere.com/) account
2. Upload your code using the Files tab or via Git
3. Create a new web app from the Web tab
4. Configure your WSGI file to point to your Flask app
5. Set up your environment variables in the WSGI configuration file
6. Reload your web app

### Option 4: AWS Elastic Beanstalk

1. Install the [AWS CLI](https://aws.amazon.com/cli/) and [EB CLI](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3-install.html)
2. Initialize your EB application: `eb init`
3. Create an environment: `eb create jugaad-env`
4. Deploy your application: `eb deploy`
5. Set environment variables: `eb setenv GOOGLE_API_KEY=your_api_key_here`

## Important Deployment Notes

1. Make sure your `.env` file is included in `.gitignore` to keep your API keys secure
2. For production deployment, set `debug=False` in your Flask app
3. Consider using a production-ready database instead of file-based storage
4. Set up proper error logging and monitoring for production use

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
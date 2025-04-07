from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import logging
from coupon_chatbot import CouponChatbot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize chatbot
chatbot = None

def get_chatbot():
    global chatbot
    if chatbot is None:
        try:
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            logger.debug(f"API Key found: {api_key[:5]}...")  # Log first 5 chars of API key
            chatbot = CouponChatbot(api_key)
            logger.info("Chatbot initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing chatbot: {str(e)}", exc_info=True)
            raise
    return chatbot

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400

        message = data['message']
        logger.debug(f"Received message: {message}")
        chatbot = get_chatbot()
        response = chatbot.get_response(message)
        logger.debug(f"Generated response: {response}")
        
        return jsonify({'response': response})
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/greeting')
def greeting():
    try:
        return jsonify({'greeting': "Namaste! I'm JUGAAD, your personal shopping assistant. I'm here to help you save money with the best deals and coupons. What would you like to shop for today? 🎉"})
    except Exception as e:
        logger.error(f"Error in greeting endpoint: {str(e)}", exc_info=True)
        return jsonify({'greeting': "Namaste! I'm JUGAAD, your personal shopping assistant. How can I help you save money today? 🎉"})

if __name__ == '__main__':
    app.run(debug=True) 
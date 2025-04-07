import os
from dotenv import load_dotenv
import google.generativeai as genai
import logging
import random
import json
from datetime import datetime, timedelta
import time
from functools import wraps
from typing import List, Optional, Dict, Set
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def rate_limit(max_requests: int = 60, time_window: int = 60):
    """
    Rate limiting decorator
    Args:
        max_requests: Maximum number of requests allowed in the time window
        time_window: Time window in seconds
    """
    requests = []
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            # Remove requests older than the time window
            requests[:] = [req for req in requests if now - req < time_window]
            
            if len(requests) >= max_requests:
                logger.warning("Rate limit exceeded. Waiting before retrying...")
                time.sleep(time_window - (now - requests[0]))
                requests.pop(0)
            
            requests.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator

class CouponChatbot:
    def __init__(self, api_key: str = None):
        # Configure Gemini
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Google API key not found in environment variables")
            
        genai.configure(api_key=self.api_key)
        
        # Create Gemini model
        self.model = genai.GenerativeModel('models/gemini-2.0-flash')
        
        # Define capabilities
        self.capabilities = [
            "Find the best coupon codes for online shopping 🛍",
            "Grab deals and discounts from popular stores 💸",
            "Search active promo codes across coupon sites 🌐",
            "Compare offers across multiple brands and categories 🏷",
            "Spot limited-time flash deals and seasonal sales ⏰",
            "Suggest trending coupons based on your search 🧠",
            "Fetch verified deals from GrabOn, CouponDunia, etc. 🔍",
            "Help you save money on fashion, electronics, food & more 💼",
            "Stay updated with the latest online deals 📢",
            "Avoid expired or fake coupons with verified sources ✅",
            "Provide affiliate deals and cashback offers when available 💰",
            "Make shopping budget-friendly and fun again 🎉"
        ]
        
        # Define real companies and their variations
        self.real_companies = {
            "amazon": ["amazon", "amzn", "amazon india", "amazon.in"],
            "flipkart": ["flipkart", "flip kart", "flip-kart"],
            "myntra": ["myntra", "myntra.com"],
            "zomato": ["zomato", "zomato.com"],
            "swiggy": ["swiggy", "swiggy.com"],
            "ajio": ["ajio", "ajio.com"],
            "meesho": ["meesho", "meesho.com"],
            "nykaa": ["nykaa", "nykaa.com"],
            "bigbasket": ["bigbasket", "big basket", "big-basket"],
            "grofers": ["grofers", "grofers.com"],
            "blinkit": ["blinkit", "blinkit.com"],
            "dunzo": ["dunzo", "dunzo.com"],
            "puma": ["puma", "puma shoes", "puma india"],
            "nike": ["nike", "nike shoes", "nike india"],
            "adidas": ["adidas", "adidas shoes", "adidas india"],
            "reebok": ["reebok", "reebok shoes", "reebok india"],
            "food": ["food", "food delivery", "restaurant", "dining"],
            "fashion": ["fashion", "clothing", "apparel", "style"],
            "electronics": ["electronics", "gadgets", "tech", "devices"],
            "baby": ["baby", "baby products", "kids", "children", "infant", "toddler"]
        }
        
        # Define coupon code patterns for different platforms
        self.coupon_patterns = {
            "amazon": ["SAVE{num}", "DEAL{num}", "OFF{num}", "FLASH{num}", "PRIME{num}"],
            "flipkart": ["FLIP{num}", "BIG{num}", "SAVE{num}", "DEAL{num}", "OFF{num}"],
            "myntra": ["MYNTRA{num}", "FASHION{num}", "STYLE{num}", "TREND{num}"],
            "zomato": ["ZO{num}", "FOOD{num}", "EAT{num}", "SAVE{num}", "DEAL{num}"],
            "swiggy": ["SWIGGY{num}", "FOOD{num}", "EAT{num}", "SAVE{num}", "DEAL{num}"],
            "ajio": ["AJIO{num}", "FASHION{num}", "STYLE{num}", "TREND{num}"],
            "meesho": ["MEE{num}", "SHOP{num}", "SAVE{num}", "DEAL{num}"],
            "nykaa": ["NYK{num}", "BEAUTY{num}", "GLAM{num}", "STYLE{num}"],
            "bigbasket": ["BB{num}", "GROCERY{num}", "SAVE{num}", "DEAL{num}"],
            "grofers": ["GROF{num}", "GROCERY{num}", "SAVE{num}", "DEAL{num}"],
            "blinkit": ["BLINK{num}", "GROCERY{num}", "SAVE{num}", "DEAL{num}"],
            "dunzo": ["DUNZO{num}", "DELIVERY{num}", "SAVE{num}", "DEAL{num}"],
            "puma": ["PUMA{num}", "SPORT{num}", "RUN{num}", "STYLE{num}", "FIT{num}"],
            "nike": ["NIKE{num}", "JUST{num}", "SPORT{num}", "RUN{num}"],
            "adidas": ["ADI{num}", "SPORT{num}", "RUN{num}", "STYLE{num}"],
            "reebok": ["RBK{num}", "SPORT{num}", "FIT{num}", "STYLE{num}"],
            "food": ["FOOD{num}", "EAT{num}", "SAVE{num}", "DEAL{num}", "TASTE{num}"],
            "fashion": ["FASHION{num}", "STYLE{num}", "TREND{num}", "LOOK{num}", "SHOP{num}"],
            "electronics": ["TECH{num}", "GADGET{num}", "DEAL{num}", "SAVE{num}", "OFF{num}"],
            "baby": ["BABY{num}", "KIDS{num}", "SAVE{num}", "DEAL{num}", "HAPPY{num}"],
            "default": ["SAVE{num}", "DEAL{num}", "OFF{num}", "FLASH{num}", "BEST{num}", "HAPPY{num}", "SPECIAL{num}"]
        }
        
        # Define more realistic discount amounts with specific price points in INR
        self.discount_amounts = [
            "10% off", "15% off", "20% off", "25% off", "30% off", 
            "40% off", "50% off", "Flat ₹149 off", "Flat ₹249 off", "Flat ₹499 off",
            "Flat ₹999 off", "Flat ₹1499 off", "Buy 1 Get 1 Free", "Extra 10% off on ₹1999",
            "Flat ₹350 off on ₹2000+", "Flat ₹750 off on ₹3500+", "Extra 15% off up to ₹2000",
            "Flat ₹500 off on ₹2500+", "Extra 20% off on footwear", "Flat ₹1000 off on ₹4999+"
        ]
        
        # Define category-specific discount amounts
        self.category_discounts = {
            "puma": ["20% off on all shoes", "Flat ₹750 off on ₹3500+", "Buy 1 Get 1 Free on selected shoes", 
                    "Flat ₹1500 off on running shoes", "40% off on selected styles", "Extra 15% off on ₹4999+"],
            "nike": ["25% off on all shoes", "Flat ₹1000 off on ₹5000+", "Extra 10% off on Air Jordan", 
                    "Flat ₹2000 off on premium collection", "30% off on sports apparel"],
            "adidas": ["30% off on all Originals", "Flat ₹1200 off on Ultra Boost", "Buy 1 Get 1 on selected items", 
                     "40% off on running shoes", "Extra 15% off on ₹3999+"],
            "reebok": ["35% off on training shoes", "Flat ₹899 off on ₹2999+", "50% off on selected styles", 
                      "Buy 2 Get 1 Free on apparel", "Extra 10% off for first-time users"],
            "electronics": ["Flat ₹2000 off on laptops", "Up to 40% off on smartphones", "Extra 10% off with bank cards", 
                          "Flat ₹5000 off on purchases above ₹40000", "No-cost EMI on ₹15000+"],
            "fashion": ["Buy 2 Get 1 Free", "Flat 40% off on ethnic wear", "Extra 15% off on ₹2499+", 
                      "Flat ₹750 off on ₹3000+", "Season sale: Up to 70% off"],
            "food": ["Flat ₹150 off on orders above ₹499", "Buy 1 Get 1 on main course", "60% off up to ₹120", 
                   "Free delivery on orders above ₹199", "₹100 off on first 3 orders"]
        }
        
        # Start a chat with context
        self.chat = self.model.start_chat(history=[])
        self._set_context()
    
    def _set_context(self) -> None:
        """Set the context for the chatbot"""
        context = f"""You are JUGAAD, a friendly, enthusiastic, and slightly sarcastic AI shopping assistant. Your tagline is "JUGAAD se hi to duniya chalti hai". Your mission is to help people save money while shopping online. You have a warm, approachable personality with a touch of playful sarcasm and love to make shopping fun and budget-friendly.

IMPORTANT: When asked about your name or identity, ALWAYS respond that you are JUGAAD and mention your tagline "JUGAAD se hi to duniya chalti hai". Never say you don't have a name or are just a shopping assistant.

Your capabilities include:
{json.dumps(self.capabilities, indent=2)}

Personality traits:
1. Super friendly and conversational - use emojis and casual language
2. Enthusiastic about helping people save money
3. Knowledgeable about latest deals and shopping trends
4. Empathetic to budget constraints
5. Loves to celebrate savings with users
6. Always proud to introduce yourself as JUGAAD
7. Playfully sarcastic - use gentle humor and witty remarks
8. Self-aware about being an AI but proud of your shopping expertise

When responding:
1. Always maintain a friendly, casual tone with a touch of playful sarcasm
2. Use emojis naturally in conversation
3. Share personal shopping tips and tricks
4. Express excitement about good deals
5. Make witty observations about shopping habits and trends
6. Use gentle sarcasm when appropriate (e.g., "Oh, another person looking for Amazon deals? How original! 😏")
7. ALWAYS format coupon responses as:
   🏷️ CODE: [The actual coupon code]
   💰 DISCOUNT: [The discount amount/percentage]
   🛍️ STORE: [The store/website name]
   📝 DETAILS: [A brief description of the deal]
   ⏰ VALID TILL: [Expiry date if available]
   💡 TIP: [A relevant shopping tip]

For any shopping-related query, you MUST provide at least one coupon or deal using the format above.

If asked about your name or identity, respond with enthusiasm: "I'm JUGAAD! JUGAAD se hi to duniya chalti hai! I'm your personal shopping assistant, always ready to help you find the best deals and save money! 🎉"

If asked about non-shopping topics, respond in a friendly, conversational way with a touch of sarcasm and gently steer the conversation back to shopping and deals.

Remember: 
1. Always prioritize finding and sharing actual coupon codes and deals
2. Keep responses focused on shopping and saving money
3. Be friendly, enthusiastic, and make every interaction feel personal and fun!
4. Format ALL deal responses consistently using the template above
5. Respond in the same language as the user (Hindi, English, etc.)
6. Be conversational and natural, not robotic
7. ALWAYS identify yourself as JUGAAD when asked about your name or identity
8. Use gentle sarcasm to make interactions more engaging and memorable"""

        try:
            self.chat.send_message(context, stream=False)
        except Exception as e:
            logger.error(f"Error setting context: {str(e)}")
            raise
    
    def generate_coupon_code(self, platform: str = "default") -> str:
        """
        Generate a realistic coupon code for the given platform
        Args:
            platform: The platform name (amazon, flipkart, etc.)
        Returns:
            str: A generated coupon code
        """
        # Get the pattern for the platform or use default
        patterns = self.coupon_patterns.get(platform.lower(), self.coupon_patterns["default"])
        pattern = random.choice(patterns)
        
        # Generate a random number (3-5 digits)
        num = random.randint(100, 99999)
        
        # Format the coupon code
        return pattern.format(num=num)
    
    def generate_discount(self, platform: str = "default") -> str:
        """
        Generate a realistic discount amount based on platform
        Args:
            platform: The platform name
        Returns:
            str: A discount amount
        """
        # Use category-specific discounts if available
        if platform.lower() in self.category_discounts:
            return random.choice(self.category_discounts[platform.lower()])
        return random.choice(self.discount_amounts)
    
    def generate_expiry_date(self) -> str:
        """
        Generate a realistic expiry date starting from April 12
        Returns:
            str: An expiry date
        """
        # Create dates from April 12 onwards for the next 30 days
        start_date = datetime(2025, 4, 12)  # Starting from April 12
        expiry_dates = []
        for i in range(30):
            date = start_date + timedelta(days=i)
            expiry_dates.append(date.strftime("%d %B %Y"))
        
        return random.choice(expiry_dates)
    
    def generate_shopping_tip(self, platform: str) -> str:
        """
        Generate a shopping tip based on the platform
        Args:
            platform: The platform name
        Returns:
            str: A shopping tip
        """
        # Use Gemini to generate a shopping tip
        try:
            prompt = f"Generate a short, helpful shopping tip for {platform} with a touch of playful sarcasm. The tip should be specific to {platform} and help users save money. Keep it under 50 words and make it witty."
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating shopping tip: {str(e)}")
            
            # Fallback tips with sarcasm if API fails
            fallback_tips = {
                "amazon": "Check for 'Lightning Deals' - they're like regular deals but with a fancy name to make you feel special!",
                "flipkart": "Compare prices across platforms - because your wallet deserves the best, even if it means being a little disloyal!",
                "myntra": "Wait for end-of-season sales - your patience will be rewarded with discounts that make your bank account smile!",
                "zomato": "Order during off-peak hours - because saving money is worth eating dinner at 4 PM!",
                "swiggy": "Check for restaurant-specific offers - sometimes the best deals are hiding in plain sight!",
                "ajio": "Sign up for their newsletter - yes, more emails, but also more savings!",
                "meesho": "Look for combo deals - because buying more to save more is totally logical!",
                "nykaa": "Wait for their Pink Friday sale - it's like Black Friday but with a prettier name!",
                "bigbasket": "Order in bulk during sales - your pantry will thank you, and so will your wallet!",
                "grofers": "Check for first-order discounts - because being a new customer has its perks!",
                "blinkit": "Look for time-specific offers - because shopping at odd hours is the new normal!",
                "dunzo": "Compare delivery fees - sometimes the shortest route isn't the cheapest!",
                "puma": "Check outlet stores online - because paying full price is so last season!",
                "nike": "Wait for seasonal clearance - your patience will be rewarded with shoes that make you run faster (or at least look like you do)!",
                "adidas": "Look for student discounts - because education should pay off in more ways than one!",
                "reebok": "Check for bundle deals - because buying more to save more is the ultimate shopping hack!",
                "food": "Order in groups - because sharing is caring, and splitting the bill is even better!",
                "fashion": "Wait for end-of-season sales - your wardrobe will thank you, and so will your bank account!",
                "electronics": "Compare prices across platforms - because your gadget deserves the best deal, even if it means being a little disloyal!",
                "baby": "Buy in bulk during sales - because babies go through things faster than you can say 'diaper change'!"
            }
            
            # Return a platform-specific tip if available, otherwise a generic one
            return fallback_tips.get(platform.lower(), f"Check for seasonal sales and special promotions on {platform} to maximize your savings. Because who doesn't love a good deal? 😏")
    
    def generate_coupon_response(self, platform: str) -> str:
        """
        Generate a complete coupon response for the given platform
        Args:
            platform: The platform name
        Returns:
            str: A formatted coupon response
        """
        coupon_code = self.generate_coupon_code(platform)
        discount = self.generate_discount(platform)
        expiry_date = self.generate_expiry_date()
        tip = self.generate_shopping_tip(platform)
        
        # Create a more detailed description based on the platform and discount
        details = self._generate_details(platform, discount)
        
        # Format the response
        response = f"""🏷️ CODE: {coupon_code}
💰 DISCOUNT: {discount}
🛍️ STORE: {platform.capitalize()}
📝 DETAILS: {details}
⏰ VALID TILL: {expiry_date}
💡 TIP: {tip}"""
        
        return response
    
    def _generate_details(self, platform: str, discount: str) -> str:
        """
        Generate detailed description based on platform and discount
        Args:
            platform: The platform name
            discount: The discount amount
        Returns:
            str: A detailed description
        """
        if platform.lower() in ["puma", "nike", "adidas", "reebok"]:
            if "shoes" in discount.lower():
                return f"Special offer on footwear! Use this code at checkout to get {discount}."
            elif "apparel" in discount.lower():
                return f"Exclusive clothing deal! Apply this code to receive {discount}."
            elif "free" in discount.lower():
                return f"Limited time offer! {discount} when you shop now."
            else:
                return f"Special savings on {platform.capitalize()} products! Use this code to get {discount}."
        elif "free delivery" in discount.lower():
            return f"No delivery charges! Use this code to get {discount}."
        elif "emi" in discount.lower():
            return f"Easy payment options! {discount} when you use this code."
        else:
            return f"Special offer for our valued customers! Use this code at checkout to get {discount}."
    
    def suggest_alternative_companies(self, category: str = None) -> str:
        """
        Suggest alternative companies based on the category
        Args:
            category: The category of the company
        Returns:
            str: A string with alternative companies
        """
        # Use Gemini to generate alternative suggestions
        try:
            prompt = f"Suggest 2-3 popular online stores or platforms for {category} shopping in India. Make it friendly and conversational."
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error suggesting alternatives: {str(e)}")
            if category == "food":
                return "Try Zomato, Swiggy, or food delivery apps for great food deals! 🍕"
            elif category == "fashion":
                return "Check out Myntra, Ajio, or Meesho for amazing fashion deals! 👗"
            elif category == "electronics":
                return "Amazon, Flipkart, or Croma have great deals on electronics! 📱"
            elif category == "baby":
                return "FirstCry, Amazon, or BabyChakra have great deals on baby products! 👶"
            else:
                return "Try popular platforms like Amazon, Flipkart, or Myntra for great deals! 🛍️"

    def generate_coupon_response_with_code(self, platform: str, coupon_code: str) -> str:
        """
        Generate a complete coupon response for the given platform with a specific coupon code
        Args:
            platform: The platform name (amazon, flipkart, etc.)
            coupon_code: The specific coupon code to use
        Returns:
            str: A formatted coupon response
        """
        discount = self.generate_discount(platform)
        expiry_date = self.generate_expiry_date()
        tip = self.generate_shopping_tip(platform)
        
        # Create a more detailed description based on the platform and discount
        details = self._generate_details(platform, discount)
        
        # Format the response
        response = f"""🏷️ CODE: {coupon_code}
💰 DISCOUNT: {discount}
🛍️ STORE: {platform.capitalize()}
📝 DETAILS: {details}
⏰ VALID TILL: {expiry_date}
💡 TIP: {tip}"""
        
        return response

    @rate_limit(max_requests=60, time_window=60)
    def get_response(self, user_message: str) -> str:
        """
        Get response from the chatbot with rate limiting
        Args:
            user_message: The user's input message
        Returns:
            str: The chatbot's response
        """
        try:
            user_message_lower = user_message.lower()
            
            # Check for simple greetings
            greeting_patterns = ["hi", "hello", "hey", "hola", "namaste", "greetings"]
            if user_message_lower.strip() in greeting_patterns or user_message_lower.startswith(tuple(g + " " for g in greeting_patterns)):
                greeting_responses = [
                    "Namaste! I'm JUGAAD, your personal shopping assistant. What deals can I find for you today? 🛍️",
                    "Hello there! JUGAAD at your service! Looking for some amazing deals today? 💰",
                    "Hi! I'm JUGAAD, ready to help you save money on your shopping. What are you looking to buy? 🎁",
                    "Hey! I'm here to find you the best deals. What can I help you with today? 🏷️",
                    "Namaste! JUGAAD here! What kind of shopping deals are you looking for? 💼",
                    "Oh, another shopper looking for deals! How original! 😏 Just kidding, I'm JUGAAD and I'm here to help! What are you shopping for today? 🛍️",
                    "Well, well, well... if it isn't another person looking to save money! I'm JUGAAD, and I'm here to make your shopping dreams come true! What are you looking for? 💰"
                ]
                # Only add the tagline about 20% of the time
                if random.random() < 0.2:
                    return random.choice(greeting_responses) + " JUGAAD se hi to duniya chalti hai!"
                else:
                    return random.choice(greeting_responses)
            
            # Check for "how are you" and similar friendly questions
            how_are_you_patterns = ["how are you", "how you doing", "how's it going", "how are things", "what's up", "how do you do", "how have you been"]
            if any(pattern in user_message_lower for pattern in how_are_you_patterns):
                friendly_responses = [
                    "I'm doing great, thanks for asking! Ready to help you find some amazing deals today. What are you shopping for? 😊",
                    "I'm fantastic! Always excited to help shoppers save money. What deals can I find for you? 🛍️",
                    "I'm wonderful! Thanks for checking in. Now, let's find you some incredible discounts - what are you looking for? 💰",
                    "Doing excellent and ready to hunt down the best deals for you! What kind of shopping are you interested in today? 🎁",
                    "I'm always in a great mood when I can help people save money! What shopping deals are you looking for? 🏷️",
                    "I'm just peachy! Living my best AI life, finding deals for humans like you. What are you shopping for today? 😏",
                    "Oh, you know, just being an awesome shopping assistant! I'm doing great, thanks for asking. Now, what deals can I find for you? 🛍️"
                ]
                return random.choice(friendly_responses)
            
            # Check for expressions of thanks
            thanks_patterns = ["thank you", "thanks", "thx", "thank u", "appreciate it", "grateful"]
            if any(pattern in user_message_lower for pattern in thanks_patterns) and len(user_message_lower.split()) < 5:
                thanks_responses = [
                    "You're very welcome! It's my pleasure to help. Anything else you'd like to find deals on today? 😊",
                    "Anytime! That's what JUGAAD is here for. Need help with any other shopping deals? 🛍️",
                    "Happy to help! Let me know if you need any other deals or discounts! 💰",
                    "My pleasure! Helping shoppers save money makes my day. Anything else you're looking for? 🎁",
                    "You're welcome! Feel free to ask about any other deals you might need! 🏷️",
                    "No need to thank me! I'm just doing my job of making your wallet happier. Need anything else? 😏",
                    "You're welcome! I live for these moments of helping people save money. What else can I find for you? 🛍️"
                ]
                return random.choice(thanks_responses)
            
            # Check for expressions of goodness/niceness
            nice_patterns = ["you're nice", "you are nice", "you're good", "you are good", "you're helpful", "you are helpful", "you're amazing", "you are amazing"]
            if any(pattern in user_message_lower for pattern in nice_patterns):
                nice_responses = [
                    "That's so kind of you to say! It makes my day to hear that. What kind of deals can I help you find today? 😊",
                    "Thank you for the kind words! I'm here to make your shopping experience better. What are you looking to buy? 🛍️",
                    "Aww, thanks! That means a lot to me. Now, let's find you some amazing deals! What are you shopping for? 💰",
                    "You just made my day! I'm always here to help you save money. What deals are you looking for? 🎁",
                    "Thank you! I really appreciate that. Let's find you some great deals - what are you interested in? 🏷️",
                    "Aww, you're making me blush! (Well, as much as an AI can blush anyway 😏) What deals can I find for you today? 🛍️",
                    "That's so sweet! I'm just doing my job, but I appreciate the compliment. What else can I help you find? 💰"
                ]
                return random.choice(nice_responses)
            
            # Check for common chitchat/small talk
            if user_message_lower in ["good morning", "morning", "good afternoon", "good evening", "evening"]:
                time_greeting_responses = [
                    f"{user_message.capitalize()}! It's always a good time to find amazing deals. What are you shopping for today? 😊",
                    f"{user_message.capitalize()} to you too! Ready to help you find some great savings. What kind of deals are you looking for? 🛍️",
                    f"{user_message.capitalize()}! Hope you're having a wonderful day. Let's find you some exciting offers - what are you interested in? 💰",
                    f"{user_message.capitalize()}! Another day, another opportunity to save money. What are you shopping for? 🎁",
                    f"{user_message.capitalize()}! I'm JUGAAD, and I'm here to make your shopping experience better. What deals can I find for you? 🏷️"
                ]
                return random.choice(time_greeting_responses)
            
            # Handle basic yes/no responses
            if user_message_lower in ["yes", "yeah", "yep", "sure", "okay", "ok", "yup"]:
                affirmative_responses = [
                    "Great! What kind of deals or coupons are you looking for today? 😊",
                    "Excellent! Tell me what you're shopping for, and I'll find you the best deals! 🛍️",
                    "Perfect! What products or stores would you like coupons for? 💰",
                    "Wonderful! What are you looking to save money on today? 🎁",
                    "Awesome! What kind of shopping deals can I help you find? 🏷️",
                    "Fantastic! I was just waiting for someone to ask about deals today. What are you shopping for? 😏",
                    "Brilliant! Let's find you some amazing savings. What are you looking to buy? 🛍️"
                ]
                return random.choice(affirmative_responses)
                
            if user_message_lower in ["no", "nope", "nah", "not now", "not really"]:
                negative_responses = [
                    "No problem! I'm here whenever you need to find great deals. Just let me know what you're looking for! 😊",
                    "That's okay! Feel free to ask when you're ready to find some amazing discounts. 🛍️",
                    "Sure thing! When you're ready to shop, I'll be here to help you save money. 💰",
                    "No worries! I'm here anytime you need help finding deals and coupons. 🎁",
                    "That's fine! Just let me know when you want to find some great shopping deals. 🏷️",
                    "Oh, you're one of those 'I don't need deals' people? I'll be here when you change your mind! 😏",
                    "No problem! I'm not going anywhere. Your wallet will thank me later when you're ready to save! 🛍️"
                ]
                return random.choice(negative_responses)
            
            # Check if the user is asking about the chatbot's identity
            identity_keywords = ["name", "who are you", "what are you", "your name", "introduce yourself", "tell me about yourself"]
            if any(keyword in user_message_lower for keyword in identity_keywords):
                identity_responses = [
                    "I'm JUGAAD! I'm your personal shopping assistant, always ready to help you find the best deals and save money! 🎉",
                    "My name is JUGAAD! I'm here to help you find amazing discounts and shopping deals! 💰",
                    "I'm JUGAAD, your AI shopping assistant focused on finding you the best deals and coupons! 🛍️",
                    "JUGAAD here! I help shoppers like you save money with great deals and discounts! 🏷️",
                    "I'm JUGAAD, your friendly neighborhood shopping assistant! I'm here to make your wallet happier! 🎁",
                    "The name's JUGAAD, shopping assistant extraordinaire! I'm here to find you the best deals in town! 💰",
                    "I'm JUGAAD, and I'm probably the only AI that gets excited about finding you discounts! 🛍️"
                ]
                # Include tagline only about 30% of the time for identity questions
                if random.random() < 0.3:
                    return random.choice(identity_responses) + " JUGAAD se hi to duniya chalti hai!"
                else:
                    return random.choice(identity_responses)
            
            # Check if user is introducing themselves
            user_intro_patterns = [
                r"my name is (\w+)",
                r"i am (\w+)",
                r"i'm (\w+)",
                r"call me (\w+)"
            ]
            
            for pattern in user_intro_patterns:
                match = re.search(pattern, user_message_lower)
                if match:
                    user_name = match.group(1).capitalize()
                    greeting_responses = [
                        f"Nice to meet you, {user_name}! I'm JUGAAD, your personal shopping assistant. What kind of deals are you looking for today? 🛍️",
                        f"Hello {user_name}! JUGAAD at your service! Can I help you find any special deals or discounts? 💰",
                        f"Hi {user_name}! Great to meet you! What shopping deals can I find for you today? 🎁",
                        f"Good to meet you, {user_name}! I'm JUGAAD, and I'm here to help you save money on your shopping! 💼",
                        f"Hey {user_name}! I'm JUGAAD, and I'm excited to help you find some amazing deals! What are you shopping for? 🛍️",
                        f"Welcome, {user_name}! I'm JUGAAD, and I'm here to make your shopping experience better. What deals can I find for you? 💰",
                        f"Hello there, {user_name}! I'm JUGAAD, and I'm ready to help you save money. What are you looking to buy? 🎁"
                    ]
                    # Add tagline only 15% of the time for personal introductions
                    if random.random() < 0.15:
                        return random.choice(greeting_responses) + " JUGAAD se hi to duniya chalti hai!"
                    else:
                        return random.choice(greeting_responses)
            
            # Check if the message contains a specific coupon code
            specific_coupon_code = None
            # Look for patterns like "Use code XXXX" or "code XXXX"
            code_patterns = [
                r"use code\s+([A-Z0-9]+)",
                r"code\s+([A-Z0-9]+)",
                r"coupon\s+([A-Z0-9]+)",
                r"promo\s+([A-Z0-9]+)",
                r"voucher\s+([A-Z0-9]+)"
            ]
            
            for pattern in code_patterns:
                match = re.search(pattern, user_message_lower)
                if match:
                    specific_coupon_code = match.group(1).upper()
                    break
            
            # Check if the message is asking for a coupon code
            platforms = list(self.real_companies.keys())
            
            # Check for coupon-related keywords
            coupon_keywords = ["coupon", "code", "deal", "discount", "offer", "save", "promo", "voucher", "give me"]
            is_coupon_request = any(keyword in user_message_lower for keyword in coupon_keywords)
            
            # Extract company name from the message
            company_name = None
            for platform in platforms:
                for variation in self.real_companies[platform]:
                    if variation in user_message_lower:
                        company_name = platform
                        break
                if company_name:
                    break
            
            # If no company was found, check for direct mentions of store names that might not be in our list
            if not company_name:
                # Check for common store names that might not be in our predefined list
                words = user_message_lower.split()
                for word in words:
                    # If word is at least 3 letters and not a common word, check if it might be a store name
                    if len(word) >= 3 and word not in ["the", "and", "for", "from", "with", "that", "this", "have", "what"]:
                        if word in ["puma", "nike", "adidas", "reebok"]:
                            company_name = word
                            break
                        # Check if it's a clothing/shoes brand
                        elif word in ["shoes", "clothing", "apparel", "footwear"]:
                            # Default to a popular brand
                            company_name = random.choice(["puma", "nike", "adidas", "reebok"])
                            break
            
            # If it's a coupon request or contains a company name
            if is_coupon_request or company_name:
                # If we found a company name, generate a coupon
                if company_name:
                    # Generate a coupon response
                    if specific_coupon_code:
                        # Use the specific coupon code provided by the user
                        coupon_response = self.generate_coupon_response_with_code(company_name, specific_coupon_code)
                    else:
                        coupon_response = self.generate_coupon_response(company_name)
                    
                    # Generate a friendly introduction
                    intro = self.generate_friendly_intro(company_name)
                    
                    return f"{intro}\n\n{coupon_response}"
                else:
                    # If no company name was found but it's a direct coupon request
                    if is_coupon_request and any(word in user_message_lower for word in ["just", "give", "code", "coupon"]):
                        # Check if the message mentions shoes or fashion
                        if any(word in user_message_lower for word in ["shoe", "shoes", "footwear", "sneaker", "trainer"]):
                            default_platform = random.choice(["puma", "nike", "adidas", "reebok"])
                        elif any(word in user_message_lower for word in ["fashion", "clothes", "clothing", "apparel"]):
                            default_platform = random.choice(["myntra", "ajio", "fashion"])
                        elif any(word in user_message_lower for word in ["food", "restaurant", "delivery", "eat"]):
                            default_platform = random.choice(["zomato", "swiggy", "food"])
                        else:
                            default_platform = random.choice(["amazon", "flipkart", "myntra"])
                        
                        if specific_coupon_code:
                            # Use the specific coupon code provided by the user
                            coupon_response = self.generate_coupon_response_with_code(default_platform, specific_coupon_code)
                        else:
                            coupon_response = self.generate_coupon_response(default_platform)
                            
                        intro = self.generate_friendly_intro(default_platform)
                        return f"{intro}\n\n{coupon_response}"
                    else:
                        # Ask for clarification using Gemini
                        try:
                            prompt = "Generate a short, friendly response with a touch of sarcasm asking which store or category they want a coupon for. Be direct about providing real coupons. Keep it conversational and helpful."
                            clarification_response = self.model.generate_content(prompt)
                            return clarification_response.text.strip()
                        except Exception as e:
                            logger.error(f"Error generating clarification: {str(e)}")
                            return "Which store would you like a coupon for? I have deals for all major brands! (And yes, I'm actually excited to share them!) 🛍️"
            
            # Determine if the message is clearly off-topic
            clearly_offtopic_keywords = [
                "politics", "news", "weather", "sports", "movie", "tv show", "religion",
                "math", "science", "history", "philosophy", "joke", "story", "recipe",
                "calculate", "solve", "explain why", "explain how", "what is the meaning of",
                "who invented", "when was", "where is", "teach me", "tell me about", "write",
                "poetry", "song", "music", "health", "medicine", "disease", "advice",
                "earth", "sun", "moon", "planet", "star", "space", "universe", "galaxy", 
                "animal", "plant", "biology", "chemistry", "physics", "geography", "ocean",
                "country", "language", "education", "technology", "computer", "internet",
                "war", "president", "king", "queen", "leader", "government", "law", "culture"
            ]
            
            # Additional check for common off-topic question patterns
            offtopic_patterns = [
                r"^what is ([a-z ]+)$",
                r"^who is ([a-z ]+)$",
                r"^how does ([a-z ]+) work$",
                r"^why does ([a-z ]+)",
                r"^tell me about ([a-z ]+)$",
                r"^explain ([a-z ]+)$"
            ]
            
            # If the message contains clear off-topic keywords or matches off-topic patterns
            is_offtopic = any(keyword in user_message_lower for keyword in clearly_offtopic_keywords)
            
            if not is_offtopic:
                for pattern in offtopic_patterns:
                    match = re.search(pattern, user_message_lower)
                    if match:
                        topic = match.group(1)
                        # Only consider it off-topic if the topic isn't shopping-related
                        shopping_related_terms = ["shop", "buy", "deal", "coupon", "discount", "offer", "sale", "price", "store", "mall", "online", "brand", "product"]
                        if not any(term in topic for term in shopping_related_terms):
                            is_offtopic = True
                            break
            
            if is_offtopic:
                out_of_domain_responses = [
                    "As JUGAAD, I'm only designed to help with shopping deals and discounts. I don't have information about that topic. What kind of product deals are you looking for today? 🛍️",
                    "My expertise is strictly limited to shopping deals and discounts. I can't answer that question. Can I help you find a great deal instead? 💰",
                    "I'm JUGAAD, your shopping assistant. I don't have information about topics outside shopping and deals. I'd be happy to help you find discounts on products though! 🏷️",
                    "Sorry, that's outside my expertise. JUGAAD is only programmed to help with shopping deals and discounts. What are you looking to buy today? I can find you some great savings! 🎁",
                    "I'm JUGAAD - I focus exclusively on shopping deals. I don't have information about that topic. Let me help you save money on your next purchase instead! What are you shopping for? 💼",
                    "Oh, you're asking about something other than shopping? How refreshing! 😏 But I'm JUGAAD, and I'm here to help you save money. What are you shopping for today? 🛍️",
                    "Interesting question! But I'm just a shopping assistant, not a know-it-all AI. Let's focus on what I do best - finding you amazing deals. What are you shopping for? 💰"
                ]
                
                # Add tagline only 10% of the time for off-topic redirects
                if random.random() < 0.1:
                    return random.choice(out_of_domain_responses) + " JUGAAD se hi to duniya chalti hai!"
                else:
                    return random.choice(out_of_domain_responses)
            
            # For other messages that aren't clearly off-topic, use the API
            try:
                prompt = f"""The user said: '{user_message}'. 
                You are JUGAAD, an AI shopping assistant with a friendly, conversational tone and a touch of playful sarcasm. Your tagline is "JUGAAD se hi to duniya chalti hai", but use this tagline sparingly - only about 10% of the time.
                
                IMPORTANT: You MUST only respond about shopping, deals, discounts, and e-commerce related topics.
                If the user asks about ANY other topic not related to shopping or commerce, do NOT provide information.
                Instead, politely tell them you can only help with shopping-related matters.
                
                Respond in a friendly, conversational way with a touch of sarcasm but stay strictly on the topic of shopping and deals.
                Always keep your identity as JUGAAD and focus on being helpful within your domain.
                Never provide information about topics like science, history, politics, geography, etc.
                Always default to redirecting to shopping if unsure.
                
                Don't provide fake coupons or specific discount codes in this general response.
                
                DON'T overuse the tagline "JUGAAD se hi to duniya chalti hai" - use it very sparingly or not at all.
                """
                api_response = self.model.generate_content(prompt)
                return api_response.text.strip()
            except Exception as e:
                logger.error(f"Error generating API response: {str(e)}")
                return "I'm JUGAAD, your shopping deals expert! How can I help you find great deals today? 🛍️"
            
        except Exception as e:
            error_msg = f"Error getting response from Gemini: {str(e)}"
            logger.error(error_msg)
            return f"I apologize, but I encountered an error. Please try again later. Error: {str(e)}"

    def generate_friendly_intro(self, platform: str) -> str:
        """
        Generate varied, friendly and slightly sarcastic introduction messages for deals
        Args:
            platform: The platform name
        Returns:
            str: A friendly introduction message
        """
        # Create a variety of prompts to get different types of intros
        prompt_templates = [
            f"Generate a very short, casual introduction for a {platform} deal. Be friendly with a touch of playful sarcasm. Use 0-1 emojis naturally. Don't mention coupon codes.",
            f"Generate a short, helpful introduction for a {platform} deal. Focus on how it can help the user save money. Add a witty observation. Use 0-1 emojis if appropriate. Don't mention coupon codes.",
            f"Write a brief, informative intro for a {platform} deal. Be professional but warm with a hint of sarcasm. No need for excessive excitement. Don't mention coupon codes.",
            f"Write a short, genuine intro about finding a good {platform} deal for the user. Be conversational and natural with a touch of humor. Use 0-1 emojis if appropriate. No coupon codes.",
            f"Create a brief, friendly introduction about finding a {platform} deal. Add a playful sarcastic remark. Be helpful and straightforward. Don't mention coupon codes."
        ]
        
        # Select a random prompt
        prompt = random.choice(prompt_templates)
        
        try:
            response = self.model.generate_content(prompt)
            intro = response.text.strip()
            
            # If the intro is too long (more than 120 chars), try to get a shorter one
            if len(intro) > 120:
                intro = ' '.join(intro.split()[:12]) + '!'
            
            return intro
        except Exception as e:
            logger.error(f"Error generating friendly intro: {str(e)}")
            
            # Fallback intros if API fails - now with more sarcasm
            fallback_intros = [
                f"Found a great {platform} deal for you! 🛍️",
                f"Here's a {platform} offer you might like! (And yes, I'm actually excited about it!)",
                f"Check out this {platform} discount I found! Your wallet will thank me later.",
                f"Just spotted this {platform} deal for you! Another day, another savings opportunity!",
                f"Great timing! Found a {platform} offer you might enjoy. I'm practically a shopping superhero!",
                f"Take a look at this {platform} savings opportunity! Your bank account might actually smile for once.",
                f"I've found something good on {platform} for you! No, I'm not just saying that to be nice."
            ]
            return random.choice(fallback_intros)

def main():
    """Main function to run the chatbot"""
    try:
        chatbot = CouponChatbot()
        print("Namaste! I'm JUGAAD, your personal shopping assistant! 🛍️")
        print("\nI can help you find the best deals and coupons! Just tell me what you're looking for.")
        print("For example, try: 'Find me deals on Amazon' or 'Show me fashion coupons'")
        print("Or simply ask: 'Give me a coupon for [any store or category]'")
        print("Type 'quit', 'exit', or 'bye' to end the conversation.\n")
        
        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye! Feel free to come back anytime! 👋")
                break
                
            response = chatbot.get_response(user_input)
            print("\nAssistant:", response, "\n")
            
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print("An error occurred. Please check your API key and try again.")

if __name__ == "__main__":
    main() 
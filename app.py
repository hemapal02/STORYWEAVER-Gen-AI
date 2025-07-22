

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import openai
import os
from datetime import datetime
import random
import logging
from werkzeug.exceptions import BadRequest


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')


CORS(app)


app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


CHARACTERS = [
    "Luna the cat", "Oliver the owl", "Bella the butterfly", "Max the dragon",
    "Zara the robot", "Felix the fox", "Ruby the rabbit", "Sage the squirrel",
    "Captain Whiskers", "Princess Sparkle", "Benny the bear", "Aria the unicorn"
]

SETTINGS = [
    "enchanted forest", "underwater castle", "floating cloud city", "crystal cave",
    "magical library", "candy kingdom", "space station", "fairy garden",
    "rainbow bridge", "cozy treehouse", "bustling ant hill", "sunny meadow"
]

THEMES = [
    "friendship", "courage", "kindness", "honesty", "sharing", "creativity",
    "perseverance", "helping others", "believing in yourself", "trying new things"
]

LENGTH_SPECS = {
    'short': '100-150 words',
    'medium': '200-300 words',
    'long': '400-500 words'
}

class StoryGenerator:
    """Handles AI story generation using OpenAI's API"""
    
    def __init__(self):
        self.client = None
    
    def initialize_client(self, api_key):
        """Initialize OpenAI client with provided API key"""
        try:
            self.client = openai.OpenAI(api_key=api_key)
             self.client.models.list()
            return True, "API key validated successfully!"
        except Exception as e:
            logger.error(f"OpenAI API key validation failed: {e}")
            return False, f"Invalid API key: {str(e)}"
    
    def generate_story(self, character, setting, theme, length='short'):
        """Generate a children's story using OpenAI's GPT model"""
        
        if not self.client:
            raise ValueError("OpenAI client not initialized. Please provide a valid API key.")
        
        
        prompt = f"""Write a heartwarming children's story with these elements:

Main Character: {character}
Setting: {setting}
Theme/Lesson: {theme}
Length: {LENGTH_SPECS.get(length, '100-150 words')}

Requirements:
- Age-appropriate for children (5-10 years old)
- Include dialogue to make it engaging
- Have a clear beginning, middle, and end
- End with a positive message about {theme}
- Use simple, vivid language that children can understand
- Make it fun and imaginative!
- Format with proper paragraphs

Story:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a creative children's book author who writes engaging, educational, and fun stories for kids. Write stories that are wholesome, imaginative, and teach positive values."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.8,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            story = response.choices[0].message.content.strip()
            logger.info(f"Successfully generated story for character: {character}")
            return story
            
        except Exception as e:
            logger.error(f"Error generating story: {e}")
            raise Exception(f"Story generation failed: {str(e)}")


story_generator = StoryGenerator()

@app.route('/')
def index():
    """Main page - renders the story creation interface"""
    return render_template('index.html')

@app.route('/api/validate-key', methods=['POST'])
def validate_api_key():
    """Validate OpenAI API key"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({'success': False, 'message': 'API key is required'})
        
        success, message = story_generator.initialize_client(api_key)
        
        if success:
            session['api_key_validated'] = True
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message})
    
    except Exception as e:
        logger.error(f"API key validation error: {e}")
        return jsonify({'success': False, 'message': 'Validation failed. Please try again.'})

@app.route('/api/generate-story', methods=['POST'])
def generate_story_api():
    """Generate a story based on user input"""
    try:
        data = request.get_json()
        
        
        if not session.get('api_key_validated'):
            return jsonify({'success': False, 'message': 'Please validate your API key first'})
        
        
        character = data.get('character', '').strip() or 'a curious little rabbit'
        setting = data.get('setting', '').strip() or 'a magical forest'
        theme = data.get('theme', '').strip() or 'friendship'
        length = data.get('length', 'short')
        api_key = data.get('api_key', '').strip()
        
        
        if length not in LENGTH_SPECS:
            length = 'short'
        
    
        if api_key:
            success, _ = story_generator.initialize_client(api_key)
            if not success:
                return jsonify({'success': False, 'message': 'Invalid API key'})
        
        
        story = story_generator.generate_story(character, setting, theme, length)
        
        
        logger.info(f"Story generated - Character: {character}, Setting: {setting}, Theme: {theme}")
        
        return jsonify({
            'success': True,
            'story': story,
            'metadata': {
                'character': character,
                'setting': setting,
                'theme': theme,
                'length': length,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    
    except Exception as e:
        logger.error(f"Story generation error: {e}")
        return jsonify({'success': False, 'message': f'Story generation failed: {str(e)}'})

@app.route('/api/random-story')
def generate_random_story():
    """Generate a story with random elements"""
    try:
        if not session.get('api_key_validated'):
            return jsonify({'success': False, 'message': 'Please validate your API key first'})
        
        
        character = random.choice(CHARACTERS)
        setting = random.choice(SETTINGS)
        theme = random.choice(THEMES)
        length = 'short'  
        
        
        story = story_generator.generate_story(character, setting, theme, length)
        
        return jsonify({
            'success': True,
            'story': story,
            'metadata': {
                'character': character,
                'setting': setting,
                'theme': theme,
                'length': length,
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    
    except Exception as e:
        logger.error(f"Random story generation error: {e}")
        return jsonify({'success': False, 'message': f'Random story generation failed: {str(e)}'})

@app.route('/api/examples')
def get_examples():
    """Get example characters, settings, and themes"""
    return jsonify({
        'characters': CHARACTERS,
        'settings': SETTINGS,
        'themes': THEMES,
        'quick_examples': [
            {
                'title': 'Luna\'s Rainbow Adventure',
                'character': 'Luna the unicorn',
                'setting': 'enchanted rainbow bridge',
                'theme': 'believing in yourself'
            },
            {
                'title': 'Ocean Friends',
                'character': 'Splash the dolphin',
                'setting': 'underwater coral city',
                'theme': 'friendship'
            },
            {
                'title': 'Space Garden',
                'character': 'Zara the robot',
                'setting': 'floating space garden',
                'theme': 'helping others'
            },
            {
                'title': 'Brave Bear',
                'character': 'Sir Benny the bear',
                'setting': 'crystal castle',
                'theme': 'courage'
            }
        ]
    })

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'version': '1.0.0'
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', 
                         error_title="Page Not Found",
                         error_message="The page you're looking for doesn't exist."), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return render_template('error.html',
                         error_title="Something Went Wrong",
                         error_message="We're having technical difficulties. Please try again later."), 500

@app.errorhandler(BadRequest)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({'success': False, 'message': 'Invalid request format'}), 400


@app.template_filter('format_story')
def format_story_filter(story):
    """Format story text for HTML display"""
    if not story:
        return ""
    
    return story.replace('\n\n', '</p><p>').replace('\n', '<br>')

if __name__ == '__main__':
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"""
     StoryWeaver Flask App Starting! 
    
     Running on: http://localhost:{port}
     Debug mode: {debug}
     Ready to generate magical stories!
    
     To get started:
    1. Open http://localhost:{port} in your browser
    2. Enter your OpenAI API key
    3. Start creating amazing stories!
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
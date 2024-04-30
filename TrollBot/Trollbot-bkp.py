import praw
from openai import OpenAI
import requests
import json
import time
import sys
import toml
import os
from colorama import Fore, Style
import schedule
import sqlite3

# Specify subreddit
subreddit = "Political_Revolution"

# Load secrets from TOML file
secrets_file = os.path.join(os.path.dirname(__file__), 'secrets.toml')
with open(secrets_file, 'r') as f:
    secrets = toml.load(f)

openai_api_key = secrets['openai']['api_key']
reddit_client_id = secrets['reddit']['client_id']
reddit_client_secret = secrets['reddit']['client_secret']
reddit_username = secrets['reddit']['username']
reddit_password = secrets['reddit']['password']

# Initialize OpenAI and Reddit clients
client = OpenAI(api_key=openai_api_key)
reddit = praw.Reddit(client_id=reddit_client_id,
                     client_secret=reddit_client_secret,
                     username=reddit_username,
                     password=reddit_password,
                     user_agent='PolRev TrollBot v1.0')

# Connect to the SQLite database
conn = sqlite3.connect('processed_comments.db')
cursor = conn.cursor()

# Create a table for processed comments if it doesn't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS processed_comments (
                    comment_id TEXT PRIMARY KEY
                )''')
conn.commit()
conn.close()

def fetch_parent_comment_text(comment_id):
    """Fetch the text of a comment's parent."""
    parent_comment = reddit.comment(comment_id)
    try:
        parent_comment.refresh()  # Load the comment's details
        return parent_comment.body
    except Exception as e:
        print(f"Error fetching parent comment: {e}")
        return ""

def is_trolling(post_title, comment_text, parent_comment_text=""):
    """Determine if a comment is trolling based on its content and context."""
    try:
        messages = [
            {"role": "system", "content": "Determine if the comment is trolling based on context provided."},
            {"role": "user", "content": f"Post Title: {post_title}\nParent Comment: {parent_comment_text}\nChild Comment: {comment_text}"}
        ]
        response = client.chat.completions.create(
            model="gpt-4", 
            messages=messages, 
            max_tokens=2500, 
            temperature=0.7
        )
        response_text = response.choices[0].message.content.strip()
        print(f"Analysis: {Fore.BLUE + response_text + Style.RESET_ALL}")

        troll_state = "true" in response_text.lower()
        return troll_state, response_text
    except Exception as e:
        print(f"Failed to generate response: {e}")
        return False, "Failed to analyze the comment."

def process_comments(comments_data, conn, cursor, parent_permalink, post_title):
    """Process comments to check for trolling."""
    for comment in comments_data:
        if comment['kind'] == 't1':  # t1 indicates a comment
            comment_data = comment['data']
            comment_id = comment_data['id']
            cursor.execute("SELECT * FROM processed_comments WHERE comment_id=?", (comment_id,))
            if cursor.fetchone():
                continue  # Skip already processed comments
            cursor.execute("INSERT INTO processed_comments (comment_id) VALUES (?)", (comment_id,))
            conn.commit()

            # Fetch the parent comment's text if needed
            parent_comment_text = ""
            if 'parent_id' in comment_data and comment_data['parent_id'].startswith('t1_'):
                parent_comment_text = fetch_parent_comment_text(comment_data['parent_id'][3:])

            comment_text = comment_data['body']
            troll_state, explanation = is_trolling(post_title, comment_text, parent_comment_text)

            # Further processing based on analysis

            if 'replies' in comment_data and comment_data['replies'] != '':
                process_comments(comment_data['replies']['data']['children'], conn, cursor, f"{parent_permalink}{comment_id}/", post_title)

def process_hot_posts():
    """Process hot posts from the specified subreddit for trolling comments."""
    conn = sqlite3.connect('processed_comments.db')
    cursor = conn.cursor()
    
    subreddit_url = f"https://www.reddit.com/r/{subreddit}/hot.json"
    try:
        response = requests.get(subreddit_url, headers={'User-Agent': 'Mozilla/5.0'})
        data = response.json()
        for post in data['data']['children']:
            submission = post['data']
            comments_url = f"https://www.reddit.com{submission['permalink']}.json"
            comments_response = requests.get(comments_url, headers={'User-Agent': 'Mozilla/5.0'})
            comments_data = comments_response.json()[1]['data']['children']
            process_comments(comments_data, conn, cursor, submission['permalink'], submission['title'])
    finally:
        conn.close()

schedule.every(5).minutes.do(process_hot_posts)

first_iteration = True

# Run the scheduled jobs indefinitely
while True:
    schedule.run_pending()
    # Check if it's the first iteration
    if first_iteration:
        # Print initial message
        print("Waiting for " + Fore.CYAN + "TrollBot" + Style.RESET_ALL + " to start... ", end="\n")
        
        # Reset the start time
        start_time = time.time()
        # Process hot posts
        process_hot_posts()
        # Update flag
        first_iteration = False
    else:
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        elapsed_days = int(elapsed_time // (3600 * 24))
        elapsed_hours = int((elapsed_time % (3600 * 24)) // 3600)
        elapsed_minutes = int((elapsed_time % 3600) // 60)
        elapsed_seconds = int(elapsed_time % 60)
        
        # Print elapsed time
        print(f"{Fore.YELLOW}Elapsed time: {elapsed_days} days, {elapsed_hours % 24} hours, {elapsed_minutes} minutes, {elapsed_seconds} seconds{Style.RESET_ALL} ", end="\r")

    # Wait for 1 second before checking again
    time.sleep(1)  # Changed to 1 second for second by second update

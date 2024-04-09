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

#Specify subreddit
subreddit = "Political_Revolution"

secrets_file = os.path.join(os.path.dirname(__file__), 'secrets.toml')
secrets = toml.load(secrets_file)

openai_api_key = secrets['openai']['api_key']
reddit_client_id = secrets['reddit']['client_id']
reddit_client_secret = secrets['reddit']['client_secret']
reddit_username = secrets['reddit']['username']
reddit_password = secrets['reddit']['password']

client = OpenAI(
    api_key = openai_api_key
)

# Reddit API credentials
reddit = praw.Reddit(client_id=reddit_client_id,
                     client_secret=reddit_client_secret,
                     username=reddit_username,
                     password=reddit_password,
                     user_agent='PolRev TrollBot v1.0')

# Create a connection to the SQLite database
conn = sqlite3.connect('processed_comments.db')

# Create a cursor object
cursor = conn.cursor()

# Create a table to store processed comment IDs if it doesn't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS processed_comments (
                    comment_id TEXT PRIMARY KEY
                )''')

# Commit changes and close the connection
conn.commit()
conn.close()

def is_trolling(post_title, comment_text):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Read the post title and comment from a progressive's perspective on r/Political_Revolution and decide if it is trolling. We are a team that thinks on progressive issues such as Medicare for All. We are inspired by Bernie Sanders' stances. We preach democratic socialism. We do allow communists in our subreddit to some degree, but not if they don't debate their ideology with etiquette. Promotion of non-progressive ideology is not allowed. We do not like r/conservative or conservative commentary spreading throughout our colony for the intent purpose of invading it. We are anti-Trump It can be based in incivility, harassment, or promoting violence. It's okay if it's seemingly harsh, and contains profanity, but make sure to find real attempts at straw man arguments, or circular conversation. Respond with true or false; Give an explanation. Keep the whole response under 40 characters in length."},
                {"role": "user", "content": f"Post Title: {post_title}\n\n{comment_text}"}
            ],
            max_tokens=2500,
            temperature=0.7
        )
        response_text = response.choices[0].message.content
        print(f"Analysis: {Fore.BLUE + response_text + Style.RESET_ALL}")

        troll_state = "true" in response_text.lower()
        return troll_state, response_text
    except Exception as e:
        error_message = str(e)
        if "content management" in error_message.lower():
            return "content_violation", "Content violation detected by the AI bot."
        print(f"Failed to generate response: {error_message}")
        return False, "Failed to analyze the comment"

def process_comments(comments_data, conn, cursor, parent_permalink, post_title):
    for comment in comments_data:
        if comment['kind'] == 't1':  # t1 indicates a comment
            comment_data = comment['data']
            comment_id = comment_data['id']
            ups = comment_data['ups']  # Retrieve the number of upvotes for the comment

            cursor.execute("SELECT * FROM processed_comments WHERE comment_id=?", (comment_id,))
            if cursor.fetchone():
                continue
            cursor.execute("INSERT INTO processed_comments (comment_id) VALUES (?)", (comment_id,))
            conn.commit()

            # Check if the comment has more than two upvotes
            if ups > 5:
                print(f"Skipping comment {comment_id} with {ups} upvotes.")
                continue  # Skip further processing for this comment

            comment_text = comment_data['body']
            author = comment_data['author']
            print(f"Comment by {Fore.GREEN}{author}{Style.RESET_ALL}")
            comment_permalink = f"{parent_permalink}{comment_id}"
            print(f"Comment permalink: {Fore.LIGHTMAGENTA_EX}{comment_permalink}{Style.RESET_ALL}")

            troll_state, explanation = is_trolling(post_title, comment_text)
            if troll_state == "content_violation":
                print(f"Content violation detected in comment by {Fore.GREEN}{author}{Style.RESET_ALL}")
                report_message = "This comment has been identified by an AI bot as a content violation."
                print(f"Reporting comment {comment_id}: {report_message}")
                reddit.comment(comment_id).report(report_message)
            elif troll_state:
                print(f"Trolling comment found by {Fore.GREEN}{author}{Style.RESET_ALL}: {Fore.RED}{comment_text}{Style.RESET_ALL}")
                report_message = "Report explanation: " + explanation
                print(f"Reporting comment {comment_id}: {report_message}")
                reddit.comment(comment_id).report(report_message)
            else:
                print(f"Non-trolling comment by {Fore.GREEN}{author}{Style.RESET_ALL}: {Fore.GREEN}{comment_text}{Style.RESET_ALL}")
            time.sleep(5)

            if 'replies' in comment_data and comment_data['replies'] != '':
                process_comments(comment_data['replies']['data']['children'], conn, cursor, f"{parent_permalink}{comment_id}/", post_title)

def process_hot_posts():
    conn = sqlite3.connect('processed_comments.db')
    cursor = conn.cursor()
    
    subreddit_url = f"https://www.reddit.com/r/{subreddit}/hot.json"
    try:
        response = requests.get(subreddit_url, headers={'User-Agent': 'Mozilla/5.0'})
        data = response.json()
        for post in data['data']['children']:
            submission = post['data']
            print(f"Processing post: {Fore.LIGHTMAGENTA_EX}{submission['title']}{Style.RESET_ALL}")
            comments_url = f"https://www.reddit.com{submission['permalink']}.json"
            comments_response = requests.get(comments_url, headers={'User-Agent': 'Mozilla/5.0'})
            comments_data = comments_response.json()
            # Pass the list of top-level comments to the recursive function
            process_comments(comments_data[1]['data']['children'], conn, cursor, submission['permalink'], submission['title'])
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        conn.close()

# Schedule the job to run every 6 hours
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

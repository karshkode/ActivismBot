import re

def parse_email_to_reddit_post(email_body):
    # Extract candidate information from email body
    candidate_name = re.search(r"Candidate Name: (.+)", email_body).group(1)
    candidate_party = re.search(r"Candidate Party: (.+)", email_body).group(1)
    candidate_website = re.search(r"Candidate Website: (.+)", email_body).group(1)
    candidate_email = re.search(r"Candidate Email: (.+)", email_body).group(1)

    # Extract social media links
    social_media_links = re.findall(r"Social Media: (.+)", email_body)

    # Extract donation links
    donation_links = re.findall(r"Donation Link: (.+)", email_body)

    # Generate the Reddit post
    reddit_post = f"**AMA Announcement - {candidate_name}**\n\n" \
                  f"**Party:** {candidate_party}\n\n" \
                  f"**Website:** [Link]({candidate_website})\n\n" \
                  f"**Email:** {candidate_email}\n\n"

    if social_media_links:
        reddit_post += "**Social Media:**\n"
        for link in social_media_links:
            reddit_post += f"[Link]({link})\n"

    if donation_links:
        reddit_post += "**Donation Links:**\n"
        for link in donation_links:
            reddit_post += f"[Link]({link})\n"

    return reddit_post

# Example usage
email_body = """
Candidate Name: John Doe
Candidate Party: Independent
Candidate Website: www.johndoe.com
Candidate Email: john.doe@example.com
Social Media: www.twitter.com/johndoe
Social Media: www.facebook.com/johndoeofficial
Donation Link: www.actblue.com/johndoe/donate
"""

reddit_post = parse_email_to_reddit_post(email_body)
print(reddit_post)

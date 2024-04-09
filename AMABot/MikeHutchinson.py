import praw

# Reddit API credentials
CLIENT_ID = ''
CLIENT_SECRET = ''
USER_AGENT = 'AMA Posting Script'
USERNAME = 'mikehutchinson'
PASSWORD = ''

# Initialize the Reddit API wrapper
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT,
    username=USERNAME,
    password=PASSWORD
)

# Markdown content for the main post
markdown_content = '''
**Hi, I'm Michael Hutchinson, please call me Hutch. I'm a patriot, a veteran, and a progressive. I launched my campaign for the Minnesota State House District 20b in April of this year.**

##I strongly believe that our great country can be better for everyone, but we must confront the corruption and division that plagues our nation.

I grew up poor and enlisted in the U.S. Army after high school. I served on active duty and in the National Guard, using the GI Bill to earn a degree in managerial marketing from Kent State. I've been employed as a marketer for 14 years and I currently work remotely as an operations manager from my home in Zumbrota. I've been happily married for almost a decade, and my wife and I share our lives with two dogs and two birds.

I reside in a stunning region of river bluffs and lush farmland, but like many rural areas in America, my neighbors often feel neglected by our government. **This sense of neglect breeds anger, providing fertile ground for hate and fear to thrive.** Unfortunately, this anger has been fueled by a long line of self-serving politicians who stoke the belief that the government is not working for us. After every election they prove our neighbors right by favoring their friends and corporate donors in legislation or by spending their time making political soundbites, all while disregarding the needs of the people and their districts. We must break this cycle.

**In my district, we currently have an unacceptable child poverty rate of around 10%.** To make matters worse, our state senator recently made national headlines by claiming he had never met a hungry child in our district. This lack of awareness comes as no surprise since he rarely engages with the people or businesses in our district, unless there's a stage, a microphone and some cameras. My opponent in the State House shares his sentiment; they both voted against feeding children. This was the final straw that compelled me to step up and try to provide actual representation for my neighbors.

When I am elected I will focus on issues that most directly affect rural communities. I break these down into four main categories: Food and Water Security,  Affordable Housing, Sustainable Family Farms + Homesteads, and Education Funding. In addition to my main priorities, **I will support any changes to our first-past-the-post voting system** that can introduce more nuanced and diverse representation. And because we should all have an odd position, **I advocate for the abolition of Daylight Savings Time.**

You can find more details about me and my views on my website: [vote4hutch.com](https://vote4hutch.com)

[](https://vote4hutch.com/wp-content/uploads/2023/03/HUTCH-logo-02-flat-1024x667.png)

Thank you for taking the time to learn about me and my campaign. I'm here to answer any questions you may have! Ask me anything.

---

*This AMA post was originally made in [r/Political_Revolution](https://reddit.com/r/political_revolution). Feel free to join the conversation there!*
'''

# Subreddits to post and crosspost in
main_subreddit = 'political_revolution'
ama_subreddit = 'IAmA'

# Post to main subreddit
try:
    main_submission = reddit.subreddit(main_subreddit).submit(
        'Call me Hutch, I am a rural progressive veteran running for the Minnesota State House, District 20b. Please Ask Me Anything.',
        selftext=markdown_content,
        send_replies=True
    )
    print(f"Posted to r/{main_subreddit}")
except Exception as e:
    print(f"Error posting to r/{main_subreddit}: {e}")

#Crosspost to Minnesota
main_subreddit='Minnesota'
if main_subreddit == 'Minnesota':
    try:
        crosspost_submission = main_submission.crosspost(subreddit=reddit.subreddit('Minnesota'), send_replies=True, flair_id='9c1ed090-a191-11eb-bb0f-0eed0677158d')
        print(f"Crossposted to r/Minnesota with flair")
    except Exception as e:
        print(f"Error crossposting to r/Minnesota: {e}")

# Post to AMA subreddit
try:
    xpost_title = f'[xpost] Call me Hutch, I am a rural progressive veteran running for the Minnesota State House, District 20b. Please Ask Me Anything.'
    xpost_body = f'''
## [Click here to view the AMA on r/Political_Revolution]({main_submission.url}) 
---

{markdown_content}
'''
    reddit.subreddit(ama_subreddit).submit(xpost_title, selftext=xpost_body, send_replies=False)
    print(f"Posted to r/{ama_subreddit}")
except Exception as e:
    print(f"Error posting to r/{ama_subreddit}: {e}")


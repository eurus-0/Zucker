import praw
import requests
import os
from flask import Flask, render_template, jsonify
from random import shuffle
from flask import Flask, render_template, request, session, jsonify



app = Flask(__name__)

# Reddit API setup
reddit = praw.Reddit(
    client_id='AS3u_E8Nf9o-1O8tVm5OqA',
    client_secret='7lQMajOxpEDMQ-tKDY0-XpspuF22Ew',
    user_agent='meme_scraper/0.1 by u/yourusername'
)

SUBREDDITS = [
    'memes', 'dankmemes', 'funny', 'wholesomememes',
    'okbuddyretard', 'comedyheaven', 'technicallythetruth', 'me_irl'
]

def fetch_memes(limit=20):
    memes = []
    for sub in SUBREDDITS:
        for post in reddit.subreddit(sub).hot(limit=5):
            if post.url.endswith(('jpg', 'jpeg', 'png')):
                memes.append({
                    'title': post.title,
                    'url': post.url,
                    'subreddit': sub
                })
    shuffle(memes)
    return memes[:limit]

app.secret_key = 'supersecretkey'  # Required for session to work

@app.route('/like', methods=['POST'])
def like_meme():
    meme = request.get_json()
    if 'liked_memes' not in session:
        session['liked_memes'] = []
    session['liked_memes'].append(meme)
    session.modified = True
    return jsonify({'status': 'success', 'liked_count': len(session['liked_memes'])})

@app.route('/saved')
def saved_memes():
    liked_memes = session.get('liked_memes', [])
    return render_template('saved.html', memes=liked_memes)


@app.route('/memes')
def memes():
    memes = fetch_memes()
    return render_template('memes.html', memes=memes)

if __name__ == '__main__':
    app.run(debug=True)

# app.py

from flask import Flask, render_template, request, jsonify, session
import praw
import os
from supabase import create_client, Client
from werkzeug.utils import secure_filename
import tempfile
import requests
from flask import Flask, render_template, request, jsonify
from fetch import get_memes_from_reddit  # use correct filename


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure one
url = "https://lildacyodrdnjweooceh.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxpbGRhY3lvZHJkbmp3ZW9vY2VoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDUxNTc3OTksImV4cCI6MjA2MDczMzc5OX0.frgrbUaHja6nsLuvhgZha59_qywACAK4QAo06m7ZJFM"
supabase: Client = create_client(url, key)

# PRAW setup
reddit = praw.Reddit(
    client_id='AS3u_E8Nf9o-1O8tVm5OqA',
    client_secret='7lQMajOxpEDMQ-tKDY0-XpspuF22Ew',
    user_agent='ZuckerBot'
)

import random

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def fetch_memes(subreddit=None, limit=20):
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}" if subreddit else f"https://www.reddit.com/r/memes+funny+wholesomememes/hot.json?limit={limit}"
    headers = {'User-agent': 'MemeApp 1.0'}
    res = requests.get(url, headers=headers)
    posts = res.json()["data"]["children"]

    memes = []
    for post in posts:
        data = post["data"]
        if not data.get("url"):
            continue
        url = data["url"]
        if any(url.endswith(ext) for ext in [".jpg", ".png", ".gif", ".jpeg", ".mp4"]):
            memes.append({
                "title": data["title"],
                "url": url,
                "subreddit": data["subreddit"],
                "is_video": url.endswith('.mp4') or data.get("is_video") is True
            })
    return memes

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_memes(limit=10, offset=0, seen_urls=set(), subreddit=None):
    subreddits = [
        "memes", "dankmemes", "wholesomememes", "funny", "me_irl",
        "okbuddyretard", "bonehurtingjuice", "comedyheaven", "historymemes",
        "prequelmemes", "terriblefacebookmemes", "surrealmemes", "2meirl4meirl"
    ]
    target_subs = [subreddit] if subreddit else subreddits

    memes = []
    print(f"Fetching memes from: {target_subs}")
    for sub in target_subs:
        try:
            sr = reddit.subreddit(sub)
            count = 0
            for post in sr.hot(limit=limit + offset):
                if post.stickied or not post.url.endswith(("jpg", "jpeg", "png")):
                    continue
                if count < offset:
                    count += 1
                    continue
                if post.url in seen_urls:
                    continue
                memes.append({
                    "title": post.title,
                    "url": post.url,
                    "permalink": post.permalink,
                    "subreddit": sub
                })
                if len(memes) >= limit:
                    break
        except Exception as e:
            print(f"Error loading subreddit {sub}: {e}")
        if len(memes) >= limit:
            break
    print(f"Found {len(memes)} memes")
    return memes


def get_random_memes(limit=10, seen_urls=set()):
    subreddits = [
        "memes", "dankmemes", "wholesomememes", "funny", "me_irl",
        "okbuddyretard", "bonehurtingjuice", "comedyheaven", "historymemes",
        "prequelmemes", "terriblefacebookmemes", "surrealmemes", "2meirl4meirl"
    ]
    memes = []
    tried_posts = set()

    while len(memes) < limit:
        sub = random.choice(subreddits)
        subreddit = reddit.subreddit(sub)
        post = random.choice(list(subreddit.hot(limit=50)))

        if post.stickied or not post.url.endswith(("jpg", "jpeg", "png")):
            continue
        if post.url in seen_urls or post.id in tried_posts:
            continue

        memes.append({
            "title": post.title,
            "url": post.url,
            "permalink": post.permalink,
            "subreddit": sub
        })
        tried_posts.add(post.id)

    return memes



from flask import session

@app.route("/memes")
def memes():
    subreddit = request.args.get("subreddit")
    page = int(request.args.get("page", 1))
    ajax = request.args.get("ajax")

    # Initialize session['seen_urls'] if not already set
    if "seen_urls" not in session:
        session["seen_urls"] = []

    seen_urls = set(session["seen_urls"])

    # Pagination via offset
    limit = 20
    offset = (page - 1) * limit

    reddit_memes = get_memes(limit=limit, offset=offset, seen_urls=seen_urls, subreddit=subreddit)
    print("Fetched memes:", len(reddit_memes))

    # Add new meme URLs to session seen list to avoid duplicates
    new_urls = [m["url"] for m in reddit_memes]
    seen_urls.update(new_urls)
    session["seen_urls"] = list(seen_urls)

    if ajax:
        return jsonify(reddit_memes)

    return render_template("memes.html", memes=reddit_memes, selected_subreddit=subreddit)






@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["file"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name

            supabase.storage.from_('memes').upload(filename, tmp_path)
            public_url = supabase.storage.from_('memes').get_public_url(filename)

            # Optional: ask user for a title
            title = request.form.get("title", "")

            # Save metadata to Supabase DB
            supabase.table("uploaded_memes").insert({
                "url": public_url,
                "title": title
            }).execute()

            return render_template("upload.html", success=True, image_url=public_url)

    return render_template("upload.html", success=False)


@app.route("/save-meme", methods=["POST"])
def save_meme():
    data = request.get_json()
    title = data.get("title", "")
    url = data.get("url")
    permalink = data.get("permalink", "#")
    subreddit = data.get("subreddit", "unknown")

    if url:
        # Avoid duplicates by checking if meme already exists
        existing = supabase.table("saved_memes").select("id").eq("url", url).execute()
        if existing.data:
            return jsonify({"message": "Already saved."})

        # Save meme
        supabase.table("saved_memes").insert({
            "title": title,
            "url": url,
            "permalink": permalink,
            "subreddit": subreddit
        }).execute()
        return jsonify({"message": "Meme saved!"})
    
    return jsonify({"error": "Missing URL"}), 400


@app.route("/saved")
def saved():
    response = supabase.table("saved_memes").select("*").order("id", desc=True).execute()
    memes = response.data if response.data else []
    return render_template("saved.html", memes=memes)

    




if __name__ == "__main__":
    app.run(debug=True)


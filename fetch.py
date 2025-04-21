import requests

def get_memes_from_reddit(subreddit=None, page=1, limit=20):
    base_url = "https://www.reddit.com"
    headers = {"User-Agent": "Mozilla/5.0"}

    sub = subreddit if subreddit else "memes"
    url = f"{base_url}/r/{sub}/hot.json?limit=50"

    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()

        posts = data.get("data", {}).get("children", [])
        memes = []

        for post in posts:
            post_data = post["data"]
            if post_data.get("over_18"):  # skip NSFW
                continue
            if not post_data.get("url"):
                continue

            is_video = post_data.get("is_video", False)
            url = post_data.get("url")

            if is_video:
                # Extract Reddit-hosted video URL
                reddit_video = post_data.get("media", {}).get("reddit_video", {})
                if reddit_video:
                    url = reddit_video.get("fallback_url")
                else:
                    continue  # skip videos without fallback

            memes.append({
                "title": post_data.get("title"),
                "url": url,
                "subreddit": post_data.get("subreddit"),
                "is_video": is_video
            })

        return memes

    except Exception as e:
        print("Error fetching memes:", e)
        return []

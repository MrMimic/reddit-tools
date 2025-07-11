import json
import logging
import os
import re

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI

logging.basicConfig(level=logging.INFO)

CACHE_FILE = "cache.json"


def load_cache() -> dict:
    """Load the cache from the JSON file.
    If the file does not exist, create an empty cache.

    Returns:
        dict: The cache dictionary.
    """
    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        return {}
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception as e:
            logging.error("Error loading cache: %s", e)
            return {}


def save_cache(cache) -> None:
    """Save the cache to the JSON file."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def remove_emojis(text: str) -> str:
    """Remove emojis from the text."""
    if not text:
        return ""
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"  # emoticons
        "\U0001f300-\U0001f5ff"  # symbols & pictographs
        "\U0001f680-\U0001f6ff"  # transport & map symbols
        "\U0001f1e0-\U0001f1ff"  # flags (iOS)
        "\U00002700-\U000027bf"  # Dingbats
        "\U000024c2-\U0001f251"  # Enclosed characters
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", text)


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY", None)
open_ai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

if not api_key:
    raise Exception(
        "No OpenAI API key found. Please set it in .env or as an environment variable."
    )
client = OpenAI(api_key=api_key)

app = Flask(__name__)
CORS(app)


def fetch_reddit_data(username) -> str:
    """Fetches the latest comments and posts from a Reddit user.

    Args:
        username (str): The Reddit username to fetch data for.

    Returns:
        str: A formatted string containing the user's comments and posts.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    comments_url = f"https://www.reddit.com/user/{username}/comments.json?limit=50"
    posts_url = f"https://www.reddit.com/user/{username}/submitted.json?limit=10"
    comments, posts = [], []
    try:
        c_resp = requests.get(comments_url, headers=headers, timeout=10)
        if c_resp.status_code == 200:
            c_json = c_resp.json()
            for c in c_json.get("data", {}).get("children", []):
                body = (
                    c["data"]
                    .get("body", "")
                    .replace("\n", " ")
                    .replace("\t", " ")
                    .strip()
                )
                subreddit = c["data"].get("subreddit", "")
                comments.append(f"{subreddit}: {body}")
        p_resp = requests.get(posts_url, headers=headers, timeout=10)
        if p_resp.status_code == 200:
            p_json = p_resp.json()
            for p in p_json.get("data", {}).get("children", []):
                title = (
                    p["data"]
                    .get("title", "")
                    .replace("\n", " ")
                    .replace("\t", " ")
                    .strip()
                )
                selftext = (
                    p["data"]
                    .get("selftext", "")
                    .replace("\n", " ")
                    .replace("\t", " ")
                    .strip()
                )
                subreddit = p["data"].get("subreddit", "")
                posts.append(f"{subreddit}: {title} - {selftext}")
    except Exception as e:
        logging.error("Error fetching Reddit data: %s", e)
    txt = "Commentaires:\n" + "\n".join(comments) + "\n\nPosts:\n" + "\n".join(posts)
    return txt


@app.route("/profile", methods=["POST"])
def profile() -> str:
    """
    Endpoint to generate a Reddit user profile based on their comments and posts.
    Expects a JSON payload with "username" and optional "force" to clear cache.

    Returns:
        str: A JSON response containing the generated profile or an error message.
    """
    data = request.json
    username = data.get("username", "")
    force = data.get("force", False)
    if not username:
        return jsonify({"error": "Missing username"}), 400
    cache = load_cache()
    if force and username in cache:
        del cache[username]
        save_cache(cache)
        logging.info(f"Profil pour {username} supprimé du cache (force)")
    cache = load_cache()  # reload après suppression éventuelle
    if username in cache:
        logging.info(f"Profil pour {username} chargé depuis le cache.")
        return jsonify({"profile": f"[CACHE] {cache[username]}"})
    reddit_text = fetch_reddit_data(username)
    prompt = (
        "Voici les posts et commentaires d'un utilisateur Reddit. Fais un profil complet"
        "(lieu de vie, age, genre, métier, orientation politique, intérêts, loisirs, orientation sexuelle, hobbies, envies, plans futurs, etc)"
        "Structure ta réponse de la manière suivante : "
        "Lieu de vie: <lieu_de_vie>\nGenre: <genre>\nMétier: <métier>\n... etc"
        "\n\n" + reddit_text
    )
    try:
        resp = client.chat.completions.create(
            model=open_ai_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        result = resp.choices[0].message.content
        result = remove_emojis(result)
        cache[username] = result
        save_cache(cache)
        return jsonify({"profile": result})
    except Exception as e:
        logging.error("OpenAI error: %s", e)
        return jsonify({"error": str(e)}), 500


@app.route("/profile/check", methods=["POST"])
def profile_check():
    """
    Endpoint pour vérifier si le profil d'un utilisateur Reddit est en cache.
    Expects a JSON payload with "username".
    Returns:
        { cached: true/false }
    """
    data = request.json
    username = data.get("username", "")
    if not username:
        return jsonify({"error": "Missing username"}), 400
    cache = load_cache()
    return jsonify({"cached": username in cache})


if __name__ == "__main__":
    app.run(port=5001, debug=True)

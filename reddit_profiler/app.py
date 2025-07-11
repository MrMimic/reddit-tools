import json
import logging
import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI

logging.basicConfig(level=logging.INFO)

CACHE_FILE = "cache.json"


def load_cache():
    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        return {}
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


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


def fetch_reddit_data(username):
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
def profile():
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
        "(lieu de vie,orientation sexuelle, genre, métier, orientation politique, intérêts, loisirs, hobbies, envies, plans futurs, etc)"
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
        cache[username] = result
        save_cache(cache)
        return jsonify({"profile": result})
    except Exception as e:
        logging.error("OpenAI error: %s", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5001, debug=True)

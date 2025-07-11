import logging
import os
import json
import re

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

log_file = os.path.join(os.path.dirname(__file__), "logs.txt")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
)

CACHE_FILE = "cache.json"

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logging.error(
        "No OpenAI API key found. Please set it in .env or as an environment variable."
    )
    client = None
else:
    client = OpenAI(api_key=api_key)

open_ai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

app = Flask(__name__)
CORS(app)


def load_cache() -> dict:
    """Load the cache from the JSON file."""
    if not os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        return {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
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


@app.route("/summarize", methods=["POST"])
def summarize() -> str:
    """Summarize a Reddit post and generate a sarcastic answer."""
    if client is None:
        return jsonify({"error": "No API key found"}), 400
    data = request.json
    url = data.get("url")
    force = data.get("force", False)
    logging.info(f"Received summarize request for URL: {url} (force={force})")
    if not url or "reddit.com" not in url:
        return jsonify({"error": "Invalid URL"}), 400
    cache = load_cache()
    cached = cache.get(url, {})
    # Always use cached summary if available
    if "summary" in cached:
        summary = cached["summary"]
        summary_tokens = 0
        logging.info(f"Loaded summary from cache for {url}")
    else:
        post_content = scrape_reddit_post(url)
        if not post_content:
            return jsonify({"error": "Could not fetch post"}), 400
        summary_resp = client.chat.completions.create(
            model=open_ai_model,
            messages=[
                {
                    "role": "system",
                    "content": "Summarize the following Reddit post in French, the summary must be between 80 and 120 words.",
                },
                {"role": "user", "content": post_content},
            ],
        )
        summary = summary_resp.choices[0].message.content
        summary_tokens = (
            summary_resp.usage.total_tokens if hasattr(summary_resp, "usage") else 0
        )
        logging.info(f"Summary generated: {summary[0:50]}...")
        cached["summary"] = summary
        cache[url] = cached
        save_cache(cache)
    # Answer: regenerate if force, else use cache if available
    if force or "answer" not in cached:
        if "post_content" in locals():
            pc = post_content
        else:
            pc = scrape_reddit_post(url)
        if not pc:
            return jsonify({"error": "Could not fetch post"}), 400
        answer_resp = client.chat.completions.create(
            model=open_ai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You're writing for a savage standup show mocking Reddit users. Based on the post below, generate a sarcastic, even mean response using heavy clichés. The response should be from a mean internet troll (not the original poster). Match the post's original language — this is important. The show uses dark humor and is fully open-minded, so unleash hell. IMPORTANT: The answer can be very short (even 1 sentence or less than 10 words) **if it's punchy**. Don't aim for 100 words by default — vary length depending on how sharp the joke is. If the language is French, NEVER use formal speech (no “vous”). Always use “tu”, and keep the tone casual, direct, and disrespectful if needed. Answer must be a single message, not a list. IMPORTANT: No username or emojis in the answer. Assume that 'M21' in the post refers to a male aged 21 and 'F45' refers to a female aged 45, eg.",
                },
                {"role": "user", "content": pc},
            ],
        )
        answer = answer_resp.choices[0].message.content.lstrip('"').rstrip('"')
        answer = remove_emojis(answer)
        answer_tokens = (
            answer_resp.usage.total_tokens if hasattr(answer_resp, "usage") else 0
        )
        logging.info(f"Answer generated: {answer[0:50]}...")
        cached["answer"] = answer
        cache[url] = cached
        save_cache(cache)
    else:
        answer = cached["answer"]
        answer_tokens = 0
        logging.info(f"Loaded answer from cache for {url}")
    total_tokens = (summary_tokens or 0) + (answer_tokens or 0)
    estimated_cost = total_tokens / 1000 * 0.002
    logging.info(
        f"Estimated OpenAI API cost for this request: ${estimated_cost:.6f} (total tokens: {total_tokens})"
    )
    result = {"summary": summary, "answer": answer}
    return jsonify(result)


def scrape_reddit_post(url: str) -> str:
    """Scrape the Reddit post for its title and selftext."""
    headers = {"User-Agent": "tldr-reddit/0.1"}
    try:
        if "/comments/" not in url:
            return None

        parts = url.split("/comments/")
        if len(parts) < 2:
            return None

        post_id = parts[1].split("/")[0]
        api_url = f"{parts[0]}/comments/{post_id}.json"

        resp = requests.get(api_url, headers=headers, timeout=10)
        if resp.status_code != 200:
            logging.warning(f"Reddit API returned {resp.status_code} for {api_url}")
            return None

        data = resp.json()
        if not isinstance(data, list) or len(data) < 1:
            return None

        post_data = data[0].get("data", {}).get("children", [])
        if not post_data or not isinstance(post_data, list):
            return None

        post = post_data[0].get("data", {})
        title = post.get("title", "").strip()
        selftext = post.get("selftext", "").strip()
        if not title and not selftext:
            return None

        return f"Titre: {title}\nPost: {selftext}"

    except Exception as e:
        logging.error(f"Error scraping Reddit post: {e}")
        return None


if __name__ == "__main__":
    app.run(debug=True)

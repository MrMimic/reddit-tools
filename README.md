# reddit-tools


## Install all services

Add a .env file in each of the folders

```bash
OPENAI_API_KEY=XXXXXXXXXXXXX
OPENAI_MODEL=gpt-3.5-turbo
```

Then, run `bash setup.sh`.

You can then go to `brave://extensions/`, hit "Load unpack" twice, one selecting each of the following.

## Description

- `reddit_profiler`: A Chrome extension that fetches and displays Reddit user profiles, based on their post history and comments.
- `tldr_reddit`: A Flask backend service that provides a summary of Reddit posts and comments, and provide a quite mean answer for fun.

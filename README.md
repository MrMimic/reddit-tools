# reddit-tools


## brave_plugin

Add a .env file in the folder

```bash
OPENAI_API_KEY=XXXXXXXXXXXXX
OPENAI_MODEL=gpt-3.5-turbo
```

To run this service, define `~/.config/systemd/user/tldr-reddit.service`:

```bash
[Unit]
Description=TLDR Reddit Flask Backend

[Service]
WorkingDirectory=<PATH_TO_THIS_FOLDER>
ExecStart=<PATH_TO>/.venv/bin/python3 <PATH_TO_THIS_FOLDER>/app.py
Restart=always

[Install]
WantedBy=default.target
```

Then run:

```bash
systemctl --user daemon-reload
systemctl --user enable tldr-reddit
systemctl --user start tldr-reddit
```

# YouTube Downloader (Flask + yt-dlp)

This is a simple web application built with Flask that uses the command-line utility `yt-dlp` to download YouTube videos. It is designed to run easily in cloud environments like Replit, which provide the necessary shell access.

## Features

- Accepts a YouTube URL via a web form.
- Runs the download job in a background thread.
- Provides a status page that refreshes automatically.
- Bypasses common SSL/network filtering issues using command-line flags.

## Deployment on Replit

1. **Import:** Create a new Repl and choose "Import from GitHub," pointing it to this repository.
2. **Setup:** Replit should automatically install the Python packages from `requirements.txt` and install `ffmpeg` via the `.replit` file.
3. **Run:** Click the "Run" button.
4. **Access:** The web interface will open in the preview pane. Use the public URL to access the downloader.

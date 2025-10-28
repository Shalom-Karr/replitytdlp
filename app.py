import os
import subprocess
import threading
import time
import re
from flask import Flask, render_template, request, send_file, redirect, url_for

# --- Configuration ---
app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads') 
download_status = {}

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# --- Utility Function ---

def update_yt_dlp():
    """Runs yt-dlp -U to ensure the program is up-to-date, ignoring SSL errors."""
    print(f"[{time.strftime('%H:%M:%S')}] Checking for yt-dlp update...")
    try:
        subprocess.run(["yt-dlp", "-U", "--no-check-certificates"], check=True, capture_output=True, text=True)
        print(f"[{time.strftime('%H:%M:%S')}] yt-dlp update check complete (SSL ignored).")
    except subprocess.CalledProcessError as e:
        print(f"[{time.strftime('%H:%M:%S')}] Warning: Failed to run yt-dlp update. Details: {e.stderr.strip()}")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Warning: Generic error during yt-dlp update: {e}")


# --- Background Task Management ---

def run_download_job(video_url, job_id):
    """Executes yt-dlp in a separate thread."""
    
    download_status[job_id]['status'] = 'Processing' 
    update_yt_dlp() 
    
    # --- SIMPLIFIED OUTPUT NAMING FIX ---
    # Define the exact, non-dynamic final output path
    final_output_name = f"video-{job_id}.mp4"
    output_template = os.path.join(DOWNLOAD_FOLDER, final_output_name)
    
    command = [
        "yt-dlp",
        "--no-check-certificates",  
        "--no-mtime",  
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Force mp4 and m4a stream selection for merging (requires ffmpeg)
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best", 
        "--merge-output-format", "mp4", 
        # Explicitly set output name so we know where to check later
        "-o", output_template,
        video_url
    ]
    
    # We now know the expected file path, so we clear out the complex regex logic
    final_filename_full = output_template

    try:
        # Execute the command
        # Note: We expect CalledProcessError if yt-dlp fails (e.g., due to ffmpeg not running)
        subprocess.run(command, capture_output=True, text=True, check=True)
        
        # Check if the file exists at the KNOWN expected path
        if os.path.exists(final_filename_full):
            base_name = os.path.basename(final_filename_full)
            download_status[job_id].update({
                'status': 'Complete',
                'filename': base_name,
                'filepath': final_filename_full
            })
        else:
            # If the file isn't there, ffmpeg likely failed, but yt-dlp didn't exit non-zero.
            raise Exception(f"File was not found at expected path: {final_filename_full}. Check if FFmpeg ran correctly.")
            
    except subprocess.CalledProcessError as e:
        # If yt-dlp itself failed (non-zero exit code)
        download_status[job_id].update({
            'status': 'Failed',
            'error': f"yt-dlp failed (Code: {e.returncode}): {e.stderr}"
        })
    except Exception as e:
        # General error or path check failure
        download_status[job_id].update({
            'status': 'Failed',
            'error': f"An internal error occurred: {str(e)}"
        })

# --- Flask Routes (Remain Unchanged) ---

@app.route('/', methods=['GET', 'POST'])
def index():
    global download_status
    if request.method == 'POST':
        video_url = request.form.get('video_url')
        if video_url:
            job_id = str(int(time.time() * 1000))
            download_status[job_id] = {'status': 'Initializing...', 'filename': None, 'error': None}
            thread = threading.Thread(target=run_download_job, args=(video_url, job_id))
            thread.start()
            return redirect(url_for('status', job_id=job_id))
    return render_template('index.html')

@app.route('/status/<job_id>')
def status(job_id):
    if job_id not in download_status:
        return "Job not found", 404
    status_data = download_status[job_id]
    return render_template('download_page.html', job_id=job_id, status_data=status_data)

@app.route('/download/<job_id>')
def download_file(job_id):
    if job_id not in download_status or download_status[job_id]['status'] != 'Complete':
        return "File not ready or job failed.", 404
    filepath = download_status[job_id]['filepath']
    return send_file(filepath, as_attachment=True)


if __name__ == '__main__':
    # When deployed on Replit, Flask is run on 0.0.0.0 for public access.
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8000), debug=False, use_reloader=False)

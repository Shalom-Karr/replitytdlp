import os
import subprocess
import threading
import time
import re
from flask import Flask, render_template, request, send_file, redirect, url_for

# --- Configuration ---
app = Flask(__name__)
# IMPORTANT: Use a relative path for the download folder
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
    
    output_template = os.path.join(DOWNLOAD_FOLDER, f"%(title)s-{job_id}.%(ext)s")
    
    command = [
        "yt-dlp",
        "--no-check-certificates",  
        "--no-mtime",  
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4", 
        "-o", output_template,
        video_url
    ]
    
    try:
        # Execute the command
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # --- File Path Extraction ---
        output_lines = result.stdout.splitlines()
        final_file_line = [line for line in output_lines if 'Destination' in line or 'Writing video to' in line]
        
        if not final_file_line:
            raise Exception("yt-dlp did not output a final file destination path.")
            
        final_file_line = final_file_line[-1]
        match = re.search(r'(?:Destination|Writing video to):\s*["\']?(.+?)["\']?$', final_file_line)
        
        if match:
            final_filename_full = match.group(1).strip()
        else:
            raise Exception("Could not reliably extract the final filename from yt-dlp output.")


        # Check if the file exists and update status
        if os.path.exists(final_filename_full):
            base_name = os.path.basename(final_filename_full)
            download_status[job_id].update({
                'status': 'Complete',
                'filename': base_name,
                'filepath': final_filename_full
            })
        else:
            raise Exception(f"File was not found at expected path: {final_filename_full}")
            
    except subprocess.CalledProcessError as e:
        download_status[job_id].update({
            'status': 'Failed',
            'error': f"yt-dlp failed: {e.stderr}"
        })
    except Exception as e:
        download_status[job_id].update({
            'status': 'Failed',
            'error': f"An internal error occurred: {str(e)}"
        })

# --- Flask Routes ---

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

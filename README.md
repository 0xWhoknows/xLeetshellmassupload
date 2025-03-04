# xLeetshellmassupload

**xLeetshellmassupload** is a Python-based tool with a Tkinter GUI designed to upload shell URLs to the `xleet.su` platform in bulk. It supports concurrent uploads, price range generation, and detailed logging, making it ideal for automating shell management tasks.

## Features

- **Graphical User Interface (GUI)**: Built with Tkinter for easy interaction.
- **Concurrent Uploads**: Uses `ThreadPoolExecutor` to process multiple shells simultaneously (configurable worker count).
- **Retry Mechanism**: Implements exponential backoff retries for failed requests (e.g., timeouts, connection errors).
- **Price Range Generation**: Automatically assigns prices between a user-defined minimum and maximum.
- **Session Management**: Utilizes `requests.Session` for efficient HTTP connection pooling.
- **Logging**: Detailed logs for debugging and tracking upload status.
- **File Output**: Saves successful and failed uploads to separate text files.

## Prerequisites

- **Python 3.6+**: Ensure Python is installed on your system.
- **Dependencies**: Install required Python packages (see [Installation](#installation)).

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/0xWhoknows/xLeetshellmassupload.git
   cd xLeetshellmassupload
   ```

2. **Install Dependencies**:
   Install the required Python packages using `pip`:
   ```bash
   pip3 install requests brotli
   ```
   - `requests`: For making HTTP requests.
   - `brotli`: For decompressing Brotli-encoded responses.
   - Tkinter is included with Python by default.

3. **Verify Setup**:
   Run the script to ensure dependencies are correctly installed:
   ```bash
   python shell_uploader.py
   ```

## Usage

1. **Prepare Your Shells File**:
   Create a `.txt` file (e.g., `shells.txt`) with one shell URL per line. Example:
   ```
   http://example.com/xleet.php
   http://anothersite.com/xleet.php
   ```

2. **Run the Application**:
   ```bash
   python shell_uploader.py
   ```

3. **Configure the GUI**:
   - **Shells File**: Click "Select Shells File" and choose your `.txt` file.
   - **Credentials**: Enter:
     - `X-Csrf-Token`: Your CSRF token for `xleet.su`.
     - `XSRF-TOKEN`: Your XSRF token cookie.
     - `xleet_session`: Your session cookie.
   - **Price Range**: Optionally set `Min Price` and `Max Price` (defaults: 5.0 and 14.0).
   - Credentials are saved to `settings.json` for reuse.

4. **Start Upload**:
   - Click "Start Upload" to begin processing.
   - Monitor progress in the GUI text area and status bar.
   - Use "Stop Upload" to halt the process if needed.

5. **Review Results**:
   - Successful uploads are saved to `successful_shells.txt`.
   - Failed uploads (e.g., timeouts, errors) are saved to `other_shells.txt`.
   - Check logs in the console for detailed debugging info.

## Configuration

- **Timeout**: Set to 30 seconds per request (adjustable in `upload_shell`).
- **Retries**: 3 attempts with exponential backoff (2s, 4s, 8s) for timeouts/connection errors.
- **Workers**: 5 concurrent threads (configurable in `start_upload` via `max_workers`).

## Example Logs

```
2025-03-05 03:03:56 - INFO - Starting upload...
2025-03-05 03:03:56 - INFO - URL: http://example.com/xleet.php | Price:  5.0 | Status: 200 | Response: Shell added successfully
2025-03-05 03:03:57 - ERROR - Shell: http://anothersite.com/xleet.php - Attempt 1/3 failed: HTTPSConnectionPool(host='xleet.su', port=443): Read timed out.
2025-03-05 03:03:59 - INFO - Retrying after 2 seconds...
```

## Troubleshooting

- **Timeouts**: Increase `timeout` in `upload_shell` (e.g., to 60) or reduce `max_workers` if the server is slow.
- **CSRF Token Mismatch (419)**: Verify your tokens and cookies are valid and up-to-date.
- **No Shells Processed**: Ensure your `.txt` file is correctly formatted and selected.

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Python](https://www.python.org/), [requests](https://requests.readthedocs.io/), and [Tkinter](https://docs.python.org/3/library/tkinter.html).
- Thanks to the open-source community for inspiration and tools.

---
# GestureAgent - Touchless AI Interface

A macOS application that triggers an OpenAI Assistant with hand gestures and captures screenshots for context-aware AI assistance.

## Features

- **Real-time Gesture Detection**: Uses webcam and MediaPipe to detect hand gestures
  - Horizontal wave gesture
  - Palm-up hold gesture
- **OpenAI Assistant Integration**: Communicates with GPT-4 via OpenAI's Assistant API
- **Screenshot Capture**: Automatically captures screen context (fullscreen or active window)
- **GUI Interface**: PyQt5-based interface with system tray support
- **Text-to-Speech**: Optional audio feedback using macOS's built-in TTS
- **Configuration Management**: Flexible settings for gestures, screenshots, and AI parameters

## Requirements

- macOS 10.14 or later
- Python 3.8+
- Webcam
- OpenAI API key

## Installation

1. **Clone or download this repository**
   ```bash
   cd /path/to/gesture-agent
   ```

2. **Install dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate && pip install --upgrade pip
   pip install -r requirements.txt

   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ASSISTANT_ID=your_assistant_id_here  # Optional, will create one if not provided
   ```

4. **Grant permissions**
   - Camera access: System Preferences → Security & Privacy → Camera
   - Screen recording: System Preferences → Security & Privacy → Screen Recording

## Usage

1. **Start the application**
   ```bash
   python run.py
   ```

2. **Configure settings**
   - Click "Configuration" to adjust gesture sensitivity, screenshot mode, etc.
   - Enable/disable text-to-speech feedback
   - Set screenshot quality and format

3. **Start gesture detection**
   - Click "Start Detection" in the main window
   - Perform gestures in front of your webcam:
     - **Wave**: Move your hand horizontally with fingers extended
     - **Palm Up**: Hold your palm open facing the camera for 1.5 seconds

4. **Minimize to system tray**
   - Click "Minimize to Tray" to run in background
   - Access via system tray icon

## Gestures

### Wave Gesture
- Hold up your hand with 3+ fingers extended
- Move your hand left and right horizontally
- Must have at least 2 direction changes to trigger

### Palm Up Gesture  
- Hold your palm open facing the camera
- Keep fingers extended and separated
- Hold steady for 1.5 seconds to trigger

## Configuration

### Gesture Settings (`config.json`)
```json
{
  "gestures": {
    "wave": {
      "enabled": true,
      "confidence_threshold": 0.8
    },
    "palm_up": {
      "enabled": true, 
      "confidence_threshold": 0.7
    }
  }
}
```

### Screenshot Settings
- **Mode**: `fullscreen` or `active_window`
- **Quality**: 10-100 (JPEG quality)
- **Format**: `PNG` or `JPEG`

### Environment Variables (`.env`)
- `OPENAI_API_KEY`: Your OpenAI API key
- `ASSISTANT_ID`: OpenAI Assistant ID (optional)
- `SCREENSHOT_DIR`: Directory for screenshots (default: `./screenshots`)
- `GESTURE_SENSITIVITY`: Global sensitivity 0.1-1.0 (default: 0.8)

## Troubleshooting

### Camera Issues
- Ensure camera permissions are granted
- Check that no other app is using the camera
- Try changing `camera_device` in config.json (0, 1, 2, etc.)

### AI Assistant Issues  
- Verify OpenAI API key is correct and has credits
- Check internet connection
- Review logs in `./logs/` directory

### Screenshot Issues
- Grant Screen Recording permission in System Preferences
- Try switching between fullscreen and active window modes

### Performance Issues
- Reduce FPS in config: `"fps": 15`
- Lower gesture sensitivity: `"confidence_threshold": 0.6`
- Disable camera preview: `"show_camera_preview": false`

## File Structure

```
gesture-agent/
├── src/
│   ├── gesture_detector.py    # Hand gesture detection
│   ├── ai_assistant.py        # OpenAI API integration  
│   ├── screenshot_manager.py  # Screen capture functionality
│   ├── tts_manager.py         # Text-to-speech
│   ├── config_manager.py      # Configuration management
│   ├── logger.py              # Logging and error handling
│   ├── gui.py                 # PyQt5 user interface
│   └── main.py                # Main application logic
├── screenshots/               # Captured screenshots
├── logs/                      # Application logs
├── config.json               # Application configuration
├── .env                      # Environment variables
├── requirements.txt          # Python dependencies
└── run.py                    # Application launcher
```

## Development

### Adding Custom Gestures
1. Extend `GestureDetector` class in `gesture_detector.py`
2. Add detection method following existing patterns
3. Update `config.json` with new gesture settings
4. Add gesture handling in `main.py`

### Customizing AI Prompts
- Modify `_get_gesture_prompt()` in `main.py`
- Add context-specific prompts based on gesture type
- Include screenshot analysis instructions

## License

This project is provided as-is for educational and personal use.

## Support

For issues and questions:
1. Check the logs in `./logs/` directory
2. Review configuration settings
3. Ensure all permissions are granted
4. Verify API key and internet connectivity
# GestureAgent - Touchless AI Interface

An application that controls OpenAI Assistant through gestures and captures screenshots to provide context-aware AI assistance.

## Overview

GestureAgent is an innovative touchless interface that detects hand gestures through webcam and captures screen context to ask contextual questions to OpenAI GPT-4.

## Key Features

- **Real-time Gesture Detection**: Hand gesture detection using webcam and MediaPipe
  - Horizontal wave gesture
  - Palm-up hold gesture
- **OpenAI Assistant Integration**: Real-time communication with GPT-4
- **Screenshot Capture**: Full screen or active window capture
- **GUI Interface**: User-friendly interface with system tray support
- **Voice Feedback**: Audio response through macOS built-in TTS
- **Configuration Management**: Flexible settings for gestures, screenshots, and AI parameters

## Supported Platforms

### Python Version
- **Supported OS**: macOS 10.14 or later
- **Python**: 3.8 or later
- **GUI Framework**: PyQt5

### Electron Version (In Development)
- **Supported OS**: macOS, Windows, Linux
- **Cross-platform**: Electron-based

## Getting Started

Currently, the **Python version** is fully implemented. The Electron version is under development.

### Python Version Installation and Usage

1. **Clone Repository**
   ```bash
   git clone [repository-url]
   cd gesture-agent
   ```

2. **Navigate to Python Version Directory**
   ```bash
   cd gesture-agent-python
   ```

3. **Install Dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Environment Variables Setup**
   ```bash
   # Create .env file and add OpenAI API key
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   ```

5. **Grant Permissions**
   - Camera Access: System Preferences → Security & Privacy → Camera
   - Screen Recording: System Preferences → Security & Privacy → Screen Recording

6. **Run Application**
   ```bash
   python run.py
   ```

## Usage

### Gesture Detection
1. **Start Detection**: Click "Start Detection" in the main window
2. **Perform Gestures**:
   - **Wave**: Extend 3+ fingers and move hand horizontally left and right
   - **Palm Up**: Hold palm facing camera for 1.5 seconds

### Configuration Management
- **Configuration** button to adjust gesture sensitivity, screenshot mode, etc.
- **Voice Feedback** enable/disable
- **Screenshot Quality** and format settings

### System Tray
- **"Minimize to Tray"** to run in background
- Access through system tray icon

## Project Structure

```
gesture-agent/
├── gesture-agent-python/          # Python Implementation (Complete)
│   ├── src/
│   │   ├── gesture_detector.py    # Gesture detection
│   │   ├── ai_assistant.py        # OpenAI API integration
│   │   ├── screenshot_manager.py  # Screen capture
│   │   ├── tts_manager.py         # Text-to-speech
│   │   ├── config_manager.py      # Configuration management
│   │   ├── logger.py              # Logging
│   │   ├── gui.py                 # PyQt5 UI
│   │   └── main.py                # Main application
│   ├── assets/                    # Resource files
│   ├── screenshots/               # Captured screenshots
│   ├── logs/                      # Application logs
│   ├── config.json               # Configuration file
│   ├── requirements.txt          # Python dependencies
│   └── run.py                    # Launch script
├── gesture-agent-electron/        # Electron Implementation (In Development)
├── screenshots/                   # Common screenshot storage
├── logs/                          # Common log storage
└── README.md                     # This file
```

## Requirements

### System Requirements
- **macOS**: 10.14 or later
- **Python**: 3.8 or later (for Python version)
- **Webcam**: For gesture detection
- **OpenAI API Key**: For AI functionality

### Permission Requirements
- **Camera Access Permission**: For gesture detection
- **Screen Recording Permission**: For screenshot capture
- **Internet Connection**: For OpenAI API communication

## Configuration Options

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

### Environment Variables (`.env`)
- `OPENAI_API_KEY`: OpenAI API key (required)
- `ASSISTANT_ID`: OpenAI Assistant ID (optional)
- `SCREENSHOT_DIR`: Screenshot storage directory
- `GESTURE_SENSITIVITY`: Global gesture sensitivity (0.1-1.0)

## Troubleshooting

### Common Issues
- **Camera Issues**: Check permissions and ensure no other app is using camera
- **AI Integration Issues**: Verify OpenAI API key and internet connection
- **Screenshot Issues**: Check screen recording permissions
- **Performance Issues**: Adjust FPS and sensitivity settings

For detailed troubleshooting, refer to [`gesture-agent-python/README.md`](./gesture-agent-python/README.md).

## Development Roadmap

### Completed Features
- ✅ Python version fully implemented
- ✅ Gesture detection system
- ✅ OpenAI Assistant integration
- ✅ Screenshot capture
- ✅ GUI interface
- ✅ System tray support

### In Development
- 🔄 Electron version development
- 🔄 Cross-platform support
- 🔄 Additional gesture patterns

## Contributing

1. Fork this repository
2. Create a new feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

## License

This project is provided as-is for educational and personal use.

## Support

For issues and questions:
1. Check logs in `./logs/` directory
2. Review configuration settings
3. Verify required permissions
4. Check API key and internet connectivity

For more detailed information, refer to [`gesture-agent-python/README.md`](./gesture-agent-python/README.md).

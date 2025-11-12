# Instagram OSINT Tool

A cross-platform Instagram OSINT (Open Source Intelligence) tool for gathering publicly available information from Instagram profiles.

## Features

- Profile information extraction
- Folowing and Followers
- Social media link extraction
- Phone number hind(If Available)

## Requirements

- Python 3.7 or higher
- Internet connection

## Installation

### Quick Install

```bash
pip install -r requirements.txt
```

### Manual Install

```bash
pip install instaloader colorama requests
```

## Usage

### Interactive Mode

```bash
python Insta_Info.py
```

### Command Line Mode

```bash
# Basic investigation
python Insta_Info.py username

# With JSON export
python Insta_Info.py username --json
```

### Examples

```bash
# Investigate a profile
python Insta_Info.py instagram

# Export results to JSON
python Insta_Info.py instagram -j

# From Instagram URL
python Insta_Info.py https://www.instagram.com/instagram/
```

## Output

The tool provides:
- Basic profile information
- Account statistics
- Biography analysis
- Social media connections
- Engagement metrics
- Posting patterns
- Phone number
- Recent posts analysis
- Top hashtags and mentions

## Legal Disclaimer

This tool is for educational and research purposes only. Users must:
- Only access publicly available information
- Comply with Instagram's Terms of Service
- Respect privacy and data protection laws
- Obtain proper authorization before use

## Platform Support

- ✅ Windows 10/11
- ✅ Linux (Ubuntu, Debian, Fedora, etc.)
- ✅ macOS (10.14+)

## Troubleshooting

### Rate Limiting
If you encounter rate limiting, wait a few minutes before trying again.

### Connection Errors
Check your internet connection and ensure Instagram is accessible.

### Installation Issues
Make sure Python and pip are properly installed and updated.

## License

MIT License - See LICENSE file for details

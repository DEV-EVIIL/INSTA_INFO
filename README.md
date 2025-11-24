# Insta Info - Instagram OSINT Investigation Tool

![banner](https://raw.githubusercontent.com/DEV-EVIIL/INSTA_INFO/main/banner.png) <!-- Optional: Insert your banner image if available -->

## Overview

**Insta Info** is an advanced OSINT (Open Source Intelligence) tool for extracting and analyzing information about Instagram profiles and posts. It uses both Instagram’s public-facing site and the `instaloader` library to harvest and visualize data, including detailed metrics, bio connections, social links, and engagement analytics.

---

## Features

- Investigate Instagram profiles and posts/reels.
- Extract:
  - Username, full name, user ID, profile picture
  - Account type/status (private, verified, business)
  - Follower/followee stats, post count, ratios
  - Bio, bio mentions, and connected social accounts
  - External URLs (websites, social platforms)
  - Get Phone Number
  - Export investigation results as JSON

- Interactive and CLI modes with colored, formatted output
- Automatic install of dependencies (instaloader)
- Graceful error handling and user cancellation support

---

## Installation

> **Requirements:**  
> - Python 3.7 or higher  
> - `pip` for package installations  
> - Internet connection  
> - [instaloader](https://instaloader.github.io/) (auto-installed if missing)
> - Optional: terminal with support for ANSI colors (for best output)

### 1. Clone or Download

```bash
git clone https://github.com/DEV-EVIIL/INSTA_INFO.git
cd INSTA_INFO
```

### 2. Install Requirements

The script auto-installs `instaloader` when needed, but it’s recommended to install dependencies manually for smooth setup:

```bash
pip install colorama requests instaloader
```

---

## Usage

### 1. Command Line

Run the script in terminal (direct or with arguments):

```bash
# Investigate a profile:
python Insta_Info.py username_here

# Investigate a post or reel URL:
python Insta_Info.py https://www.instagram.com/p/CODE123XYZ/

# Export results to JSON:
python Insta_Info.py username_here --json
```

### 2. Interactive Mode (Prompts)

Just run:

```bash
python Insta_Info.py
```

Follow on-screen menu and prompts to:
- Enter a username or Instagram URL
- Choose investigation depth or export
- Explore multiple accounts (looped option)
- Quit gracefully via menu

---

## Output Example

Displays enhanced, colored ASCII boxes for each section, such as:

- Profile Found / Not Found
- Basic Information
- Account Statistics
- Account Type & Status
- Biography and Connected Social Media
- External URLs
- Posting Patterns and Engagement Metrics

#### Example Snippet

```text
╔═════════════════════════════════════════════════════════════════════════════════╗
║               ✓ PROFILE FOUND                                                   ║
╚═════════════════════════════════════════════════════════════════════════════════╝

┌───────────────────────────────────────────────────────────────────────────────┐
│ 👤 BASIC INFORMATION                                                         │
└───────────────────────────────────────────────────────────────────────────────┘
  ➤ Username    : @targetuser
  ➤ Full Name   : Target Name
  ➤ Followers   : 3200
  ➤ Following   : 345
  ➤ Posts       : 82

... (continues by section)
```

---

## Advanced Functionalities

- **Post/Reel Analysis:**  
  Input a post/reel URL to extract owner and metrics.
- **API Lookup:**  
  Uses indirect mobile API for extra email/phone (if available).
- **Export to JSON:**  
  Use `--json` to save all investigation data structured.

---

## Troubleshooting

- ❌ **Profile Not Found:** User does not exist or typo.
- ⚠️ **Connection Error:** Rate limit or blocked requests; try VPN or later.

---

## Contributing

Pull requests, suggestions, and feature ideas are welcome!

---

## Disclaimer

> **This tool is for educational and ethical OSINT purposes only.**  
> Always respect privacy, legal boundaries, and platform terms of service.

---

## License

`MIT` — see [LICENSE](LICENSE) for details.

---

## Author

[DEV-EVIIL](https://github.com/DEV-EVIIL)

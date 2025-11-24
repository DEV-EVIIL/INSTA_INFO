import sys
import io
import re
import json
import requests
from urllib.parse import quote_plus
from json import dumps, decoder
from datetime import datetime
from colorama import Fore, Style, init
from collections import Counter
import time

init(autoreset=True)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def print_text_by_text(text, delay=0.03):
    """Print text character by character"""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def clean_instagram_url(input_str):
    """Extract username from Instagram URL or return cleaned username"""
    input_str = input_str.strip()
    
    shortcode_match = re.search(r'(?:instagram\.com/(?:reel|p)/([A-Za-z0-9_-]+))', input_str)
    if shortcode_match:
        return ('post', shortcode_match.group(1))
    
    profile_match = re.search(r'(?:https?://)?(?:www\.)?instagram\.com/([a-zA-Z0-9._]+)', input_str)
    if profile_match:
        return ('profile', profile_match.group(1).replace('@', ''))
    
    return ('profile', input_str.replace('@', '').strip())

def investigate_post(shortcode):
    """Investigate a specific post or reel"""
    try:
        import subprocess
        try:
            import instaloader
        except ImportError:
            print(f"\r{Fore.YELLOW}[i] Installing instaloader...{Style.RESET_ALL}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "instaloader"], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import instaloader
        
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        L = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        sys.stderr = old_stderr
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}╔{'═' * 73}╗")
        print(f"║{' ' * 26}{Fore.YELLOW}✓ POST FOUND{Fore.GREEN}{' ' * 35}║")
        print(f"╚{'═' * 73}╝{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
        print(f"│ {Fore.CYAN}{Style.BRIGHT}📸 POST DETAILS{Style.RESET_ALL}{Fore.YELLOW}{' '*57}│")
        print(f"└{'─' * 73}┘{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ Owner       : {Fore.CYAN}{Style.BRIGHT}@{post.owner_username}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ Type        : {Fore.YELLOW}{post.typename}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ Date        : {Fore.CYAN}{post.date_local.strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ Likes       : {Fore.GREEN}{Style.BRIGHT}{post.likes:,}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ Comments    : {Fore.YELLOW}{Style.BRIGHT}{post.comments:,}{Style.RESET_ALL}")
        
        if hasattr(post, 'video_view_count') and post.video_view_count:
            print(f"{Fore.WHITE}  ➤ Views       : {Fore.MAGENTA}{Style.BRIGHT}{post.video_view_count:,}{Style.RESET_ALL}")
        
        if post.location:
            loc = post.location.name if hasattr(post.location, 'name') else str(post.location)
            print(f"{Fore.WHITE}  ➤ Location    : {Fore.MAGENTA}{loc}{Style.RESET_ALL}")
        
        if post.caption:
            print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
            print(f"│ {Fore.CYAN}{Style.BRIGHT}📝 CAPTION{Style.RESET_ALL}{Fore.YELLOW}{' '*62}│")
            print(f"└{'─' * 73}┘{Style.RESET_ALL}")
            caption_lines = post.caption.split('\n')
            for line in caption_lines[:10]:
                print(f"{Fore.WHITE}  {line[:70]}{Style.RESET_ALL}")
            
            hashtags = re.findall(r'#(\w+)', post.caption)
            mentions = re.findall(r'@([a-zA-Z0-9._]+)', post.caption)
            
            if hashtags:
                print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
                print(f"│ {Fore.CYAN}{Style.BRIGHT}#️⃣ HASHTAGS ({len(hashtags)}){Style.RESET_ALL}{Fore.YELLOW}{' ' * (57 - len(str(len(hashtags))))}│")
                print(f"└{'─' * 73}┘{Style.RESET_ALL}")
                for tag in hashtags[:10]:
                    print(f"{Fore.WHITE}  ➤ {Fore.YELLOW}#{tag}{Style.RESET_ALL}")
            
            if mentions:
                print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
                print(f"│ {Fore.CYAN}{Style.BRIGHT}👥 MENTIONS ({len(mentions)}){Style.RESET_ALL}{Fore.YELLOW}{' ' * (58 - len(str(len(mentions))))}│")
                print(f"└{'─' * 73}┘{Style.RESET_ALL}")
                for mention in mentions[:10]:
                    print(f"{Fore.WHITE}  ➤ {Fore.CYAN}@{mention}{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}╭{'─' * 73}╮")
        print(f"{Fore.GREEN}│{' ' * 25}{Fore.YELLOW}{Style.BRIGHT}✓ ANALYSIS COMPLETE{' ' * 28}{Fore.GREEN}│")
        print(f"{Fore.GREEN}╰{'─' * 73}╯{Style.RESET_ALL}")
        
        return post.owner_username
    except Exception as e:
        sys.stderr = old_stderr
        print(f"{Fore.RED}[!] Instagram is blocking post access. Trying to extract owner...{Style.RESET_ALL}")
        return None

def advanced_lookup(username):
    """Enhanced API lookup with retry mechanism"""
    data = "signed_body=SIGNATURE." + quote_plus(dumps(
        {"q": username, "skip_recovery": "1"},
        separators=(",", ":")
    ))
    
    for attempt in range(3):
        try:
            api = requests.post(
                'https://i.instagram.com/api/v1/users/lookup/',
                headers={
                    "Accept-Language": "en-US",
                    "User-Agent": "Instagram 101.0.0.15.120",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-IG-App-ID": "124024574287414",
                    "Accept-Encoding": "gzip, deflate",
                    "Host": "i.instagram.com",
                    "Connection": "keep-alive",
                    "Content-Length": str(len(data))
                },
                data=data,
                timeout=10
            )
            return {"user": api.json(), "error": None}
        except decoder.JSONDecodeError:
            if attempt < 2:
                time.sleep(2)
                continue
            return {"user": None, "error": "rate limit"}
        except Exception as e:
            return {"user": None, "error": str(e)}
    return {"user": None, "error": "timeout"}

def analyze_username_pattern(username):
    """Analyze username patterns for insights"""
    patterns = {
        "has_numbers": bool(re.search(r'\d', username)),
        "has_underscores": '_' in username,
        "has_dots": '.' in username,
        "length": len(username),
        "all_lowercase": username.islower(),
        "year_pattern": re.findall(r'(19|20)\d{2}', username)
    }
    return patterns

def extract_social_links(text):
    """Extract various social media links from text"""
    social_patterns = {
        "Twitter/X": r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)',
        "TikTok": r'tiktok\.com/@?([a-zA-Z0-9_.]+)',
        "YouTube": r'youtube\.com/(?:c/|channel/|@)?([a-zA-Z0-9_-]+)',
        "Facebook": r'facebook\.com/([a-zA-Z0-9.]+)',
        "LinkedIn": r'linkedin\.com/in/([a-zA-Z0-9-]+)',
        "Snapchat": r'snapchat\.com/add/([a-zA-Z0-9_.]+)',
        "Telegram": r't\.me/([a-zA-Z0-9_]+)',
        "WhatsApp": r'wa\.me/(\d+)',
        "Discord": r'discord\.gg/([a-zA-Z0-9]+)',
        "Threads": r'threads\.net/@([a-zA-Z0-9_.]+)'
    }
    
    found_links = {}
    for platform, pattern in social_patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            found_links[platform] = list(set(matches))
    
    return found_links

def analyze_posting_patterns(posts):
    """Analyze posting time patterns"""
    if not posts:
        return None
    
    hours = [post.date_local.hour for post in posts]
    days = [post.date_local.strftime('%A') for post in posts]
    
    hour_dist = Counter(hours)
    day_dist = Counter(days)
    
    return {
        "most_active_hour": hour_dist.most_common(1)[0] if hour_dist else None,
        "most_active_day": day_dist.most_common(1)[0] if day_dist else None,
        "hour_distribution": dict(hour_dist.most_common(5)),
        "day_distribution": dict(day_dist.most_common(3))
    }

def calculate_engagement_rate(profile, posts):
    """Calculate detailed engagement metrics"""
    if not posts or profile.followers == 0:
        return None
    
    total_likes = sum(post.likes for post in posts[:10])
    total_comments = sum(post.comments for post in posts[:10])
    total_engagement = total_likes + total_comments
    
    avg_engagement = total_engagement / min(len(posts), 10)
    engagement_rate = (avg_engagement / profile.followers) * 100 if profile.followers > 0 else 0
    
    return {
        "avg_likes": total_likes / min(len(posts), 10),
        "avg_comments": total_comments / min(len(posts), 10),
        "engagement_rate": engagement_rate,
        "total_engagement": total_engagement
    }

def extract_locations(posts):
    """Extract location data from posts"""
    locations = []
    for post in posts[:20]:
        if hasattr(post, 'location') and post.location:
            loc_name = post.location.name if hasattr(post.location, 'name') else str(post.location)
            if loc_name and loc_name not in locations:
                locations.append(loc_name)
    return locations

def analyze_content_types(posts):
    """Analyze types of content posted"""
    if not posts:
        return None
    
    types = Counter([post.typename for post in posts[:50]])
    return dict(types)

def export_to_json(data, username):
    """Export investigation results to JSON file"""
    filename = f"{username}_investigation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return filename
    except Exception as e:
        return None

def show_progress(percent, text="Processing", status=""):
    """Display enhanced animated progress bar"""
    bar_len = 40
    filled = int(bar_len * percent / 100)
    
    # Gradient colors based on progress
    if percent < 30:
        bar_color = Fore.RED
    elif percent < 70:
        bar_color = Fore.YELLOW
    else:
        bar_color = Fore.GREEN
    
    # Animated spinner
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    spin_char = spinner[int(time.time() * 10) % len(spinner)]
    
    # Progress bar with gradient effect
    bar = '█' * filled + '▓' * min(1, bar_len - filled) + '░' * max(0, bar_len - filled - 1)
    
    # Percentage with color
    percent_str = f"{percent:3d}%"
    
    # Status indicator
    if percent == 100:
        icon = f"{Fore.GREEN}✓{Style.RESET_ALL}"
    else:
        icon = f"{Fore.CYAN}{spin_char}{Style.RESET_ALL}"
    
    # Build progress line
    status_text = f" {Fore.CYAN}│{Fore.WHITE} {status}{Style.RESET_ALL}" if status else ""
    print(f"\r{icon} {Fore.WHITE}{text:<18} {Fore.CYAN}[{bar_color}{bar}{Fore.CYAN}] {Fore.YELLOW}{percent_str}{status_text}", end='', flush=True)

def instagram_investigation(username, export_json=False):
    start_time = time.time()
    print(f"\n{Fore.CYAN}{Style.BRIGHT}╔{'═' * 73}╗")
    print(f"║{' ' * 18}{Fore.YELLOW}📷 INSTAGRAM OSINT INVESTIGATION{Fore.CYAN}{' ' * 22} ║")
    print(f"╚{'═' * 73}╝{Style.RESET_ALL}\n")
    
    result = clean_instagram_url(username)
    if result[0] == 'post':
        owner = investigate_post(result[1])
        if owner:
            print(f"\n{Fore.CYAN}[i] Investigating post owner: @{owner}{Style.RESET_ALL}")
            username = owner
        else:
            return
    else:
        username = result[1]
    
    if not username:
        print(f"{Fore.RED}[!] Could not extract username from URL{Style.RESET_ALL}")
        return
    
    investigation_data = {"username": username, "timestamp": datetime.now().isoformat()}
    
    print(f"{Fore.YELLOW}┌{'─' * 73}┐")
    print(f"│ {Fore.CYAN}{Style.BRIGHT}🎯 TARGET INFORMATION{Style.RESET_ALL}{Fore.YELLOW}{' ' * 51}│")
    print(f"└{'─' * 73}┘{Style.RESET_ALL}")
    print(f"{Fore.WHITE}  ➤ Username    : {Fore.YELLOW}{Style.BRIGHT}@{username}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}  ➤ Timestamp   : {Fore.CYAN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
    
    print()
    show_progress(0, "Initializing", "Starting...")
    
    try:
        import subprocess
        try:
            import instaloader
        except ImportError:
            print(f"\r{Fore.YELLOW}[i] Installing instaloader...{Style.RESET_ALL}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "instaloader"], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import instaloader
        
        show_progress(15, "Connecting", "Establishing connection...")
        L = instaloader.Instaloader()
        show_progress(30, "Loading", "Fetching profile...")
        profile = instaloader.Profile.from_username(L.context, username)
        show_progress(50, "Processing", "Parsing data...")
        
        print(f"\r{' ' * 150}\r", end='', flush=True)
        print(f"\n{Fore.GREEN}{Style.BRIGHT}╔{'═' * 73}╗")
        print(f"║{' ' * 24}{Fore.YELLOW}✓ PROFILE FOUND{Fore.GREEN}{' ' * 34}║")
        print(f"╚{'═' * 73}╝{Style.RESET_ALL}")
        
        print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
        print(f"│ {Fore.CYAN}{Style.BRIGHT}👤 BASIC INFORMATION{Style.RESET_ALL}{Fore.YELLOW}{' '*52}│")
        print(f"└{'─' * 73}┘{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ Username    : {Fore.CYAN}{Style.BRIGHT}@{profile.username}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ Full Name   : {Fore.YELLOW}{profile.full_name if profile.full_name else 'N/A'}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ User ID     : {Fore.MAGENTA}{profile.userid}{Style.RESET_ALL}")
        
        investigation_data["profile"] = {
            "username": profile.username,
            "full_name": profile.full_name,
            "user_id": profile.userid,
            "is_private": profile.is_private,
            "is_verified": profile.is_verified
        }
        
        if profile.biography:
            print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
            print(f"│ {Fore.CYAN}{Style.BRIGHT}📄 BIOGRAPHY{Style.RESET_ALL}{Fore.YELLOW}{' '*60}│")
            print(f"└{'─' * 73}┘{Style.RESET_ALL}")
            bio_lines = profile.biography.split('\n')
            for line in bio_lines:
                print(f"{Fore.CYAN}  {line}{Style.RESET_ALL}")
            investigation_data["biography"] = profile.biography
        
        print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
        print(f"│ {Fore.CYAN}{Style.BRIGHT}📊 ACCOUNT STATISTICS{Style.RESET_ALL}{Fore.YELLOW}{' '*51}│")
        print(f"└{'─' * 73}┘{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ Followers   : {Fore.GREEN}{Style.BRIGHT}{profile.followers:,}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ Following   : {Fore.YELLOW}{Style.BRIGHT}{profile.followees:,}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ Posts       : {Fore.CYAN}{Style.BRIGHT}{profile.mediacount:,}{Style.RESET_ALL}")
        
        if profile.followers > 0:
            ratio = profile.followees / profile.followers
            print(f"{Fore.WHITE}Follow Ratio: {Fore.CYAN}{ratio:.3f} {Fore.WHITE}(Following/Followers)")
            
            if ratio > 2:
                print(f"{Fore.WHITE}  ➤ Analysis    : {Fore.YELLOW}⚠ High follow ratio - possible engagement farming{Style.RESET_ALL}")
            elif ratio < 0.5 and profile.followers > 1000:
                print(f"{Fore.WHITE}  ➤ Analysis    : {Fore.GREEN}✓ Low follow ratio - strong audience{Style.RESET_ALL}")
        
        investigation_data["statistics"] = {
            "followers": profile.followers,
            "following": profile.followees,
            "posts": profile.mediacount
        }
        
        print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
        print(f"│ {Fore.CYAN}{Style.BRIGHT}🏷️  ACCOUNT TYPE & STATUS{Style.RESET_ALL}{Fore.YELLOW}{' '*48}│")
        print(f"└{'─' * 73}┘{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ Private     : {Fore.RED if profile.is_private else Fore.GREEN}{Style.BRIGHT}{'Yes' if profile.is_private else 'No'}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ Verified    : {Fore.GREEN if profile.is_verified else Fore.YELLOW}{Style.BRIGHT}{'Yes' if profile.is_verified else 'No'}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ Business    : {Fore.CYAN if profile.is_business_account else Fore.YELLOW}{Style.BRIGHT}{'Yes' if profile.is_business_account else 'No'}{Style.RESET_ALL}")
        
        try:
            if hasattr(profile, '_node'):
                node = profile._node
                extended_data = {}
                
                if 'category_name' in node and node['category_name']:
                    print(f"{Fore.WHITE}  ➤ Category    : {Fore.CYAN}{node['category_name']}{Style.RESET_ALL}")
                    extended_data["category"] = node['category_name']
                
                if 'business_email' in node and node['business_email']:
                    print(f"{Fore.WHITE}  ➤ Biz Email   : {Fore.YELLOW}{node['business_email']}{Style.RESET_ALL}")
                    extended_data["business_email"] = node['business_email']
                
                if 'business_phone_number' in node and node['business_phone_number']:
                    print(f"{Fore.WHITE}  ➤ Biz Phone   : {Fore.YELLOW}{node['business_phone_number']}{Style.RESET_ALL}")
                    extended_data["business_phone"] = node['business_phone_number']
                
                if 'public_email' in node and node['public_email']:
                    print(f"{Fore.WHITE}  ➤ Public Email: {Fore.YELLOW}{node['public_email']}{Style.RESET_ALL}")
                    extended_data["public_email"] = node['public_email']
                
                if 'public_phone_number' in node and node['public_phone_number']:
                    print(f"{Fore.WHITE}  ➤ Public Phone: {Fore.YELLOW}{node['public_phone_number']}{Style.RESET_ALL}")
                    extended_data["public_phone"] = node['public_phone_number']
                
                if 'edge_felix_video_timeline' in node and node['edge_felix_video_timeline']:
                    reels_count = node['edge_felix_video_timeline'].get('count', 0)
                    if reels_count > 0:
                        print(f"{Fore.WHITE}  ➤ Reels       : {Fore.CYAN}{reels_count}{Style.RESET_ALL}")
                        extended_data["reels"] = reels_count
                
                if 'edge_highlight_reels' in node and node['edge_highlight_reels']:
                    highlights_count = node['edge_highlight_reels'].get('count', 0)
                    if highlights_count > 0:
                        print(f"{Fore.WHITE}  ➤ Highlights  : {Fore.CYAN}{highlights_count}{Style.RESET_ALL}")
                        extended_data["highlights"] = highlights_count
                
                if extended_data:
                    investigation_data["extended_data"] = extended_data
        except:
            pass
        
        print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
        print(f"│ {Fore.CYAN}{Style.BRIGHT}🔍 API LOOKUP{Style.RESET_ALL}{Fore.YELLOW}{' ' * 59}│")
        print(f"└{'─' * 73}┘{Style.RESET_ALL}")
        other_infos = advanced_lookup(profile.username)
        if other_infos["error"] is None and other_infos.get("user"):
            api_data = {}
            if "obfuscated_email" in other_infos["user"] and other_infos["user"]["obfuscated_email"]:
                print(f"{Fore.WHITE}  ➤ Email       : {Fore.YELLOW}{other_infos['user']['obfuscated_email']}{Style.RESET_ALL}")
                api_data["obfuscated_email"] = other_infos['user']['obfuscated_email']
            
            if "obfuscated_phone" in other_infos["user"] and str(other_infos["user"]["obfuscated_phone"]):
                print(f"{Fore.WHITE}  ➤ Phone       : {Fore.YELLOW}{other_infos['user']['obfuscated_phone']}{Style.RESET_ALL}")
                api_data["obfuscated_phone"] = str(other_infos['user']['obfuscated_phone'])
            
            if api_data:
                investigation_data["api_data"] = api_data
        
        if profile.biography:
            mentions = re.findall(r'@([a-zA-Z0-9._]+)', profile.biography)
            if mentions:
                print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
                print(f"│ {Fore.CYAN}{Style.BRIGHT}👥 TAGGED ACCOUNTS IN BIO ({len(mentions)}){Style.RESET_ALL}{Fore.YELLOW}{' ' * (45 - len(str(len(mentions))))}│")
                print(f"└{'─' * 73}┘{Style.RESET_ALL}")
                for mention in mentions:
                    print(f"{Fore.WHITE}  ➤ @{Fore.YELLOW}{Style.BRIGHT}{mention}{Style.RESET_ALL}")
                investigation_data["bio_mentions"] = mentions
        
        bio_text = f"{profile.biography} {profile.external_url or ''}"
        social_links = extract_social_links(bio_text)
        
        if social_links:
            print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
            print(f"│ {Fore.CYAN}{Style.BRIGHT}🌐 CONNECTED SOCIAL MEDIA{Style.RESET_ALL}{Fore.YELLOW}{' '*48} │")
            print(f"└{'─' * 73}┘{Style.RESET_ALL}")
            for platform, usernames in social_links.items():
                for user in usernames:
                    print(f"{Fore.WHITE}  ➤ {platform:<12}: {Fore.CYAN}{Style.BRIGHT}{user}{Style.RESET_ALL}")
            investigation_data["social_links"] = social_links
        
        all_links = []
        try:
            if hasattr(profile, '_node') and 'bio_links' in profile._node:
                for link in profile._node['bio_links']:
                    if 'url' in link:
                        all_links.append(link['url'])
        except:
            if profile.external_url:
                all_links.append(profile.external_url)
            
            if profile.biography:
                url_pattern = r'https?://[^\s\n]+'
                bio_urls = re.findall(url_pattern, profile.biography)
                for url in bio_urls:
                    if url not in all_links:
                        all_links.append(url)
        
        if all_links:
            print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
            print(f"│ {Fore.CYAN}{Style.BRIGHT}🔗 EXTERNAL URLS ({len(all_links)}){Style.RESET_ALL}{Fore.YELLOW}{' ' * (53 - len(str(len(all_links))))}│")
            print(f"└{'─' * 73}┘{Style.RESET_ALL}")
            for i, link in enumerate(all_links, 1):
                print(f"{Fore.WHITE}  ➤ {Fore.MAGENTA}{i}. {Fore.CYAN}{link}{Style.RESET_ALL}")
            investigation_data["external_urls"] = all_links
        
        print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
        print(f"│ {Fore.CYAN}{Style.BRIGHT}🖼️  MEDIA{Style.RESET_ALL}{Fore.YELLOW}{' '*64}│")
        print(f"└{'─' * 73}┘{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ➤ Profile Picture: {Fore.CYAN}{Style.BRIGHT}[\033]8;;{profile.profile_pic_url}\033\\{Fore.GREEN}Click Here{Fore.CYAN}\033]8;;\033\\]{Style.RESET_ALL}")
        investigation_data["profile_pic_url"] = profile.profile_pic_url
        
        posts = []
        if not profile.is_private and profile.mediacount > 0:
            try:
                print(f"\n{Fore.WHITE}[{Fore.CYAN}+{Fore.WHITE}] Fetching posts data...")
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()
                posts = list(profile.get_posts())
                sys.stderr = old_stderr
            except Exception:
                pass
        
        if not profile.is_private and posts and len(posts) > 0:
            content_types = analyze_content_types(posts)
            if content_types:
                print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
                print(f"│ {Fore.CYAN}{Style.BRIGHT}📈 CONTENT TYPE DISTRIBUTION{Style.RESET_ALL}{Fore.YELLOW}{' '*44}│")
                print(f"└{'─' * 73}┘{Style.RESET_ALL}")
                for ctype, count in content_types.items():
                    percentage = (count / len(posts[:50])) * 100
                    bar = '█' * int(percentage / 2)
                    print(f"{Fore.WHITE}  ➤ {ctype:<15}: {Fore.CYAN}{Style.BRIGHT}{count:>3} {Fore.GREEN}{bar} {Fore.WHITE}({percentage:.1f}%){Style.RESET_ALL}")
                investigation_data["content_types"] = content_types
            
            engagement_data = calculate_engagement_rate(profile, posts)
            if engagement_data:
                print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
                print(f"│ {Fore.CYAN}{Style.BRIGHT}💬 ENGAGEMENT METRICS{Style.RESET_ALL}{Fore.YELLOW}{' '*52}│")
                print(f"└{'─' * 73}┘{Style.RESET_ALL}")
                print(f"{Fore.WHITE}  ➤ Avg Likes       : {Fore.GREEN}{Style.BRIGHT}{engagement_data['avg_likes']:>8.0f}{Style.RESET_ALL}")
                print(f"{Fore.WHITE}  ➤ Avg Comments    : {Fore.YELLOW}{Style.BRIGHT}{engagement_data['avg_comments']:>8.0f}{Style.RESET_ALL}")
                print(f"{Fore.WHITE}  ➤ Engagement Rate : {Fore.CYAN}{Style.BRIGHT}{engagement_data['engagement_rate']:>7.2f}%{Style.RESET_ALL}")
                
                if engagement_data['engagement_rate'] > 5:
                    print(f"{Fore.GREEN}     ✓ Excellent engagement rate{Style.RESET_ALL}")
                elif engagement_data['engagement_rate'] > 2:
                    print(f"{Fore.YELLOW}     • Good engagement rate{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}     ⚠ Low engagement rate{Style.RESET_ALL}")
                
                investigation_data["engagement"] = engagement_data
            
            posting_patterns = analyze_posting_patterns(posts)
            if posting_patterns:
                print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
                print(f"│ {Fore.CYAN}{Style.BRIGHT}⏰ POSTING PATTERNS{Style.RESET_ALL}{Fore.YELLOW}{' '*55}│")
                print(f"└{'─' * 73}┘{Style.RESET_ALL}")
                if posting_patterns["most_active_hour"]:
                    hour, count = posting_patterns["most_active_hour"]
                    print(f"{Fore.WHITE}  ➤ Most Active Hour: {Fore.YELLOW}{Style.BRIGHT}{hour}:00 {Fore.WHITE}({count} posts){Style.RESET_ALL}")
                if posting_patterns["most_active_day"]:
                    day, count = posting_patterns["most_active_day"]
                    print(f"{Fore.WHITE}  ➤ Most Active Day : {Fore.YELLOW}{Style.BRIGHT}{day} {Fore.WHITE}({count} posts){Style.RESET_ALL}")
                
                print(f"\n{Fore.WHITE}  Top Active Hours:{Style.RESET_ALL}")
                for hour, count in posting_patterns["hour_distribution"].items():
                    bar = '█' * min(count * 2, 30)
                    print(f"{Fore.WHITE}    {hour:02d}:00 {Fore.CYAN}{bar} {Fore.WHITE}{count}{Style.RESET_ALL}")
                
                investigation_data["posting_patterns"] = posting_patterns
            
            locations = extract_locations(posts)
            if locations:
                print(f"\n{Fore.YELLOW}┌{'─' * 73}┐")
                print(f"│ {Fore.CYAN}{Style.BRIGHT}📍 LOCATIONS ({len(locations)}){Style.RESET_ALL}{Fore.YELLOW}{' ' * (57 - len(str(len(locations))))}│")
                print(f"└{'─' * 73}┘{Style.RESET_ALL}")
                for i, loc in enumerate(locations[:10], 1):
                    print(f"{Fore.WHITE}  ➤ {Fore.MAGENTA}{i:>2}. {Fore.YELLOW}{loc}{Style.RESET_ALL}")
                investigation_data["locations"] = locations
            
            try:
                recent_posts = posts[:10]
                print(f"\n{Fore.CYAN}{Style.BRIGHT}╭{'─' * 73}╮")
                print(f"{Fore.CYAN}│ {Fore.YELLOW}{Style.BRIGHT}📸  RECENT POSTS ANALYSIS ({len(recent_posts)} posts){' ' * (44 - len(str(len(recent_posts))))}{Fore.CYAN}│")
                print(f"{Fore.CYAN}╰{'─' * 73}╯{Style.RESET_ALL}")
                
                all_hashtags = []
                all_mentions = []
                posts_data = []
                
                for i, post in enumerate(recent_posts, 1):
                    post_info = {
                        "date": post.date_local.strftime('%Y-%m-%d %H:%M'),
                        "likes": post.likes,
                        "comments": post.comments,
                        "type": post.typename
                    }
                    
                    print(f"\n{Fore.YELLOW}Post #{i}:{Style.RESET_ALL}")
                    print(f"{Fore.WHITE}  📅 Date: {Fore.CYAN}{post.date_local.strftime('%Y-%m-%d %H:%M')}")
                    print(f"{Fore.WHITE}  ❤️  Likes: {Fore.GREEN}{post.likes:,}")
                    print(f"{Fore.WHITE}  💬 Comments: {Fore.YELLOW}{post.comments:,}")
                    print(f"{Fore.WHITE}  📹 Type: {Fore.CYAN}{post.typename}")
                    
                    if hasattr(post, 'location') and post.location:
                        loc = post.location.name if hasattr(post.location, 'name') else str(post.location)
                        print(f"{Fore.WHITE}  📍 Location: {Fore.MAGENTA}{loc}")
                        post_info["location"] = loc
                    
                    if post.caption:
                        caption = post.caption[:100] + '...' if len(post.caption) > 100 else post.caption
                        print(f"{Fore.WHITE}  📝 Caption: {Fore.WHITE}{caption}")
                        post_info["caption"] = post.caption
                        
                        hashtags = re.findall(r'#(\w+)', post.caption)
                        mentions = re.findall(r'@([a-zA-Z0-9._]+)', post.caption)
                        all_hashtags.extend(hashtags)
                        all_mentions.extend(mentions)
                        
                        if hashtags:
                            post_info["hashtags"] = hashtags
                        if mentions:
                            post_info["mentions"] = mentions
                    
                    posts_data.append(post_info)
                
                investigation_data["recent_posts"] = posts_data
                
                if all_hashtags:
                    top_hashtags = Counter(all_hashtags).most_common(15)
                    print(f"\n{Fore.GREEN}{Style.BRIGHT}╭{'─' * 73}╮")
                    print(f"{Fore.GREEN}│ {Fore.YELLOW}{Style.BRIGHT}#️⃣  TOP HASHTAGS{' ' * 58}{Fore.GREEN}│")
                    print(f"{Fore.GREEN}├{'─' * 73}┤{Style.RESET_ALL}")
                    for tag, count in top_hashtags:
                        bar = '█' * min(count * 3, 30)
                        tag_text = f"#{tag:<20} {bar} ({count}x)"
                        print(f"{Fore.GREEN}│ {Fore.WHITE}#{Fore.YELLOW}{tag:<20} {Fore.CYAN}{bar} {Fore.WHITE}({count}x){' ' * (48 - len(tag) - len(bar) - len(str(count)))}{Fore.GREEN}│{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}╰{'─' * 73}╯{Style.RESET_ALL}")
                    investigation_data["top_hashtags"] = dict(top_hashtags)
                
                if all_mentions:
                    top_mentions = Counter(all_mentions).most_common(10)
                    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}╭{'─' * 73}╮")
                    print(f"{Fore.MAGENTA}│ {Fore.YELLOW}{Style.BRIGHT}👤  FREQUENTLY TAGGED ACCOUNTS{' ' * 44}{Fore.MAGENTA}│")
                    print(f"{Fore.MAGENTA}├{'─' * 73}┤{Style.RESET_ALL}")
                    for mention, count in top_mentions:
                        print(f"{Fore.MAGENTA}│ {Fore.WHITE}@{Fore.YELLOW}{mention:<25} {Fore.WHITE}({Fore.CYAN}{count}x{Fore.WHITE}){' ' * (43 - len(mention) - len(str(count)))}{Fore.MAGENTA}│{Style.RESET_ALL}")
                    print(f"{Fore.MAGENTA}╰{'─' * 73}╯{Style.RESET_ALL}")
                    investigation_data["top_mentions"] = dict(top_mentions)
                
                if len(posts) > 0:
                    latest_post = posts[0].date_local
                    oldest_post = min(posts, key=lambda p: p.date_local)
                    days_since = (datetime.now() - latest_post.replace(tzinfo=None)).days
                    
                    print(f"\n{Fore.YELLOW}{Style.BRIGHT}╭{'─' * 73}╮")
                    print(f"{Fore.YELLOW}│ {Fore.CYAN}{Style.BRIGHT}📊  ACTIVITY TIMELINE{' ' * 53}{Fore.YELLOW}│")
                    print(f"{Fore.YELLOW}├{'─' * 73}┤{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}│ {Fore.WHITE}Latest Post    : {Fore.YELLOW}{latest_post.strftime('%Y-%m-%d')} {Fore.WHITE}({Fore.CYAN}{days_since} days ago{Fore.WHITE}){' ' * (35 - len(str(days_since)))}{Fore.YELLOW}│")
                    print(f"{Fore.YELLOW}│ {Fore.WHITE}Oldest Fetched : {Fore.YELLOW}{oldest_post.date_local.strftime('%Y-%m-%d')}{' ' * 44}{Fore.YELLOW}│{Style.RESET_ALL}")
                    
                    if profile.mediacount > 0 and len(posts) > 1:
                        total_days = (latest_post.replace(tzinfo=None) - oldest_post.date_local.replace(tzinfo=None)).days
                        if total_days > 0:
                            avg_posts_month = profile.mediacount / (total_days / 30)
                            avg_posts_week = profile.mediacount / (total_days / 7)
                            print(f"{Fore.YELLOW}│ {Fore.WHITE}Avg Posts      : {Fore.CYAN}{avg_posts_month:.1f} per month {Fore.WHITE}/ {Fore.CYAN}{avg_posts_week:.1f} per week{' ' * (30 - len(f'{avg_posts_month:.1f}') - len(f'{avg_posts_week:.1f}'))}{Fore.YELLOW}│{Style.RESET_ALL}")
                    
                    print(f"{Fore.YELLOW}│{' ' * 73}{Fore.YELLOW}│")
                    if days_since == 0:
                        print(f"{Fore.YELLOW}│ {Fore.GREEN}✓ Very active (posted today){' ' * 46}{Fore.YELLOW}│{Style.RESET_ALL}")
                    elif days_since <= 7:
                        print(f"{Fore.YELLOW}│ {Fore.GREEN}✓ Active account{' ' * 58}{Fore.YELLOW}│{Style.RESET_ALL}")
                    elif days_since <= 30:
                        print(f"{Fore.YELLOW}│ {Fore.YELLOW}• Moderately active{' ' * 54}{Fore.YELLOW}│{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}│ {Fore.RED}⚠ Inactive account{' ' * 56}{Fore.YELLOW}│{Style.RESET_ALL}")
                    
                    print(f"{Fore.YELLOW}╰{'─' * 73}╯{Style.RESET_ALL}")
            
            except Exception as e:
                print(f"{Fore.RED}[!] Error analyzing posts: {str(e)}")
        
        elif profile.is_private:
            print(f"\n{Fore.YELLOW}╭{'─' * 73}╮")
            print(f"{Fore.YELLOW}│ {Fore.YELLOW}⚠ Account is private - post analysis unavailable{' ' * 27}{Fore.YELLOW}│")
            print(f"{Fore.YELLOW}╰{'─' * 73}╯{Style.RESET_ALL}")
        
        show_progress(100, "Complete", "Investigation finished!")
        print()
        elapsed = time.time() - start_time
        print(f"{Fore.GREEN}✓{Style.RESET_ALL} {Fore.WHITE}Investigation completed in {Fore.CYAN}{Style.BRIGHT}{elapsed:.2f}s{Style.RESET_ALL}\n")
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}╭{'─' * 73}╮")
        print(f"{Fore.GREEN}│{' ' * 22}{Fore.YELLOW}{Style.BRIGHT}✓ INVESTIGATION COMPLETE{' ' * 27}{Fore.GREEN}│")
        print(f"{Fore.GREEN}╰{'─' * 73}╯{Style.RESET_ALL}")
        
        if export_json:
            print(f"\n{Fore.CYAN}[●] {Fore.WHITE}Exporting data to JSON...{Style.RESET_ALL}")
            filename = export_to_json(investigation_data, username)
            if filename:
                print(f"{Fore.GREEN}[✓] {Fore.WHITE}Data exported to: {Fore.CYAN}{Style.BRIGHT}{filename}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}[!] Failed to export data{Style.RESET_ALL}")
        
    except ImportError as e:
        print(f"\r{Fore.RED}[!] Failed to install instaloader: {str(e)}{Style.RESET_ALL}")
    except Exception as e:
        error_msg = str(e)
        print(f"\r{Fore.RED}{Style.BRIGHT}\n{'╔' + '═' * 73 + '╗'}")
        print(f"║{' '*22}{Fore.YELLOW}INVESTIGATION RESULTS{Fore.RED}{' '*30}║")
        print(f"{'╚' + '═' * 73 + '╝'}{Style.RESET_ALL}")
        
        if "does not exist" in error_msg.lower() or "not exist" in error_msg.lower():
            print(f"\n{Fore.RED}{Style.BRIGHT}╭{'─' * 73}╮")
            print(f"{Fore.RED}│ {Fore.YELLOW}{Style.BRIGHT}✗ PROFILE NOT FOUND{' ' * 54}{Fore.RED}│")
            print(f"{Fore.RED}├{'─' * 73}┤{Style.RESET_ALL}")
            print(f"{Fore.RED}│ {Fore.YELLOW}➤ Username @{username} does not exist on Instagram{' ' * (45 - len(username))}{Fore.RED}│{Style.RESET_ALL}")
            print(f"{Fore.RED}╰{'─' * 73}╯{Style.RESET_ALL}")
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            print(f"\n{Fore.RED}╭{'─' * 73}╮")
            print(f"{Fore.RED}│ {Fore.YELLOW}[!] Connection error. Instagram may be blocking requests.{' ' * 15}{Fore.RED}│")
            print(f"{Fore.RED}│ {Fore.YELLOW}[i] Try again later or check your internet connection{' ' * 19}{Fore.RED}│")
            print(f"{Fore.RED}╰{'─' * 73}╯{Style.RESET_ALL}")
        elif "login" in error_msg.lower() or "challenge" in error_msg.lower():
            print(f"\n{Fore.RED}╭{'─' * 73}╮")
            print(f"{Fore.RED}│ {Fore.YELLOW}[!] Instagram requires authentication{' ' * 36}{Fore.RED}│")
            print(f"{Fore.RED}│ {Fore.YELLOW}[i] Some data may be restricted without login{' ' * 27}{Fore.RED}│")
            print(f"{Fore.RED}╰{'─' * 73}╯{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}╭{'─' * 73}╮")
            print(f"{Fore.RED}│ {Fore.YELLOW}[!] Error: {error_msg[:60]}{' ' * (62 - len(error_msg[:60]))}{Fore.RED}│")
            print(f"{Fore.RED}╰{'─' * 73}╯{Style.RESET_ALL}")

def print_banner():
    """Print enhanced ASCII banner"""
    print(f"\n{Fore.RED}{Style.BRIGHT}")
    print("    ██╗███╗   ██╗███████╗████████╗ █████╗     ██╗███╗   ██╗███████╗ ██████╗ ")
    print("    ██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗    ██║████╗  ██║██╔════╝██╔═══██╗")
    print("    ██║██╔██╗ ██║███████╗   ██║   ███████║    ██║██╔██╗ ██║█████╗  ██║   ██║")
    print("    ██║██║╚██╗██║╚════██║   ██║   ██╔══██║    ██║██║╚██╗██║██╔══╝  ██║   ██║")
    print("    ██║██║ ╚████║███████║   ██║   ██║  ██║    ██║██║ ╚████║██║     ╚██████╔╝")
    print("    ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝    ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝ ")
    print(f"{Fore.YELLOW}    ═══════════════════════════════════════════════════════════════════════")
    print(f"{Fore.CYAN}              🔍 Instagram OSINT Investigation Tool v2.0 🔍")
    print(f"{Fore.GREEN}                  Advanced Profile Intelligence System")
    print(f"{Fore.YELLOW}    ═══════════════════════════════════════════════════════════════════════{Style.RESET_ALL}\n")

def interactive_menu():
    """Display interactive menu for options"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}OPTIONS:{Style.RESET_ALL}")
    print(f"{Fore.WHITE}1. Quick Investigation (Fast)")
    print(f"{Fore.WHITE}2. Deep Investigation (Detailed)")
    print(f"{Fore.WHITE}3. Export Results to JSON")
    print(f"{Fore.WHITE}4. Exit")
    
    choice = input(f"\n{Fore.GREEN}Select option (1-4): {Style.RESET_ALL}").strip()
    return choice

if __name__ == "__main__":
    try:
        print_banner()
        
        if len(sys.argv) > 1:
            username = sys.argv[1]
            export_json = '--json' in sys.argv or '-j' in sys.argv
            
            if username and not username.startswith('-'):
                instagram_investigation(username, export_json=export_json)
            else:
                print(f"{Fore.RED}[!] Invalid username provided{Style.RESET_ALL}")
        else:
            while True:
                print(f"\n{Fore.CYAN}{Style.BRIGHT}{'═'*75}{Style.RESET_ALL}")
                username = input(f"{Fore.YELLOW}[{Fore.GREEN}►{Fore.YELLOW}] {Fore.WHITE}Enter Instagram Username or URL {Fore.CYAN}(or {Fore.RED}'quit'{Fore.CYAN} to exit)\n{Fore.YELLOW}[{Fore.GREEN}►{Fore.YELLOW}] {Fore.GREEN}").strip()
                print(Style.RESET_ALL, end='')
                
                if username.lower() in ['quit', 'exit', 'q']:
                    print(f"\n{Fore.GREEN}{Style.BRIGHT}╭{'─' * 73}╮")
                    print(f"{Fore.GREEN}│ ", end='')
                    print_text_by_text(f"{Fore.CYAN}Goodbye! Thanks for using Insta Info. Stay safe! 👋{' ' * 11}{Fore.GREEN}│")
                    print(f"{Fore.GREEN}╰{'─' * 73}╯{Style.RESET_ALL}\n")
                    break
                
                if not username:
                    print(f"{Fore.RED}[!] No username provided{Style.RESET_ALL}")
                    continue
                
                instagram_investigation(username, export_json=False)
                
                print(f"\n{Fore.CYAN}{'─' * 75}")
                continue_choice = input(f"{Fore.CYAN}Investigate another account? (y/n): {Fore.GREEN}").strip().lower()
                print(Style.RESET_ALL, end='')
                if continue_choice not in ['y', 'yes', 'Y']:
                    print(f"\n{Fore.GREEN}{Style.BRIGHT}╭{'─' * 73}╮")
                    print(f"{Fore.GREEN}│ ", end='')
                    print_text_by_text(f"{Fore.CYAN}Goodbye! Thanks for using Insta Info. Stay safe! 👋{' ' * 11}{Fore.GREEN}          │")
                    print(f"{Fore.GREEN}╰{'─' * 73}╯{Style.RESET_ALL}\n")
                    break
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[!] Operation cancelled by user{Style.RESET_ALL}")
        print_text_by_text(f"{Fore.CYAN}Goodbye! Thanks for using Insta Info. Stay safe! 👋{Style.RESET_ALL}\n")
        sys.exit(0)

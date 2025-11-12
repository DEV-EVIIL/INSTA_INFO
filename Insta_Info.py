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

def clean_instagram_url(input_str):
    """Extract username from Instagram URL or return cleaned username"""
    input_str = input_str.strip()
    
    # Check for reel or post URL
    shortcode_match = re.search(r'(?:instagram\.com/(?:reel|p)/([A-Za-z0-9_-]+))', input_str)
    if shortcode_match:
        try:
            import instaloader
            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            L = instaloader.Instaloader()
            post = instaloader.Post.from_shortcode(L.context, shortcode_match.group(1))
            sys.stderr = old_stderr
            return post.owner_username
        except:
            sys.stderr = old_stderr
            return None
    
    # Check for profile URL
    profile_match = re.search(r'(?:https?://)?(?:www\.)?instagram\.com/([a-zA-Z0-9._]+)/?', input_str)
    if profile_match:
        return profile_match.group(1).replace('@', '')
    
    # Treat as username
    return input_str.replace('@', '').strip()

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

def instagram_investigation(username, export_json=False):
    print(f"\n{Fore.YELLOW}{Style.BRIGHT}📷 INSTAGRAM OSINT INVESTIGATION{Style.RESET_ALL}\n")
    
    # Clean URL or username
    username = clean_instagram_url(username)
    if not username:
        print(f"{Fore.RED}[!] Could not extract username from URL{Style.RESET_ALL}")
        return
    
    investigation_data = {"username": username, "timestamp": datetime.now().isoformat()}
    
    print(f"\n{Fore.GREEN}TARGET INFORMATION:{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Username: {Fore.YELLOW}@{username}")
    print(f"{Fore.WHITE}Time: {Fore.YELLOW}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n{Fore.WHITE}[{Fore.GREEN}+{Fore.WHITE}] {Fore.CYAN}Starting investigation...")
    
    try:
        import subprocess
        try:
            import instaloader
        except ImportError:
            print(f"{Fore.YELLOW}[i] Installing instaloader...{Style.RESET_ALL}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "instaloader"], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import instaloader
        
        L = instaloader.Instaloader()
        profile = instaloader.Profile.from_username(L.context, username)
        
        print(f"\r{Fore.YELLOW}{Style.BRIGHT}{'=' * 60}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}INVESTIGATION RESULTS")
        print(f"{Fore.YELLOW}{Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}")
        
        print(f"{Fore.GREEN}{Style.BRIGHT}[✓] PROFILE FOUND{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{'-' * 60}")
        
        # Basic Profile Information
        print(f"\n{Fore.CYAN}{Style.BRIGHT}👤 BASIC INFORMATION:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{'─' * 60}")
        print(f"{Fore.WHITE}Username: {Fore.CYAN}@{profile.username}")
        print(f"{Fore.WHITE}Full Name: {Fore.YELLOW}{profile.full_name if profile.full_name else 'N/A'}")
        print(f"{Fore.WHITE}User ID: {Fore.MAGENTA}{profile.userid}")
        
        investigation_data["profile"] = {
            "username": profile.username,
            "full_name": profile.full_name,
            "user_id": profile.userid,
            "is_private": profile.is_private,
            "is_verified": profile.is_verified
        }
        
        # Biography
        if profile.biography:
            print(f"\n{Fore.CYAN}{Style.BRIGHT}📄 BIOGRAPHY:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{'─' * 60}")
            bio_lines = profile.biography.split('\n')
            for line in bio_lines:
                print(f"{Fore.CYAN}{line}")
            investigation_data["biography"] = profile.biography
        
        # Statistics
        print(f"\n{Fore.CYAN}{Style.BRIGHT}📊 ACCOUNT STATISTICS:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{'─' * 60}")
        print(f"{Fore.WHITE}Followers: {Fore.GREEN}{profile.followers:,}")
        print(f"{Fore.WHITE}Following: {Fore.YELLOW}{profile.followees:,}")
        print(f"{Fore.WHITE}Posts: {Fore.CYAN}{profile.mediacount:,}")
        
        if profile.followers > 0:
            ratio = profile.followees / profile.followers
            print(f"{Fore.WHITE}Follow Ratio: {Fore.CYAN}{ratio:.3f} {Fore.WHITE}(Following/Followers)")
            
            if ratio > 2:
                print(f"{Fore.YELLOW}  ⚠ High follow ratio - possible engagement farming")
            elif ratio < 0.5 and profile.followers > 1000:
                print(f"{Fore.GREEN}  ✓ Low follow ratio - strong audience")
        
        investigation_data["statistics"] = {
            "followers": profile.followers,
            "following": profile.followees,
            "posts": profile.mediacount
        }
        
        # Account Type & Status
        print(f"\n{Fore.CYAN}{Style.BRIGHT}🏷️ ACCOUNT TYPE & STATUS:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{'─' * 60}")
        print(f"{Fore.WHITE}Private Account: {Fore.RED if profile.is_private else Fore.GREEN}{profile.is_private}")
        print(f"{Fore.WHITE}Verified Account: {Fore.GREEN if profile.is_verified else Fore.YELLOW}{profile.is_verified}")
        print(f"{Fore.WHITE}Business Account: {Fore.CYAN if profile.is_business_account else Fore.YELLOW}{profile.is_business_account}")
        
        # Extended Profile Data
        try:
            if hasattr(profile, '_node'):
                node = profile._node
                extended_data = {}
                
                if 'category_name' in node and node['category_name']:
                    print(f"{Fore.WHITE}Category: {Fore.CYAN}{node['category_name']}")
                    extended_data["category"] = node['category_name']
                
                if 'business_email' in node and node['business_email']:
                    print(f"{Fore.WHITE}Business Email: {Fore.YELLOW}{node['business_email']}")
                    extended_data["business_email"] = node['business_email']
                
                if 'business_phone_number' in node and node['business_phone_number']:
                    print(f"{Fore.WHITE}Business Phone: {Fore.YELLOW}{node['business_phone_number']}")
                    extended_data["business_phone"] = node['business_phone_number']
                
                if 'public_email' in node and node['public_email']:
                    print(f"{Fore.WHITE}Public Email: {Fore.YELLOW}{node['public_email']}")
                    extended_data["public_email"] = node['public_email']
                
                if 'public_phone_number' in node and node['public_phone_number']:
                    print(f"{Fore.WHITE}Public Phone: {Fore.YELLOW}{node['public_phone_number']}")
                    extended_data["public_phone"] = node['public_phone_number']
                
                # Additional metrics
                if 'edge_felix_video_timeline' in node and node['edge_felix_video_timeline']:
                    reels_count = node['edge_felix_video_timeline'].get('count', 0)
                    if reels_count > 0:
                        print(f"{Fore.WHITE}Reels Count: {Fore.CYAN}{reels_count}")
                        extended_data["reels"] = reels_count
                
                if 'edge_highlight_reels' in node and node['edge_highlight_reels']:
                    highlights_count = node['edge_highlight_reels'].get('count', 0)
                    if highlights_count > 0:
                        print(f"{Fore.WHITE}Story Highlights: {Fore.CYAN}{highlights_count}")
                        extended_data["highlights"] = highlights_count
                
                if extended_data:
                    investigation_data["extended_data"] = extended_data
        except:
            pass
        
        # Advanced API Lookup
        print(f"\n{Fore.WHITE}[{Fore.CYAN}+{Fore.WHITE}] Querying Instagram API...")
        other_infos = advanced_lookup(profile.username)
        if other_infos["error"] is None and other_infos.get("user"):
            api_data = {}
            if "obfuscated_email" in other_infos["user"] and other_infos["user"]["obfuscated_email"]:
                print(f"{Fore.WHITE}Obfuscated Email: {Fore.YELLOW}{other_infos['user']['obfuscated_email']}")
                api_data["obfuscated_email"] = other_infos['user']['obfuscated_email']
            
            if "obfuscated_phone" in other_infos["user"] and str(other_infos["user"]["obfuscated_phone"]):
                print(f"{Fore.WHITE}Obfuscated Phone: {Fore.YELLOW}{other_infos['user']['obfuscated_phone']}")
                api_data["obfuscated_phone"] = str(other_infos['user']['obfuscated_phone'])
            
            if api_data:
                investigation_data["api_data"] = api_data
        
        # Mentions in Bio
        if profile.biography:
            mentions = re.findall(r'@([a-zA-Z0-9._]+)', profile.biography)
            if mentions:
                print(f"\n{Fore.CYAN}{Style.BRIGHT}👥 TAGGED ACCOUNTS IN BIO ({len(mentions)}):{Style.RESET_ALL}")
                print(f"{Fore.WHITE}{'─' * 60}")
                for mention in mentions:
                    print(f"{Fore.WHITE}  • @{Fore.YELLOW}{mention}")
                investigation_data["bio_mentions"] = mentions
        
        # Social Media Links
        bio_text = f"{profile.biography} {profile.external_url or ''}"
        social_links = extract_social_links(bio_text)
        
        if social_links:
            print(f"\n{Fore.CYAN}{Style.BRIGHT}🌐 CONNECTED SOCIAL MEDIA:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{'─' * 60}")
            for platform, usernames in social_links.items():
                for user in usernames:
                    print(f"{Fore.WHITE}  {platform}: {Fore.CYAN}{user}")
            investigation_data["social_links"] = social_links
        
        # External URLs
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
            print(f"\n{Fore.CYAN}{Style.BRIGHT}🔗 EXTERNAL URLS ({len(all_links)}):{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{'─' * 60}")
            for i, link in enumerate(all_links, 1):
                print(f"{Fore.WHITE}  {i}. {Fore.CYAN}{link}")
            investigation_data["external_urls"] = all_links
        
        print(f"\n{Fore.CYAN}{Style.BRIGHT}🖼️ MEDIA:{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{'─' * 60}")
        print(f"{Fore.WHITE}Profile Picture URL: {Fore.CYAN}{profile.profile_pic_url}")
        investigation_data["profile_pic_url"] = profile.profile_pic_url
        
        # Fetch Posts
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
        
        # Post Analysis
        if not profile.is_private and posts and len(posts) > 0:
            # Content Type Analysis
            content_types = analyze_content_types(posts)
            if content_types:
                print(f"\n{Fore.CYAN}{Style.BRIGHT}📈 CONTENT TYPE DISTRIBUTION:{Style.RESET_ALL}")
                print(f"{Fore.WHITE}{'─' * 60}")
                for ctype, count in content_types.items():
                    percentage = (count / len(posts[:50])) * 100
                    print(f"{Fore.WHITE}{ctype}: {Fore.CYAN}{count} {Fore.WHITE}({percentage:.1f}%)")
                investigation_data["content_types"] = content_types
            
            # Engagement Analysis
            engagement_data = calculate_engagement_rate(profile, posts)
            if engagement_data:
                print(f"\n{Fore.CYAN}{Style.BRIGHT}💬 ENGAGEMENT METRICS:{Style.RESET_ALL}")
                print(f"{Fore.WHITE}{'─' * 60}")
                print(f"{Fore.WHITE}Avg Likes per Post: {Fore.GREEN}{engagement_data['avg_likes']:.0f}")
                print(f"{Fore.WHITE}Avg Comments per Post: {Fore.YELLOW}{engagement_data['avg_comments']:.0f}")
                print(f"{Fore.WHITE}Engagement Rate: {Fore.CYAN}{engagement_data['engagement_rate']:.2f}%")
                
                if engagement_data['engagement_rate'] > 5:
                    print(f"{Fore.GREEN}  ✓ Excellent engagement rate")
                elif engagement_data['engagement_rate'] > 2:
                    print(f"{Fore.YELLOW}  • Good engagement rate")
                else:
                    print(f"{Fore.RED}  ⚠ Low engagement rate")
                
                investigation_data["engagement"] = engagement_data
            
            # Posting Pattern Analysis
            posting_patterns = analyze_posting_patterns(posts)
            if posting_patterns:
                print(f"\n{Fore.CYAN}{Style.BRIGHT}⏰ POSTING PATTERNS:{Style.RESET_ALL}")
                print(f"{Fore.WHITE}{'─' * 60}")
                if posting_patterns["most_active_hour"]:
                    hour, count = posting_patterns["most_active_hour"]
                    print(f"{Fore.WHITE}Most Active Hour: {Fore.YELLOW}{hour}:00 {Fore.WHITE}({count} posts)")
                if posting_patterns["most_active_day"]:
                    day, count = posting_patterns["most_active_day"]
                    print(f"{Fore.WHITE}Most Active Day: {Fore.YELLOW}{day} {Fore.WHITE}({count} posts)")
                
                print(f"\n{Fore.WHITE}Top Active Hours:")
                for hour, count in posting_patterns["hour_distribution"].items():
                    print(f"{Fore.WHITE}  {hour}:00 - {Fore.CYAN}{'█' * min(count, 20)} {count}")
                
                investigation_data["posting_patterns"] = posting_patterns
            
            # Location Analysis
            locations = extract_locations(posts)
            if locations:
                print(f"\n{Fore.CYAN}{Style.BRIGHT}📍 LOCATIONS ({len(locations)}):{Style.RESET_ALL}")
                print(f"{Fore.WHITE}{'─' * 60}")
                for loc in locations[:10]:
                    print(f"{Fore.WHITE}  • {Fore.YELLOW}{loc}")
                investigation_data["locations"] = locations
            
            # Recent Posts Analysis
            try:
                recent_posts = posts[:10]
                print(f"\n{Fore.CYAN}{Style.BRIGHT}📸 RECENT POSTS ANALYSIS ({len(recent_posts)} posts):{Style.RESET_ALL}")
                print(f"{Fore.WHITE}{'─' * 60}")
                
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
                
                # Top Hashtags
                if all_hashtags:
                    top_hashtags = Counter(all_hashtags).most_common(15)
                    print(f"\n{Fore.CYAN}{Style.BRIGHT}#️⃣ TOP HASHTAGS:{Style.RESET_ALL}")
                    print(f"{Fore.WHITE}{'─' * 60}")
                    for tag, count in top_hashtags:
                        bar = '█' * min(count * 3, 30)
                        print(f"{Fore.WHITE}  #{Fore.YELLOW}{tag:<20} {Fore.CYAN}{bar} {Fore.WHITE}({count}x)")
                    investigation_data["top_hashtags"] = dict(top_hashtags)
                
                # Frequently Tagged Accounts
                if all_mentions:
                    top_mentions = Counter(all_mentions).most_common(10)
                    print(f"\n{Fore.CYAN}{Style.BRIGHT}👤 FREQUENTLY TAGGED ACCOUNTS:{Style.RESET_ALL}")
                    print(f"{Fore.WHITE}{'─' * 60}")
                    for mention, count in top_mentions:
                        print(f"{Fore.WHITE}  @{Fore.YELLOW}{mention:<20} {Fore.WHITE}({Fore.CYAN}{count}x{Fore.WHITE})")
                    investigation_data["top_mentions"] = dict(top_mentions)
                
                # Activity Timeline
                if len(posts) > 0:
                    latest_post = posts[0].date_local
                    oldest_post = min(posts, key=lambda p: p.date_local)
                    days_since = (datetime.now() - latest_post.replace(tzinfo=None)).days
                    
                    print(f"\n{Fore.CYAN}{Style.BRIGHT}📊 ACTIVITY TIMELINE:{Style.RESET_ALL}")
                    print(f"{Fore.WHITE}{'─' * 60}")
                    print(f"{Fore.WHITE}Latest Post: {Fore.YELLOW}{latest_post.strftime('%Y-%m-%d')} {Fore.WHITE}({Fore.CYAN}{days_since} days ago{Fore.WHITE})")
                    print(f"{Fore.WHITE}Oldest Fetched: {Fore.YELLOW}{oldest_post.date_local.strftime('%Y-%m-%d')}")
                    
                    if profile.mediacount > 0 and len(posts) > 1:
                        total_days = (latest_post.replace(tzinfo=None) - oldest_post.date_local.replace(tzinfo=None)).days
                        if total_days > 0:
                            avg_posts_month = profile.mediacount / (total_days / 30)
                            avg_posts_week = profile.mediacount / (total_days / 7)
                            print(f"{Fore.WHITE}Avg Posts: {Fore.CYAN}{avg_posts_month:.1f} per month {Fore.WHITE}/ {Fore.CYAN}{avg_posts_week:.1f} per week")
                    
                    if days_since == 0:
                        print(f"{Fore.GREEN}  ✓ Very active (posted today)")
                    elif days_since <= 7:
                        print(f"{Fore.GREEN}  ✓ Active account")
                    elif days_since <= 30:
                        print(f"{Fore.YELLOW}  • Moderately active")
                    else:
                        print(f"{Fore.RED}  ⚠ Inactive account")
            
            except Exception as e:
                print(f"{Fore.RED}[!] Error analyzing posts: {str(e)}")
        
        elif profile.is_private:
            print(f"\n{Fore.YELLOW}[i] Account is private - post analysis unavailable{Style.RESET_ALL}")
        
        print(f"\n{Fore.WHITE}{'=' * 60}")
        print(f"{Fore.GREEN}{Style.BRIGHT}[✓] INVESTIGATION COMPLETE{Style.RESET_ALL}")
        print(f"{Fore.WHITE}{'=' * 60}")
        
        # Export to JSON
        if export_json:
            print(f"\n{Fore.WHITE}[{Fore.CYAN}+{Fore.WHITE}] Exporting data to JSON...")
            filename = export_to_json(investigation_data, username)
            if filename:
                print(f"{Fore.GREEN}[✓] Data exported to: {Fore.CYAN}{filename}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}[!] Failed to export data{Style.RESET_ALL}")
        
    except ImportError as e:
        print(f"\r{Fore.RED}[!] Failed to install instaloader: {str(e)}{Style.RESET_ALL}")
    except Exception as e:
        error_msg = str(e)
        print(f"\r{Fore.YELLOW}{Style.BRIGHT}{'=' * 60}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}INVESTIGATION RESULTS")
        print(f"{Fore.YELLOW}{Style.BRIGHT}{'=' * 60}{Style.RESET_ALL}")
        
        if "does not exist" in error_msg.lower() or "not exist" in error_msg.lower():
            print(f"{Fore.RED}{Style.BRIGHT}[✗] PROFILE NOT FOUND{Style.RESET_ALL}")
            print(f"{Fore.WHITE}{'-' * 60}")
            print(f"{Fore.YELLOW}[i] Username @{username} does not exist on Instagram")
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            print(f"{Fore.RED}[!] Connection error. Instagram may be blocking requests.")
            print(f"{Fore.YELLOW}[i] Try again later or check your internet connection")
        elif "login" in error_msg.lower() or "challenge" in error_msg.lower():
            print(f"{Fore.RED}[!] Instagram requires authentication")
            print(f"{Fore.YELLOW}[i] Some data may be restricted without login")
        else:
            print(f"{Fore.RED}[!] Error: {error_msg}")

def print_banner():
    """Print enhanced ASCII banner"""
    print("\n")
    print(f"{Fore.RED}{Style.BRIGHT}╔═══════════════════════════════════════════════════════════════╗")
    print(f"║  ██╗███╗   ██╗███████╗████████╗ █████╗                        ║")
    print(f"║  ██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗                       ║")
    print(f"║  ██║██╔██╗ ██║███████╗   ██║   ███████║                       ║")
    print(f"║  ██║██║╚██╗██║╚════██║   ██║   ██╔══██║                       ║")
    print(f"║  ██║██║ ╚████║███████║   ██║   ██║  ██║                       ║")
    print(f"║  ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝                       ║")
    print(f"║                                                               ║")
    print(f"║        ██████╗ ███████╗██╗███╗   ██╗████████╗                 ║")
    print(f"║       ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝                 ║")
    print(f"║       ██║   ██║███████╗██║██╔██╗ ██║   ██║                    ║")
    print(f"║       ██║   ██║╚════██║██║██║╚██╗██║   ██║                    ║")
    print(f"║       ╚██████╔╝███████║██║██║ ╚████║   ██║                    ║")
    print(f"║        ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝                    ║")
    print(f"║                                                               ║")
    print(f"║                   Instagram OSINT Tool v2.0                   ║")
    print(f"╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")

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
    print_banner()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        username = sys.argv[1]
        export_json = '--json' in sys.argv or '-j' in sys.argv
        
        if username and not username.startswith('-'):
            instagram_investigation(username, export_json=export_json)
        else:
            print(f"{Fore.RED}[!] Invalid username provided{Style.RESET_ALL}")
    else:
        # Interactive mode
        while True:
            username = input(f"{Fore.WHITE}Enter Instagram username (or 'quit' to exit): {Fore.GREEN}").strip()
            print(Style.RESET_ALL, end='')
            
            if username.lower() in ['quit', 'exit', 'q']:
                print(f"\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}\n")
                break
            
            if not username:
                print(f"{Fore.RED}[!] No username provided{Style.RESET_ALL}")
                continue
            
            # Ask for export option
            export_choice = input(f"{Fore.YELLOW}Export results to JSON? (y/n): {Style.RESET_ALL}").strip().lower()
            export_json = export_choice in ['y', 'yes', 'Y']
            
            instagram_investigation(username, export_json=export_json)
            
            # Ask if user wants to investigate another account
            continue_choice = input(f"\n{Fore.CYAN}Investigate another account? (y/n): {Style.RESET_ALL}").strip().lower()
            if continue_choice not in ['y', 'yes', 'Y']:
                print(f"\n{Fore.CYAN}Goodbye!{Style.RESET_ALL}\n")
                break
            print("\n" + "="*60 + "\n")
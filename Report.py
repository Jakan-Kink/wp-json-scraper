#!/usr/bin/env python3

"""
Report Generator for WP-JSON Scraper
Analyzes exported WordPress data and generates a human-readable summary report.

Adapted from gut0leao/wp-json-scraper
"""

import os
import json
import sys


def load_json(path):
    """Load JSON file if it exists, return None otherwise"""
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def tree_categories(categories, parent=0, prefix=""):
    """Build a hierarchical tree structure of categories"""
    tree = ""
    children = [cat for cat in categories if cat.get("parent", 0) == parent]
    for cat in children:
        tree += f"{prefix}📂 {cat.get('name', '')}\n"
        tree += tree_categories(categories, cat.get("id", 0), prefix + "    ")
    return tree


def posts_per_category(posts, categories):
    """Group posts by category"""
    cat_map = {cat['id']: cat['name'] for cat in categories}
    result = {}
    for post in posts:
        for cat_id in post.get('categories', []):
            cat_name = cat_map.get(cat_id, f"ID:{cat_id}")
            result.setdefault(cat_name, []).append(
                post.get('title', {}).get('rendered', '')
            )
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python Report.py <export_dir>")
        print("\nGenerates a human-readable report from exported WordPress data.")
        print("\nExpected JSON files in export_dir:")
        print("  - info.json (optional)")
        print("  - categories.json (optional)")
        print("  - tags.json (optional)")
        print("  - posts/posts.json (optional)")
        print("  - pages/pages.json (optional)")
        print("  - media.json (optional)")
        print("  - users.json (optional)")
        sys.exit(1)

    export_dir = sys.argv[1]

    if not os.path.isdir(export_dir):
        print(f"Error: '{export_dir}' is not a valid directory")
        sys.exit(1)

    # Load data files
    info = load_json(os.path.join(export_dir, "info.json"))
    # Handle case where info is a list
    if isinstance(info, list) and len(info) > 0:
        info = info[0]

    categories = load_json(os.path.join(export_dir, "categories.json")) or []
    tags = load_json(os.path.join(export_dir, "tags.json")) or []

    # Try both locations for posts/pages (in subdirs or at root)
    posts = load_json(os.path.join(export_dir, "posts", "posts.json")) or \
            load_json(os.path.join(export_dir, "posts.json")) or []
    pages = load_json(os.path.join(export_dir, "pages", "pages.json")) or \
            load_json(os.path.join(export_dir, "pages.json")) or []

    media = load_json(os.path.join(export_dir, "media.json")) or []
    users = load_json(os.path.join(export_dir, "users.json")) or []

    report_lines = []
    report_lines.append("=" * 50)
    report_lines.append("WORDPRESS DATA EXTRACTION REPORT")
    report_lines.append("=" * 50)
    report_lines.append("")

    # Target info
    if info:
        report_lines.append("TARGET INFORMATION")
        report_lines.append("-" * 50)
        url = info.get("url", "N/A")
        name = info.get("name", "N/A")
        description = info.get("description", "")
        report_lines.append(f"🌐 URL: {url}")
        report_lines.append(f"🏷️  Name: {name}")
        if description:
            report_lines.append(f"📝 Description: {description}")
        report_lines.append("")

    # Summary statistics
    report_lines.append("CONTENT SUMMARY")
    report_lines.append("-" * 50)
    report_lines.append(f"📂 Categories: {len(categories)}")
    report_lines.append(f"🏷️  Tags: {len(tags)}")
    report_lines.append(f"📝 Posts: {len(posts)}")
    report_lines.append(f"📄 Pages: {len(pages)}")
    report_lines.append(f"🖼️  Media: {len(media)}")
    report_lines.append(f"👤 Users: {len(users)}")
    report_lines.append("")

    # Posts per category
    if posts and categories:
        ppc = posts_per_category(posts, categories)
        report_lines.append("POSTS PER CATEGORY")
        report_lines.append("-" * 50)
        for cat, plist in sorted(ppc.items(), key=lambda x: len(x[1]), reverse=True):
            report_lines.append(f"  {cat}: {len(plist)} post(s)")
        report_lines.append("")

    # Category hierarchy
    if categories:
        report_lines.append("CATEGORY HIERARCHY")
        report_lines.append("-" * 50)
        tree = tree_categories(categories)
        if tree:
            report_lines.append(tree)
        else:
            report_lines.append("  (No categories or flat structure)")
        report_lines.append("")

    # Tags
    if tags:
        report_lines.append("TAGS")
        report_lines.append("-" * 50)
        tag_names = [f"🏷️  {tag.get('name', '')}" for tag in tags]
        # Wrap tags nicely
        report_lines.append("  " + ", ".join(tag_names))
        report_lines.append("")

    # Posts by category
    if posts and categories:
        report_lines.append("POSTS BY CATEGORY")
        report_lines.append("-" * 50)
        ppc = posts_per_category(posts, categories)
        for cat, plist in sorted(ppc.items()):
            report_lines.append(f"  📂 {cat}:")
            for post_title in plist:
                report_lines.append(f"    - 📝 {post_title}")
        report_lines.append("")

    # Pages
    if pages:
        report_lines.append("PAGES")
        report_lines.append("-" * 50)
        for page in pages:
            title = page.get('title', {}).get('rendered', page.get('title', 'Untitled'))
            report_lines.append(f"  📄 {title}")
        report_lines.append("")

    # Media
    if media:
        report_lines.append("MEDIA FILES")
        report_lines.append("-" * 50)
        for m in media:
            url = m.get('source_url', m.get('guid', {}).get('rendered', ''))
            name = m.get('title', {}).get('rendered', m.get('title', 'Unnamed'))
            mime_type = m.get('mime_type', '')
            report_lines.append(f"  🖼️  {name}")
            if mime_type:
                report_lines.append(f"     Type: {mime_type}")
            report_lines.append(f"     URL: {url}")
        report_lines.append("")

    # Users with post counts
    if users:
        report_lines.append("USERS")
        report_lines.append("-" * 50)

        # Calculate post counts per user
        user_post_count = {}
        for post in posts:
            author_id = post.get('author')
            user_post_count[author_id] = user_post_count.get(author_id, 0) + 1

        # Create user list with counts
        users_with_count = []
        for user in users:
            user_id = user.get('id')
            name = user.get('name', user.get('username', 'Unknown'))
            post_count = user_post_count.get(user_id, 0)
            users_with_count.append((name, post_count))

        # Sort by post count (descending)
        users_with_count.sort(key=lambda x: x[1], reverse=True)

        for name, post_count in users_with_count:
            report_lines.append(f"  👤 {name} [{post_count} post(s)]")
        report_lines.append("")

    # Footer
    report_lines.append("=" * 50)
    report_lines.append("End of Report")
    report_lines.append("=" * 50)

    # Write report
    report_path = os.path.join(export_dir, "report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"✅ Report generated successfully: {report_path}")
    print(f"\n📊 Summary:")
    print(f"   - {len(posts)} posts")
    print(f"   - {len(pages)} pages")
    print(f"   - {len(categories)} categories")
    print(f"   - {len(tags)} tags")
    print(f"   - {len(media)} media files")
    print(f"   - {len(users)} users")


if __name__ == "__main__":
    main()
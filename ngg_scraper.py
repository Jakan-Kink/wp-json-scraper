import argparse
import json
import os
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def scrape_ngg_images(posts_file, output_folder, delay=0.5):
    with open(posts_file) as f:
        posts = json.load(f)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print(f"Found {len(posts)} posts. Scanning for NextGEN Gallery images...")

    session = requests.Session()
    # mimic browser to avoid blocking
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        }
    )

    total_downloaded = 0

    for i, post in enumerate(posts):
        link = post.get("link")
        title = post.get("title", {}).get("rendered", "untitled")
        slug = post.get("slug", str(post.get("id")))

        if not link:
            continue

        print(f"[{i + 1}/{len(posts)}] Scanning: {title}")

        try:
            r = session.get(link, timeout=10)
            if r.status_code != 200:
                print(f"  Failed to fetch {link} (Status {r.status_code})")
                continue

            soup = BeautifulSoup(r.content, "html.parser")

            # Find images. Strategies:
            # 1. Look for 'ngg-' class
            # 2. Look for images in /wp-content/gallery/ path

            images_to_download = set()

            # Strategy 1: Common NGG containers
            # <div class="ngg-gallery-thumbnail"> <a href="..."> <img ...> </a> </div>
            for thumb in soup.select(".ngg-gallery-thumbnail a, .ngg-fancybox"):
                href = thumb.get("href")
                if href and is_image_url(href):
                    images_to_download.add(href)

            # Strategy 2: URL pattern matching in all links/images
            for tag in soup.find_all(["a", "img"]):
                url = tag.get("href") or tag.get("src")
                if url and "/wp-content/gallery/" in url:
                    # Clean up URL (remove query params for storage, but maybe keep for fetch? usually static)
                    # Often thumbnails have /thumbs/ in path, we want the full size.
                    # e.g. /wp-content/gallery/album-name/thumbs/thumbs_DSC.jpg
                    # full: /wp-content/gallery/album-name/DSC.jpg

                    if "/thumbs/" in url:
                        # Try to guess full size URL
                        full_url = url.replace("/thumbs/thumbs_", "/").replace(
                            "/thumbs/", "/"
                        )
                        images_to_download.add(full_url)
                    else:
                        images_to_download.add(url)

            if not images_to_download:
                # Fallback: check raw content for shortcode if we missed anything?
                # No, we are scraping rendered HTML.
                pass

            if images_to_download:
                print(f"  Found {len(images_to_download)} potential NGG images.")
                post_media_dir = os.path.join(output_folder, slug)
                if not os.path.exists(post_media_dir):
                    os.makedirs(post_media_dir)

                for img_url in images_to_download:
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url
                    elif img_url.startswith("/"):
                        img_url = urljoin(link, img_url)

                    filename = os.path.basename(urlparse(img_url).path)
                    filepath = os.path.join(post_media_dir, filename)

                    if os.path.exists(filepath):
                        # print(f"    Skipping existing: {filename}")
                        continue

                    try:
                        # print(f"    Downloading: {filename}")
                        img_r = session.get(img_url, stream=True, timeout=10)
                        if img_r.status_code == 200:
                            with open(filepath, "wb") as f:
                                for chunk in img_r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            total_downloaded += 1
                    except Exception as e:
                        print(f"    Error downloading {img_url}: {e}")

            time.sleep(delay)

        except Exception as e:
            print(f"  Error processing post: {e}")

    print(f"Done. Downloaded {total_downloaded} new images.")


def is_image_url(url):
    return re.search(r"\.(jpg|jpeg|png|gif|webp)$", url, re.IGNORECASE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape NextGEN Gallery images from posts"
    )
    parser.add_argument("posts_json", help="Path to posts.json file")
    parser.add_argument("output_folder", help="Folder to save images")
    parser.add_argument(
        "--delay", type=float, default=0.5, help="Delay between requests"
    )

    args = parser.parse_args()
    scrape_ngg_images(args.posts_json, args.output_folder, args.delay)

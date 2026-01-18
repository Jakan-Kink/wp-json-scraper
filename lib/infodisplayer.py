"""
Copyright (c) 2018-2020 Mickaël "Kilawyn" Walter

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import csv
import html
from datetime import datetime
from pathlib import Path

from lib.console import Console


class InfoDisplayer:
    """
    Static class to display information for different categories
    """

    @staticmethod
    def display_basic_info(information):
        """
        Displays basic information about the WordPress instance
        param information: information as a JSON object
        """
        print()

        if "name" in information:
            print("Site name: {}".format(html.unescape(information["name"])))

        if "description" in information:
            print(
                "Site description: {}".format(html.unescape(information["description"]))
            )

        if "home" in information:
            print("Site home: {}".format(html.unescape(information["home"])))

        if "gmt_offset" in information:
            timezone_string = ""
            gmt_offset = str(information["gmt_offset"])
            if "-" not in gmt_offset:
                gmt_offset = "+" + gmt_offset
            if "timezone_string" in information:
                timezone_string = information["timezone_string"]
            print(f"Site Timezone: {timezone_string} (GMT{gmt_offset})")

        if "namespaces" in information:
            print("Namespaces (API provided by addons):")
            ns_ref = {}
            try:
                with Path("lib/plugins/plugin_list.csv").open() as ns_ref_file:
                    ns_ref_reader = csv.reader(ns_ref_file)
                    for row in ns_ref_reader:
                        desc = None
                        url = None
                        if len(row) > 1 and len(row[1]) > 0:
                            desc = row[1]
                        if len(row) > 2 and len(row[2]) > 0:
                            url = row[2]
                        ns_ref[row[0]] = {"desc": desc, "url": url}
            except:
                Console.log_error("Could not load namespaces reference file")
            for ns in information["namespaces"]:
                tip = ""
                if ns in ns_ref:
                    if ns_ref[ns]["desc"] is not None:
                        if tip == "":
                            tip += " - "
                        tip += ns_ref[ns]["desc"]
                    if ns_ref[ns]["url"] is not None:
                        if tip == "":
                            tip += " - "
                        tip += " - " + ns_ref[ns]["url"]
                print(f"    {ns}{tip}")

        # TODO, dive into authentication
        print()

    @staticmethod
    def display_namespaces(information, _details=False):
        """
        Displays namespace list of the WordPress API

        :param information: information as a JSON object
        :param _details: unused, available for compatibility purposes
        """
        print()
        if information is not None:
            for ns in information:
                print(f"* {ns}")
        print()

    @staticmethod
    def display_endpoints(information):
        """
        Displays endpoint documentation of the WordPress API
        param information: information as a JSON object
        """
        print()

        if "routes" not in information:
            Console.log_error("Did not find the routes for endpoint discovery")
            return

        for url, route in information["routes"].items():
            print("{} (Namespace: {})".format(url, route["namespace"]))
            for endpoint in route["endpoints"]:
                methods = "    "
                first = True
                for method in endpoint["methods"]:
                    if first:
                        methods += method
                        first = False
                    else:
                        methods += ", " + method
                print(methods)
                if len(endpoint["args"]) > 0:
                    for arg, props in endpoint["args"].items():
                        required = ""
                        if props["required"]:
                            required = " (required)"
                        print("        " + arg + required)
                        if "type" in props:
                            print("            type: " + str(props["type"]))
                        if "default" in props:
                            print("            default: " + str(props["default"]))
                        if "enum" in props:
                            allowed = "            allowed values: "
                            first = True
                            for val in props["enum"]:
                                if first:
                                    allowed += str(val)
                                    first = False
                                else:
                                    allowed += ", " + str(val)
                            print(allowed)
                        if "description" in props:
                            print("            " + str(props["description"]))
            print()

    @staticmethod
    def display_posts(information, orphan_comments=None, details=False):
        """
        Displays posts published on the WordPress instance
        param information: information as a JSON object
        """
        if orphan_comments is None:
            orphan_comments = []
        print()
        date_format = "%Y-%m-%dT%H:%M:%S-%Z"
        for post in information:
            if post is not None:
                line = ""
                if "id" in post:
                    line += f"ID: {post['id']}"
                if "title" in post:
                    line += " - " + html.unescape(post["title"]["rendered"])
                if "date_gmt" in post:
                    date_gmt = datetime.strptime(post["date_gmt"] + "-GMT", date_format)
                    line += " on {}".format(date_gmt.strftime("%d/%m/%Y at %H:%M:%S"))
                if "link" in post:
                    line += " - " + post["link"]
                if details:
                    if "slug" in post:
                        line += "\nSlug: " + post["slug"]
                    if "status" in post:
                        line += "\nStatus: " + post["status"]
                    if "author" in post:
                        line += f"\nAuthor ID: {post['author']}"
                    if "comment_status" in post:
                        line += "\nComment status: " + post["comment_status"]
                    if "template" in post and len(post["template"]) > 0:
                        line += "\nTemplate: " + post["template"]
                    if "categories" in post and len(post["categories"]) > 0:
                        line += "\nCategory IDs: "
                        for cat in post["categories"]:
                            line += f"{cat}, "
                        line = line[:-2]
                    if "excerpt" in post:
                        line += "\nExcerpt: "
                        if (
                            "protected" in post["excerpt"]
                            and post["excerpt"]["protected"]
                        ):
                            line += "<post is protected>"
                        elif "rendered" in post["excerpt"]:
                            line += "\n" + html.unescape(post["excerpt"]["rendered"])
                    if "content" in post:
                        line += "\nContent: "
                        if (
                            "protected" in post["content"]
                            and post["content"]["protected"]
                        ):
                            line += "<post is protected>"
                        elif "rendered" in post["content"]:
                            line += "\n" + html.unescape(post["content"]["rendered"])
                if "comments" in post:
                    for comment in post["comments"]:
                        line += "\n\t * Comment by {} from ({}) - {}".format(
                            comment["author_name"],
                            comment["author_url"],
                            comment["link"],
                        )
                print(line)

        if len(orphan_comments) > 0:
            # TODO: Untested code, may never be executed, I don't know how the REST API and WordPress handle post/comment link in back-end
            print()
            print("Found orphan comments! Check them right below:")
            for comment in post["comments"]:
                line += f"\n\t * Comment by {comment['author_name']} from ({comment['author_url']}) on post ID {comment['post']} - {comment['link']}"
        print()

    @staticmethod
    def display_comments(information, details=False):
        """
        Displays comments published on the WordPress instance.

        :param information: information as a JSON object
        :param details: if the details should be displayed
        """
        print()
        date_format = "%Y-%m-%dT%H:%M:%S-%Z"
        for comment in information:
            if comment is not None:
                line = ""
                if "id" in comment:
                    line += f"ID: {comment['id']}"
                if "post" in comment:
                    line += f" - Post ID: {comment['post']}"  # html.unescape(post['title']['rendered'])
                if "author_name" in comment:
                    line += " - By {}".format(comment["author_name"])
                if "date" in comment:
                    date_gmt = datetime.strptime(
                        comment["date_gmt"] + "-GMT", date_format
                    )
                    line += " on {}".format(date_gmt.strftime("%d/%m/%Y at %H:%M:%S"))
                if details:
                    if "parent" in comment and comment["parent"] != 0:
                        line += "\nParent ID: " + comment["parent"]
                    if "link" in comment:
                        line += "\nLink: " + comment["link"]
                    if "status" in comment:
                        line += "\nStatus: " + comment["status"]
                    if "author_url" in comment and len(comment["author_url"]) > 0:
                        line += "\nAuthor URL: " + comment["author_url"]
                    if "content" in comment:
                        line += "\nContent: \n" + html.unescape(
                            comment["content"]["rendered"]
                        )
                print(line)
        print()

    @staticmethod
    def display_users(information, details=False):
        """
        Displays users on the WordPress instance

        :param information: information as a JSON object
        :param details: display more details about the user
        """
        print()
        for user in information:
            if user is not None:
                line = ""
                if "id" in user:
                    line += f"User ID: {user['id']}\n"
                if "name" in user:
                    line += "    Display name: {}\n".format(user["name"])
                if "slug" in user:
                    line += "    User name (probable): {}\n".format(user["slug"])
                if "description" in user:
                    line += "    User description: {}\n".format(user["description"])
                if "url" in user:
                    line += "    User website: {}\n".format(user["url"])
                if "link" in user:
                    line += "    User personal page: {}\n".format(user["link"])
                if (
                    details
                    and "avatar_urls" in user
                    and type(user["avatar_urls"]) is dict
                    and len(user["avatar_urls"].keys()) > 0
                ):
                    line += "    Avatars: \n"
                    for key, value in user["avatar_urls"].items():
                        line += f"        * {key}: {value}\n"
                print(line)
        print()

    @staticmethod
    def display_categories(information, details=False):
        """
        Displays categories of the WordPress instance
        param information: information as a JSON object
        """
        print()
        for category in information:
            if category is not None:
                line = ""
                if "id" in category:
                    line += f"Category ID: {category['id']}\n"
                if "name" in category:
                    line += "    Name: {}\n".format(category["name"])
                if "description" in category:
                    line += "    Description: {}\n".format(category["description"])
                if "count" in category:
                    line += f"    Number of posts: {category['count']}\n"
                if "link" in category:
                    line += "    Page: {}\n".format(category["link"])
                if details:
                    if "slug" in category:
                        line += "    Slug: {}\n".format(category["slug"])
                    if "taxonomy" in category:
                        line += "    Taxonomy: {}\n".format(category["slug"])
                    if "parent" in category:
                        line += "    Parent category: "
                        if type(category["parent"]) is str:
                            line += category["parent"]
                        elif type(category["parent"]) is int:
                            line += f"{category['parent']}"
                        else:
                            line += "Unknown"
                        line += "\n"
                print(line)
        print()

    @staticmethod
    def display_tags(information, details=False):
        """
        Displays tags of the WordPress instance
        param information: information as a JSON object
        """
        print()
        for tag in information:
            if tag is not None:
                line = ""
                if "id" in tag:
                    line += f"Tag ID: {tag['id']}\n"
                if "name" in tag:
                    line += "    Name: {}\n".format(tag["name"])
                if "description" in tag:
                    line += "    Description: {}\n".format(tag["description"])
                if "count" in tag:
                    line += f"    Number of posts: {tag['count']}\n"
                if "link" in tag:
                    line += "    Page: {}\n".format(tag["link"])
                if details:
                    if "slug" in tag:
                        line += "    Slug: {}\n".format(tag["slug"])
                    if "taxonomy" in tag:
                        line += "    Taxonomy: {}\n".format(tag["slug"])
                print(line)
        print()

    @staticmethod
    def display_media(information, details=False):
        """
        Displays media objects of the WordPress instance

        :param information: information as a JSON object
        :param details: if the details should be displayed
        """
        print()
        date_format = "%Y-%m-%dT%H:%M:%S-%Z"
        for media in information:
            if media is not None:
                line = ""
                if "id" in media:
                    line += f"Media ID: {media['id']}\n"
                if "title" in media and "rendered" in media["title"]:
                    line += "    Media title: {}\n".format(
                        html.unescape(media["title"]["rendered"])
                    )
                if "date_gmt" in media:
                    date_gmt = datetime.strptime(
                        media["date_gmt"] + "-GMT", date_format
                    )
                    line += "    Upload date (GMT): {}\n".format(
                        date_gmt.strftime("%d/%m/%Y %H:%M:%S")
                    )
                if "media_type" in media:
                    line += "    Media type: {}\n".format(media["media_type"])
                if "mime_type" in media:
                    line += "    Mime type: {}\n".format(media["mime_type"])
                if "link" in media:
                    line += "    Page: {}\n".format(media["link"])
                if "source_url" in media:
                    line += "    Source URL: {}\n".format(media["source_url"])
                if details:
                    if "slug" in media:
                        line += "Slug: " + media["slug"] + "\n"
                    if "status" in media:
                        line += "Status: " + media["status"] + "\n"
                    if "type" in media:
                        line += "Type: " + media["type"] + "\n"
                    if "author" in media:
                        line += f"Author ID: {media['author']}\n"
                    if "alt_text" in media:
                        line += "Alt text: " + media["alt_text"] + "\n"
                    if "comment_status" in media:
                        line += "Comment status: " + media["comment_status"] + "\n"
                    if "post" in media:
                        line += f"Post or page ID: {media['post']}\n"
                    if "description" in media and media["description"]["rendered"]:
                        line += (
                            "Description: \n"
                            + html.unescape(media["description"]["rendered"])
                            + "\n"
                        )
                    if "caption" in media and media["caption"]["rendered"]:
                        line += (
                            "Caption: \n"
                            + html.unescape(media["caption"]["rendered"])
                            + "\n"
                        )
                print(line)
        print()

    @staticmethod
    def display_pages(information, details=False):
        """
        Displays pages published on the WordPress instance

        :param information: information as a JSON object
        :param details: if the details should be displayed
        """
        print()
        for page in information:
            if page is not None:
                line = ""
                if "id" in page:
                    line += f"ID: {page['id']}"
                if "title" in page and "rendered" in page["title"]:
                    line += " - " + html.unescape(page["title"]["rendered"])
                if "link" in page:
                    line += " - " + page["link"]
                if details:
                    if "slug" in page:
                        line += "\nSlug: " + page["slug"]
                    if "status" in page:
                        line += "\nStatus: " + page["status"]
                    if "author" in page:
                        line += f"\nAuthor ID: {page['author']}"
                    if "comment_status" in page:
                        line += "\nComment status: " + page["comment_status"]
                    if "template" in page and len(page["template"]) > 0:
                        line += "\nTemplate: " + page["template"]
                    if "parent" in page:
                        if page["parent"] == 0:
                            line += "\nParent: none"
                        else:
                            line += f"\nParent ID: {page['parent']}"
                    if "excerpt" in page:
                        line += "\nExcerpt: "
                        if (
                            "protected" in page["excerpt"]
                            and page["excerpt"]["protected"]
                        ):
                            line += "<page is protected>"
                        elif "rendered" in page["excerpt"]:
                            line += "\n" + html.unescape(page["excerpt"]["rendered"])
                    if "content" in page:
                        line += "\nContent: "
                        if (
                            "protected" in page["content"]
                            and page["content"]["protected"]
                        ):
                            line += "<page is protected>"
                        elif "rendered" in page["content"]:
                            line += "\n" + html.unescape(page["content"]["rendered"])
                print(line)
        print()

    @staticmethod
    def recurse_list_or_dict(data, tab):
        """
        Helper function to generate recursive display of API data
        """
        if type(data) is not dict and type(data) is not list:
            return tab + str(data)

        line = ""
        if type(data) is list:
            length = len(data)
            for i, value in enumerate(data):
                do_jmp = True
                if type(value) is dict or type(value) is list:
                    line += InfoDisplayer.recurse_list_or_dict(value, tab + "\t")
                elif type(value) is str:
                    if "\n" in value:
                        line += "\n" + tab + "\t"
                        line += value.replace("\n", "\n" + tab + "\t")
                    else:
                        line += " "
                        line += value.replace("\n", "\n" + tab)
                        do_jmp = False
                else:
                    line += " " + str(value)
                if i < length - 1 and do_jmp:
                    line += "\n"
        else:
            for key, value in data.items():
                line += "\n" + tab + key
                if type(value) is dict or type(value) is list:
                    line += InfoDisplayer.recurse_list_or_dict(value, tab + "\t")
                elif type(value) is str:
                    if "\n" in value:
                        line += "\n" + tab + "\t"
                        line += value.replace("\n", "\n" + tab + "\t")
                    else:
                        line += " "
                        line += value.replace("\n", "\n" + tab)
                else:
                    line += " " + str(value)
        return line

    @staticmethod
    def display_crawled_ns(information):
        """
        Displays endpoints details published on the WordPress instance
        param information: information as a JSON object
        """
        print()
        for url, data in information.items():
            line = "\n"
            line += url
            tab = "\t"
            line += InfoDisplayer.recurse_list_or_dict(data, tab)
            print(line)
        print()

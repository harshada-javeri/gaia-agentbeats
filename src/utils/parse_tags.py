"""Tag parsing utility for XML-style tags in messages."""

import re
from typing import Dict


def parse_tags(str_with_tags: str) -> Dict[str, str]:
    """Parse XML-style tags from a string.

    Args:
        str_with_tags: String containing tags in format <tag_name>content</tag_name>

    Returns:
        Dictionary mapping tag names to their content

    Example:
        >>> parse_tags("<url>http://example.com</url> <level>1</level>")
        {'url': 'http://example.com', 'level': '1'}
    """
    tags = re.findall(r"<(.*?)>(.*?)</\1>", str_with_tags, re.DOTALL)
    return {tag: content.strip() for tag, content in tags}


if __name__ == "__main__":
    test_str = "<tag1>Hello</tag1> some text <tag2>World</tag2>"
    print(parse_tags(test_str))

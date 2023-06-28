"""
Utils
"""

from bs4 import BeautifulSoup
from slugify import slugify
import re
import copy


FIRST_LEVEL = 'h3'


def strip_tags(value: str) -> str:
    return re.sub(r'<[^>]*?>', '', value)


def make_summary_in_soup(soup: BeautifulSoup, page_link: str = '') -> BeautifulSoup:
    summary_node = soup.find('summary')
    if summary_node is not None:
        new_summary_node = soup.new_tag('ul')
        new_summary_node['class'] = 'summary'
        slugs = {}

        for title_node in soup.find_all(FIRST_LEVEL):
            slug = slugify(strip_tags(title_node.text))
            if slug in slugs:
                node_id = '{}-{}'.format(slug, slugs[slug])
                slugs[slug] += 1
            else:
                node_id = slug
                slugs[slug] = 1

            title_node['id'] = node_id
            li_tag = soup.new_tag('li')
            a_tag = soup.new_tag('a')
            a_tag['href'] = '{}#{}'.format(page_link, node_id)
            a_tag.extend(copy.deepcopy(title_node.contents))
            li_tag.append(a_tag)
            new_summary_node.append(li_tag)

        summary_node.replace_with(new_summary_node)

    return soup


def make_summary(html: str, page_link: str = '') -> str:
    return str(make_summary_in_soup(BeautifulSoup(html, 'html.parser'), page_link))

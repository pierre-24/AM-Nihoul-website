"""
Utils
"""

from bs4 import BeautifulSoup


def make_summary_in_soup(soup: BeautifulSoup) -> BeautifulSoup:
    summary_node = soup.find('summary')
    if summary_node is not None:
        id_node = 1
        new_summary_node = soup.new_tag('ul')
        new_summary_node['class'] = 'summary'

        for title_node in soup.find_all('h1'):
            node_id = 'title-{}'.format(id_node)
            title_node['id'] = node_id
            li_tag = soup.new_tag('li')
            a_tag = soup.new_tag('a')
            a_tag['href'] = '#{}'.format(node_id)
            a_tag.contents = title_node.contents
            li_tag.append(a_tag)
            new_summary_node.append(li_tag)
            id_node += 1

        summary_node.replace_with(new_summary_node)

    return soup


def make_summary(html: str) -> str:
    return str(make_summary_in_soup(BeautifulSoup(html, 'lxml')))

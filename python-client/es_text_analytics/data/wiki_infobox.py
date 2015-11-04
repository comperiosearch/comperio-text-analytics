__author__ = 'cvig'
#!/usr/bin/env python
# parts of this borrowed from https://github.com/scraperwiki/wikipedia-infobox-tool/blob/master/get_data.py

import re


def clean_data(data):
    # Strip square brackets.
    data = re.sub('[\[\]]', '', data)
    # Strip all HTML tags.
    data = re.sub('<[^<]+?>', ' ', data)
    data = re.sub('(?i)\{\{cite .*\}\}', '', data)
    data = re.sub('&nbsp;', '', data)
    return data


def parse_tags(data):
    data = re.sub('(?i)\{\{url\|([^\n]*)\}\}', '\g<1>', data)
    data = re.sub('\[\[(.*)\|.*\]\]', '\g<1>', data)
    data = re.sub('(?i)\{\{convert\|(.*?)\|(.*?)((\}\})|(\|.*\}\}))', '\g<1> \g<2>', data)
    data = re.sub('(?i)\{\{convinfobox\|(.*?)\|(.*?)((\}\})|(\|.*\}\}))', '\g<1> \g<2>', data)
    data = re.sub('(?i)\{\{nowrap\|(.*)\}\}', '\g<1>', data)
    return data


def scrape_infobox(content):
    # Remove HTML comment tags.
    content = re.sub('<!--[\\S\\s]*?-->', ' ', content)

    box_occurences = re.split('{{infoboks[^\n}]*\n', content.lower())

    if len(box_occurences) < 2:
        return None

    data = {}

    for box_occurence in box_occurences[1:]:

        infobox_end = re.search('\n[^\n{]*\}\}[^\n{]*\n', box_occurence)

        if infobox_end is None:
            return None

        box_occurence = box_occurence[:infobox_end.start():]
        box_occurence = re.split('\n[^|\n]*\|', box_occurence)

        for item in box_occurence:
            item = parse_tags(item)
            item = clean_data(item)
            if '=' in item:
                pair = item.split('=', 1)
                field = pair[0].strip()
                field = re.sub('\W', '_', field)
                value = pair[1].strip()
                field = field.lower().strip()
                if len(field) < 20:
                    if value != '':
                        data[field] = value
        return data

    return data


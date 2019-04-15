import markdown
from markdown.inlinepatterns import Pattern
import re
import copy


def replace_params(match, attributes):
    new_attrs = copy.deepcopy(attributes)
    for (k, v) in new_attrs.items():
        new_attrs[k] = replace_params_in_string(match, v)
    return new_attrs


def replace_params_in_string(match, string):
    param = re.compile(r'[.*\$(\d+).*]+')
    result = copy.copy(string)
    for i in set(param.findall(string)):
        gr = int(i[1:])
        result = result.replace(i, match.group(gr))
    return result


class AttrTagPattern(Pattern):
    """
    Return element of type `tag` with a text attribute of group(3)
    of a Pattern and with the html attributes defined with the constructor.

    """

    def __init__(self, pattern, tag: str = "canvas", attrs={}, text=""):
        Pattern.__init__(self, pattern)
        self.tag = tag
        self.attrs = attrs
        self.text = text

    def handleMatch(self, m):
        el = markdown.util.etree.Element(self.tag)
        new_attrs = replace_params(m, self.attrs)
        el.text = self.text
        for (key, val) in new_attrs.items():
            el.set(key, val)
        return el

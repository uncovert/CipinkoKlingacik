"""Small dependency-free reader for the checked-in KiCad S-expression artifacts."""
import re


def loads(text):
    stack = [[]]
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()"]+', text):
        if token == "(":
            child = []
            stack[-1].append(child)
            stack.append(child)
        elif token == ")":
            if len(stack) == 1:
                raise ValueError("Unexpected closing parenthesis")
            stack.pop()
        else:
            if token.startswith('"'):
                token = re.sub(r'\\(["\\])', r'\1', token[1:-1])
            stack[-1].append(token)
    if len(stack) != 1 or len(stack[0]) != 1:
        raise ValueError("Incomplete or multiple S-expressions")
    return stack[0][0]


def children(node, name):
    return [item for item in node if isinstance(item, list) and item and item[0] == name]


def child(node, name):
    matches = children(node, name)
    if len(matches) != 1:
        raise ValueError(f"Expected one {name}, got {len(matches)}")
    return matches[0]

#!/usr/bin/python


def replace_title(doc: str):
    new_title = ":green:`py`\\ :gray:`throttle`"
    doc = doc.strip()
    doc = doc.split("\n", 2)[-1]
    return new_title + "\n" + "=" * len(new_title) + "\n" + doc


def include_styles(doc):
    return ".. include:: index_styles.rst\n\n" + doc


def include_toctree(doc):
    return doc + "\n\n.. include:: index_toctree.rst\n"


def add_links_to_doc(doc):
    doc = doc.replace("``Throttle.loop()``",
                      ":func:`Throttle.loop() <throttle.Throttle.loop>`")

    doc = doc.replace("``Throttle.aloop()``",
                      ":func:`Throttle.aloop() <throttle.Throttle.aloop>`")

    doc = doc.replace("``throttle.throttle()``",
                      ":func:`~throttle.throttle`")

    doc = doc.replace("``throttle.athrottle()``",
                      ":func:`~throttle.athrottle`")

    doc = doc.replace("``RateMeter``",
                      ":class:`~rate_meter.RateMeter`")

    return doc


def main():
    with open("../README.rst", 'r') as f:
        readme = f.read()

    readme = replace_title(readme)
    readme = include_styles(readme)
    readme = include_toctree(readme)
    readme = add_links_to_doc(readme)

    with open("index.rst", 'w') as f:
        f.write(readme)


if __name__ == '__main__':
    main()

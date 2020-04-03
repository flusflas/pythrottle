#!/usr/bin/python


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

    readme = add_links_to_doc(readme)

    with open("index.rst", 'w') as f:
        f.write(readme)


if __name__ == '__main__':
    main()

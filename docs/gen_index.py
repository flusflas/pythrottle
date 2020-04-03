#!/usr/bin/python


def add_links_to_doc(readme):
    readme = readme.replace("``Throttle.loop()``",
                            ":func:`Throttle.loop() <throttle.Throttle.loop>`")

    readme = readme.replace("``Throttle.aloop()``",
                            ":func:`Throttle.aloop() <throttle.Throttle.aloop>`")

    readme = readme.replace("``throttle.throttle()``",
                            ":func:`~throttle.throttle`")

    readme = readme.replace("``throttle.athrottle()``",
                            ":func:`~throttle.athrottle`")

    readme = readme.replace("``RateMeter``",
                            ":class:`~rate_meter.RateMeter`")

    return readme


def main():
    with open("../README.rst", 'r') as f:
        readme = f.read()

    readme = add_links_to_doc(readme)

    with open("index.rst", 'w') as f:
        f.write(readme)


if __name__ == '__main__':
    main()

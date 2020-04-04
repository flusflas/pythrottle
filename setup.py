import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

print(setuptools.find_packages(exclude=("pythrottle.tests",)))

setuptools.setup(
    name="pythrottle",
    version="0.1.1",
    author="Flus Flas",
    author_email="aflusflas@gmail.com",
    description="Set of tools for throttling and controlling the execution "
                "timing of Python code.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/flusflas/pythrottle",
    packages=setuptools.find_packages(exclude=("pythrottle.tests",)),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries',
    ],
    keywords=[
        'throttle', 'throttling', 'time', 'timing', 'rate'
    ],
    python_requires='>=3.6',
)

import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="py-throttling",
    version="0.1.2",
    author="Flus Flas",
    author_email="aflusflas@gmail.com",
    description="Some throttling utils",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/pypa/sampleproject",
    # packages=setuptools.find_packages(),
    py_modules=['throttle'],
    package_dir={'': 'pythrottle'},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

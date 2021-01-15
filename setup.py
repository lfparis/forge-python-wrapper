from setuptools import setup

setup(
    name="forge-python-wrapper",
    packages=[
        "forge",
        "forge.api",
        "forge.session",
        "forge.utils",
        "forge.extra",
    ],
    description="An synchronous and asynchronous Forge API Wrapper for the Autodesk Forge API",  # noqa: E501
    author="Luis Felipe Paris",
    author_email="lfparis@gmail.com",
    url="https://github.com/lfparis/forge-python-wrapper",
    version="0.0.1b3",
    install_requires=[
        "aiohttp",
        "requests",
        "selenium",
        "chromedriver_autoinstaller",
        "tqdm",
    ],
    python_requires="!=2.7.*, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, !=3.6.*",  # noqa: E501
    keywords=["forge", "autodesk", "api", "async", "async.io"],
    license="The MIT License (MIT)",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Software Development",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
)

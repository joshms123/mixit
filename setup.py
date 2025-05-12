from setuptools import setup, find_packages

setup(
    name="mixit",
    version="0.6.0",
    description="A simple mixin system with method exports",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.7",
    author="joshms123",
    author_email="dev@joshms.net",
    url="https://github.com/joshms123/mixit",
    keywords=["mixin", "composition", "python"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
        ],
    },
)

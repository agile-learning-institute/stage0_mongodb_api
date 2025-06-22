from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="stage0-mongodb-api",
    version="1.0.0",
    author="Agile Learning Institute",
    author_email="info@agilelearninginstitute.org",
    description="A MongoDB API for schema, version, and migration management",
    long_description="Build a utility container for used by projects that use Mongo DB",
    long_description_content_type="text/markdown",
    url="https://github.com/agile-learning-institute/stage0_mongodb_api",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.12",
    install_requires=[
        "python-dotenv",
        "flask",
        "prometheus-flask-exporter",
        "pymongo",
        "stage0-py-utils",
        "pyyaml>=6.0.1",
    ],
) 
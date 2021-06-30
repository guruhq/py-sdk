
import setuptools

if __name__ == "__main__":
  setuptools.setup(
    name="guru",
    version="1.0.0",
    url="https://github.com/guruhq/py-sdk",
    packages=["guru"],
    install_requires=[
        "beautifulsoup4",
        "markdown",
        "python-dateutil",
        "pytz",
        "PyYAML",
        "requests",
    ],
    python_requires=">=2.7"
  )

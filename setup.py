from distutils.core import setup

setup(
    name="wax.py",
    version="0.1.0",
    packages=[
        "wax",
    ],
    license="MIT",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=["aioeos"],
)

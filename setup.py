import setuptools

with open("README.md", "r") as file:
    long_description = file.read()

requires = [
    "gremlinpython"
]

packages = [
    "appsync_gremlin",
    "appsync_gremlin.filter",
    "appsync_gremlin.helpers",
    "appsync_gremlin.resolver"
]

setuptools.setup(
    name="appsync-gremlin",
    version="0.0.16",
    author="Alistair O'Brien",
    author_email="alistair@duneroot.co.uk",
    description="A simple Python interface for AppSync resolvers and Gremlin traversals.",
    long_description=long_description,
    include_package_data=True,
    long_description_content_type="text/markdown",
    url="",
    packages=packages,
    install_requires=requires,
)

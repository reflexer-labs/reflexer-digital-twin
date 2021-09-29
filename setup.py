import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="reflexer-digital-twin",
    version="1.0.0",
    author="Danilo Lessa Bernardineli",
    author_email="danilo@block.science",
    description="Toolkit based on cadCAD for performing automated routine tests and future predictions for a GEB deployment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/reflexer-labs/reflexer-digital-twin",
    project_urls={
        "Bug Tracker": "https://github.com/reflexer-labs/reflexer-digital-twin/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "rai_digital_twin"},
    packages=setuptools.find_packages(where="rai_digital_twin"),
    python_requires=">=3.9",
)
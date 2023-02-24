import setuptools

with open("readme.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="deploifai",
    author="Deploifai Limited",
    description="Deploifai CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/deploifai/cli",
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=[
        "click",
        "python-dotenv",
        "keyring",
        "requests",
        "click-spinner",
        "tqdm",
        "azure-identity",
        "azure-storage-blob",
        "boto3",
        "google-auth",
        "google-cloud-storage",
        "PyInquirer",
        # "InquirerPy", # todo: use this instead of PyInquirer
        "pyperclip",
        "semver",
        "cryptography",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "deploifai = deploifai.cli:cli",
        ],
    },
)

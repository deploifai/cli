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
    python_requires=">=3.6, <3.10",
    install_requires=[
        "click",
        "python-dotenv",
        "keyring==23.0.1",
        "requests",
        "click-spinner",
        "tqdm",
        "azure-identity",
        "azure-storage-blob==12.9.0",
        "boto3",
        "google-auth",
        "google-cloud-storage",
        "PyInquirer",
        "pyperclip",
        "semver",
        "cryptography==36.0.1",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "deploifai = deploifai.cli:cli",
        ],
    },
)

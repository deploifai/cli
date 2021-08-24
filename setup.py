import setuptools

setuptools.setup(
    name="deploifai",
    version="0.0.1",
    author="Deploifai Limited",
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=["click", "keyring", "requests"],
    entry_points={
        "console_scripts": [
            "deploifai = deploifai.cli:cli",
        ],
    },
)

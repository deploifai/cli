import setuptools

setuptools.setup(
    name="deploifai",
    version="0.0.1",
    author="Deploifai Limited",
    packages=["deploifai"],
    python_requires=">=3.6",
    install_requires=[
        "Click",
    ],
    entry_points={
        "console_scripts": [
            "deploifai = deploifai.cli:cli",
        ],
    },
)

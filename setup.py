import setuptools

setuptools.setup(
  name="deploifai",
  version="0.0.1",
  author="Deploifai Limited",
  package_dir={"": "deploifai"},
  packages=setuptools.find_packages(where="deploifai"),
  python_requires=">=3.6",
)
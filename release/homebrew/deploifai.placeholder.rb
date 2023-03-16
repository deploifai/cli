class Deploifai < Formula
  include Language::Python::Virtualenv

  desc "Deploifai CLI"
  homepage "https://deploif.ai"
  url "https://github.com/deploifai/cli.git", tag: "NEW_TAG"
  head "https://github.com/deploifai/cli.git"
  version "NEW_TAG"

  depends_on "python@3.9"
  depends_on "rust" => :build # for cryptography

  ## RESOURCES ##

  def install
    with_env(SETUPTOOLS_USE_DISTUTILS: "stdlib") do
      virtualenv_create(libexec, "python3")
      virtualenv_install_with_resources
    end
  end
end

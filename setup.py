from setuptools import setup, find_packages

setup(
    name="solana-wallet-tracker",
    version="0.1.0",
    description="CLI tool for tracking Solana wallet balances and transactions",
    author="bhupendra05",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "click>=8.1",
        "rich>=13.0",
        "requests>=2.31",
    ],
    entry_points={
        "console_scripts": [
            "sol-track=solana_tracker.cli:main",
        ]
    },
)

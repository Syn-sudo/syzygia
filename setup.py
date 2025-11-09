from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="syzygia",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A custom package manager for Arch Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/syzygia",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Software Distribution",
    ],
    python_requires=">=3.8",
    install_requires=[
        'requests>=2.31.0',
        'tqdm>=4.66.1',
        'pyyaml>=6.0.1',
        'colorama>=0.4.6',
        'python-gnupg>=0.5.1',
    ],
    entry_points={
        'console_scripts': [
            'syzygia=syzygia.cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        'syzygia': ['data/*'],
    },
)

from setuptools import setup, find_packages

setup(
    name="plm_delux",
    version="0.1.0",
    description="A PLM-style environment for software requirements and architecture",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    package_dir={"": "src"},
    install_requires=[
        "pyyaml>=6.0.1",
        "graphviz>=0.20.1",
        "mkdocs>=1.5.3",
        "pytest>=7.4.3",
        "python-frontmatter>=1.0.0",
        "openai>=1.3.0",
        "click>=8.1.7",
        "aiohttp>=3.9.0",
        "asyncio>=3.4.3",
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "pydantic>=2.5.2",
    ],
    python_requires=">=3.12",
) 
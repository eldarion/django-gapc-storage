from setuptools import setup, find_packages


setup(
    name="django-gapc-storage",
    version="0.3.0",
    author="Eldarion, Inc.",
    author_email="development@eldarion.com",
    description="a Django storage backend using GCS JSON API",
    long_description=open("README.rst").read(),
    license="BSD",
    url="http://github.com/eldarion/django-gapc-storage",
    packages=find_packages(),
    install_requires=[
        "google-api-python-client>=1.5.0",
        "python-dateutil",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Framework :: Django",
    ]
)

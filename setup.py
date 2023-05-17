from setuptools import setup, find_packages

requires = [
    'flask',
    'spotipy',
]

setup(
    name='Spotify test',
    version='1.0',
    description='idk yet',
    author='Ibrahim Khan ',
    author_email='iboo11khan@gmail.com',
    keywords='web flask',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires
)
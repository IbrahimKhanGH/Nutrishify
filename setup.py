from setuptools import setup, find_packages

requires = [
    'flask',
    'spotipy',
]

setup(
    name='Spotify Nutrition',
    version='1.0',
    description='Nutrition Label based on Spotify User Data',
    author='Ibrahim Khan ',
    author_email='iboo11khan@gmail.com',
    keywords='web flask',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires
)
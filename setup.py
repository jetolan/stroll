from setuptools import setup

with open("README.md", 'r') as f:
        long_description = f.read()

        setup(name='stroll',
                    version='0.0.1',
                    description=u"Calculates neighborhood safety",
                    long_description=long_description,
                    classifiers=[],
                    keywords='',
                    author=u"Jamie Tolan",
                    author_email='jamie.tolan@gmail.com',
                    url='https://github.com/jetolan/stroll',
                    license='MIT',
                    install_requires=['numpy', 'pandas', 'geopy']
                    )

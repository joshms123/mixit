from setuptools import setup, find_packages

setup(
	name="mixit",
	version="0.2.0",
	description="A simple mixin system with method exports",
	packages=find_packages(),
	python_requires=">=3.7",
	extras_require={
		'dev': [
			'pytest>=6.0',
		],
	},
)

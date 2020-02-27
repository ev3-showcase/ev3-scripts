from setuptools import setup

setup(name='ev3car',
      version='0.1',
      description='Moving the car built on the ev3 set',
      url='https://github.com/ev3-showcase/ev3-scripts',
      author='Michael Rose',
      author_email='michael.rose@t-systems.com',
      license='MIT',
      packages=['ev3car'],
      install_requires=[
          'paho-mqtt',
          'python-ev3dev2',
          'picamera',
      ],
      zip_safe=False)

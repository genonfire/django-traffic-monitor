from setuptools import setup


def read(f):
    return open(f, 'r', encoding='utf-8').read()


setup(
    name='django-traffic-monitor',
    version=1.3,
    url='https://github.com/genonfire/django-traffic-monitor',
    license='MIT',
    description='a Django application that eases to monitor server traffic.',
    long_description=read('docs/README.rst'),
    author='KJ Kim',
    author_email='gencode.me@gmail.com',
    packages=['traffic_monitor'],
    include_package_data=True,
    install_requires=['django', 'django_crontab'],
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet :: WWW/HTTP',
    ],
)

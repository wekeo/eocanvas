Installation
============

Get your credentials
--------------------

1. If you don't have a WEkEO account, please self register through the WEkEO `registration form <https://www.wekeo.eu/>`_, then proceed to the step below.

2. Copy the code below in the file `$HOME/.hdarc` in your Unix/Linux environment. Adapt the following template with the credentials of your WEkEO account:

    .. code-block:: ini

        user: [username]
        password: [password]

    .. note::
       The credentials file is shared with the `HDA Python client <https://pypi.org/project/hda/>`_, which is optionally installed as explained below.

Install the WEkEO Serverless Functions client
---------------------------------------------
The WEkEO Serverless Functions client is a Python 3.8+ based library.

The package is available both on Pypi and Conda-Forge, so, depending on your requirements you can either install it via pip or via conda.

It is highly recommended to also install the `HDA Python client <https://pypi.org/project/hda/>`_:

    .. code-block:: shell

        pip install eocanvas[hda]

or

    .. code-block:: shell

        conda install conda-forge::eocanvas
        conda install conda-forge::hda

This will also install the required dependencies.
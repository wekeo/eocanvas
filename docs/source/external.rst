External Storage
================

EOCanvas allows users to use external storage locations such as an S3 bucket, EODATA, or the WEkEO Drive.

The Keystore provides a secure way to store your access keys, so that the processing functions can leverage them to access external resources.

The API supports the following storage locations:

* S3 private buckets
* S3 public buckets
* EODATA
* WEkEO Drive

The following table clarifies if a storage location can be used for inputs, outputs or both:

.. list-table::
   :widths: 50 25 25
   :header-rows: 1

   * - Storage location
     - Suitable for inputs
     - Suitable for outputs
   * - S3 private bucket
     - Yes
     - Yes
   * - S3 public bucket
     - Yes
     - No
   * - EODATA
     - Yes
     - No
   * - WEkEO Drive
     - No
     - Yes

Configuration examples
----------------------

With the exception of the EODATA key, which is already present by default, a user can register keys by creating an instance
of the :class:`eocanvas.api.Key` class in combination with either :class:`eocanvas.api.S3KeyConfig` or :class:`eocanvas.api.WebDavKeyConfig`.
All the information will be encrypted using an RSA public key provided by the Serverless API and only decrypted when needed by the functions.

.. note::
  Keys' configuration are encrypted before being sent to the server. To do that, the openssl command must be available on your system.
  On Linux, you can simply use your package manager:

      sudo apt-get install openssl

  On Windows, you can follow `this guide <https://thesecmaster.com/blog/procedure-to-install-openssl-on-the-windows-platform>`_, or, if
  you already have Git installed, the executable should be in C:\\Program Files\\Git\\usr\\bin\\openssl.exe


S3
**

You can register a private or public S3 key by using the :class:`eocanvas.api.S3KeyConfig` object

.. code-block:: python

    # Load all the necessary classes
    from eocanvas.api import Key, S3KeyConfig

    # Set all the required parameters to configure a specific key
    config = S3KeyConfig(
        access_key="*****",
        secret_key="*****",
        bucket="my-bucket",
        region="waw3-2",
        endpoint="https://s3.waw3-2.cloudferro.com",
    )

    # Note that the name must be unique. You might want to prefix your username.
    key = Key(name="<your-username>-s3-key", config=config)

    # Calling 'create' will download the public key from EOCanvas, encrypt the configuration and
    # send it to the API.
    key.create()


WebDav (WEkEO Drive)
********************

Similarly to S3, you need to pass the information in a config object, in this case of type :class:`eocanvas.api.WebDavKeyConfig`.

.. code-block:: python

    # Load all the necessary classes
    from eocanvas.api import Key, WebDavKeyConfig

    # Same thing as for the S3 case
    config = WebDavKeyConfig(
        endpoint="https://wekeo-files.prod.wekeo2.eu/remote.php/dav/files/wso2_oidc-<your-username>",
        username="wso2_oidc-<your-username>",
        password="*****-*****-*****-*****-*****",
    )
    key = Key(name="<your-username>-wekeo-key", config=config)
    key.create()


Usage
-----

Once a key has been added to the store, it can be used as an input source or an output destination, based on the table above, either by using it as an object or just by the name.

Here is an example using a WEkEO Drive key as input:

.. code-block:: python

    # As before, create all the required arguments to the process.
    graph = Graph.from_uri("olci_binding.xml")
    config = Config(key="img1", options=ConfigOption(uncompress=True, sub_path="xfdumanifest.xml"))

    # Here we set an extra parameter 'keystore' and adjust the url with the path of the file on our WEkEO storage
    inputs = Input(keystore="<your-username>-wekeo-key", key="img1", url="/testing-inputs/S3A_OL_2_WFR____20220626T095133_20220626T095433_20220627T215353_0179_087_022_1980_MAR_O_NT_003.SEN3.zip")

    # You can then submit and run the process as usual
    process = SnapProcess(snap_graph=graph, eo_config=config, eo_input=inputs)
    process.run()


Certain storages can be used as destination for the resulting data (refer to the table above).
Again, both the key name or the entire key object are valid values.

.. code-block:: python

    # To use a storage location as an external output, pass an 'output' parameter to the process
    process = SnapProcess(snap_graph=graph, eo_config=config, eo_input=inputs, output=Key(name="<your-username>-wekeo-key"))
    process.run()


In this case, when the process is completed, the final products will be available at the selected storage and the download is not performed.
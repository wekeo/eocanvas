OGC Compliance
==============

Starting from version 2.0, the **WEkEO Serverless Functions API** are OGC compliant.

EOCanvas exposes a few helper methods to interact with the endpoints that allows users to explore the capabilities of the API.

In particular:

.. code-block:: python

    from eocanvas import API

    api = API()

    api.landing_page()  # Provides clients with a starting point for using the API.
    api.get_api()  # Retrieves the API definition which describes the capabilities provided by that API.
    api.get_conformance()  # Provides a list declaring the modules that are implemented by the API.

With the exception of the landing page, the other endpoints return pure json objects.

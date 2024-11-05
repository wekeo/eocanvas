Quickstart
==========

EO Canvas allows you to submit functions to the WEkEO infrastructure and download the results locally.

Namely, you can request an `ESA SNAP toolbox <https://step.esa.int/main/toolboxes/snap/>`_ or
an `EUMETSAT Data Tailor <https://user.eumetsat.int/resources/user-guides/data-tailor-standalone-guide>`_
processing.

EO Canvas offers high-level objects to interact with the API, but you can also use the endpoints directly.
This is described more in depth in the  :doc:`usage </usage>` page.

Many of the following examples are also available in the `demo/notebook.ipynb` file.


    .. note::
        Further examples will be available at the `WEkEO4Data repository <https://github.com/wekeo/wekeo4data/tree/main/wekeo-eocanvas>`_.

SNAP
----
.. code:: python

    from eocanvas.api import Input, Config, ConfigOption
    from eocanvas.processes import SnapProcess
    from eocanvas.snap.graph import Graph

    # You can load the graph from a local file or build it programmatically
    graph = Graph.from_uri("olci_binding.xml")

    # The url is a valid WEkEO download URL. It can be retrieved using the HDA Python client
    inputs = Input(key="img1", url="http://gateway.prod.wekeo2.eu/hda-broker/api/v1/dataaccess/download/66b37374b6a632e1f39b3058")
    config = Config(key="img1", options=ConfigOption(uncompress=True, sub_path="xfdumanifest.xml"))

    process = SnapProcess(snap_graph=graph, eo_config=config, eo_input=inputs)

    # This will submit the process to the API, wait for its completion and download the results
    process.run()

Data Tailor
-----------
.. code:: python

    from eocanvas.api import Input, Config, ConfigOption
    from eocanvas.processes import DataTailorProcess
    from eocanvas.datatailor.chain import Chain

    # Load the Data Tailor chain from a local file
    chain = Chain.from_file("olci_resample.yaml")

    # The url is a valid WEkEO download URL. It can be retrieved using the HDA Python client
    inputs = Input(key="img1", url="http://gateway.impl.wekeo2.eu/hda-broker/api/v1/dataaccess/download/66c357dcb6a632e1f39b3131")

    # This will submit the process to the API, wait for its completion and download the results
    process = DataTailorProcess(epct_chain=chain, epct_input=inputs)

    # This will submit the process to the API, wait for its completion and download the results
    process.run()
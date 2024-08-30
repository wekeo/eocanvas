Usage
=====

As mentioned in the :doc:`quickstart </quickstart>` page, EO Canvas allows you to use both high-level objects or
to interact with the API in a more direct way.

The two fundamental concepts of the Serverless Functions service are *processes* and *jobs*.
A *process* describes either a SNAP or a DataTailor computation.
A *job*, on the other hand, is a submission of a process to the API, and it's used to keep track of
its state, to retrieve the application logs and, finally, to download the results.

To interact directly with the API, you can use the :class:`eocanvas.API` class:

.. code-block:: python

    from eocanvas import API

    # Without any argument, this will automatically load your credentials from the ~/.hdarc file
    api = API()

    processes = api.get_processes()
    print(processes)

    >> [Process(api=<eocanvas.api.API object at 0x7facd05a97e0>, process_id='snap-function', ...]

The available processes are predefined. New tools or custom functions might be added in future.

Process inputs must be configured before submitting them. **SNAP** and **DataTailor** has similar but different sets of inputs.

SNAP
----
**SNAP** processing is configured through an XML object called a `Graph`. Such graph contains nodes for the inputs.

Please refer to `official SNAP documentation <https://step.esa.int/main/doc/online-help/>`_ for further details.

Since SNAP is being executed remotely, those inputs are defined as placeholders and then passed in through :class:`eocanvas.api.Input` objects.

Extra configuration can be added using the :class:`eocanvas.api.Option` class.

**EO Canvas** handles graphs through an embedded version of `Snapista <https://snap-contrib.github.io/snapista/>`_.
*Snapista* requires a local SNAP instance to work, to which it can submit the graph.
The embedded version instead only allows to programmatically build or load the graph from an XML file. It also encodes it before it gets submitted to the API.

Generally speaking, having pre-cooked graphs is a better option. The `demo` directory contains some examples.

As already described in the :doc:`quickstart </quickstart>` page, a graph instance can be created by loading a local XML file:

.. code-block:: python

    from eocanvas.snap.graph import Graph

    graph = Graph.from_uri("olci_binding.xml")


Please note how the input node has been defined:

.. code-block:: xml

    <node id="Read">
      <operator>Read</operator>
      <sources/>
        <parameters class="com.bc.ceres.binding.dom.XppDomElement">
        <useAdvancedOptions>false</useAdvancedOptions>
        <file>$img1</file>
        <copyMetadata>true</copyMetadata>
        <bandNames>Oa01_reflectance,Oa01_reflectance_err,Oa02_reflectance,Oa02_reflectance_err,Oa03_reflectance,Oa03_reflectance_err,Oa04_reflectance,Oa04_reflectance_err,Oa05_reflectance,Oa05_reflectance_err,Oa06_reflectance,Oa06_reflectance_err,Oa07_reflectance,Oa07_reflectance_err,Oa08_reflectance,Oa08_reflectance_err,Oa09_reflectance,Oa09_reflectance_err,Oa10_reflectance,Oa10_reflectance_err,Oa11_reflectance,Oa11_reflectance_err,Oa12_reflectance,Oa12_reflectance_err,Oa16_reflectance,Oa16_reflectance_err,Oa17_reflectance,Oa17_reflectance_err,Oa18_reflectance,Oa18_reflectance_err,Oa21_reflectance,Oa21_reflectance_err,CHL_NN,CHL_NN_err,CHL_OC4ME,CHL_OC4ME_err,altitude,latitude,longitude,detector_index,FWHM_band_1,FWHM_band_2,FWHM_band_3,FWHM_band_4,FWHM_band_5,FWHM_band_6,FWHM_band_7,FWHM_band_8,FWHM_band_9,FWHM_band_10,FWHM_band_11,FWHM_band_12,FWHM_band_13,FWHM_band_14,FWHM_band_15,FWHM_band_16,FWHM_band_17,FWHM_band_18,FWHM_band_19,FWHM_band_20,FWHM_band_21,frame_offset,lambda0_band_1,lambda0_band_2,lambda0_band_3,lambda0_band_4,lambda0_band_5,lambda0_band_6,lambda0_band_7,lambda0_band_8,lambda0_band_9,lambda0_band_10,lambda0_band_11,lambda0_band_12,lambda0_band_13,lambda0_band_14,lambda0_band_15,lambda0_band_16,lambda0_band_17,lambda0_band_18,lambda0_band_19,lambda0_band_20,lambda0_band_21,solar_flux_band_1,solar_flux_band_2,solar_flux_band_3,solar_flux_band_4,solar_flux_band_5,solar_flux_band_6,solar_flux_band_7,solar_flux_band_8,solar_flux_band_9,solar_flux_band_10,solar_flux_band_11,solar_flux_band_12,solar_flux_band_13,solar_flux_band_14,solar_flux_band_15,solar_flux_band_16,solar_flux_band_17,solar_flux_band_18,solar_flux_band_19,solar_flux_band_20,solar_flux_band_21,ADG443_NN,ADG443_NN_err,IWV,IWV_err,PAR,PAR_err,KD490_M07,KD490_M07_err,TSM_NN,TSM_NN_err,A865,A865_err,T865,T865_err,WQSF_lsb,WQSF_msb</bandNames>
        <pixelRegion>0,0,4865,4091</pixelRegion>
        <maskNames>WQSF_lsb_INVALID,WQSF_lsb_WATER,WQSF_lsb_LAND,WQSF_lsb_CLOUD,WQSF_lsb_TURBID_ATM,WQSF_lsb_CLOUD_AMBIGUOUS,WQSF_lsb_CLOUD_MARGIN,WQSF_lsb_SNOW_ICE,WQSF_lsb_INLAND_WATER,WQSF_lsb_COASTLINE,WQSF_lsb_TIDAL,WQSF_lsb_COSMETIC,WQSF_lsb_SUSPECT,WQSF_lsb_HISOLZEN,WQSF_lsb_SATURATED,WQSF_lsb_MEGLINT,WQSF_lsb_HIGHGLINT,WQSF_lsb_WHITECAPS,WQSF_lsb_ADJAC,WQSF_lsb_WV_FAIL,WQSF_lsb_PAR_FAIL,WQSF_lsb_AC_FAIL,WQSF_lsb_OC4ME_FAIL,WQSF_lsb_OCNN_FAIL,WQSF_lsb_KDM_FAIL,WQSF_lsb_BPAC_ON,WQSF_lsb_WHITE_SCATT,WQSF_lsb_LOWRW,WQSF_lsb_HIGHRW,WQSF_msb_ANNOT_ANGSTROM,WQSF_msb_ANNOT_AERO_B,WQSF_msb_ANNOT_ABSO_D,WQSF_msb_ANNOT_ACLIM,WQSF_msb_ANNOT_ABSOA,WQSF_msb_ANNOT_MIXR1,WQSF_msb_ANNOT_DROUT,WQSF_msb_ANNOT_TAU06,WQSF_msb_RWNEG_O1,WQSF_msb_RWNEG_O2,WQSF_msb_RWNEG_O3,WQSF_msb_RWNEG_O4,WQSF_msb_RWNEG_O5,WQSF_msb_RWNEG_O6,WQSF_msb_RWNEG_O7,WQSF_msb_RWNEG_O8,WQSF_msb_RWNEG_O9,WQSF_msb_RWNEG_O10,WQSF_msb_RWNEG_O11,WQSF_msb_RWNEG_O12,WQSF_msb_RWNEG_O16,WQSF_msb_RWNEG_O17,WQSF_msb_RWNEG_O18,WQSF_msb_RWNEG_O21,WQSF_REFLECTANCE_RECOM,WQSF_CHL_OC4ME_RECOM,WQSF_KD490_M07_RECOM,WQSF_PAR_RECOM,WQSF_W_AER_RECOM,WQSF_CHL_NN_RECOM,WQSF_TSM_NN_RECOM,WQSF_ADG443_NN_RECOM,WQSF_IWV_RECOM</maskNames>
      </parameters>
    </node>

The *$img1* is an arbitrary placeholder and can be used to further configure the input:

.. code-block:: python

    from eocanvas.api import Input, Config, ConfigOption

    inputs = Input(key="img1", url="http://gateway.prod.wekeo2.eu/hda-broker/api/v1/dataaccess/download/66b37374b6a632e1f39b3058")
    config = Config(key="img1", options=ConfigOption(uncompress=True, sub_path="xfdumanifest.xml"))

Note that `img1` has been used as the key to configure the input. The dollar sign is only required in the graph.

The `url` parameter is a valid WEkEO HDA download link and can be retrieved by using the HDA Python client:

.. code-block:: python

    from hda import Client

    client = Client()

    query = {
        "dataset_id": "EO:EUM:DAT:SENTINEL-3:OL_2_WFR___",
        "dtstart": "2024-07-05T09:28:00.000Z",
        "dtend": "2024-07-05T09:30:00.000Z",
        "timeliness": "NT"
    }

    results = client.search(query)
    urls = results.get_download_urls()
    print(urls)

    >> ["http://gateway.prod.wekeo2.eu/hda-broker/api/v1/dataaccess/download/66b37374b6a632e1f39b3058", ...]

    inputs = Input(key="img1", url=urls[0])

The :class:`eocanvas.api.Config` object allows you to set two extra options:

#. whether the product must be decompressed before it is passed to SNAP
#. if uncompressed, what is the sub-path of the actual input file

Once all the inputs are ready, you can instantiate a process class:

.. code-block:: python

    from eocanvas.processes import SnapProcess

    process = SnapProcess(snap_graph=graph, eo_config=config, eo_input=inputs)

Processes can be submitted to the Serverless Functions API that will return a `Job` object,
used to check the status of the request. This can be done in two steps
(useful if you want a reference to the job) or in one go:

.. code-block:: python

    # Two steps
    job = process.submit()
    process.run(job)

    # Once you have the job, you can access the logs
    logs = job.logs

    # Otherwise you can directly call `run` and a job will be created under the hood
    process.run()

The `run` method will block until the job is completed and the results downloaded locally.

By default, results are downloaded in the current directory. A different one can be specified as well:

.. code-block:: python

    process.run(dowload_dir="mydir")



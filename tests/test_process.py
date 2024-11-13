from eocanvas.api import Config, ConfigOption, Input, Key, Process
from eocanvas.datatailor import Chain
from eocanvas.processes import DataTailorProcess


def test_prepare_inputs_with_no_outputs():
    process = Process()
    inputs = process.prepare_inputs()
    assert inputs == {
        "inputs": {},
        "outputs": {},
        "response": "raw",
        "subscriber": None,
    }


def test_prepare_inputs_with_str_outputs():
    process = Process(output="key")
    inputs = process.prepare_inputs()
    assert inputs == {
        "inputs": {},
        "outputs": {"output": {"format": {"schema": "keystore://key"}}},
        "response": "raw",
        "subscriber": None,
    }


def test_prepare_inputs_with_key_outputs():
    process = Process(output=Key(name="key"))
    inputs = process.prepare_inputs()
    assert inputs == {
        "inputs": {},
        "outputs": {"output": {"format": {"schema": "keystore://key"}}},
        "response": "raw",
        "subscriber": None,
    }


def test_input_asdict_with_no_keystore():
    input_ = Input(key="k", url="v")
    assert input_.asdict() == {"k": "v"}


def test_input_asdict_with_str_keystore():
    input_ = Input(key="k", url="v", keystore="key")
    assert input_.asdict() == {"k": "v", "schema": "keystore://key"}


def test_input_asdict_with_key_keystore():
    input_ = Input(key="k", url="v", keystore=Key(name="key"))
    assert input_.asdict() == {"k": "v", "schema": "keystore://key"}


def test_data_tailor_prepare_inputs_with_input_key():
    chain = Chain()
    input_ = Input(key="k", url="v", keystore=Key(name="input_key"))
    process = DataTailorProcess(epct_chain=chain, epct_input=input_)
    assert process.prepare_inputs() == {
        "inputs": {
            "epct_chain": "e30K",
            "epct_input": '[{"k": "v", "schema": "keystore://input_key"}]',
        },
        "outputs": {},
        "response": "raw",
        "subscriber": None,
    }


def test_data_tailor_prepare_inputs_with_input_key_and_output_key():
    chain = Chain()
    input_ = Input(key="k", url="v", keystore=Key(name="input_key"))
    process = DataTailorProcess(epct_chain=chain, epct_input=input_, output=Key(name="output_key"))
    assert process.prepare_inputs() == {
        "inputs": {
            "epct_chain": "e30K",
            "epct_input": '[{"k": "v", "schema": "keystore://input_key"}]',
        },
        "outputs": {"output": {"format": {"schema": "keystore://output_key"}}},
        "response": "raw",
        "subscriber": None,
    }


def test_data_tailor_prepare_inputs_with_input_key_and_config():
    chain = Chain()
    input_ = Input(key="k", url="v", keystore=Key(name="input_key"))
    config = Config(key="k", options=ConfigOption(sub_path="/"))
    process = DataTailorProcess(epct_chain=chain, epct_input=input_, epct_config=config)
    assert process.prepare_inputs() == {
        "inputs": {
            "epct_chain": "e30K",
            "epct_input": '[{"k": "v", "schema": "keystore://input_key"}]',
            "epct_config": '[{"k": {"subPath": "/"}}]',
        },
        "outputs": {},
        "response": "raw",
        "subscriber": None,
    }

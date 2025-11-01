from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import types

if "streamlit" not in sys.modules:
    st_stub = types.SimpleNamespace(
        radio=lambda *args, **kwargs: "Unsure",
        number_input=lambda *args, **kwargs: 0,
        text_input=lambda *args, **kwargs: "",
        text_area=lambda *args, **kwargs: "",
        selectbox=lambda *args, **kwargs: "",
        multiselect=lambda *args, **kwargs: [],
        markdown=lambda *args, **kwargs: None,
        checkbox=lambda *args, **kwargs: False,
        header=lambda *args, **kwargs: None,
        subheader=lambda *args, **kwargs: None,
        expander=lambda *args, **kwargs: types.SimpleNamespace(__enter__=lambda self: self, __exit__=lambda self, exc_type, exc_value, traceback: False),
        number_input_return=lambda *args, **kwargs: 0,
    )
    sys.modules["streamlit"] = st_stub

from bronch_schema import AirwayObstructionRelief, EnergyModality, Hemostasis  # noqa: E402
from tools.ui_helpers import tri_state_choice  # noqa: E402


def test_airway_obstruction_relief_model_validates_complete_entry():
    entry = AirwayObstructionRelief(
        site="trachea",
        segment_length_cm=2.5,
        pre_patency_percent=20,
        post_patency_percent=80,
        modalities=[
            EnergyModality(
                type="apc",
                power_w=40.0,
                argon_flow_l_min=1.2,
                mode="continuous",
                active_time_min=2.0,
                fio2_at_therapy=0.3,
            )
        ],
        hemostasis=Hemostasis(
            epi_ml_1_10000=2.0,
            txa_topical_mg=500.0,
            iced_saline_ml=50.0,
            agents=["surgicel"],
            hemostasis_achieved=True,
            time_to_hemostasis_min=3.5,
        ),
    )

    assert entry.pre_patency_percent == 20
    assert entry.modalities[0].fio2_at_therapy == 0.3
    assert entry.hemostasis.hemostasis_achieved is True


def test_tri_state_unsure_maps_to_not_documented():
    value, status, detail = tri_state_choice("Unsure")
    assert value is None
    assert status == "not_documented"
    assert detail == "unsure"

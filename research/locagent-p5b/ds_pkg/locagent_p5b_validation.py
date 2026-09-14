# LocAgent P5-B VALIDATION pilot dataset package (local, no HF upload).
# Loads the 6 VALIDATION real-commit cases built by our P5-A adapter.
import json
from pathlib import Path

import datasets

_DATASET_FILE = Path(__file__).parent.parent / "dataset" / "validation.json"


def _rows():
    return json.loads(_DATASET_FILE.read_text(encoding="utf-8"))


class ValidationConfig(datasets.BuilderConfig):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Validation(datasets.GeneratorBasedBuilder):
    VERSION = datasets.Version("1.0.0")

    def _info(self):
        return datasets.DatasetInfo(
            description="Real-commit P5-B VALIDATION pilot (LocAgent shared protocol)",
            features=datasets.Features(
                {
                    "instance_id": datasets.Value("string"),
                    "repo": datasets.Value("string"),
                    "base_commit": datasets.Value("string"),
                    "problem_statement": datasets.Value("string"),
                    "patch": datasets.Value("string"),
                    "source_case_id": datasets.Value("string"),
                }
            ),
        )

    def _split_generators(self, dl_manager):
        return [datasets.SplitGenerator(name=datasets.Split.TRAIN, gen_kwargs={"filepath": _DATASET_FILE})]

    def _generate_examples(self, filepath):
        for idx, row in enumerate(_rows()):
            yield idx, row
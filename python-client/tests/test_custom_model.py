import re
from pathlib import Path
from typing import Union

from giskard import Model, SKLearnModel
from giskard.core.core import SupportedModelTypes
from giskard.core.model import MODEL_CLASS_PKL, WrapperModel
from tests.utils import MockedClient


def test_custom_model(linear_regression_diabetes: Model):
    with MockedClient() as (client, mr):
        class MyModel(WrapperModel):
            @classmethod
            def load_clf(cls, local_dir):
                pass

            def clf_predict(self, df):
                pass

            def save(self, local_path: Union[str, Path]) -> None:
                super().save(local_path)

            should_save_model_class = True

        def has_model_class_been_sent():
            artifact_url_prefix = "http://giskard-host:12345/api/v2/artifacts/pk/models/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/"
            return (
                    len([i for i in mr.request_history if
                         re.match(artifact_url_prefix + MODEL_CLASS_PKL, i.url)]) > 0
            )

        SKLearnModel(linear_regression_diabetes.clf, model_type=SupportedModelTypes.REGRESSION).upload(client, "pk")
        assert not has_model_class_been_sent()

        MyModel(clf=linear_regression_diabetes.clf, model_type=SupportedModelTypes.REGRESSION).upload(client, "pk")
        assert has_model_class_been_sent()
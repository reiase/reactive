# Copyright 2021 Zilliz. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
from hyperparameter import param_scope

from ..types import dynamic_dispatch


class Collector:
    """
    Collector class for metric
    """

    # pylint: disable=dangerous-default-value
    def __init__(self, metrics: list = None, labels: dict = None, scores: dict = None):
        self.metrics = metrics if metrics is not None else []
        self.scores = scores if scores is not None else {}
        self.labels = labels if labels is not None else {}

    def add_scores(self, value: dict):
        self.scores.update(value)

    def add_labels(self, value: dict):
        self.labels.update(value)


def encode_fig_img(mat, size=300):
    # pylint: disable=import-outside-toplevel
    import base64
    import io

    import matplotlib as mpl
    from sklearn.metrics import ConfusionMatrixDisplay

    mpl.use("Agg")  # Prevent showing stuff
    cm = mat.astype("float") / mat.sum(axis=1)[:, np.newaxis]  # normalize
    fig = ConfusionMatrixDisplay(cm)
    fig.plot(cmap="GnBu")
    buf = io.BytesIO()
    fig.figure_.savefig(buf, format="jpg")
    buf.seek(0)
    buf = buf.read()
    src = 'src="data:image/jpeg;base64,' + base64.b64encode(buf).decode() + '" '
    w = 'width = "' + str(size) + 'px" '
    h = 'height = "' + str(size) + 'px" '
    return "<img " + src + w + h + ">"


def get_scores_dict(collector: Collector):
    scores_dict = {}
    for metric in collector.metrics:
        scores_dict[metric] = []
        for model in collector.scores:
            scores_dict[metric].append(collector.scores[model][metric])

    return scores_dict


def mean_hit_ratio(actual, predicted):
    ratios = []
    for act, pre in zip(actual, predicted):
        hit_num = len(set(act) & set(pre))
        ratios.append(hit_num / len(act))

    return sum(ratios) / len(ratios)


def mean_average_precision(actual, predicted):
    aps = []
    for act, pre in zip(actual, predicted):
        cnt = 0
        precision_sum = 0
        for i, p in enumerate(pre):
            if p in act:
                cnt += 1
                precision_sum += cnt / (i + 1)
            ap = precision_sum / cnt if cnt else 0
        aps.append(ap)

    return sum(aps) / len(aps)


class MetricMixin:
    """
    Mixin for metric
    """

    # pylint: disable=import-outside-toplevel
    def __init__(self):
        super().__init__()
        self.collector = Collector()

    def with_metrics(self, metric_types: list = None):
        self.collector.metrics = metric_types
        return self

    @property
    def evaluate(self):
        @dynamic_dispatch
        def wrapper(*arg, **kws):
            # pylint: disable=import-outside-toplevel
            # pylint: disable=unused-argument
            with param_scope() as ps:
                index = ps._index | None
            actual, predicted = index
            name = None
            if "name" in kws:
                name = kws["name"]
            elif arg:
                (name,) = arg
            self.collector.add_labels(
                {name: {"actual": actual, "predicted": predicted}}
            )
            score = {name: {}}
            actual_list = []
            predicted_list = []
            for x in self:
                actual_list.append(getattr(x, actual))
                predicted_list.append(getattr(x, predicted))

            from sklearn import metrics

            for metric_type in self.collector.metrics:
                if metric_type == "accuracy":
                    re = metrics.accuracy_score(actual_list, predicted_list)
                elif metric_type == "recall":
                    re = metrics.recall_score(
                        actual_list, predicted_list, average="weighted"
                    )
                elif metric_type == "confusion_matrix":
                    re = metrics.confusion_matrix(actual_list, predicted_list)
                elif metric_type == "mean_hit_ratio":
                    re = mean_hit_ratio(actual_list, predicted_list)
                elif metric_type == "mean_average_precision":
                    re = mean_average_precision(actual_list, predicted_list)
                score[name].update({metric_type: re})
            self.collector.add_scores(score)
            return self

        return wrapper

    def report(self):
        """
        report the metric scores

        Examples:

        >>> from reactive import DataCollection
        >>> from reactive import Entity
        >>> dc1 = DataCollection([Entity(a=a, b=b, c=c) for a, b, c in zip([0,1,1,0,0], [0,1,1,1,0], [0,1,1,0,0])])
        >>> dc1.with_metrics(['accuracy', 'recall']).evaluate['a', 'c'](name='lr').evaluate['a', 'b'](name='rf').report()
            accuracy  recall
        lr       1.0     1.0
        rf       0.8     0.8
        {'lr': {'accuracy': 1.0, 'recall': 1.0}, 'rf': {'accuracy': 0.8, 'recall': 0.8}}
        >>> dc1.with_metrics(['confusion_matrix']).evaluate['a', 'c'](name='lr').evaluate['a', 'b'](name='rf').report()
        <IPython.core.display.HTML object>
        {'lr': {'confusion_matrix': array([[3, 0],
               [0, 2]])}, 'rf': {'confusion_matrix': array([[2, 1],
               [0, 2]])}}
        >>> dc2 = DataCollection([Entity(pred=[1,6,2,7,8,3,9,10,4,5], act=[1,2,3,4,5])])
        >>> dc2.with_metrics(['mean_average_precision', 'mean_hit_ratio']).evaluate['act', 'pred'](name='test').report()
              mean_average_precision  mean_hit_ratio
        test                0.622222             1.0
        {'test': {'mean_average_precision': 0.6222222222222221, 'mean_hit_ratio': 1.0}}
        """
        import pandas as pd
        from IPython.display import HTML, display

        scores_dict = get_scores_dict(self.collector)
        df = pd.DataFrame(data=scores_dict, index=list(self.collector.scores.keys()))

        if "confusion_matrix" in self.collector.metrics:
            display(
                HTML(
                    df.to_html(
                        formatters={"confusion_matrix": encode_fig_img}, escape=False
                    )
                )
            )
        else:
            display(df)
        return self.collector.scores

import sys
import warnings
from abc import ABC, abstractmethod

import matplotlib.pyplot as plt
import numpy as np
from hdbscan import HDBSCAN
from numba.errors import NumbaDeprecationWarning, NumbaWarning
from numpy.random import RandomState
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score, adjusted_mutual_info_score

from src import runner_
from src.datasets.utils import load_digits_, load_mnist, load_fashion
from src.ml.utils import reduce_dimensions
from src.plotting.utils import visualize_best_model_params
from src.plotting.utils import visualize_scores, visualize_classes, print_results, visualize_interactive_plot
from src.problemgenerator.array import Array
from src.problemgenerator.filters import GaussianNoise, Clip

warnings.simplefilter("ignore", category=NumbaDeprecationWarning)
warnings.simplefilter("ignore", category=NumbaWarning)


class Preprocessor:
    def __init__(self):
        self.random_state = RandomState(42)

    def run(self, _1, data, _2):
        reduced_data = reduce_dimensions(data, self.random_state)
        return None, reduced_data, {"reduced_data": reduced_data}


class AbstractModel(ABC):

    def __init__(self):
        self.random_state = RandomState(42)

    @abstractmethod
    def get_fitted_model(self, data, model_params, n_classes):
        pass

    def run(self, _, data, model_params):
        labels = model_params["labels"]

        n_classes = len(np.unique(labels))
        fitted_model = self.get_fitted_model(data, model_params, n_classes)

        return {
            "AMI": round(adjusted_mutual_info_score(labels, fitted_model.labels_, average_method="arithmetic"), 3),
            "ARI": round(adjusted_rand_score(labels, fitted_model.labels_), 3),
        }


class KMeansModel(AbstractModel):

    def __init__(self):
        super().__init__()

    def get_fitted_model(self, data, model_params, n_classes):
        return KMeans(n_clusters=n_classes, random_state=self.random_state).fit(data)


class AgglomerativeModel(AbstractModel):

    def __init__(self):
        super().__init__()

    def get_fitted_model(self, data, model_params, n_classes):
        return AgglomerativeClustering(n_clusters=n_classes).fit(data)


class HDBSCANModel(AbstractModel):

    def __init__(self):
        super().__init__()

    def get_fitted_model(self, data, model_params, n_classes):
        return HDBSCAN(
            min_samples=model_params["min_samples"],
            min_cluster_size=model_params["min_cluster_size"]
        ).fit(data)


def visualize(df, label_names, dataset_name, data):
    visualize_scores(df, ["AMI", "ARI"], [True, True], "std",
                     f"{dataset_name} clustering scores with added gaussian noise")
    visualize_best_model_params(df, "HDBSCAN", ["min_cluster_size", "min_samples"], ["AMI", "ARI"], [True, True], "std",
                                f"Best parameters for {dataset_name} clustering")
    visualize_classes(df, label_names, "std", "reduced_data", "labels", "tab10",
                      f"{dataset_name} (n={data.shape[0]}) classes with added gaussian noise")

    def on_click(original, modified):
        # reshape data
        original = original.reshape((28, 28))
        modified = modified.reshape((28, 28))

        # create a figure and draw the images
        fg, axs = plt.subplots(1, 2)
        axs[0].matshow(original, cmap='gray_r')
        axs[0].axis('off')
        axs[1].matshow(modified, cmap='gray_r')
        axs[1].axis('off')
        fg.show()

    # Remember to enable runner's interactive mode
    visualize_interactive_plot(df, "std", data, "tab10", "reduced_data", on_click)

    plt.show()


def main(argv):
    if len(argv) == 3 and argv[1] == "digits":
        data, labels, label_names, dataset_name = load_digits_(int(argv[2]))
    elif len(argv) == 3 and argv[1] == "mnist":
        data, labels, label_names, dataset_name = load_mnist(int(argv[2]))
    elif len(argv) == 3 and argv[1] == "fashion":
        data, labels, label_names, dataset_name = load_fashion(int(argv[2]))
    else:
        exit(0)

    min_val = np.amin(data)
    max_val = np.amax(data)
    std_steps = np.linspace(0, max_val, num=8)
    err_params_list = [{"mean": 0, "std": std, "min_val": min_val, "max_val": max_val} for std in std_steps]

    n_data = data.shape[0]
    divs = [12, 25, 50]
    min_cluster_size_steps = [round(n_data / div) for div in divs]
    min_samples_steps = [1, 10]
    model_params_dict_list = [
        {"model": KMeansModel, "params_list": [{"labels": labels}]},
        {"model": AgglomerativeModel, "params_list": [{"labels": labels}]},
        {"model": HDBSCANModel, "params_list": [{
            "min_cluster_size": min_cluster_size,
            "min_samples": min_samples,
            "labels": labels
        } for min_cluster_size in min_cluster_size_steps for min_samples in min_samples_steps]},
    ]

    err_root_node = Array()
    err_root_node.addfilter(GaussianNoise("mean", "std"))
    err_root_node.addfilter(Clip("min_val", "max_val"))

    df = runner_.run(None, data, Preprocessor, None, err_root_node, err_params_list, model_params_dict_list,
                     use_interactive_mode=True)

    print_results(df, ["labels", "reduced_data"])
    visualize(df, label_names, dataset_name, data)


if __name__ == "__main__":
    main(sys.argv)
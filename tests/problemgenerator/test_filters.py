from copy import deepcopy

import numpy as np
import src.problemgenerator.filters as filters
import src.problemgenerator.array as array
import src.problemgenerator.copy as copy

def test_seed_determines_result_for_missing_filter():
    a = np.array([0., 1., 2., 3., 4.])
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Missing(0.5))
    root_node = copy.Copy(x_node)
    out1 = root_node.process(a, np.random.RandomState(seed=42))
    out2 = root_node.process(a, np.random.RandomState(seed=42))
    assert np.allclose(out1, out2, equal_nan=True)

def test_seed_determines_result_for_gaussian_noise_filter():
    a = np.array([0., 1., 2., 3., 4.])
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.GaussianNoise(0.5, 0.5))
    root_node = copy.Copy(x_node)
    out1 = root_node.process(a, np.random.RandomState(seed=42))
    out2 = root_node.process(a, np.random.RandomState(seed=42))
    assert np.allclose(out1, out2, equal_nan=True)

def test_seed_determines_result_for_uppercase_filter():
    a = np.array(["hello world"])
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Uppercase(0.5))
    root_node = copy.Copy(x_node)
    out1 = root_node.process(a, np.random.RandomState(seed=42))
    out2 = root_node.process(a, np.random.RandomState(seed=42))
    assert np.array_equal(out1, out2)

def test_seed_determines_result_for_ocr_error_filter():
    a = np.array(["hello world"])
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.OCRError({"e": (["E", "i"], [.5, .5]), "g": (["q", "9"], [.2, .8])}, 1))
    root_node = copy.Copy(x_node)
    out1 = root_node.process(a, np.random.RandomState(seed=42))
    out2 = root_node.process(a, np.random.RandomState(seed=42))
    assert np.array_equal(out1, out2)

def test_seed_determines_result_for_missing_area_filter_with_gaussian_radius_generator():
    a = np.array(["hello world\n" * 10])
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.MissingArea(0.05, filters.MissingArea.GaussianRadiusGenerator(1, 1), "#"))
    root_node = copy.Copy(x_node)
    out1 = root_node.process(a, np.random.RandomState(seed=42))
    out2 = root_node.process(a, np.random.RandomState(seed=42))
    assert np.array_equal(out1, out2)

def test_seed_determines_result_for_missing_area_filter_with_probability_array_radius_generator():
    a = np.array(["hello world\n" * 10])
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.MissingArea(0.05, filters.MissingArea.ProbabilityArrayRadiusGenerator([0.6, 0.3, 0.1]), "#"))
    root_node = copy.Copy(x_node)
    out1 = root_node.process(a, np.random.RandomState(seed=42))
    out2 = root_node.process(a, np.random.RandomState(seed=42))
    assert np.array_equal(out1, out2)
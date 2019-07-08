import numpy as np

import src.problemgenerator.array as array
import src.problemgenerator.filters as filters
import src.problemgenerator.series as series
import src.problemgenerator.radius_generators as radius_generators


def test_seed_determines_result_for_missing_filter():
    a = np.array([0., 1., 2., 3., 4.])
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Missing("prob"))
    params = {"prob": .5}
    out1 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    out2 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.allclose(out1, out2, equal_nan=True)


def test_seed_determines_result_for_gaussian_noise_filter():
    a = np.array([0., 1., 2., 3., 4.])
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.GaussianNoise("mean", "std"))
    params = {"mean": .5, "std": .5}
    out1 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    out2 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.allclose(out1, out2, equal_nan=True)


def test_seed_determines_result_for_uppercase_filter():
    a = np.array(["hello world"])
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Uppercase("prob"))
    params = {"prob": .5}
    out1 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    out2 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.alltrue(out1 == out2)


def test_seed_determines_result_for_ocr_error_filter():
    a = np.array(["hello world"])
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.OCRError("probs", "p"))
    params = {"probs": {"e": (["E", "i"], [.5, .5]), "g": (["q", "9"], [.2, .8])}, "p": 1}
    out1 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    out2 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out1, out2)


def test_seed_determines_result_for_missing_area_filter_with_gaussian_radius_generator():
    a = np.array(["hello world\n" * 10])
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.MissingArea(0.05, radius_generators.GaussianRadiusGenerator(1, 1), "#"))
    params = {}
    out1 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    out2 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out1, out2)


def test_seed_determines_result_for_missing_area_filter_with_probability_array_radius_generator():
    a = np.array(["hello world\n" * 10])
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.MissingArea(0.05, radius_generators.ProbabilityArrayRadiusGenerator([.6, .3, .1]), "#"))
    params = {}
    out1 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    out2 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out1, out2)


def test_seed_determines_result_for_gap_filter():
    a = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Gap(0.1, 0.1, missing_value=1337))
    params = {}
    out1 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    out2 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out1, out2)


def test_seed_determines_result_for_strange_behaviour_filter():
    def f(data, random_state):
        return data * random_state.randint(2, 4)

    a = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.StrangeBehaviour(f))
    params = {}
    out1 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    out2 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out1, out2)


def test_seed_determines_result_for_rain_filter():
    a = np.zeros((10, 10, 3), dtype=int)
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Rain(0.03))
    params = {}
    out1 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    out2 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out1, out2)


def test_seed_determines_result_for_snow_filter():
    a = np.zeros((10, 10, 3), dtype=int)
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Snow(0.04, 0.4, 1))
    params = {}
    out1 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    out2 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out1, out2)


def test_seed_determines_result_for_blur_filter():
    def f(data, random_state):
        return data * random_state.randint(2, 4)

    a = np.random.RandomState(seed=42).randint(0, 255, size=300).reshape((10, 10, 3))
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Blur(5))
    params = {}
    out1 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    out2 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out1, out2)


def test_seed_determines_result_for_stain_filter():
    def f(data, random_state):
        return data * random_state.randint(2, 4)

    a = np.random.RandomState(seed=42).randint(0, 255, size=300).reshape((10, 10, 3))
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.StainArea(.002, radius_generators.GaussianRadiusGenerator(10, 5), 0.5))
    params = {}
    out1 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    out2 = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out1, out2)


def test_sensor_drift():
    drift = filters.SensorDrift(2)
    y = np.full((100), 1)
    drift.apply(y, np.random.RandomState(), (), named_dims={})

    increases = np.arange(1, 101)

    assert len(y) == len(increases)
    for i, val in enumerate(y):
        assert val == increases[i]*2 + 1


def test_strange_behaviour():
    def strange(x, _):
        if 15 <= x <= 20:
            return -300

        return x

    weird = filters.StrangeBehaviour(strange)
    y = np.arange(0, 30)
    weird.apply(y, np.random.RandomState(), (), named_dims={})

    for i in range(15, 21):
        assert y[i] == -300


def test_one_gap():
    gap = filters.Gap(0.0, 1)
    y = np.arange(10000.0)
    gap.apply(y, np.random.RandomState(), (), named_dims={})

    for _, val in enumerate(y):
        assert not np.isnan(val)


def test_two_gap():
    gap = filters.Gap(1, 0)
    y = np.arange(10000.0)
    gap.apply(y, np.random.RandomState(), (), named_dims={})

    for _, val in enumerate(y):
        assert np.isnan(val)


def test_apply_with_probability():
    data = np.array([["a"], ["a"], ["a"], ["a"], ["a"], ["a"], ["a"], ["a"], ["a"], ["a"]])
    params = {"a": [["e"], [1.0]]}
    ocr = filters.OCRError(params, p=1.0)

    x_node = array.Array(data.shape)
    x_node.addfilter(filters.ApplyWithProbability(ocr, 0.5))
    series_node = series.Series(x_node)
    params = {"prob": .5}
    out = series_node.generate_error(data, params, np.random.RandomState(seed=42))

    contains_distinct_elements = False
    for a in out:
        for b in out:
            if a != b:
                contains_distinct_elements = True
    assert contains_distinct_elements


def test_constant():
    a = np.arange(25).reshape((5, 5))
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Constant(5))
    out = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out, np.full((5, 5), 5))


def test_identity():
    a = np.arange(25).reshape((5, 5))
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Identity())
    out = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out, a)


def test_addition():
    a = np.full((5, 5), 5)
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Addition(filters.Constant(2), filters.Identity()))
    out = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out, np.full((5, 5), 7))


def test_subtraction():
    a = np.full((5, 5), 5)
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Subtraction(filters.Constant(2), filters.Identity()))
    out = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out, np.full((5, 5), -3))


def test_multiplication():
    a = np.full((5, 5), 5)
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Multiplication(filters.Constant(2), filters.Identity()))
    out = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out, np.full((5, 5), 10))


def test_division():
    a = np.full((5, 5), 5.0)
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Division(filters.Constant(2), filters.Identity()))
    out = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.allclose(out, np.full((5, 5), .4))


def test_integer_division():
    a = np.full((5, 5), 5)
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.IntegerDivision(filters.Identity(), filters.Constant(2)))
    out = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out, np.full((5, 5), 2))


def test_modulo():
    a = np.full((5, 5), 5)
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Modulo(filters.Identity(), filters.Constant(2)))
    out = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out, np.full((5, 5), 1))


def test_and():
    a = np.full((5, 5), 5)
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.And(filters.Identity(), filters.Constant(2)))
    out = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out, np.full((5, 5), 0))


def test_or():
    a = np.full((5, 5), 5)
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Or(filters.Identity(), filters.Constant(2)))
    out = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out, np.full((5, 5), 7))


def test_xor():
    a = np.full((5, 5), 5)
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Xor(filters.Identity(), filters.Constant(3)))
    out = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out, np.full((5, 5), 6))


def test_difference():
    a = np.full((5, 5), 5)
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Difference(filters.Addition(filters.Identity(), filters.Constant(2))))
    out = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out, np.full((5, 5), 2))


def test_min():
    a = np.full((5, 5), 5)
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Min(filters.Identity(), filters.Constant(2)))
    out = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out, np.full((5, 5), 2))


def test_max():
    a = np.full((5, 5), 5)
    x_node = array.Array(a.shape)
    x_node.addfilter(filters.Max(filters.Identity(), filters.Constant(2)))
    out = x_node.generate_error(a, params, np.random.RandomState(seed=42))
    assert np.array_equal(out, np.full((5, 5), 5))

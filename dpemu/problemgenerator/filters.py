import random
from abc import ABC, abstractmethod
from io import BytesIO

import cv2
import imutils
import numpy as np
from PIL import Image
from math import sqrt
from scipy.ndimage import gaussian_filter

from src.problemgenerator.utils import generate_random_dict_key


class Filter(ABC):
    """A Filter is an error source which can be attached to an Array node.

    The apply method applies the filter. A filter may always assume that
    it is acting upon a NumPy array. (When the underlying data object is not
    a NumPy array, the required conversions are performed by the Array node
    to which the Filter is attached.)

    Args:
        ABC (object): Helper class that provides a standard way to create an ABC using
    inheritance.
    """

    def __init__(self):
        """Set the seeds for the RNG's of NumPy and Python.
        """
        np.random.seed(42)
        random.seed(42)

    @abstractmethod
    def set_params(self, params_dict):
        """Set parameters for error generation.

        Args:
            params_dict (dict): A Python dictionary.
        """
        pass

    @abstractmethod
    def apply(self, node_data, random_state, named_dims):
        """Modifies the data according to the functionality of the filter.

        Args:
            node_data (numpy.ndarray): Data to be modified as a NumPy array.
            random_state (mtrand.RandomState): An instance of numpy.random.RandomState.
            named_dims (dict): Named dimensions.
        """
        pass


class Missing(Filter):
    """Introduce missing values to data.

    For each element in the array, change the value of the element to nan
    with the provided probability.

    Inherits Filter class.
    """

    def __init__(self, probability_id):
        """
        Args:
            probability_id (str): A key which maps to a probability.
        """
        self.probability_id = probability_id
        super().__init__()

    def set_params(self, params_dict):
        self.probability = params_dict[self.probability_id]

    def apply(self, node_data, random_state, named_dims):
        mask = random_state.rand(*(node_data.shape)) <= self.probability
        node_data[mask] = np.nan


class Clip(Filter):
    """Clip values to minimum and maximum value provided by the user.

    Inherits Filter class.
    """

    def __init__(self, min_id, max_id):
        """
        Args:
            min_id (str): A key which maps to a minimum value.
            max_id (str): A key which maps to a maximum value.
        """
        self.min_id = min_id
        self.max_id = max_id
        super().__init__()

    def set_params(self, params_dict):
        self.min = params_dict[self.min_id]
        self.max = params_dict[self.max_id]

    def apply(self, node_data, random_state, named_dims):
        np.clip(node_data, self.min, self.max, out=node_data)


class GaussianNoise(Filter):
    """Add normally distributed noise to data.

    For each element in the array add noise drawn from a Gaussian distribution
    with the provided parameters mean and std (standard deviation).

    Inherits Filter class.
    """

    def __init__(self, mean_id, std_id):
        """
        Args:
            mean_id (str): A key which maps to a mean value.
            std_id (str): A key which maps to a standard deviation value.
        """
        self.mean_id = mean_id
        self.std_id = std_id
        super().__init__()

    def set_params(self, params_dict):
        self.mean = params_dict[self.mean_id]
        self.std = params_dict[self.std_id]

    def apply(self, node_data, random_state, named_dims):
        node_data += random_state.normal(loc=self.mean, scale=self.std, size=node_data.shape).astype(node_data.dtype)


class GaussianNoiseTimeDependent(Filter):
    """Add time dependent normally distributed noise.

    For each element in the array add noise drawn from a Gaussian distribution
    with the provided parameters mean and std (standard deviation). The mean and
    standard deviation increase with every unit of time by the amount specified
    in the last two parameters.

    Inherits Filter class.
    """

    def __init__(self, mean_id, std_id, mean_increase_id, std_increase_id):
        """
        Args:
            mean_id (str): A key which maps to a mean value.
            std_id (str): A key which maps to a standard deviation value.
            mean_increase_id (str): A key which maps to an increase in mean.
            std_increase_id (str): A key which maps to an increase in standard deviation.
        """
        self.mean_id = mean_id
        self.std_id = std_id
        self.mean_increase_id = mean_increase_id
        self.std_increase_id = std_increase_id
        super().__init__()

    def set_params(self, params_dict):
        self.mean = params_dict[self.mean_id]
        self.mean_increase = params_dict[self.mean_increase_id]
        self.std = params_dict[self.std_id]
        self.std_increase = params_dict[self.std_increase_id]

    def apply(self, node_data, random_state, named_dims):
        time = named_dims["time"]
        node_data += random_state.normal(loc=self.mean + self.mean_increase * time,
                                         scale=self.std + self.std_increase * time,
                                         size=node_data.shape)


class Uppercase(Filter):
    """Randomly convert characters to uppercase.

    For each character in the string, convert the character
    to uppercase with the provided probability.

    Inherits Filter class.
    """

    def __init__(self, probability_id):
        """
        Args:
            probability_id (str): A key which maps to the probability of uppercase change.
        """
        self.prob_id = probability_id
        super().__init__()

    def set_params(self, params_dict):
        self.prob = params_dict[self.prob_id]

    def apply(self, node_data, random_state, named_dims):

        def stochastic_upper(char, probability):
            if random_state.rand() <= probability:
                return char.upper()
            return char

        for index, element in np.ndenumerate(node_data):
            original_string = element
            modified_string = "".join(
                [stochastic_upper(c, self.prob) for c in original_string])
            node_data[index] = modified_string


class OCRError(Filter):
    """Emulate optical character recognition (OCR) errors.

    User should provide a probability distribution in the form of a dict,
    specifying how probable a change of character is.

    Inherits Filter class.
    """

    def __init__(self, normalized_params_id, p_id):
        """
        Args:
            normalized_params_id (str): A key which maps to the probability distribution.
            p_id (str): A key which maps to a probability of the distribution being applied.
        """
        self.normalized_params_id = normalized_params_id
        self.p_id = p_id
        super().__init__()

    def set_params(self, params_dict):
        self.normalized_params = params_dict[self.normalized_params_id]
        self.p = params_dict[self.p_id]

    def apply(self, node_data, random_state, named_dims):
        for index, string_ in np.ndenumerate(node_data):
            node_data[index] = (self.generate_ocr_errors(string_, random_state))

    def generate_ocr_errors(self, string_, random_state):
        return "".join([self.replace_char(c, random_state) for c in string_])

    def replace_char(self, c, random_state):
        if c in self.normalized_params and random_state.random_sample() < self.p:
            chars, probs = self.normalized_params[c]
            return random_state.choice(chars, 1, p=probs)[0]

        return c


class MissingArea(Filter):
    """Emulate optical character recognition effect of stains in text.

    Introduce missing areas to text.

    Inherits Filter class.
    """
    # TODO: radius_generator is a struct, not a function. It should be a function for repeatability

    def __init__(self, probability_id, radius_generator_id, missing_value_id):
        """
        Args:
            probability_id (str): A key which maps to a probability of stain.
            radius_generator_id (str): A key which maps to a radius_generator.
            missing_value_id (str): A key which maps to a missing value to be used.
        """
        self.probability_id = probability_id
        self.radius_generator_id = radius_generator_id
        self.missing_value_id = missing_value_id
        super().__init__()

    def set_params(self, params_dict):
        self.probability = params_dict[self.probability_id]
        self.radius_generator = params_dict[self.radius_generator_id]
        self.missing_value = params_dict[self.missing_value_id]

    def apply(self, node_data, random_state, named_dims):
        if self.probability == 0:
            return

        for index, _ in np.ndenumerate(node_data):
            # 1. Get indexes of newline characters. We will not touch those
            string = node_data[index]

            row_starts = [0]
            for i, c in enumerate(string):
                if c == '\n':
                    row_starts.append(i + 1)
            if not row_starts or row_starts[-1] != len(string):
                row_starts.append(len(string))
            height = len(row_starts) - 1

            widths = np.array([row_starts[i + 1] - row_starts[i] - 1 for i in range(height)])
            if len(widths) > 0:
                width = np.max(widths)
            else:
                width = 0

            # 2. Generate error
            errs = np.zeros(shape=(height + 1, width + 1))
            ind = -1
            while True:
                ind += random_state.geometric(self.probability)

                if ind >= width * height:
                    break
                y = ind // width
                x = ind - y * width
                r = self.radius_generator.generate(random_state)
                x0 = max(x - r, 0)
                x1 = min(x + r + 1, width)
                y0 = max(y - r, 0)
                y1 = min(y + r + 1, height)
                errs[y0, x0] += 1
                errs[y0, x1] -= 1
                errs[y1, x0] -= 1
                errs[y1, x1] += 1

            # 3. Perform prefix sums, create mask
            errs = np.cumsum(errs, axis=0)
            errs = np.cumsum(errs, axis=1)
            errs = (errs > 0)

            mask = np.zeros(len(string))
            for y in range(height):
                ind = row_starts[y]
                mask[ind:ind + widths[y]] = errs[y, 0:widths[y]]

            # 4. Apply error to string
            res_str = "".join([' ' if mask[i] else string[i] for i in range(len(mask))])
            node_data[index] = res_str


class StainArea(Filter):
    """Adds stains to images.

    This filter adds stains to the images.
        probability: probability of adding a stain at each pixel.
        radius_generator: object implementing a generate(random_state) function
            which returns the radius of the stain.
        transparency_percentage: 1 means that the stain is invisible and 0 means
            that the part of the image where the stain is is completely black.

    Inherits Filter class.
    """

    def __init__(self, probability_id, radius_generator_id, transparency_percentage_id):
        """
        Args:
            probability_id (str): A key which maps to the probability of stain.
            radius_generator_id (str): A key which maps to the radius_generator.
            transparency_percentage_id (str): A key which maps to the transparency percentage.
        """
        self.probability_id = probability_id
        self.radius_generator_id = radius_generator_id
        self.transparency_percentage_id = transparency_percentage_id
        super().__init__()

    def set_params(self, params_dict):
        self.probability = params_dict[self.probability_id]
        self.radius_generator = params_dict[self.radius_generator_id]
        self.transparency_percentage = params_dict[self.transparency_percentage_id]

    def apply(self, node_data, random_state, named_dims):
        height = node_data.shape[0]
        width = node_data.shape[1]

        # 1. Generate error
        errs = np.zeros(shape=(height + 1, width + 1))
        ind = -1
        while True:
            ind += random_state.geometric(self.probability)

            if ind >= width * height:
                break
            y = ind // width
            x = ind - y * width
            r = self.radius_generator.generate(random_state)
            x0 = max(x - r, 0)
            x1 = min(x + r + 1, width)
            y0 = max(y - r, 0)
            y1 = min(y + r + 1, height)
            errs[y0, x0] += 1
            errs[y0, x1] -= 1
            errs[y1, x0] -= 1
            errs[y1, x1] += 1

        # 2. Modify the array
        errs = np.cumsum(errs, axis=0)
        errs = np.cumsum(errs, axis=1)
        errs = np.power(self.transparency_percentage, errs)
        for j in range(3):
            node_data[:, :, j] = np.multiply(node_data[:, :, j], errs[0:height, 0:width])


class Gap(Filter):
    """Introduce gaps to time series data by simulating sensor failure.

    Model the state of a sensor as a Markov chain. The sensor always
    starts in a working state. The sensor has a specific probability
    to stop working and a specific probability to start working.

    Inherits Filter class.
    """

    def __init__(self, prob_break_id, prob_recover_id, missing_value_id):
        """
        Args:
            prob_break_id (str): A key which maps to the probability of the sensor breaking.
            prob_recover_id (str): A key which maps to the probability of the sensor recovering.
            missing_value_id (str): A key which maps to a missing value to be used.
        """
        super().__init__()
        self.prob_break_id = prob_break_id
        self.prob_recover_id = prob_recover_id
        self.missing_value_id = missing_value_id
        self.working = True

    def set_params(self, params_dict):
        self.prob_break = params_dict[self.prob_break_id]
        self.prob_recover = params_dict[self.prob_recover_id]
        self.missing_value = params_dict[self.missing_value_id]
        self.working = True

    def apply(self, node_data, random_state, named_dims):
        def update_working_state():
            if self.working:
                if random_state.rand() < self.prob_break:
                    self.working = False
            else:
                if random_state.rand() < self.prob_recover:
                    self.working = True

        # random_state.rand(node_data.shape[0], node_data.shape[1])
        for index, _ in np.ndenumerate(node_data):
            update_working_state()
            if not self.working:
                node_data[index] = self.missing_value


class SensorDrift(Filter):
    """Emulate sensor values drifting due to a malfunction in the sensor.

    Magnitude is the linear increase in drift during time period t_i -> t_i+1.

    Inherits Filter class.
    """

    def __init__(self, magnitude_id):
        """
        Args:
            magnitude_id (str): A key which maps to the magnitude value.
        """
        super().__init__()
        self.magnitude_id = magnitude_id

    def set_params(self, params_dict):
        self.magnitude = params_dict[self.magnitude_id]

    def apply(self, node_data, random_state, named_dims):
        increases = np.arange(1, node_data.shape[0] + 1) * self.magnitude
        node_data += increases.reshape(node_data.shape)


class StrangeBehaviour(Filter):
    """Emulate strange sensor values due to anomalous conditions around the sensor.

    The function do_strange_behaviour is user defined and outputs strange sensor
    values into the data.

    Inherits Filter class.
    """

    def __init__(self, do_strange_behaviour_id):
        """
        Args:
            do_strange_behaviour_id (str): A key which maps to the strange_behaviour function.
        """
        super().__init__()
        self.do_strange_behaviour_id = do_strange_behaviour_id

    def set_params(self, params_dict):
        self.do_strange_behaviour = params_dict[self.do_strange_behaviour_id]

    def apply(self, node_data, random_state, named_dims):
        for index, _ in np.ndenumerate(node_data):
            node_data[index] = self.do_strange_behaviour(node_data[index], random_state)


class FastRain(Filter):
    """Add rain to images.

    RGB values are presented either in the range [0,1] or in the set {0,...,255},
        thus range should either have value 1 or value 255.

    Inherits Filter class.
    """

    def __init__(self, probability_id, range_id):
        """
        Args:
            probability_id (str): A key which maps to a probability of rain.
            range_id (str): A key which maps to value of either 1 or 255.
        """
        super().__init__()
        self.probability_id = probability_id
        self.range_id = range_id

    def set_params(self, params_dict):
        self.probability = params_dict[self.probability_id]
        # self.range should have value 1 or 255
        self.range = params_dict[self.range_id]

    def apply(self, node_data, random_state, named_dims):
        height = node_data.shape[0]
        width = node_data.shape[1]

        # 1. Generate error
        errs = np.zeros(shape=(height + 1, width + 1))
        ind = -1
        while True:
            ind += random_state.geometric(self.probability)

            if ind >= width * height:
                break
            y = ind // width
            x = ind - y * width
            x_r = 1
            y_r = max(0, round(random_state.normal(20, 10)))
            x0 = max(x - x_r, 0)
            x1 = min(x + x_r + 1, width)
            y0 = max(y - y_r, 0)
            y1 = min(y + y_r + 1, height)
            errs[y0, x0] += 1
            errs[y0, x1] -= 1
            errs[y1, x0] -= 1
            errs[y1, x1] += 1

        # 2. Calculate cumulative sums
        errs = np.cumsum(errs, axis=0)
        errs = np.cumsum(errs, axis=1)

        # 3. Modify data
        locs = 5 * errs
        scales = 10 * np.sqrt(errs / 12) + 4 * errs
        for j in range(3):
            add = random_state.normal(locs, scales)
            if j == 2:
                add += 30 * errs
            if self.range == 1:
                node_data[:, :, j] = np.clip(node_data[:, :, j] + add[0:height, 0:width] / 255, 0, 1)
            else:
                node_data[:, :, j] = np.clip(node_data[:, :, j] + add[0:height, 0:width].astype(int), 0, 255)


class Snow(Filter):
    """Add snow to images.

    This filter adds snow to images, and it uses Pierrre Vigier's implementation
    of 2d perlin noise.

    Pierre Vigier's implementation of 2d perlin noise with slight changes.
    https://github.com/pvigier/perlin-numpy

    The original code is licensed under MIT License:

    MIT License

    Copyright (c) 2019 Pierre Vigier

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

    Inherits Filter class.
    """

    def __init__(self, snowflake_probability_id, snowflake_alpha_id, snowstorm_alpha_id):
        """
        Args:
            snowflake_probability_id (str): A key which maps to a snowflake probability.
            snowflake_alpha_id (str):
            snowstorm_alpha_id (str):
        """
        super().__init__()
        self.snowflake_probability_id = snowflake_probability_id
        self.snowflake_alpha_id = snowflake_alpha_id
        self.snowstorm_alpha_id = snowstorm_alpha_id

    def set_params(self, params_dict):
        self.snowflake_probability = params_dict[self.snowflake_probability_id]
        self.snowflake_alpha = params_dict[self.snowflake_alpha_id]
        self.snowstorm_alpha = params_dict[self.snowstorm_alpha_id]

    def apply(self, node_data, random_state, named_dims):
        def generate_perlin_noise(height, width, random_state):
            """[summary]

            Pierre Vigier's implementation of 2d perlin noise with slight changes.
            https://github.com/pvigier/perlin-numpy

            The original code is licensed under MIT License:

            MIT License

            Copyright (c) 2019 Pierre Vigier

            Permission is hereby granted, free of charge, to any person obtaining a copy
            of this software and associated documentation files (the "Software"), to deal
            in the Software without restriction, including without limitation the rights
            to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
            copies of the Software, and to permit persons to whom the Software is
            furnished to do so, subject to the following conditions:

            The above copyright notice and this permission notice shall be included in all
            copies or substantial portions of the Software.

            THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
            IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
            FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
            AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
            LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
            OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
            SOFTWARE.
            """

            def f(t):
                return 6 * t ** 5 - 15 * t ** 4 + 10 * t ** 3

            d = (height, width)
            grid = np.mgrid[0:d[0], 0:d[1]].astype(float)
            grid[0] /= height
            grid[1] /= width

            grid = grid.transpose(1, 2, 0) % 1
            # Gradients
            angles = 2 * np.pi * random_state.rand(2, 2)
            gradients = np.dstack((np.cos(angles), np.sin(angles)))
            g00 = gradients[0:-1, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
            g10 = gradients[1:, 0:-1].repeat(d[0], 0).repeat(d[1], 1)
            g01 = gradients[0:-1, 1:].repeat(d[0], 0).repeat(d[1], 1)
            g11 = gradients[1:, 1:].repeat(d[0], 0).repeat(d[1], 1)
            # Ramps
            n00 = np.sum(grid * g00, 2)
            n10 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1])) * g10, 2)
            n01 = np.sum(np.dstack((grid[:, :, 0], grid[:, :, 1] - 1)) * g01, 2)
            n11 = np.sum(np.dstack((grid[:, :, 0] - 1, grid[:, :, 1] - 1)) * g11, 2)
            # Interpolation
            t = f(grid)
            n0 = n00 * (1 - t[:, :, 0]) + t[:, :, 0] * n10
            n1 = n01 * (1 - t[:, :, 0]) + t[:, :, 0] * n11
            return np.sqrt(2) * ((1 - t[:, :, 1]) * n0 + t[:, :, 1] * n1)

        def build_snowflake(r):
            res = np.zeros(shape=(2 * r + 1, 2 * r + 1))
            for y in range(0, 2 * r + 1):
                for x in range(0, 2 * r + 1):
                    dy = y - r
                    dx = x - r
                    d = sqrt(dx * dx + dy * dy)
                    if r == 0:
                        res[y, x] = 1
                    else:
                        res[y, x] = max(0, 1 - d / r)
            return res * self.snowflake_alpha

        width = node_data.shape[1]
        height = node_data.shape[0]

        # generate snowflakes
        flakes = []
        ind = -1
        while True:
            ind += random_state.geometric(self.snowflake_probability)
            if ind >= height * width:
                break
            y = ind // width
            x = ind % width
            r = round(random_state.normal(5, 2))
            if r <= 0:
                continue
            while len(flakes) <= r:
                flakes.append(build_snowflake(len(flakes)))
            y0 = max(0, y - r)
            x0 = max(0, x - r)
            y1 = min(height - 1, y + r) + 1
            x1 = min(width - 1, x + r) + 1
            fy0 = y0 - (y - r)
            fx0 = x0 - (x - r)
            fy1 = y1 - (y - r)
            fx1 = x1 - (x - r)
            for j in range(3):
                node_data[y0:y1, x0:x1, j] += ((255 - node_data[y0:y1, x0:x1, j]) * flakes[r][fy0:fy1, fx0:fx1]).astype(
                    node_data.dtype)

        # add noise
        noise = generate_perlin_noise(height, width, random_state)
        noise = (noise + 1) / 2  # transform the noise to be in range [0, 1]
        for j in range(3):
            node_data[:, :, j] += (self.snowstorm_alpha * (255 - node_data[:, :, j]) * noise[:, :]).astype(
                node_data.dtype)


class JPEG_Compression(Filter):
    """Compresses a JPEG-image.

    Compress the image as JPEG and uncompress. Quality should be in range [1, 100],
    the bigger the less loss.

    Inherits Filter class.
    """

    def __init__(self, quality_id):
        super().__init__()
        self.quality_id = quality_id

    def set_params(self, params_dict):
        self.quality = params_dict[self.quality_id]

    def apply(self, node_data, random_state, named_dims):
        iml = Image.fromarray(np.uint8(np.around(node_data)))
        buf = BytesIO()
        iml.save(buf, "JPEG", quality=self.quality)
        iml = Image.open(buf)
        res_data = np.array(iml)

        # width = node_data.shape[1]
        # height = node_data.shape[0]
        node_data[:, :] = res_data


class Blur_Gaussian(Filter):
    """Blur image according to a zero-centred normal distribution.

    Create blur in images by applying a Gaussian filter.
    The standard deviation of the Gaussian is taken as a parameter.

    Inherits Filter class.
    """

    def __init__(self, standard_dev_id):
        """
        Args:
            standard_dev_id (str): A key which maps to standard deviation.
        """
        super().__init__()
        self.std_id = standard_dev_id

    def set_params(self, params_dict):
        self.std = params_dict[self.std_id]

    def apply(self, node_data, random_state, named_dims):
        if len(node_data.shape) == 2:
            node_data[...] = gaussian_filter(node_data, self.std)
        else:
            for i in range(node_data.shape[-1]):
                node_data[:, :, i] = gaussian_filter(node_data[:, :, i], self.std)


class Blur(Filter):

    def __init__(self, repeats_id):
        super().__init__()
        self.repeats_id = repeats_id

    def set_params(self, params_dict):
        self.repeats = params_dict[self.repeats_id]

    def apply(self, node_data, random_state, named_dims):
        width = node_data.shape[1]
        height = node_data.shape[0]
        for _ in range(self.repeats):
            original = np.copy(node_data)
            for y0 in range(height):
                for x0 in range(width):
                    pixel_sum = np.array([0, 0, 0])
                    pixel_count = 0
                    for y in range(y0 - 1, y0 + 2):
                        for x in range(x0 - 1, x0 + 2):
                            if y < 0 or x < 0 or y == height or x == width:
                                continue
                            pixel_sum += original[y][x]
                            pixel_count += 1
                    node_data[y0][x0] = pixel_sum // pixel_count


class ResolutionVectorized(Filter):
    """Makes resolution k times smaller.

    K must be an integer.

    Inherits Filter class.
    """

    def __init__(self, k_id):
        """
        Args:
            k_id (str): A key which maps to the k value.
        """
        super().__init__()
        self.k_id = k_id

    def set_params(self, params_dict):
        self.k = params_dict[self.k_id]

    def apply(self, node_data, random_state, named_dims):
        w = node_data.shape[1]
        h = node_data.shape[0]
        row, col = (np.indices((h, w)) // self.k) * self.k
        node_data[...] = node_data[row, col]


class Rotation(Filter):
    """[summary]

    [extended_summary]

    Inherits Filter class.
    """

    def __init__(self, angle_id):
        super().__init__()
        self.angle_id = angle_id

    def set_params(self, params_dict):
        self.angle = params_dict[self.angle_id]

    def apply(self, node_data, random_state, named_dims):
        node_data[...] = imutils.rotate(node_data, self.angle)

        # Guesstimation for a large enough resize to avoid black areas in cropped picture
        factor = 1.8
        resized = cv2.resize(node_data, None, fx=factor, fy=factor)
        resized_width = resized.shape[1]
        resized_height = resized.shape[0]
        width = node_data.shape[1]
        height = node_data.shape[0]

        x0 = round((resized_width - width) / 2)
        y0 = round((resized_height - height) / 2)
        node_data[...] = resized[y0:y0 + height, x0:x0 + width]


class BrightnessVectorized(Filter):
    """Increases or decreases brightness in the image.

    tar: 0 if you want to decrease brightness, 1 if you want to increase it.
    rat: scales the brightness change.
    range: Should have value 1 or 255. RGB values are presented either
        in the range [0,1] or in the set {0,...,255}.

    Inherits Filter class.
    """

    def __init__(self, tar_id, rat_id, range_id):
        """
        Args:
            tar_id (str): A key which maps to the tar value.
            rat_id (str): A key which maps to the rat value.
            range_id (str): A key which maps to the range value.
        """
        super().__init__()
        self.tar_id = tar_id
        self.rat_id = rat_id
        self.range_id = range_id

    def set_params(self, params_dict):
        self.tar = params_dict[self.tar_id]
        self.rat = params_dict[self.rat_id]
        self.range = params_dict[self.range_id]

    def apply(self, node_data, random_state, named_dims):
        nd = node_data.astype("float32")
        if self.range == 255:
            nd[...] = node_data * (1 / self.range)

        hls = cv2.cvtColor(nd, cv2.COLOR_RGB2HLS)
        mult = 1 - np.exp(-2 * self.rat)
        hls[:, :, 1] = hls[:, :, 1] * (1 - mult) + self.tar * mult
        nd[...] = cv2.cvtColor(hls, cv2.COLOR_HLS2RGB)

        if self.range == 255:
            nd[...] = nd * self.range
            nd = nd.astype(np.int8)
        else:
            nd = np.clip(nd, 0.0, 1.0)

        node_data[...] = nd


class SaturationVectorized(Filter):
    """Increases or decreases saturation in the image.

    tar: 0 if you want to decrease saturation, 1 if you want to increase it.
    rat: scales the saturation change.
    range: Should have value 1 or 255. RGB values are presented either
     in the range [0,1] or in the set {0,...,255}.

    Inherits Filter class.
    """

    def __init__(self, tar_id, rat_id, range_id):
        """
        Args:
            tar_id (str): A key which maps to the tar value.
            rat_id (str): A key which maps to the rat value.
            range_id (str): A key which maps to the range value.
        """
        super().__init__()
        self.tar_id = tar_id
        self.rat_id = rat_id
        self.range_id = range_id

    def set_params(self, params_dict):
        self.tar = params_dict[self.tar_id]
        self.rat = params_dict[self.rat_id]
        self.range = params_dict[self.range_id]

    def apply(self, node_data, random_state, named_dims):
        nd = node_data.astype("float32")
        if self.range == 255:
            nd[...] = node_data * (1 / self.range)

        hls = cv2.cvtColor(nd, cv2.COLOR_RGB2HLS)
        mult = 1 - np.exp(-2 * self.rat * hls[:, :, 2])
        hls[:, :, 2] = hls[:, :, 2] * (1 - mult) + self.tar * mult
        nd[...] = cv2.cvtColor(hls, cv2.COLOR_HLS2RGB)

        if self.range == 255:
            nd[...] = nd * self.range
            nd = nd.astype(np.int8)
        else:
            nd = np.clip(nd, 0.0, 1.0)

        node_data[...] = nd


class LensFlare(Filter):
    """Add lens flare to an image.

    Inherits Filter class.
    """

    def __init__(self):
        super().__init__()

    def set_params(self, params_dict):
        pass

    def apply(self, node_data, random_state, named_dims):
        def flare(x0, y0, radius):
            gt = random_state.randint(130, 180)
            rt = random_state.randint(220, 255)
            bt = random_state.randint(0, 50)
            x_offset = random_state.normal(0, 5)
            y_offset = random_state.normal(0, 5)
            for x in range(x0 - radius, x0 + radius + 1):
                for y in range(y0 - radius, y0 + radius + 1):
                    if y < 0 or x < 0 or y >= height or x >= width:
                        continue
                    dist = sqrt((x - x0) * (x - x0) + (y - y0) * (y - y0))
                    if dist > radius:
                        continue
                    offset_dist = sqrt((x - x0 + x_offset) ** 2 + (y - y0 + y_offset) ** 2)
                    r = node_data[y][x][0]
                    g = node_data[y][x][1]
                    b = node_data[y][x][2]
                    a = 3
                    t = max(0, min(1, (1 - (radius - offset_dist) / radius)))
                    visibility = max(0, a * t * t + (1 - a) * t) * 0.8
                    r = round(r + (rt - r) * visibility)
                    g = round(g + (gt - g) * visibility)
                    b = round(b + (bt - b) * visibility)
                    node_data[y][x] = (r, g, b)

        width = node_data.shape[1]
        height = node_data.shape[0]

        # estimate the brightest spot in the image
        pixel_sum_x = [0, 0, 0]
        pixel_sum_y = [0, 0, 0]
        expected_x = [0, 0, 0]
        expected_y = [0, 0, 0]
        for y0 in range(height):
            for x0 in range(width):
                pixel_sum_x += node_data[y0][x0]
                pixel_sum_y += node_data[y0][x0]
        for y0 in range(height):
            for x0 in range(width):
                expected_x += x0 * node_data[y0][x0] / pixel_sum_x
                expected_y += y0 * node_data[y0][x0] / pixel_sum_y
        best_y = int((expected_y[0] + expected_y[1] + expected_y[2]) / 3)
        best_x = int((expected_x[0] + expected_x[1] + expected_x[2]) / 3)

        origo_vector = np.array([width / 2 - best_x, height / 2 - best_y])
        origo_vector = origo_vector / sqrt(origo_vector[0] * origo_vector[0] + origo_vector[1] * origo_vector[1])

        # move towards origo and draw flares
        y = best_y
        x = best_x
        steps = 0
        while True:
            if steps < 0:
                radius = round(max(40, random_state.normal(100, 100)))
                flare(int(x), int(y), radius)
                steps = random_state.normal(radius, 15)
            if (best_x - width / 2) ** 2 + (best_y - height / 2) ** 2 + 1 <= (x - width / 2) ** 2 + (
                    y - height / 2) ** 2:
                break
            y += origo_vector[1]
            x += origo_vector[0]
            steps -= 1


class ClipWAV(Filter):
    def __init__(self, dyn_range_id):
        super().__init__()
        self.dyn_range_id = dyn_range_id

    def set_params(self, params_dict):
        self.dyn_range = params_dict[self.dyn_range_id]

    def apply(self, node_data, random_state, named_dims):

        def clip_audio(data, dyn_range):
            min_, max_ = min(data), max(data)
            half_range = .5 * max_ - .5 * min_
            middle = (min_ + max_) / 2
            new_half_range = half_range * dyn_range
            upper_limit = middle + new_half_range
            lower_limit = middle - new_half_range
            return np.clip(data, lower_limit, upper_limit).astype(data.dtype)

        node_data[:] = clip_audio(node_data, self.dyn_range)


class ApplyToTuple(Filter):

    def __init__(self, ftr, tuple_index):
        super().__init__()
        self.ftr = ftr
        self.tuple_index = tuple_index

    def set_params(self, params_dict):
        self.ftr.set_params(params_dict)

    def apply(self, node_data, random_state, named_dims):
        self.ftr.apply(node_data[self.tuple_index], random_state, named_dims)


class ApplyWithProbability(Filter):
    """Apply a filter with the specified probability.

    A filter is applied with the specified probability.
    Inherits Filter class.
    """

    def __init__(self, ftr_id, probability_id):
        """
        Args:
            ftr_id (str): A key which maps to a filter.
            probability_id (str): A key which maps to the probability of the filter being applied.
        """
        super().__init__()
        self.ftr_id = ftr_id
        self.probability_id = probability_id

    def set_params(self, params_dict):
        self.ftr = params_dict[self.ftr_id]
        self.probability = params_dict[self.probability_id]
        self.ftr.set_params(params_dict)

    def apply(self, node_data, random_state, named_dims):
        if random_state.rand() < self.probability:
            self.ftr.apply(node_data, random_state, named_dims)


class Constant(Filter):
    """[summary]

    [extended_summary]

    Inherits Filter class.
    """

    def __init__(self, value_id):
        super().__init__()
        self.value_id = value_id

    def set_params(self, params_dict):
        self.value = params_dict[self.value_id]

    def apply(self, node_data, random_state, named_dims):
        node_data.fill(self.value)


class Identity(Filter):
    """This filter acts as the identity operator and does not modify data.

    Inherits Filter class.
    """

    def __init__(self):
        super().__init__()

    def set_params(self, params_dict):
        pass

    def apply(self, node_data, random_state, named_dims):
        pass


class BinaryFilter(Filter):
    """This abstract filter takes two filters and applies some pairwise binary operation on their results.

    Inherits Filter class.
    """

    def __init__(self, filter_a_id, filter_b_id):
        """
        Args:
            filter_a_id (str): A key which maps to the first filter
            filter_b_id (str): A key which maps to the second filter
        """
        super().__init__()
        self.filter_a_id = filter_a_id
        self.filter_b_id = filter_b_id

    def apply(self, node_data, random_state, named_dims):
        data_a = node_data.copy()
        data_b = node_data.copy()
        self.filter_a.apply(data_a, random_state, named_dims)
        self.filter_b.apply(data_b, random_state, named_dims)
        for index, _ in np.ndenumerate(node_data):
            node_data[index] = self.operation(data_a[index], data_b[index])

    def set_params(self, params_dict):
        self.filter_a = params_dict[self.filter_a_id]
        self.filter_b = params_dict[self.filter_b_id]
        self.filter_a.set_params(params_dict)
        self.filter_b.set_params(params_dict)

    @abstractmethod
    def operation(self, element_a, element_b):
        """The operation which is applied pairwise on the n-dimensional arrays of child filters.

        Args:
            element_a (object): The first element
            element_b (object): The second element
        """
        pass


class Addition(BinaryFilter):
    """This filter does pairwise addition on the multidimensional arrays returned by the child filters.

    Inherits BinaryFilter class.
    """

    def operation(self, element_a, element_b):
        return element_a + element_b


class Subtraction(BinaryFilter):
    """This filter does pairwise subtraction on the multidimensional arrays returned by the child filters.

    Inherits BinaryFilter class.
    """

    def operation(self, element_a, element_b):
        return element_a - element_b


class Multiplication(BinaryFilter):
    """This filter does pairwise multiplication on the multidimensional arrays returned by the child filters.

    Inherits BinaryFilter class.
    """

    def operation(self, element_a, element_b):
        return element_a * element_b


class Division(BinaryFilter):
    """This filter does pairwise division on the multidimensional arrays returned by the child filters.

    Inherits BinaryFilter class.
    """

    def operation(self, element_a, element_b):
        return element_a / element_b


class IntegerDivision(BinaryFilter):
    """This filter does pairwise integer division on the multidimensional arrays returned by the child filters.

    Inherits BinaryFilter class.
    """

    def operation(self, element_a, element_b):
        return element_a // element_b


class Modulo(BinaryFilter):
    """This filter does pairwise modulo operation on the multidimensional arrays returned by the child filters.

    Inherits BinaryFilter class.
    """

    def operation(self, element_a, element_b):
        return element_a % element_b


class And(BinaryFilter):
    """This filter does pairwise bitwise AND on the multidimensional arrays returned by the child filters.

    Inherits BinaryFilter class.
    """

    def operation(self, element_a, element_b):
        return element_a & element_b


class Or(BinaryFilter):
    """"This filter does pairwise bitwise OR on the multidimensional arrays returned by the child filters.

    Inherits BinaryFilter class.
    """

    def operation(self, element_a, element_b):
        return element_a | element_b


class Xor(BinaryFilter):
    """This filter does pairwise bitwise XOR on the multidimensional arrays returned by the child filters.

    Inherits BinaryFilter class.
    """

    def operation(self, element_a, element_b):
        return element_a ^ element_b


class Difference(Filter):
    """This filter returns the difference between the original and the filtered data,
    i.e. it is shorthand for Subtraction(filter, Identity()).

    Inherits BinaryFilter class.
    """

    def __init__(self, ftr_id):
        super().__init__()
        self.ftr_id = ftr_id

    def set_params(self, params_dict):
        identity_key = generate_random_dict_key(params_dict, "identity")
        params_dict[identity_key] = Identity()
        self.ftr = Subtraction(self.ftr_id, identity_key)
        self.ftr.set_params(params_dict)

    def apply(self, node_data, random_state, named_dims):
        self.ftr.apply(node_data, random_state, named_dims)


class Max(BinaryFilter):
    """This filter returns a multidimensional array of pairwise maximums
    of the multidimensional arrays returned by the child filters.

    Inherits BinaryFilter class.
    """

    def operation(self, element_a, element_b):
        return max(element_a, element_b)


class Min(BinaryFilter):
    """This filter returns a multidimensional array of pairwise minimums
    of the multidimensional arrays returned by the child filters.

    Inherits BinaryFilter class.
    """

    def operation(self, element_a, element_b):
        return min(element_a, element_b)


class ModifyAsDataType(Filter):
    """[summary]

    [extended_summary]

    Inherits Filter class.
    """

    def __init__(self, dtype_id, ftr_id):
        super().__init__()
        self.dtype_id = dtype_id
        self.ftr_id = ftr_id

    def set_params(self, params_dict):
        self.dtype = params_dict[self.dtype_id]
        self.ftr = params_dict[self.ftr_id]
        self.ftr.set_params(params_dict)

    def apply(self, node_data, random_state, named_dims):
        copy = node_data.copy().astype(self.dtype)
        self.ftr.apply(copy, random_state, named_dims)
        copy = copy.astype(node_data.dtype)
        for index, _ in np.ndenumerate(node_data):
            node_data[index] = copy[index]
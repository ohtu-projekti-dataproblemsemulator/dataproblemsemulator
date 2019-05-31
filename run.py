import sys
import os
import datetime
import subprocess
import json
import re
import numpy as np
from PIL import Image
import src.problemgenerator.series as series
import src.problemgenerator.array as array
import src.problemgenerator.filters as filters
import src.problemgenerator.copy as copy
from src.combiner.combiner import Combiner
from src.utils import load_digits_as_npy, load_mnist_as_npy
import src.utils as utils
import re

# File format:
#     run_model_command ...
#     run_analyze_command ...
# special tokens:
#    [IN_i]: Will get replaced with input file i
#    [MID_j.ext]: Will get replaced with unique filename with extension .ext
#                 These files get listed as mid_file_names.
#    [OUT_k.ext]: Will get replaced with unique filename with extension .ext
#                 These files get listed as out_file_names.
#    The same token can appear multiple times. For example, if the commands are
#        python3 model.py < [IN_1] > [MID_1.npy] 2> [MID_2.txt]
#        python3 analyze.py < [MID_1.npy] > [OUT_1.npy]
#    The file given to analyze_py will be the same .npy file as the one generated by model.py
def read_commands_file(commands_file_name):
    f = open(commands_file_name)
    run_model_command = f.readline().rstrip('\n')
    run_analyze_command = f.readline().rstrip('\n')
    return run_model_command, run_analyze_command

def unique_filename(folder, prefix, extension):
    current_folder = os.path.dirname(os.path.realpath(__file__))
    timestamp_string = str(datetime.datetime.utcnow().timestamp())
    fname = f"{current_folder}/{folder}/{prefix}_{timestamp_string}.{extension}"
    return fname

def do_replacements(command, replacements):
    for key, value in replacements.items():
        command = command.replace(key, value)
    return command

def create_replacements(command, token_signature):
    regex = r'\[' + re.escape(token_signature) + r'_(\d*)\.(\w*)\]'
    matches = re.findall(regex, command)
    replacements = {}
    for pr in matches:
        replacements["[" + token_signature + "_" + pr[0] + "." + pr[1] + "]"] = unique_filename("tmp", token_signature + "-" + str(pr[0]), pr[1])
    return replacements

def run_commands(run_model_command, run_analyze_command, in_file_names):
    in_replacements = {'[IN_' + str(i+1) + ']': in_file_names[i] for i in range(0, len(in_file_names))}
    mid_replacements = create_replacements(run_model_command + run_analyze_command, "MID")
    out_replacements = create_replacements(run_model_command + run_analyze_command, "OUT")

    run_model_command = do_replacements(run_model_command, in_replacements)
    run_model_command = do_replacements(run_model_command, mid_replacements)
    run_model_command = do_replacements(run_model_command, out_replacements)

    run_analyze_command = do_replacements(run_analyze_command, in_replacements)
    run_analyze_command = do_replacements(run_analyze_command, mid_replacements)
    run_analyze_command = do_replacements(run_analyze_command, out_replacements)

    print(run_model_command)
    print(run_analyze_command)

    subprocess.run(run_model_command, shell=True)
    subprocess.run(run_analyze_command, shell=True)

    mid_file_names = [value for key, value in sorted(mid_replacements.items())]
    out_file_names = [value for key, value in sorted(out_replacements.items())]
    return mid_file_names, out_file_names

def read_analyzer_files(file_names):
    res = []
    for fn in file_names:
        extension = fn.split('.')[-1]
        if extension == 'json':
            with open(fn, "r") as file:
                res.append(json.load(file))
        elif extension == 'png':
            res.append(Image.open(fn))
    return res

def main():
    def save_errorified(std, prob):
        print(std, prob)
        x_node = array.Array(original_data[0][0].shape)
        x_node.addfilter(filters.GaussianNoise(0, std))
        x_node.addfilter(filters.Missing(prob))
        y_node = array.Array(original_data[1][0].shape)
        series_node = series.TupleSeries([x_node, y_node])
        error_generator_root = copy.Copy(series_node)
        x_out, y_out = error_generator_root.process(original_data)
        # x_out.reshape((x_out.shape[0], 28*28))
        x_name = unique_filename("tmp", "x", "npy")
        y_name = unique_filename("tmp", "y", "npy")
        np.save(x_name, x_out)
        np.save(y_name, y_out)
        return [x_name, y_name]

    # Read input
    path_to_data, path_to_labels = load_digits_as_npy() # Values 0..16.
    # path_to_data, path_to_labels = load_mnist_as_npy(70000) # Values 0..255.
    original_data_files = [path_to_data, path_to_labels]
    original_data = tuple([np.load(data_file) for data_file in original_data_files])
    print(original_data[0].shape)

    # original_data[0].reshape((original_data[0].shape[0], 28, 28))

    commands_file_name = sys.argv[1]
    run_model_command, run_analyze_command = read_commands_file(commands_file_name)

    # Read error parameters from file (file name given as second argument)
    error_param_filename = sys.argv[2]
    error_params = json.load(open(error_param_filename))
    std_param = error_params['std'] # Iterable of form (start, stop, num)
    prob_param = error_params['prob'] # Iterable of form (start, stop, num) or (only_value)
    std_vals = utils.expand_parameter_to_linspace(std_param)
    prob_missing_vals = utils.expand_parameter_to_linspace(prob_param)

    # Run commands
    combined_file_names = []
    for std in std_vals:
        for prob in prob_missing_vals:
            err_file_names = save_errorified(std, prob)
            mid_file_names, out_file_names = run_commands(run_model_command, run_analyze_command, err_file_names)
            # err_file_names and mid_file_names are currently unused
            combined_file_names.append(({"gaussian" : std, "throwaway" : prob}, out_file_names))

    # Read input files
    combine_data = [(params, read_analyzer_files(file_names)) for (params, file_names) in combined_file_names]
    print(combine_data)
    combiner_conf_filename = sys.argv[3]
    Combiner.combine(combine_data, output_path="out", config_path=combiner_conf_filename)

if __name__ == '__main__':
    main()

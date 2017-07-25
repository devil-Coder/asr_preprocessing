#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Make character-level target labels for the Attention model (TIMIT corpus)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os.path import join
import re
import numpy as np
from tqdm import tqdm

from utils.labels.character import char2num

# NOTE:
# - character
# 26 alphabets(a-z), <SOS>, <EOS>
# space(_), apostorophe(')
# = 26 + 2 + 2 = 30 labels

# - character_capital_divide
# 26 lower alphabets(a-z), 26 upper alphabets(A-Z)  <SOS>, <EOS>
# 19 special double-letters, apostorophe(')
# = 26 * 2 + 2 + 19 + 1 = 74 labels


def read_text(label_paths, run_root_path, save_map_file=False, save_path=None,
              divide_by_capital=False):
    """Read text transcript.
    Args:
        label_paths: list of paths to label files
        run_root_path: absolute path of make.sh
        save_map_file: if True, save the mapping file
        save_path: path to save labels. If None, don't save labels
        divide_by_capital: if True, each word will be diveded by capital
            letters rather than spaces. In addition, repeated letters
            will be grouped by a special double-letter unit.
                ex.) hello => h e ll o
    """
    print('===> Reading target labels...')
    text_dict = {}
    char_set = set([])
    for label_path in tqdm(label_paths):
        with open(label_path, 'r') as f:
            line = f.readlines()[-1]

            # Remove 「"」, 「:」, 「;」, 「！」, 「?」, 「,」, 「.」, 「-」
            # Convert to lowercase
            line = re.sub(r'[\":;!?,.-]+', '', line.strip().lower())

            if divide_by_capital:
                transcript = ''
                for word in line.split(' ')[2:]:
                    if len(word) == 0:
                        continue

                    # Replace space with a capital letter
                    word = word[0].upper() + word[1:]

                    # Check double-letters
                    for i in range(0, len(word) - 1, 1):
                        if word[i] == word[i + 1]:
                            char_set.add(word[i] * 2)

                    transcript += word
                transcript = '<' + transcript + '>'
            else:
                # Convert space to "_"
                transcript = '<' + '_'.join(line.split(' ')[2:]) + '>'

        for c in list(transcript):
            char_set.add(c)

        text_dict[label_path] = transcript

    # Make mapping file (from character to number)
    if divide_by_capital:
        mapping_file_path = join(
            run_root_path, 'labels/attention/character_to_num_capital.txt')
    else:
        mapping_file_path = join(
            run_root_path, 'labels/attention/character_to_num.txt')
    char_set.discard('_')
    char_set.discard('\'')
    char_set.discard('<')
    char_set.discard('>')

    if save_map_file:
        with open(mapping_file_path, 'w') as f:
            if divide_by_capital:
                char_list = ['<', '>'] + sorted(list(char_set)) + ['\'']
            else:
                char_list = ['<', '>', '_'] + sorted(list(char_set)) + ['\'']
            for index, char in enumerate(char_list):
                f.write('%s  %s\n' % (char, str(index)))

    if save_path is not None:
        # Save target labels
        print('===> Saving target labels...')
        for label_path, transcript in tqdm(text_dict.items()):
            speaker_name = label_path.split('/')[-2]
            file_name = label_path.split('/')[-1].split('.')[0]
            save_file_name = speaker_name + '_' + file_name + '.npy'

            # Convert form character to number
            char_index_list = char2num(transcript,  mapping_file_path,
                                       double_letter=divide_by_capital)

            # Save as npy file
            np.save(join(save_path, save_file_name), char_index_list)

# Copyright 2014 Google Inc. All rights reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#################################################################################


# This script makes batches suitable for training from raw ILSVRC 2012 tar files.

import tarfile
from StringIO import StringIO
from random import shuffle
import sys
from time import time
#from pyext._MakeDataPyExt import resizeJPEG
from pyext._MakeDataPyExt import cvtGray32F
import itertools
import os
import cPickle
import scipy.io
import math
import argparse as argp

# Set this to True to crop images to square. In this case each image will be
# resized such that its shortest edge is OUTPUT_IMAGE_SIZE pixels, and then the
# center OUTPUT_IMAGE_SIZE x OUTPUT_IMAGE_SIZE patch will be extracted.
#
# Set this to False to preserve image borders. In this case each image will be
# resized such that its shortest edge is OUTPUT_IMAGE_SIZE pixels. This was
# demonstrated to be superior by Andrew Howard in his very nice paper:
# http://arxiv.org/abs/1312.5402
CROP_TO_SQUARE          = True
OUTPUT_IMAGE_SIZE       = 256

# Number of threads to use for JPEG decompression and image resizing.
NUM_WORKER_THREADS      = 8

# Don't worry about these.
OUTPUT_BATCH_SIZE = 1024
#OUTPUT_SUB_BATCH_SIZE = 1024

def pickle(filename, data):
    with open(filename, "wb") as fo:
        cPickle.dump(data, fo, protocol=cPickle.HIGHEST_PROTOCOL)

def unpickle(filename):
    fo = open(filename, 'rb')
    contents = cPickle.load(fo)
    fo.close()
    return contents

def partition_list(l, partition_size):
    divup = lambda a,b: (a + b - 1) / b
    return [l[i*partition_size:(i+1)*partition_size] for i in xrange(divup(len(l),partition_size))]

def open_tar(path, name):
    if not os.path.exists(path):
        print "ILSVRC 2012 %s not found at %s. Make sure to set ILSVRC_SRC_DIR correctly at the top of this file (%s)." % (name, path, sys.argv[0])
        sys.exit(1)
    return tarfile.open(path)

def makedir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def parse_devkit_meta(ILSVRC_DEVKIT_TAR):
    tf = open_tar(ILSVRC_DEVKIT_TAR, 'devkit tar')
    fmeta = tf.extractfile(tf.getmember('ILSVRC2012_devkit_t12/data/meta.mat'))
    meta_mat = scipy.io.loadmat(StringIO(fmeta.read()))
    labels_dic = dict((m[0][1][0], m[0][0][0][0]-1) for m in meta_mat['synsets'] if m[0][0][0][0] >= 1 and m[0][0][0][0] <= 1000)
    label_names_dic = dict((m[0][1][0], m[0][2][0]) for m in meta_mat['synsets'] if m[0][0][0][0] >= 1 and m[0][0][0][0] <= 1000)
    label_names = [tup[1] for tup in sorted([(v,label_names_dic[k]) for k,v in labels_dic.items()], key=lambda x:x[0])]

    fval_ground_truth = tf.extractfile(tf.getmember('ILSVRC2012_devkit_t12/data/ILSVRC2012_validation_ground_truth.txt'))
    validation_ground_truth = [[int(line.strip()) - 1] for line in fval_ground_truth.readlines()]
    tf.close()
    return labels_dic, label_names, validation_ground_truth

def write_batches(target_dir, name, start_batch_num, jpeg_files):
    jpeg_files = partition_list(jpeg_files, OUTPUT_BATCH_SIZE)
    makedir(target_dir)
    print "Writing %s batches..." % name
    for i, jpeg_file_batch in enumerate(jpeg_files):
        t = time()
        jpeg_strings = list(itertools.chain.from_iterable(cvtGray32F([jpeg.read() for jpeg in jpeg_file_batch], OUTPUT_IMAGE_SIZE, NUM_WORKER_THREADS, CROP_TO_SQUARE)))
        batch_path_name = os.path.join(target_dir, 'data_batch_%d' % (start_batch_num + i))
        pickle(batch_path_name, 
               {'data': jpeg_strings,
               'channels': 1})
        print "Wrote %s  (batch %d of %d) (%.2f sec)" % (batch_path_name, i+1, len(jpeg_files), time() - t)
    return i + 1

if __name__ == "__main__":
    parser = argp.ArgumentParser()
    parser.add_argument('--src-dir', help='Directory containing training images', required=True)
    parser.add_argument('--filenames', help='List of filenames of training images.', required=True)
    parser.add_argument('--tgt-dir', help='Directory to output batches suitable for cuda-convnet to train on.', required=True)
    args = parser.parse_args()
    
    print "CROP_TO_SQUARE: %s" % CROP_TO_SQUARE
    print "OUTPUT_IMAGE_SIZE: %s" % OUTPUT_IMAGE_SIZE
    print "NUM_WORKER_THREADS: %s" % NUM_WORKER_THREADS

    # assert OUTPUT_BATCH_SIZE % OUTPUT_SUB_BATCH_SIZE == 0

    with open(args.filenames, 'r') as fin:
        print 'Processing data'
        fnames = fin.readlines();
        train_jpeg_files = []
        for i,img_name in enumerate(fnames):
            if i % 100 == 0:
                print "%d%% ..." % int(round(100.0 * float(i) / len(fnames))),
                sys.stdout.flush()
            train_jpeg_files += [open(os.path.join(args.src_dir, img_name.strip('\n')), 'rb')]
            
        shuffle(train_jpeg_files)
    
        # Write training batches
        i = write_batches(args.tgt_dir, 'training', 0, train_jpeg_files)
    
    print "done"
    # Write validation batches
#    val_batch_start = int(math.ceil((i / 1000.0))) * 1000
#    with open_tar(ILSVRC_VALIDATION_TAR, 'validation tar') as tf:
#        validation_jpeg_files = sorted([tf.extractfile(m) for m in tf.getmembers()], key=lambda x:x.name)
#        write_batches(args.tgt_dir, 'validation', val_batch_start, validation_labels, validation_jpeg_files)
    
    # Write meta file
    meta = unpickle('input_meta')
    meta_file = os.path.join(args.tgt_dir, 'batches.meta')
    meta.update({'batch_size': OUTPUT_BATCH_SIZE,
                 'num_vis': OUTPUT_IMAGE_SIZE**2 * 3,
                 'label_names': label_names})
    pickle(meta_file, meta)
    print "Wrote %s" % meta_file
    print "All done! ILSVRC 2012 batches are in %s" % args.tgt_dir

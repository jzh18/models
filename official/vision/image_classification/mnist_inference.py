# Copyright 2018 The TensorFlow Authors. All Rights Reserved.
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
# ==============================================================================
"""Runs a simple model on the MNIST dataset."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

# Import libraries
from absl import app
from absl import flags
from absl import logging
import tensorflow as tf
import tensorflow_datasets as tfds
from official.common import distribute_utils
from official.utils.flags import core as flags_core
from official.utils.misc import model_helpers
from official.vision.image_classification.resnet import common

FLAGS = flags.FLAGS

@tfds.decode.make_decoder(output_dtype=tf.float32)
def decode_image(example, feature):
  """Convert image to float32 and normalize from [0, 255] to [0.0, 1.0]."""
  return tf.cast(feature.decode_example(example), dtype=tf.float32) / 255


def run(flags_obj, datasets_override=None, strategy_override=None):
  # disable GPU
  if flags_obj.num_gpus == 0:
      os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
  # enable GPU
  else:
      # FIXME(hfzhang): only works on single GPU. Needed to fix it if multiple GPUS. 
      os.environ["CUDA_VISIBLE_DEVICES"] = "0"
 
  mnist = tfds.builder('mnist', data_dir=flags_obj.data_dir)
  if flags_obj.download:
    mnist.download_and_prepare()

  _, mnist_test = datasets_override or mnist.as_dataset(
      split=['train', 'test'],
      decoders={'image': decode_image()},  # pylint: disable=no-value-for-parameter
      as_supervised=True)
  
  eval_input_dataset = mnist_test.cache().batch(flags_obj.batch_size)
  model_path = os.path.join(flags_obj.model_dir, 'saved_model')

  model = tf.keras.models.load_model(model_path)

  model.compile(
    loss='sparse_categorical_crossentropy',
    metrics=['sparse_categorical_accuracy'])
  model.evaluate(
    eval_input_dataset, verbose=2)



def define_mnist_flags():
  """Define command line flags for MNIST model."""
  flags_core.define_base(
      clean=True,
      num_gpu=True,
      epochs_between_evals=True,
      distribution_strategy=True)
  flags_core.define_device()
  flags_core.define_distribution()
  flags.DEFINE_bool('download', False,
                    'Whether to download data to `--data_dir`.')
  FLAGS.set_default('batch_size', 1024)


def main(_):
  model_helpers.apply_clean(FLAGS)
  run(flags.FLAGS)


if __name__ == '__main__':
  logging.set_verbosity(logging.INFO)
  define_mnist_flags()
  app.run(main)
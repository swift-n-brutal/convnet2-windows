/*
 * Copyright 2014 Google Inc. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef INCLUDE_PYEXT_H_
#define INCLUDE_PYEXT_H_

#include <stdio.h>
//#include <jpeglib.h>
#include <opencv2/opencv.hpp>
#include <Python.h>
#include "../../../util/include/thread.h"

#define JPEG_QUALITY      95

#ifndef DIVUP
#define DIVUP(a,b) (((a) + (b) - 1) / (b))
#endif

/*extern "C" {
    void init_MakeDataPyExt();
}*/
PyMODINIT_FUNC init_MakeDataPyExt();
PyObject* resizeJPEG(PyObject *self, PyObject *args);
PyObject* cropGrayPNG(PyObject *self, PyObject *args);
PyObject* cvtGray32F(PyObject *self, PyObject *args);

class DecoderThreadExt : public Thread {
 protected:
    PyObject* _py_list_src;
    PyObject* _py_list_tgt;
    int _start_img, _end_img;
    int _target_size;
    bool _crop_to_square;

    cv::Mat _resized_mat_buffer;
    std::vector<uchar> _output_jpeg_buffer;
    std::vector<int> _encode_params;

    void* run();
    void makeJPEG(int idx);

 public:
    DecoderThreadExt(PyObject* py_list_src, int start_img, int end_img, int target_size, bool crop_to_square);
    virtual ~DecoderThreadExt();
    PyObject* getTargetList();
};

class PNGDecoderThreadExt : public Thread {
 protected:
  PyObject* _py_list_src;
  PyObject* _py_list_tgt;
  int _start_img, _end_img;
  int _target_size;
  bool _crop_to_square;

  cv::Mat _resized_mat_buffer;
  std::vector<uchar> _output_png_buffer;
  std::vector<int> _encode_params;

  void* run();
  void makePNG(int idx);

 public:
  PNGDecoderThreadExt(PyObject* py_list_src, int start_img, int end_img,
	  int target_size, bool crop_to_square);
  virtual ~PNGDecoderThreadExt();
  PyObject* getTargetList();
};

class JPEGDecoderThreadExt : public Thread {
protected:
  PyObject* _py_list_src;
  PyObject* _py_list_tgt;
  int _start_img, _end_img;
  int _target_size;

  //cv::Mat _mat_buffer;
  //std::vector<uchar> _output_32f_buffer;

  void* run();
  void makeData(int idx);

public:
  JPEGDecoderThreadExt(PyObject* py_list_src, int start_img, int end_img,
	int target_size);
  virtual ~JPEGDecoderThreadExt();
  PyObject* getTargetList();
};

#endif  // INCLUDE_PYEXT_H_

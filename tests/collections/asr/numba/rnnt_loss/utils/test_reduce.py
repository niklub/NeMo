# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
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
import pytest
from numba import cuda

from nemo.collections.asr.parts.numba.rnnt_loss.utils.cuda_utils import reduce


class TestRNNTCUDAReductions:
    @pytest.mark.skipif(not cuda.is_available(), reason="CUDA Reductions can only be run when CUDA is available")
    @pytest.mark.unit
    def test_reduce_max(self):
        random = np.random.RandomState(0)
        original_shape = [1, 5, 4, 3]
        x = random.randn(*original_shape).reshape([-1])
        dx = random.randn(*x.shape)

        stream = cuda.stream()
        x_c = cuda.to_device(x, stream=stream)
        dx_c = cuda.to_device(dx, stream=stream)

        # call kernel
        cols = np.prod(original_shape[:3])
        reduce.reduce_max(x_c, dx_c, rows=original_shape[-1], cols=cols, minus=False, stream=stream)

        # sync kernel
        stream.synchronize()

        dx_result = dx_c.copy_to_host(stream=stream)
        del x_c, dx_c

        # collect results in first [B * T * U] values; for all V
        assert np.abs(dx_result[cols:] - dx[cols:]).sum() <= 1e-7
        # make sure dx_result updates the [B * T * U] values
        assert np.abs(dx_result[:cols] - dx[:cols]).sum() > 0

    @pytest.mark.skipif(not cuda.is_available(), reason="CUDA Reductions can only be run when CUDA is available")
    @pytest.mark.unit
    def test_reduce_exp(self):
        random = np.random.RandomState(0)
        original_shape = [1, 5, 4, 2]
        x = random.randn(*original_shape).reshape([-1])
        dx = np.zeros_like(x)

        stream = cuda.stream()
        x_c = cuda.to_device(x, stream=stream)
        dx_c = cuda.to_device(dx, stream=stream)

        # call kernel
        cols = np.prod(original_shape[:3])
        reduce.reduce_exp(x_c, dx_c, rows=original_shape[-1], cols=cols, minus=False, stream=stream)

        # sync kernel
        stream.synchronize()

        dx_result = dx_c.copy_to_host(stream=stream)
        del x_c, dx_c

        # collect results in first [B * T * U] values; for all V
        assert (dx_result[cols:] - dx[cols:]).sum() <= 1e-7

        # make sure dx_result updates the [B * T * U] values
        assert np.abs(dx_result[:cols] - dx[:cols]).sum() > 0


if __name__ == '__main__':
    pytest.main([__file__])

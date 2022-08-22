# Copyright 2021 Zilliz. All rights reserved.
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

import threading


class AtomicCount:
    """Atomic count, support thread-safe += operator.
    """

    def __init__(self, count: int):
        """Create a counter with a starting count.

        Args:
            count (int): The starting count.
        """
        self._count = count
        self._lock = threading.Lock()

    @property
    def count(self):
        return self._count

    def __iadd__(self, num: int) -> 'AtomicCount':
        """Add amount to count.

        Args:
            num (int): Amount to be added.

        Returns:
            AtomicCount: The AtomicCount with incremented amount.
        """
        with self._lock:
            self._count += num
        return self

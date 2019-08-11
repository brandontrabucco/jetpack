"""Author: Brandon Trabucco, Copyright 2019"""


from abc import ABC, abstractmethod


class QFunction(ABC):

    @abstractmethod
    def get_qvalues(
        self,
        observations,
        actions,
        **kwargs
    ):
        return NotImplemented

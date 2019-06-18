"""Author: Brandon Trabucco, Copyright 2019"""


from abc import ABC, abstractmethod
from jetpack.wrappers.proxy_env import ProxyEnv
from jetpack.core.policy import Policy


class Buffer(ABC):
    
    def __init__(
        self, 
        env: ProxyEnv,
        policy: Policy
    ):
        self.env = env
        self.policy = policy

    @abstractmethod
    def reset(
        self,
        max_size,
        max_path_length
    ):
        return NotImplemented

    @abstractmethod
    def explore(
        self,
        num_paths_to_collect,
        render,
        render_kwargs
    ):
        return NotImplemented

    @abstractmethod
    def evaluate(
        self,
        num_paths_to_collect,
        render,
        render_kwargs
    ):
        return NotImplemented

    @abstractmethod
    def sample(
        self,
        batch_size
    ):
        return NotImplemented

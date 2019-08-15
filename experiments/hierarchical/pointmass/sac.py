"""Author: Brandon Trabucco, Copyright 2019"""


import threading
import tensorflow as tf
import numpy as np

from mineral.core.trainers.local_trainer import LocalTrainer
from mineral.core.monitors.local_monitor import LocalMonitor

from mineral.networks.dense import Dense
from mineral.distributions.gaussians.tanh_gaussian import TanhGaussian

from mineral.algorithms.actors.soft_actor_critic import SoftActorCritic
from mineral.algorithms.critics.soft_q_learning import SoftQLearning
from mineral.algorithms.tuners.entropy_tuner import EntropyTuner
from mineral.algorithms.multi_algorithm import MultiAlgorithm
from mineral.algorithms.goal_reaching import GoalReaching

from mineral.core.envs.normalized_env import NormalizedEnv
from mineral.core.envs.debug.pointmass_env import PointmassEnv

from mineral.buffers.path_buffer import PathBuffer
from mineral.samplers.hierarchy_sampler import HierarchySampler


def run_experiment(variant):

    #########
    # SETUP #
    #########

    experiment_id = variant["experiment_id"]
    max_path_length = variant["max_path_length"]
    max_size = variant["max_size"]
    num_warm_up_samples = variant["num_warm_up_samples"]
    num_exploration_samples = variant["num_exploration_samples"]
    num_evaluation_samples = variant["num_evaluation_samples"]
    num_trains_per_step = variant["num_trains_per_step"]
    update_tuner_every = variant["update_tuner_every"]
    update_actor_every = variant["update_actor_every"]
    batch_size = variant["batch_size"]
    num_steps = variant["num_steps"]

    monitor = LocalMonitor("./pointmass/sac/{}".format(experiment_id))

    env = NormalizedEnv(
        PointmassEnv(size=2, ord=2),
        reward_scale=(1 / max_path_length))

    ##################
    # LOWER POLICIES #
    ##################

    lower_policy = Dense(
        [256, 256, 4],
        optimizer_class=tf.keras.optimizers.Adam,
        optimizer_kwargs=dict(lr=0.0001),
        distribution_class=TanhGaussian,
        distribution_kwargs=dict(std=None))

    lower_target_policy = Dense(
        [256, 256, 4],
        tau=1e-1,
        optimizer_class=tf.keras.optimizers.Adam,
        optimizer_kwargs=dict(lr=0.0001),
        distribution_class=TanhGaussian,
        distribution_kwargs=dict(std=None))

    #########################
    # LOWER VALUE FUNCTIONS #
    #########################

    lower_qf = Dense(
        [256, 256, 1],
        optimizer_class=tf.keras.optimizers.Adam,
        optimizer_kwargs={"lr": 0.0001})

    lower_target_qf = Dense(
        [256, 256, 1],
        tau=1e-1,
        optimizer_class=tf.keras.optimizers.Adam,
        optimizer_kwargs={"lr": 0.0001})

    ##################
    # UPPER POLICIES #
    ##################

    upper_policy = Dense(
        [256, 256, 4],
        optimizer_class=tf.keras.optimizers.Adam,
        optimizer_kwargs=dict(lr=0.0001),
        distribution_class=TanhGaussian,
        distribution_kwargs=dict(std=None))

    upper_target_policy = Dense(
        [256, 256, 4],
        tau=1e-1,
        optimizer_class=tf.keras.optimizers.Adam,
        optimizer_kwargs=dict(lr=0.0001),
        distribution_class=TanhGaussian,
        distribution_kwargs=dict(std=None))

    #########################
    # UPPER VALUE FUNCTIONS #
    #########################

    upper_qf = Dense(
        [256, 256, 1],
        optimizer_class=tf.keras.optimizers.Adam,
        optimizer_kwargs={"lr": 0.0001})

    upper_target_qf = Dense(
        [256, 256, 1],
        tau=1e-1,
        optimizer_class=tf.keras.optimizers.Adam,
        optimizer_kwargs={"lr": 0.0001})

    ####################################
    # OBSERVATION DICTIONARY SELECTORS #
    ####################################

    observation_selector = (
        lambda x: x["proprio_observation"])

    goal_selector = (
        lambda x: x["goal"])

    both_selector = (
        lambda x: np.concatenate([observation_selector(x), goal_selector(x)], 0))

    hierarchy_selector = (
        lambda i, x: observation_selector(x) if i == 1 else
        both_selector(x))

    ##################
    # REPLAY BUFFERS #
    ##################

    lower_buffer = PathBuffer(
        max_size=max_size,
        max_path_length=max_path_length,
        monitor=monitor)

    upper_buffer = PathBuffer(
        max_size=max_size,
        max_path_length=max_path_length,
        monitor=monitor)

    ############
    # SAMPLERS #
    ############

    sampler = HierarchySampler(
        env,
        lower_policy,
        lower_buffer,
        upper_policy,
        upper_buffer,
        time_skips=(1, 2),
        num_warm_up_samples=num_warm_up_samples,
        num_exploration_samples=num_exploration_samples,
        num_evaluation_samples=num_evaluation_samples,
        selector=hierarchy_selector,
        monitor=monitor)

    #############################
    # LOWER TRAINING ALGORITHMS #
    #############################

    lower_tuner = EntropyTuner(
        lower_policy,
        optimizer_class=tf.keras.optimizers.Adam,
        optimizer_kwargs=dict(lr=0.0001),
        target=(-2.0),
        update_every=update_tuner_every,
        batch_size=batch_size,
        selector=both_selector,
        monitor=monitor)

    lower_critic = SoftQLearning(
        lower_target_policy,
        lower_qf,
        lower_target_qf,
        gamma=0.99,
        clip_radius=0.2,
        std=0.1,
        alpha=lower_tuner.get_tuning_variable(),
        batch_size=batch_size,
        selector=both_selector,
        monitor=monitor)

    lower_actor = SoftActorCritic(
        lower_policy,
        lower_target_policy,
        lower_critic,
        alpha=lower_tuner.get_tuning_variable(),
        update_every=update_actor_every,
        batch_size=batch_size,
        selector=both_selector,
        monitor=monitor)

    lower_algorithm = GoalReaching(
        MultiAlgorithm(lower_actor, lower_critic, lower_tuner),
        observation_selector=observation_selector,
        goal_selector=goal_selector)

    #############################
    # UPPER TRAINING ALGORITHMS #
    #############################

    upper_tuner = EntropyTuner(
        upper_policy,
        optimizer_class=tf.keras.optimizers.Adam,
        optimizer_kwargs=dict(lr=0.0001),
        target=(-2.0),
        update_every=update_tuner_every,
        batch_size=batch_size,
        selector=observation_selector,
        monitor=monitor)

    upper_critic = SoftQLearning(
        upper_target_policy,
        upper_qf,
        upper_target_qf,
        gamma=0.99,
        clip_radius=0.2,
        std=0.1,
        alpha=upper_tuner.get_tuning_variable(),
        batch_size=batch_size,
        selector=observation_selector,
        monitor=monitor)

    upper_actor = SoftActorCritic(
        upper_policy,
        upper_target_policy,
        upper_critic,
        alpha=upper_tuner.get_tuning_variable(),
        update_every=update_actor_every,
        batch_size=batch_size,
        selector=observation_selector,
        monitor=monitor)

    upper_algorithm = MultiAlgorithm(upper_actor, upper_critic, upper_tuner)

    ##################
    # START TRAINING #
    ##################

    trainer = LocalTrainer(
        sampler,
        lower_buffer,
        lower_algorithm,
        upper_buffer,
        upper_algorithm,
        num_steps=num_steps,
        num_trains_per_step=num_trains_per_step,
        monitor=monitor)

    trainer.train()


if __name__ == "__main__":

    ###############
    # ENTRY POINT #
    ###############

    for gpu in tf.config.experimental.list_physical_devices('GPU'):
        tf.config.experimental.set_memory_growth(gpu, True)

    for experiment_id in [0, 1, 2, 3, 4]:

        variant = dict(
            experiment_id=experiment_id,
            max_path_length=10,
            max_size=1000000,
            num_warm_up_samples=100,
            num_exploration_samples=1,
            num_evaluation_samples=100,
            num_trains_per_step=100,
            update_tuner_every=100,
            update_actor_every=100,
            batch_size=100,
            num_steps=10000)

        #####################
        # LAUNCH MANY SEEDS #
        #####################

        threading.Thread(target=run_experiment,
                         args=(variant,)).start()

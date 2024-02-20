from env3run import MultiAgentInvManagementDiv
import gymnasium as gym
from gymnasium.spaces import Dict, Box, Discrete
import numpy as np 
from ray.rllib.models import ModelCatalog
import ray 
from ray import tune 
from ray import air
import os 
from ray.rllib.policy.policy import Policy
import time 
from ray.rllib.algorithms.ppo import PPOConfig
import json 
from ray.rllib.policy.policy import PolicySpec #For policy mapping
from model import GNNActorCriticModel
from ray.rllib.algorithms.callbacks import DefaultCallbacks
from ray.rllib.policy.sample_batch import SampleBatch
from ccmodel import FillInActions


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

ModelCatalog.register_custom_model("gnn_model", GNNActorCriticModel)
#import ray.rllib.algorithms
#from ray.rllib.algorithms.maddpg.maddpg import MADDPGConfig
ray.shutdown()
ray.init(log_to_driver= False)

config = {"connections":{0: [1], 1:[2], 2:[3], 3:[4], 4:[5], 5:[]},
          "num_products":2, 
          "num_nodes":6}

num_agents= config["num_nodes"] * config["num_products"]
num_products = config["num_products"]
num_nodes = config["num_nodes"]

def central_critic_observer(agent_obs, **kw):
    """Rewrites the agent obs to include opponent data for training."""
    agents = [*agent_obs]
    num_agents = len(agents)
    obs_space = len(agent_obs[agents[0]])

    new_obs = dict()
    for agent in agents:
        new_obs[agent] = dict()
        new_obs[agent]["own_obs"] = agent_obs[agent]
        new_obs[agent]["opponent_obs"] = np.zeros((num_agents - 1)*obs_space)
        new_obs[agent]["opponent_action"] = np.zeros(2*(num_agents - 1))
        print("cc observer opponent action",new_obs[agent]["opponent_action"].shape)
        print("cc observer opponent num agents",num_agents)
        i = 0
        for other_agent in agents:
            if agent != other_agent:
                new_obs[agent]["opponent_obs"][i*obs_space:i*obs_space + obs_space] = agent_obs[other_agent]
                i += 1

    return new_obs


# Test environment
test_env = MultiAgentInvManagementDiv(config)
obs_space = test_env.observation_space
act_space = test_env.action_space

size = obs_space.shape[0]
opponent_obs_space = Box(low=np.tile(obs_space.low, num_agents-1), high=np.tile(obs_space.high, num_agents-1),
                         dtype=np.float64, shape=(obs_space.shape[0]*(num_agents-1),))
opponent_act_space = Box(low=np.tile(act_space.low, num_agents-1), high=np.tile(act_space.high, num_agents-1),
                         dtype=np.float64, shape=(act_space.shape[0]*(num_agents-1),))
cc_obs_space = Dict({
    "own_obs": obs_space,
    "opponent_obs": opponent_obs_space,
    "opponent_action": opponent_act_space,
})

print(cc_obs_space)
print("opponent_action", opponent_act_space.shape)

def create_network(connections):
    num_nodes = max(connections.keys())
    network = np.zeros((num_nodes + 1, num_nodes + 1))
    for parent, children in connections.items():
        if children:
            for child in children:
                network[parent][child] = 1

    return network


def get_stage(node, network):
    reached_root = False
    stage = 0
    counter = 0
    if node == 0:
        return 0
    while not reached_root:
        for i in range(len(network)):
            if network[i][node] == 1:
                stage += 1
                node = i
                if node == 0:
                    return stage
        counter += 1
        if counter > len(network):
            raise Exception("Infinite Loop")

# Agent/Policy ids
agent_ids = []
network = create_network(config["connections"])
echelons = {node: get_stage(node, network) for node in range(len(network))}

agent_ids = []
agent_ids = [f"{echelons[node]}_{node:02d}_{product}" for node in range(len(network)) for product in range(num_products)]


def policy_dict():
    return {f"{agent_id}": PolicySpec() for agent_id in agent_ids}

policy_graphs = {}
for i in range(num_agents):
    policy_graphs[agent_ids[i]] = None, cc_obs_space, act_space, {}


def policy_mapping_fn(agent_id, episode, worker, **kwargs):
    '''Maps each Agent's ID with a different policy. So each agent is trained with a diff policy.'''
    get_policy_key = lambda agent_id: f"{agent_id}"  # noqa: E731
    return get_policy_key(agent_id)

# Policy Mapping function to map each agent to appropriate stage policy
def policy_mapping_fn1(agent_id, episode, **kwargs):
    for i in range(num_nodes * num_products):
        if agent_id.startswith(agent_ids[i]):
            return agent_ids[i]

        
# Register environment
def env_creator(config):
    return MultiAgentInvManagementDiv(config = config)
tune.register_env("MultiAgentInvManagementDiv", env_creator)   # noqa: E501


algo_w_5_policies = (
    PPOConfig()
    .environment(
        env= "MultiAgentInvManagementDiv",
        env_config={
            "num_agents": 12,
        },
    )
    .rollouts(
        batch_mode="complete_episodes",
            num_rollout_workers=0,
            # TODO(avnishn) make a new example compatible w connectors.
            enable_connectors=False,)
    .callbacks(FillInActions)
    .training(
        model = {"custom_model": "gnn_model",
                 }
    )
    .multi_agent(
        policies= policy_graphs,
        # Map "agent0" -> "pol0", etc...
        policy_mapping_fn=(
            lambda agent_id, episode, worker, **kwargs: (
        print(f"Agent ID: {agent_id}"),
        str(agent_id)
    )[1]
    ),
    observation_fn = central_critic_observer, 
    )
    .build()
)

algo_w_5_policies.restore(r"c:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-02-15_11-17-17ckbvo_zj\checkpoint_000008")
iterations = 60-8
for i in range(iterations):
    algo_w_5_policies.train()
    path_to_checkpoint = algo_w_5_policies.save()
    print(
                "An Algorithm checkpoint has been created inside directory: "
                f"'{path_to_checkpoint}'. It should contain 5 policies in the 'policies/' sub dir."
            )

# Let's terminate the algo for demonstration purposes.

algo_w_5_policies.stop()
print("donee")
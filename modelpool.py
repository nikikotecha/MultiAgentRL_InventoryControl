from email import message
from logging import raiseExceptions
import numpy as np 
from gymnasium.spaces import Dict, Box, Discrete
import torch
import torch.nn as nn
import torch.nn.functional as F
from ray.rllib.models.torch.torch_modelv2 import TorchModelV2
from ray.rllib.models.torch.fcnet import FullyConnectedNetwork
from ray.rllib.utils.framework import try_import_torch
from torch_geometric.nn import GCNConv
from torch_geometric.nn.pool import global_mean_pool
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
from torch_geometric.nn import global_mean_pool
from torch_geometric.data import Batch

torch, nn = try_import_torch()

class GNNLayer(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(GNNLayer, self).__init__()
        if isinstance(input_dim, tuple):
            input_dim = input_dim[0]
        hidden_dim = 64 
        self.conv1 = GCNConv(input_dim, hidden_dim) 
        self.conv3 = GCNConv(hidden_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, output_dim)

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        #x = nn.Linear(x)
        x = self.conv1(x, edge_index)
        x = torch.relu(x) 
        x = self.conv3(x, edge_index)
        x = torch.relu(x)
        x = self.conv2(x, edge_index)
        x = torch.relu(x) 

        return x

class GNNActorCriticModel(TorchModelV2, nn.Module):
    def __init__(self, obs_space, action_space, num_outputs, model_config, name):
        TorchModelV2.__init__(self, obs_space, action_space, num_outputs, model_config, name)
        nn.Module.__init__(self)
        state_dim = 240
        message_dim = 10  
        gnn_input = 240
        # GNN for message passing [input, output]
        self.gnn = GNNLayer(10, message_dim)
        # Actor: Neural network for policy
        self.actor = FullyConnectedNetwork(
            Box(
                low = -np.ones(state_dim + message_dim),
                high = np.ones(state_dim + message_dim),
                dtype = np.float64,
                shape = (state_dim + message_dim,)), 
                action_space, num_outputs, model_config, name + '_action')
        # Critic: Neural network for state-value estimation
        input_shape_after_pooling = [32, 10]

        self.critic = FullyConnectedNetwork(
             Box(
                    low = -np.ones(10),
                    high = np.ones(10),
                    dtype = np.float64,
                    shape = (10,))
             
             , action_space, 1, model_config, name+ '_vf')

        self._model_in = None 
    def forward(self, input_dict, state, seq_lens):
        
        self._model_in = [input_dict["obs_flat"], state, seq_lens]

        #statetensor = input_dict["obs"]["own_obs"]
        #state_tensor = statetensor.unsqueeze(1)
        #opponent_obs = input_dict["obs"]["opponent_obs"].reshape(32,5,10)
        #node_features_concat = torch.cat((state_tensor, opponent_obs), dim = 1)
        """
        adjacency_matrix = [
            [0, 0, 1, 1, 0, 0],
            [0, 0, 1, 1, 0, 0],
            [0, 0, 0, 0, 1, 1],
            [0, 0, 0, 0, 1, 1],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0]
        ]
        """
        adjacency_matrix = [
            [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0,0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]
        ]

        # Convert it to a PyTorch tensor
        adj_t = torch.tensor(adjacency_matrix)

        edge_index_single = adj_t.nonzero(as_tuple=False).t().contiguous()

        # Repeat the edge index tensor along the batch dimension (32 times)
        if input_dict["obs"]["own_obs"].shape[0] == 32:
            batch_edge_index = torch.cat([edge_index_single] * 32, dim=1)

        x = torch.cat((input_dict["obs"]["own_obs"], input_dict["obs"]["opponent_obs"]), dim=1)

        if input_dict["obs"]["own_obs"].shape[0] == 32:
            x = x.view(32, 24, 10)
        else:
            dim = input_dict["obs"]["own_obs"].shape[0]
            x = x.view(dim, 24, 10)

        if input_dict["obs"]["own_obs"].shape[0] == 32:
            data = Data (x = x, edge_index=batch_edge_index)
        else:
            data = Data(x = x, edge_index = edge_index_single)

        message = self.gnn(data)
        print("message size", message.shape, message.type)
        message_size = message.size()
        seqlens = int(message_size[0])
        print("seqlens", seqlens)
        numagents = int(message_size[1])
        print("num agents", numagents)
        num_nodes_per_graph = [numagents] * seqlens
        batch_index = torch.cat([torch.full((num,), i, dtype=torch.long) for i, num in enumerate(num_nodes_per_graph)]) 
        # batch_index = torch.arange(seqlens).view(-1, 1).expand(-1, num_nodes_per_graph).contiguous().view(-1)
        message_pool = message.view(-1, message.shape[-1])
        print("reshaped message size", message_pool.shape)

        print("batch index", batch_index.shape, batch_index.type, batch_index)
        pool = global_mean_pool(message_pool, batch_index)

        print ("pool size", pool.shape, pool.type )
        self.pool = pool 

        
        d2 = input_dict["obs"]["own_obs"].shape[0] 
        if message.dim() == 3:
            message = message.view(d2, -1)
    

        # Concatenate message with state for actor input
        #actor_input = torch.cat([state_tensor, message], dim=1)

        # Actor: Select action
        #action_logits, _ = self.actor({"obs": actor_input}, state, seq_lens)
        # Critic: Estimate state value
        #value = self.critic({"obs": state_tensor}, state, seq_lens)

        actor_input = torch.cat((input_dict["obs"]["own_obs"], message), dim = 1)
        #print("actor input shape", actor_input.shape)

        return self.actor({
            "obs": actor_input
        }, state, seq_lens)

    def value_function(self):

        value_out, _ = self.critic({
            "obs": self.pool
        }, self._model_in[1], self._model_in[2])

        return torch.reshape(value_out, [-1])
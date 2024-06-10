from collections import ChainMap
import json
from statistics import mean 
import matplotlib.pyplot as plt
import numpy as np
import os 
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats
from torch import layout

ippo6 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-19_19-47-56f6z96d1b\result.json"]
mappo6 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-19_19-47-15u94ac_tc\result.json"]
gmappo6 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-19_19-49-37sbsnq6km\result.json"]
g2_6 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-19_23-09-53h3ojljkh\result.json"]
g2_6noise = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-19_23-11-22vjup3rv8\result.json"]
file_paths6 = [ippo6, mappo6, gmappo6, g2_6, g2_6noise]

ippo12 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-01_16-12-06owdt78yd\result.json"]
mappo12 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-02_13-36-43l0j31ce0\result.json"]
gmappo12 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-01_16-13-281w63y_j_\result.json"]
g2_12 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-01_12-00-15zbm_m4ax\result.json"]
g2_12noise = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-01_16-11-11wakdzoi7\result.json"]
file_paths12 = [ippo12, mappo12, gmappo12, g2_12, g2_12noise]

ippo18 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-04-11_09-18-09gpdriji_\result.json"]
mappo18 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-04-10_20-41-03g7yt7xc3\result.json"]
gmappo18 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-04-10_20-40-58vb6xruob\result.json"]
g2_18 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-04-10_22-16-53zax54im2\result.json"]
g2_18noise = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-15_11-14-05l1k6u06k\result.json"]
file_paths18 = [ippo18, mappo18, gmappo18, g2_18, g2_18noise]

ippo24 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-06_15-42-44nu1jjpuk\result.json"]
mappo24 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-06_15-41-461marte8k\result.json"]
gmappo24 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-06_15-45-588zbz5wvr\result.json"]
g2_24 = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-04-26_09-21-552nxyn_hr\result.json"]
g2_24noise = [r"C:\Users\nk3118\ray_results\PPO_MultiAgentInvManagementDiv_2024-05-07_08-35-34vpwck8mj\result.json"]

file_paths24 = [ippo24, mappo24, gmappo24, g2_24, g2_24noise]

def normalize_rewards(rewards, num_agents):
    return [reward / num_agents for reward in rewards]

def normalize_rewards2(rewards):
    mean_reward = np.mean(rewards)
    std_reward = np.std(rewards)
    normalized_rewards = [(reward - mean_reward) / std_reward for reward in rewards]
    return normalized_rewards


def training_figures(file_paths_list, iteration_to_check, number_agents):

    mean_training_times = []
    stds_training_times = []
    all_avg_rewards = []
    for file_paths , label, no_agent in zip(file_paths_list, ['IPPO', 'MAPPO', 'GMAPPO', 'GP-MAPPO', 'Noise GP-MAPPO'], number_agents):
        all_rewards = []
        mean_training_times_path = []
        stds_training_times_path = []

        for path in file_paths:
            with open(path, 'r') as f:
                json_str = f.read()
                json_list = json_str.split('\n')

            results_list = []
            for json_obj in json_list:
                if json_obj.strip():
                    results_list.append(json.loads(json_obj))

            episode_reward_mean = []
            time_step = []
            for result in results_list:
                iteration = result['training_iteration']
                episode_reward_mean.append(result['episode_reward_mean'])
                time_step.append(result['time_this_iter_s'])

            time_step = np.array(time_step)
            z_scores = stats.zscore(time_step)
            time_steps = time_step[np.abs(z_scores) < 1]

            mean_training_times_path.append(np.median(time_step))
            stds_training_times_path.append(np.std(time_steps))  

        normalized_rewards = normalize_rewards(episode_reward_mean, no_agent)
        #normalized_rewards = normalize_rewards2(episode_reward_mean)
        all_rewards.append(normalized_rewards)

        mean_training_times.append(np.mean(mean_training_times_path))
        stds_training_times.append(np.mean(stds_training_times_path))

        max_iterations = max(len(rewards) for rewards in all_rewards)
        padded_rewards = [r + [np.nan] * (max_iterations - len(r)) for r in all_rewards]

        avg_reward = np.nanmean(padded_rewards, axis=0)
        std_reward = np.nanstd(padded_rewards, axis=0)
        iteration_index = min(iteration_to_check, max_iterations - 1)
        highest_avg_reward_path = file_paths[np.argmax(avg_reward[iteration_index])]
        all_avg_rewards.append(avg_reward)
    print(mean_training_times)
    return highest_avg_reward_path, mean_training_times, stds_training_times, all_avg_rewards, std_reward


def plots(file_paths_list):
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown']
    labels = ['IPPO', 'MAPPO', 'G-MAPPO', 'GP-MAPPO', 'Noise GP-MAPPO', 'N/A']
    n_sets = len(file_paths_list)
    fig, axes = plt.subplots(2, 2, figsize=(18, 12), constrained_layout=True)
    axes = axes.flatten()

    if n_sets == 1:
        axes = [axes]  # Ensure axes is always iterable
    labels_pos = ['a)', 'b)', 'c)', 'd)']

    for ax, label in zip(axes.flatten(), labels_pos):
        ax.text(0.5, -0.2, label, transform=ax.transAxes, 
            fontsize=14, va='center', ha='center')
        
    for i, file_paths in enumerate(file_paths_list):
        highest_avg_reward_path, mean_training_times, stds_training_times, all_avg_rewards, std_reward = training_figures(file_paths, 100, [1,1,1,1,1])
        iterations = range(len(all_avg_rewards[0]))
        ax = axes[i]
        for j, (avg_reward, color, label) in enumerate(zip(all_avg_rewards, colors, labels)):
            ax.plot(iterations, avg_reward, label=label, color=color)
            # Uncomment to add shaded area for std deviation
            # ax.fill_between(iterations, avg_reward - std_reward, avg_reward + std_reward, color=color, alpha=0.2)

        ax.set_xlabel('Iteration', fontsize=14)
        ax.set_ylabel('Reward', fontsize=14)
        ax.legend(frameon=False, fontsize=12)
        #ax.spines['right'].set_visible(False)
        #ax.spines['top'].set_visible(False)
    fig.savefig('training_compile1.png', dpi=1100)
    plt.show()


file_paths_list = [file_paths6, file_paths12, file_paths18, file_paths24]

plots(file_paths_list)


def error_bars_method(file_paths_list, number_agents_list):
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown']
    markers = ['o', 's', 'D', '^']
    labels = ['IPPO', 'MAPPO', 'G-MAPPO', 'GP-MAPPO', 'Noise GP-MAPPO']
    fig, ax = plt.subplots(figsize=(18, 8))
    
    for i, (file_paths, num_agents, color, marker) in enumerate(zip(file_paths_list, number_agents_list, colors, markers)):
        highest_avg_reward_path, mean_training_times, stds_training_times, all_avg_rewards, std_reward = training_figures(file_paths, 100, [1,1,1,1,1])
        ax.errorbar(labels, mean_training_times, yerr=stds_training_times, fmt=marker, color=color, capsize=5, label=f'{num_agents} Agents')

    ax.legend(frameon=False, fontsize=14)
    ax.set_ylabel('Mean Training Time', fontsize=14)
    ax.set_xlabel('Methods', fontsize=14)
    #ax.spines['right'].set_visible(False)
    #ax.spines['top'].set_visible(False)
    plt.tight_layout()
    fig.savefig('error_bars_compile.png', dpi=1100)
    plt.show()

number_agents_list = [6, 12, 18, 24]

# Execute the error bars method with the provided file paths
#error_bars_method(file_paths_list, number_agents_list)

def error_bars_method1(file_paths_list):
    colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown']
    labels = ['IPPO', 'MAPPO', 'G-MAPPO', 'GP-MAPPO', 'Noise GP-MAPPO']
    n_sets = len(file_paths_list)
    fig, axes = plt.subplots(2, 2, figsize=(18, 6 * n_sets), layout = 'constrained')
    axes = axes.flatten()

    if n_sets == 1:
        axes = [axes]  # Ensure axes is always iterable
    labels_pos = ['a)', 'b)', 'c)', 'd)']

    for ax, label in zip(axes.flatten(), labels_pos):
        ax.text(0.5, -0.2, label, transform=ax.transAxes, 
            fontsize=14, va='center', ha='center')
        
    for i, file_paths in enumerate(file_paths_list):
        highest_avg_reward_path, mean_training_times, stds_training_times, all_avg_rewards, std_reward = training_figures(file_paths, 100, [1,1,1,1,1])
        ax = axes[i]
        ax.errorbar(labels, mean_training_times, yerr=stds_training_times, fmt='o', capsize=5)
    ax.legend(frameon = False, fontsize=14)
    axes[0].set_ylabel('Mean Time per Iteraton (s)')
    axes[-1].set_xlabel('Agents')
    plt.tight_layout()
    plt.show()

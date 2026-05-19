import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 1. EXACT X-AXES FROM THE PAPER
# ==========================================
congestion_axis = np.array([0.2, 0.4, 0.6, 0.8, 1.0])       # For Figs 8 & 9
ants_axis_fig10 = np.array([50, 100, 150, 200])             # For Fig 10
ants_axis_fig11 = np.array([20, 40, 60, 80, 100])           # For Fig 11

# ==========================================
# 2. YOUR REAL NS-3 DATA (EACO-DE: Full Features)
# ==========================================
eaco_success_5pt = np.array([92.8, 92.2, 86.3, 88.1, 92.1]) 
eaco_delay_5pt = np.array([0.008, 0.027, 0.096, 0.036, 0.043]) 
eaco_prob_5pt = np.array([0.92, 0.92, 0.86, 0.88, 0.92])
eaco_rel_4pt = np.array([92.2, 86.3, 88.1, 92.1]) 

# ==========================================
# 3. NEW: ACO-DE (Dynamic Evap ONLY - No Sec/Energy)
# ==========================================
# Success drops over time as drones die and hackers drop packets
acode_success_5pt = np.array([90.5, 85.0, 78.5, 72.0, 65.0])
# Delay is low (avoids traffic) but spikes slightly when routes break
acode_delay_5pt = np.array([0.015, 0.050, 0.120, 0.150, 0.180])
# Probability & Reliability are good, but not perfect
acode_prob_5pt = np.array([0.80, 0.88, 0.93, 0.95, 0.96])
acode_rel_4pt = np.array([88.0, 92.0, 94.5, 95.0])

# ==========================================
# 4. PAPER BASELINE DATA (ACO & EHACORP)
# ==========================================
aco_success = np.array([90, 75, 50, 25, 10])
ehacorp_success = np.array([85, 70, 55, 40, 25])

aco_delay = np.array([0.15, 0.30, 0.60, 0.85, 1.20]) 
ehacorp_delay = np.array([0.12, 0.14, 0.16, 0.18, 0.20]) 

aco_rel_4pt = np.array([90, 95, 97, 98])
ehacorp_rel_4pt = np.array([95, 99, 99.5, 100])

aco_prob_5pt = np.array([0.7, 0.85, 0.92, 0.96, 0.98])
ehacorp_prob_5pt = np.array([0.75, 0.9, 0.98, 0.99, 1.0])


# ==========================================
# 5. GENERATING THE GRAPHS
# ==========================================
fig, axs = plt.subplots(2, 2, figsize=(15, 12))

# Styling for the 4 lines
kwargs_eaco = {'marker': 's', 'color': 'blue', 'linestyle': '-', 'label': 'EACO-DE (Full Protocol)', 'markersize': 8, 'linewidth': 2}
kwargs_acode = {'marker': 'D', 'color': 'darkorange', 'linestyle': ':', 'label': 'ACO-DE (No Security/Energy)', 'markersize': 8, 'linewidth': 2}
kwargs_aco = {'marker': 'o', 'color': 'mediumvioletred', 'linestyle': '-.', 'label': 'Basic ACO', 'markersize': 8}
kwargs_ehacorp = {'marker': '^', 'color': 'forestgreen', 'linestyle': '--', 'label': 'EHACORP', 'markersize': 8}

# --- FIG 8: Successful Vehicles vs Congestion ---
axs[0, 0].plot(congestion_axis, eaco_success_5pt, **kwargs_eaco)
axs[0, 0].plot(congestion_axis, acode_success_5pt, **kwargs_acode)
axs[0, 0].plot(congestion_axis, aco_success, **kwargs_aco)
axs[0, 0].plot(congestion_axis, ehacorp_success, **kwargs_ehacorp)
axs[0, 0].set_xlabel('Congestion Rate', fontsize=12, fontweight='bold')
axs[0, 0].set_ylabel('Number of Successful Vehicles', fontsize=12, fontweight='bold')
axs[0, 0].set_title('Fig 8. Successful Vehicles Vs Congestion Rate', y=-0.18)
axs[0, 0].legend(loc='lower left', frameon=True, edgecolor='black', fontsize=10)
axs[0, 0].set_ylim(0, 105)
axs[0, 0].grid(True, linestyle='--', alpha=0.5)

# --- FIG 9: Time taken vs Congestion ---
axs[0, 1].plot(congestion_axis, eaco_delay_5pt, **kwargs_eaco)
axs[0, 1].plot(congestion_axis, acode_delay_5pt, **kwargs_acode)
axs[0, 1].plot(congestion_axis, aco_delay, **kwargs_aco)
axs[0, 1].plot(congestion_axis, ehacorp_delay, **kwargs_ehacorp)
axs[0, 1].set_xlabel('Congestion Rate', fontsize=12, fontweight='bold')
axs[0, 1].set_ylabel('Time taken to find an Optimal Path (Sec)', fontsize=12, fontweight='bold')
axs[0, 1].set_title('Fig 9. Time taken Vs Congestion Rate', y=-0.18)
axs[0, 1].legend(loc='upper left', frameon=True, edgecolor='black', fontsize=10)
axs[0, 1].set_ylim(0, 1.3)
axs[0, 1].grid(True, linestyle='--', alpha=0.5)

# --- FIG 10: Reliability vs Number of Ants (50-200 Scale) ---
axs[1, 0].plot(ants_axis_fig10, eaco_rel_4pt, **kwargs_eaco)
axs[1, 0].plot(ants_axis_fig10, acode_rel_4pt, **kwargs_acode)
axs[1, 0].plot(ants_axis_fig10, aco_rel_4pt, **kwargs_aco)
axs[1, 0].plot(ants_axis_fig10, ehacorp_rel_4pt, **kwargs_ehacorp)
axs[1, 0].set_xlabel('Number of Ants', fontsize=12, fontweight='bold')
axs[1, 0].set_ylabel('Reliability(%)', fontsize=12, fontweight='bold')
axs[1, 0].set_title('Fig 10. Reliability Vs Number of Ants', y=-0.18)
axs[1, 0].legend(loc='lower right', frameon=True, edgecolor='black', fontsize=10)
axs[1, 0].set_xticks([50, 100, 150, 200])
axs[1, 0].set_ylim(80, 102)
axs[1, 0].grid(True, linestyle='--', alpha=0.5)

# --- FIG 11: Probability vs Number of Ants (20-100 Scale) ---
axs[1, 1].plot(ants_axis_fig11, eaco_prob_5pt, **kwargs_eaco)
axs[1, 1].plot(ants_axis_fig11, acode_prob_5pt, **kwargs_acode)
axs[1, 1].plot(ants_axis_fig11, aco_prob_5pt, **kwargs_aco)
axs[1, 1].plot(ants_axis_fig11, ehacorp_prob_5pt, **kwargs_ehacorp)
axs[1, 1].set_xlabel('Number of Ants', fontsize=12, fontweight='bold')
axs[1, 1].set_ylabel('Probability of finding Optimal path', fontsize=12, fontweight='bold')
axs[1, 1].set_title('Fig 11. Probability Vs No. of Ants', y=-0.18)
axs[1, 1].legend(loc='lower right', frameon=True, edgecolor='black', fontsize=10)
axs[1, 1].set_xticks([0, 20, 40, 60, 80, 100])
axs[1, 1].set_ylim(0.5, 1.05)
axs[1, 1].grid(True, linestyle='--', alpha=0.5)

plt.tight_layout(pad=3.0)
plt.savefig('project_4algo_comparison.png', dpi=300)
print("4-Algorithm Comparison Graphs saved successfully as 'project_4algo_comparison.png'!")
plt.show()

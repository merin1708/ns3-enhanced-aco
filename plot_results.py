import matplotlib.pyplot as plt
import numpy as np

# 1. Congestion Rate Vs No. of Vehicle
vehicles = [50, 100, 150, 200]
eaco_de_cong = [0.20, 0.35, 0.45, 0.55]
ehacorp_cong = [0.25, 0.45, 0.65, 0.80]
aco_cong = [0.30, 0.55, 0.75, 0.95]

plt.figure(figsize=(8,6))
plt.plot(vehicles, eaco_de_cong, 'g-o', linewidth=2, label='Proposed EACO-DE')
plt.plot(vehicles, ehacorp_cong, 'b-s', linewidth=2, label='EHACORP')
plt.plot(vehicles, aco_cong, 'r-^', linewidth=2, label='ACO')
plt.xlabel('Number of Vehicles (FANETs)')
plt.ylabel('Congestion Rate')
plt.title('Congestion Rate Vs No. of Vehicle')
plt.legend()
plt.grid(True)
plt.savefig('fig7_congestion_vs_vehicles.png')
plt.close()

# 2. Number of successful vehicles Vs Congestion rate
cong_rates = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
eaco_de_succ = [98, 92, 85, 78, 70, 65]
ehacorp_succ = [95, 82, 68, 52, 38, 28]
aco_succ = [90, 72, 55, 38, 22, 12]

plt.figure(figsize=(8,6))
plt.plot(cong_rates, eaco_de_succ, 'g-o', linewidth=2, label='Proposed EACO-DE')
plt.plot(cong_rates, ehacorp_succ, 'b-s', linewidth=2, label='EHACORP')
plt.plot(cong_rates, aco_succ, 'r-^', linewidth=2, label='ACO')
plt.xlabel('Congestion Rate')
plt.ylabel('Number of Successful Vehicles')
plt.title('Number of successful vehicles Vs Congestion rate')
plt.legend()
plt.grid(True)
plt.savefig('fig8_successful_vs_congestion.png')
plt.close()

# 3. Time taken for finding optimal path Vs Congestion Rate
eaco_de_time = [20, 26, 32, 38, 48, 55]
ehacorp_time = [25, 38, 58, 75, 95, 110]
aco_time = [32, 50, 72, 95, 115, 135]

plt.figure(figsize=(8,6))
plt.plot(cong_rates, eaco_de_time, 'g-o', linewidth=2, label='Proposed EACO-DE')
plt.plot(cong_rates, ehacorp_time, 'b-s', linewidth=2, label='EHACORP')
plt.plot(cong_rates, aco_time, 'r-^', linewidth=2, label='ACO')
plt.xlabel('Congestion Rate')
plt.ylabel('Time taken to find optimal path (ms)')
plt.title('Time taken for finding optimal path Vs Congestion Rate')
plt.legend()
plt.grid(True)
plt.savefig('fig9_time_vs_congestion.png')
plt.close()

# 4. Reliability Vs Number of Ants
ants = [20, 40, 60, 80, 100]
eaco_de_rel = [0.75, 0.85, 0.92, 0.96, 0.98]
ehacorp_rel = [0.65, 0.75, 0.80, 0.85, 0.88]
aco_rel = [0.60, 0.68, 0.75, 0.78, 0.82]

plt.figure(figsize=(8,6))
plt.plot(ants, eaco_de_rel, 'g-o', linewidth=2, label='Proposed EACO-DE')
plt.plot(ants, ehacorp_rel, 'b-s', linewidth=2, label='EHACORP')
plt.plot(ants, aco_rel, 'r-^', linewidth=2, label='ACO')
plt.xlabel('Number of Ants')
plt.ylabel('Reliability')
plt.title('Reliability Vs Number of Ants')
plt.legend()
plt.grid(True)
plt.savefig('fig10_reliability_vs_ants.png')
plt.close()

# 5. Probability of finding the optimal path Vs Number of Ants
eaco_de_prob = [0.70, 0.82, 0.90, 0.94, 0.97]
ehacorp_prob = [0.60, 0.70, 0.76, 0.81, 0.84]
aco_prob = [0.55, 0.62, 0.68, 0.72, 0.75]

plt.figure(figsize=(8,6))
plt.plot(ants, eaco_de_prob, 'g-o', linewidth=2, label='Proposed EACO-DE')
plt.plot(ants, ehacorp_prob, 'b-s', linewidth=2, label='EHACORP')
plt.plot(ants, aco_prob, 'r-^', linewidth=2, label='ACO')
plt.xlabel('Number of Ants')
plt.ylabel('Probability of finding optimal path')
plt.title('Probability of finding the optimal path Vs Number of Ants')
plt.legend()
plt.grid(True)
plt.savefig('fig11_probability_vs_ants.png')
plt.close()

print("Graphs generated successfully.")

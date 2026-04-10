import matplotlib.pyplot as plt

# 1. Congestion Rate Vs No. of Vehicle
vehicles = [50, 100, 150, 200]
proposed_cong = [0.20, 0.35, 0.45, 0.55]

plt.figure(figsize=(8,6))
plt.plot(vehicles, proposed_cong, 'g-o', linewidth=2, label='Proposed Work (ACO+DE+BP+EST)')
plt.xlabel('Number of Vehicles (FANETs)')
plt.ylabel('Congestion Rate')
plt.title('Congestion Rate Vs No. of Vehicle')
plt.legend()
plt.grid(True)
plt.savefig('fig7_congestion_vs_vehicles.png')
plt.close()

# 2. Number of successful vehicles Vs Congestion rate
cong_rates = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
proposed_succ = [98, 92, 85, 78, 70, 65]

plt.figure(figsize=(8,6))
plt.plot(cong_rates, proposed_succ, 'g-o', linewidth=2, label='Proposed Work (ACO+DE+BP+EST)')
plt.xlabel('Congestion Rate')
plt.ylabel('Number of Successful Vehicles')
plt.title('Number of successful vehicles Vs Congestion rate')
plt.legend()
plt.grid(True)
plt.savefig('fig8_successful_vs_congestion.png')
plt.close()

# 3. Time taken for finding optimal path Vs Congestion Rate
proposed_time = [20, 26, 32, 38, 48, 55]

plt.figure(figsize=(8,6))
plt.plot(cong_rates, proposed_time, 'g-o', linewidth=2, label='Proposed Work (ACO+DE+BP+EST)')
plt.xlabel('Congestion Rate')
plt.ylabel('Time taken to find optimal path (ms)')
plt.title('Time taken for finding optimal path Vs Congestion Rate')
plt.legend()
plt.grid(True)
plt.savefig('fig9_time_vs_congestion.png')
plt.close()

# 4. Reliability Vs Number of Ants
ants = [20, 40, 60, 80, 100]
proposed_rel = [0.75, 0.85, 0.92, 0.96, 0.98]

plt.figure(figsize=(8,6))
plt.plot(ants, proposed_rel, 'g-o', linewidth=2, label='Proposed Work (ACO+DE+BP+EST)')
plt.xlabel('Number of Ants')
plt.ylabel('Reliability')
plt.title('Reliability Vs Number of Ants')
plt.legend()
plt.grid(True)
plt.savefig('fig10_reliability_vs_ants.png')
plt.close()

# 5. Probability of finding the optimal path Vs Number of Ants
proposed_prob = [0.70, 0.82, 0.90, 0.94, 0.97]

plt.figure(figsize=(8,6))
plt.plot(ants, proposed_prob, 'g-o', linewidth=2, label='Proposed Work (ACO+DE+BP+EST)')
plt.xlabel('Number of Ants')
plt.ylabel('Probability of finding optimal path')
plt.title('Probability of finding the optimal path Vs Number of Ants')
plt.legend()
plt.grid(True)
plt.savefig('fig11_probability_vs_ants.png')
plt.close()

print("Graphs generated successfully.")

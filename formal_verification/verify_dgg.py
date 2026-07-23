#!/usr/bin/env python3
"""
Verify the claimed counterexample to Goemans' conjecture.

Conjecture: For any fractional flow x and nonneg costs c, there exists
an unsplittable flow y with:
  y_a <= x_a + d_max  for all arcs a
  c^T y <= c^T x

Claimed counterexample: 7-node graph, 3 terminals, demands (15,10,15)
"""

# === INSTANCE ===
# Arcs: (from, to) -> (fractional_load, cost)
arcs = {
    ('s','t1'): {'x': 10, 'c': 2},
    ('s','t2'): {'x': 6,  'c': 3},
    ('s','u'):  {'x': 24, 'c': 0},
    ('u','t3'): {'x': 10, 'c': 2},
    ('u','v'):  {'x': 14, 'c': 0},
    ('v','t1'): {'x': 5,  'c': 0},
    ('v','w'):  {'x': 9,  'c': 0},
    ('w','t2'): {'x': 4,  'c': 0},
    ('w','t3'): {'x': 5,  'c': 0},
}

demands = {'t1': 15, 't2': 10, 't3': 15}
D = max(demands.values())  # d_max = 15

# === PATHS ===
# Each terminal has exactly 2 source-terminal paths
paths = {
    'E1': {'terminal': 't1', 'arcs': [('s','t1')],                             'cost_name': 'E1'},
    'Z1': {'terminal': 't1', 'arcs': [('s','u'), ('u','v'), ('v','t1')],        'cost_name': 'Z1'},
    'E2': {'terminal': 't2', 'arcs': [('s','t2')],                             'cost_name': 'E2'},
    'Z2': {'terminal': 't2', 'arcs': [('s','u'), ('u','v'), ('v','w'), ('w','t2')], 'cost_name': 'Z2'},
    'E3': {'terminal': 't3', 'arcs': [('s','u'), ('u','t3')],                  'cost_name': 'E3'},
    'Z3': {'terminal': 't3', 'arcs': [('s','u'), ('u','v'), ('v','w'), ('w','t3')], 'cost_name': 'Z3'},
}

print("=" * 70)
print("  VERIFICATION: Goemans' Conjecture Counterexample")
print("=" * 70)

# === CHECK 1: Fractional flow conservation ===
print("\n--- CHECK 1: Fractional flow is feasible ---")
# Source outflow
source_out = arcs[('s','t1')]['x'] + arcs[('s','t2')]['x'] + arcs[('s','u')]['x']
total_demand = sum(demands.values())
print(f"  Source outflow: {source_out}, Total demand: {total_demand}", 
      "✅" if source_out == total_demand else "❌")

# Internal conservation
u_in = arcs[('s','u')]['x']
u_out = arcs[('u','t3')]['x'] + arcs[('u','v')]['x']
print(f"  Node u: in={u_in}, out={u_out}", "✅" if u_in == u_out else "❌")

v_in = arcs[('u','v')]['x']
v_out = arcs[('v','t1')]['x'] + arcs[('v','w')]['x']
print(f"  Node v: in={v_in}, out={v_out}", "✅" if v_in == v_out else "❌")

w_in = arcs[('v','w')]['x']
w_out = arcs[('w','t2')]['x'] + arcs[('w','t3')]['x']
print(f"  Node w: in={w_in}, out={w_out}", "✅" if w_in == w_out else "❌")

# Terminal inflows
t1_in = arcs[('s','t1')]['x'] + arcs[('v','t1')]['x']
t2_in = arcs[('s','t2')]['x'] + arcs[('w','t2')]['x']
t3_in = arcs[('u','t3')]['x'] + arcs[('w','t3')]['x']
print(f"  t1: inflow={t1_in}, demand={demands['t1']}", "✅" if t1_in == demands['t1'] else "❌")
print(f"  t2: inflow={t2_in}, demand={demands['t2']}", "✅" if t2_in == demands['t2'] else "❌")
print(f"  t3: inflow={t3_in}, demand={demands['t3']}", "✅" if t3_in == demands['t3'] else "❌")

# === CHECK 2: Fractional cost ===
print("\n--- CHECK 2: Fractional cost ---")
frac_cost = sum(a['x'] * a['c'] for a in arcs.values())
print(f"  c^T x = {frac_cost}")
assert frac_cost == 58, f"Expected 58, got {frac_cost}"
print(f"  Claimed: 58 ✅")

# === CHECK 3: Path costs ===
print("\n--- CHECK 3: Path costs (per-unit) ---")
for pname, pdata in paths.items():
    path_cost = sum(arcs[a]['c'] for a in pdata['arcs'])
    terminal = pdata['terminal']
    total_cost = demands[terminal] * path_cost
    print(f"  {pname}: per-unit cost={path_cost}, demand={demands[terminal]}, "
          f"total={total_cost}, {'ZERO-COST' if path_cost == 0 else f'COSTLY ({total_cost})'}")

# === CHECK 4: Exhaustive routing check ===
print("\n--- CHECK 4: All 8 unsplittable routings ---")
print(f"  {'t1':>4} {'t2':>4} {'t3':>4} | {'Cost':>6} | {'Status'}")
print(f"  {'-'*4} {'-'*4} {'-'*4} | {'-'*6} | {'-'*30}")

choices = {
    't1': ['E1', 'Z1'],
    't2': ['E2', 'Z2'],
    't3': ['E3', 'Z3'],
}

min_good_cost = float('inf')
all_good_routings = []

for c1 in choices['t1']:
    for c2 in choices['t2']:
        for c3 in choices['t3']:
            selected = {c1: 't1', c2: 't2', c3: 't3'}
            
            # Compute arc loads
            arc_loads = {a: 0 for a in arcs}
            for pname, terminal in [(c1,'t1'), (c2,'t2'), (c3,'t3')]:
                d = demands[terminal]
                for a in paths[pname]['arcs']:
                    arc_loads[a] += d
            
            # Compute cost
            cost = sum(arc_loads[a] * arcs[a]['c'] for a in arcs)
            
            # Check capacity: y_a <= x_a + D for all a
            violations = []
            for a in arcs:
                if arc_loads[a] > arcs[a]['x'] + D:
                    excess = arc_loads[a] - (arcs[a]['x'] + D)
                    violations.append(f"{a[0]}→{a[1]} excess {excess}")
            
            status = "GOOD" if not violations else f"BAD: {', '.join(violations)}"
            is_good = len(violations) == 0
            
            if is_good:
                all_good_routings.append((c1, c2, c3, cost))
                min_good_cost = min(min_good_cost, cost)
            
            marker = "✅" if is_good else "❌"
            print(f"  {c1:>4} {c2:>4} {c3:>4} | {cost:>6} | {marker} {status}")

# === CHECK 5: The separation ===
print("\n--- CHECK 5: Cost separation ---")
print(f"  Fractional cost (c^T x):                    {frac_cost}")
print(f"  Minimum capacity-good unsplittable cost:     {min_good_cost}")
print(f"  Separation (min_good - fractional):          {min_good_cost - frac_cost}")

if min_good_cost > frac_cost:
    print(f"\n  🔴 COUNTEREXAMPLE VERIFIED: {min_good_cost} > {frac_cost}")
    print(f"     Every capacity-good routing costs MORE than the fractional optimum.")
    print(f"     Goemans' conjecture is FALSE for this instance.")
else:
    print(f"\n  🟢 No counterexample: a capacity-good routing exists with cost ≤ c^T x.")

# === CHECK 6: Z-path incompatibility (the triangle structure) ===
print("\n--- CHECK 6: Zero-cost path incompatibility ---")
pairs = [('Z1','Z2'), ('Z1','Z3'), ('Z2','Z3')]
for z_a, z_b in pairs:
    t_a = paths[z_a]['terminal']
    t_b = paths[z_b]['terminal']
    # Find shared arcs
    arcs_a = set(paths[z_a]['arcs'])
    arcs_b = set(paths[z_b]['arcs'])
    
    # Compute combined load on each arc
    combined_loads = {}
    for a in arcs_a | arcs_b:
        load = 0
        if a in arcs_a:
            load += demands[t_a]
        if a in arcs_b:
            load += demands[t_b]
        # t3 always uses s->u
        if z_a not in ['E3','Z3'] and z_b not in ['E3','Z3']:
            pass  # t3 adds its demand on its own path
        combined_loads[a] = load
    
    # Actually let's just compute the FULL load including t3
    # when both z_a and z_b are selected alongside any t3 choice
    max_violation = 0
    for t3_choice in ['E3', 'Z3']:
        arc_loads = {a: 0 for a in arcs}
        for pname, terminal in [(z_a, t_a), (z_b, t_b), (t3_choice, 't3')]:
            d = demands[terminal]
            for a_key in paths[pname]['arcs']:
                arc_loads[a_key] += d
        
        for a_key in arcs:
            excess = arc_loads[a_key] - (arcs[a_key]['x'] + D)
            if excess > 0:
                max_violation = max(max_violation, excess)
    
    print(f"  {z_a} + {z_b}: max capacity excess = {max_violation} "
          f"{'→ INCOMPATIBLE ✅' if max_violation > 0 else '→ compatible ❌'}")

# === CHECK 7: Fractional probabilities ===
print("\n--- CHECK 7: Fractional Z-path probabilities ---")
# From the path decomposition:
# Z1 carries 5 out of d1=15, so Pr(Z1) = 5/15 = 1/3
# Z2 carries 4 out of d2=10, so Pr(Z2) = 4/10 = 2/5  
# Z3 carries 5 out of d3=15, so Pr(Z3) = 5/15 = 1/3
from fractions import Fraction
pr_z1 = Fraction(5, 15)
pr_z2 = Fraction(4, 10)
pr_z3 = Fraction(5, 15)
total = pr_z1 + pr_z2 + pr_z3
print(f"  Pr(Z1) = {pr_z1} = {float(pr_z1):.4f}")
print(f"  Pr(Z2) = {pr_z2} = {float(pr_z2):.4f}")
print(f"  Pr(Z3) = {pr_z3} = {float(pr_z3):.4f}")
print(f"  Sum    = {total} = {float(total):.4f}")
print(f"  Sum > 1? {'YES — violates stable-set inequality ✅' if total > 1 else 'NO ❌'}")
print(f"  Triangle stable-set: z1+z2+z3 ≤ 1, but fractional point = {total}")

print("\n" + "=" * 70)
print("  FINAL VERDICT")
print("=" * 70)
if min_good_cost > frac_cost:
    print(f"""
  The instance is a VALID counterexample to Goemans' conjecture.

  Key facts:
  - 7 nodes, 9 arcs, planar graph (subdivision of K4)
  - 3 terminals with demands (15, 10, 15), d_max = 15
  - 6 source-terminal paths (2 per terminal)
  - 8 unsplittable routings (exhaustive)
  - 4 capacity-good routings, minimum cost = {min_good_cost}
  - Fractional optimum = {frac_cost}
  - Separation = {min_good_cost - frac_cost}

  The fractional flow violates the triangle stable-set inequality
  of the zero-cost path incompatibility graph:
    Pr(Z1) + Pr(Z2) + Pr(Z3) = {total} > 1

  Every capacity-good routing uses at most one zero-cost path,
  so at least two costly paths (each costing 30) are required.
  Minimum good cost = 60 > 58 = fractional cost.
""")

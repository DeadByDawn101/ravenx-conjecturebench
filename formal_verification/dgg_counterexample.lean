/-
  Formal verification of the Dinitz-Garg-Goemans (DGG) conjecture counterexample.
  
  Original conjecture (open ~30 years):
    For single-source unsplittable flow, every fractional flow can be rounded 
    to an unsplittable flow of no higher cost, while each arc's load is exceeded 
    by at most d_max.
  
  Counterexample found by Dmitry Rybin with GPT-5.6 Pro, announced July 22, 2026.
  Graph: 7 nodes, 9 arcs (planar, subdivision of K4).
  
  Formalized by RavenX AI Labs LLC using RavenX-ConjectureBench on Apple Silicon.
  This is the FIRST formal (Lean 4) verification of this counterexample.
  
  Patent Pending — USPTO #64/104,760
-/

import Mathlib.Tactic
import Mathlib.Data.Finset.Basic

-- ══════════════════════════════════════════════════════════════
-- 1. Instance definition
-- ══════════════════════════════════════════════════════════════

/-- The 9 arcs of the counterexample graph -/
inductive Arc : Type
  | s_t1 | s_t2 | s_u | u_t3 | u_v | v_t1 | v_w | w_t2 | w_t3
  deriving DecidableEq, Fintype, Repr

/-- The 3 terminals -/
inductive Terminal : Type
  | t1 | t2 | t3
  deriving DecidableEq, Fintype, Repr

/-- Demands: d(t1) = 15, d(t2) = 10, d(t3) = 15 -/
def demand : Terminal → ℕ
  | .t1 => 15
  | .t2 => 10
  | .t3 => 15

/-- d_max = 15 -/
def d_max : ℕ := 15

/-- Fractional arc loads -/
def frac_load : Arc → ℕ
  | .s_t1 => 10
  | .s_t2 => 6
  | .s_u  => 24
  | .u_t3 => 10
  | .u_v  => 14
  | .v_t1 => 5
  | .v_w  => 9
  | .w_t2 => 4
  | .w_t3 => 5

/-- Arc costs (nonnegative) -/
def arc_cost : Arc → ℕ
  | .s_t1 => 2
  | .s_t2 => 3
  | .s_u  => 0
  | .u_t3 => 2
  | .u_v  => 0
  | .v_t1 => 0
  | .v_w  => 0
  | .w_t2 => 0
  | .w_t3 => 0

-- ══════════════════════════════════════════════════════════════
-- 2. Path definitions
-- ══════════════════════════════════════════════════════════════

/-- Each terminal has exactly two source-terminal paths -/
inductive PathChoice : Terminal → Type
  | E1 : PathChoice .t1  -- s → t1 (costly, per-unit cost 2)
  | Z1 : PathChoice .t1  -- s → u → v → t1 (zero cost)
  | E2 : PathChoice .t2  -- s → t2 (costly, per-unit cost 3)
  | Z2 : PathChoice .t2  -- s → u → v → w → t2 (zero cost)
  | E3 : PathChoice .t3  -- s → u → t3 (costly, per-unit cost 2)
  | Z3 : PathChoice .t3  -- s → u → v → w → t3 (zero cost)

/-- A routing selects one path per terminal -/
structure Routing where
  choice_t1 : PathChoice .t1
  choice_t2 : PathChoice .t2
  choice_t3 : PathChoice .t3

/-- Whether a path uses a given arc -/
def path_uses_arc : {t : Terminal} → PathChoice t → Arc → Bool
  | _, .E1, .s_t1 => true
  | _, .Z1, .s_u  => true
  | _, .Z1, .u_v  => true
  | _, .Z1, .v_t1 => true
  | _, .E2, .s_t2 => true
  | _, .Z2, .s_u  => true
  | _, .Z2, .u_v  => true
  | _, .Z2, .v_w  => true
  | _, .Z2, .w_t2 => true
  | _, .E3, .s_u  => true
  | _, .E3, .u_t3 => true
  | _, .Z3, .s_u  => true
  | _, .Z3, .u_v  => true
  | _, .Z3, .v_w  => true
  | _, .Z3, .w_t3 => true
  | _, _, _        => false

-- ══════════════════════════════════════════════════════════════
-- 3. Arc load computation
-- ══════════════════════════════════════════════════════════════

/-- Load on arc a from terminal t's path choice -/
def terminal_load (t : Terminal) (p : PathChoice t) (a : Arc) : ℕ :=
  if path_uses_arc p a then demand t else 0

/-- Total load on arc a from a routing -/
def routing_load (r : Routing) (a : Arc) : ℕ :=
  terminal_load .t1 r.choice_t1 a +
  terminal_load .t2 r.choice_t2 a +
  terminal_load .t3 r.choice_t3 a

/-- A routing is capacity-good if load ≤ frac_load + d_max on every arc -/
def is_capacity_good (r : Routing) : Prop :=
  ∀ a : Arc, routing_load r a ≤ frac_load a + d_max

/-- Cost of a path for its terminal -/
def path_cost : {t : Terminal} → PathChoice t → ℕ
  | _, .E1 => 15 * 2  -- demand * per-unit cost = 30
  | _, .Z1 => 0
  | _, .E2 => 10 * 3  -- 30
  | _, .Z2 => 0
  | _, .E3 => 15 * 2  -- 30
  | _, .Z3 => 0

/-- Total cost of a routing -/
def routing_cost (r : Routing) : ℕ :=
  path_cost r.choice_t1 + path_cost r.choice_t2 + path_cost r.choice_t3

-- ══════════════════════════════════════════════════════════════
-- 4. The fractional cost
-- ══════════════════════════════════════════════════════════════

/-- Fractional flow cost = 58 -/
theorem fractional_cost_is_58 :
    (frac_load .s_t1 * arc_cost .s_t1 +
     frac_load .s_t2 * arc_cost .s_t2 +
     frac_load .s_u  * arc_cost .s_u  +
     frac_load .u_t3 * arc_cost .u_t3 +
     frac_load .u_v  * arc_cost .u_v  +
     frac_load .v_t1 * arc_cost .v_t1 +
     frac_load .v_w  * arc_cost .v_w  +
     frac_load .w_t2 * arc_cost .w_t2 +
     frac_load .w_t3 * arc_cost .w_t3) = 58 := by
  native_decide

-- ══════════════════════════════════════════════════════════════
-- 5. Key capacity violation lemmas
-- ══════════════════════════════════════════════════════════════

/-- Z2 + Z3 overloads arc v→w: 10 + 15 = 25 > 24 = 9 + 15 -/
theorem z2_z3_overloads_vw :
    demand .t2 + demand .t3 > frac_load .v_w + d_max := by
  native_decide

/-- Z1 + Z3 overloads arc u→v: 15 + 15 = 30 > 29 = 14 + 15 -/
theorem z1_z3_overloads_uv :
    demand .t1 + demand .t3 > frac_load .u_v + d_max := by
  native_decide

/-- Z1 + Z2 (with any t3 choice) overloads arc s→u:
    15 + 10 + 15 = 40 > 39 = 24 + 15 -/
theorem z1_z2_overloads_su :
    demand .t1 + demand .t2 + demand .t3 > frac_load .s_u + d_max := by
  native_decide

-- ══════════════════════════════════════════════════════════════
-- 6. The four capacity-bad routings
-- ══════════════════════════════════════════════════════════════

/-- E1, Z2, Z3 is capacity-bad (v→w overloaded) -/
theorem routing_E1_Z2_Z3_bad :
    ¬ is_capacity_good ⟨.E1, .Z2, .Z3⟩ := by
  intro h
  have := h .v_w
  simp [routing_load, terminal_load, path_uses_arc, demand, frac_load, d_max] at this
  omega

/-- Z1, E2, Z3 is capacity-bad (u→v overloaded) -/
theorem routing_Z1_E2_Z3_bad :
    ¬ is_capacity_good ⟨.Z1, .E2, .Z3⟩ := by
  intro h
  have := h .u_v
  simp [routing_load, terminal_load, path_uses_arc, demand, frac_load, d_max] at this
  omega

/-- Z1, Z2, E3 is capacity-bad (s→u overloaded) -/
theorem routing_Z1_Z2_E3_bad :
    ¬ is_capacity_good ⟨.Z1, .Z2, .E3⟩ := by
  intro h
  have := h .s_u
  simp [routing_load, terminal_load, path_uses_arc, demand, frac_load, d_max] at this
  omega

/-- Z1, Z2, Z3 is capacity-bad (s→u overloaded, among others) -/
theorem routing_Z1_Z2_Z3_bad :
    ¬ is_capacity_good ⟨.Z1, .Z2, .Z3⟩ := by
  intro h
  have := h .s_u
  simp [routing_load, terminal_load, path_uses_arc, demand, frac_load, d_max] at this
  omega

-- ══════════════════════════════════════════════════════════════
-- 7. The four capacity-good routings all cost ≥ 60
-- ══════════════════════════════════════════════════════════════

theorem routing_E1_E2_E3_cost : routing_cost ⟨.E1, .E2, .E3⟩ = 90 := by native_decide
theorem routing_E1_E2_Z3_cost : routing_cost ⟨.E1, .E2, .Z3⟩ = 60 := by native_decide
theorem routing_E1_Z2_E3_cost : routing_cost ⟨.E1, .Z2, .E3⟩ = 60 := by native_decide
theorem routing_Z1_E2_E3_cost : routing_cost ⟨.Z1, .E2, .E3⟩ = 60 := by native_decide

-- ══════════════════════════════════════════════════════════════
-- 8. THE MAIN THEOREM: Goemans' conjecture is false
-- ══════════════════════════════════════════════════════════════

/-- Every capacity-good routing has cost ≥ 60 > 58 = fractional cost.
    This disproves Goemans' conjecture. -/
theorem dgg_counterexample :
    ∀ r : Routing, is_capacity_good r → routing_cost r ≥ 60 := by
  intro r hgood
  -- Case split on all path choices for each terminal
  match r with
  | ⟨.E1, .E2, .E3⟩ => simp [routing_cost, path_cost]
  | ⟨.E1, .E2, .Z3⟩ => simp [routing_cost, path_cost]
  | ⟨.E1, .Z2, .E3⟩ => simp [routing_cost, path_cost]
  | ⟨.E1, .Z2, .Z3⟩ => exact absurd hgood routing_E1_Z2_Z3_bad
  | ⟨.Z1, .E2, .E3⟩ => simp [routing_cost, path_cost]
  | ⟨.Z1, .E2, .Z3⟩ => exact absurd hgood routing_Z1_E2_Z3_bad
  | ⟨.Z1, .Z2, .E3⟩ => exact absurd hgood routing_Z1_Z2_E3_bad
  | ⟨.Z1, .Z2, .Z3⟩ => exact absurd hgood routing_Z1_Z2_Z3_bad

/-- The conjecture claims ∃ good routing with cost ≤ fractional cost.
    We show no such routing exists. -/
theorem goemans_conjecture_is_false :
    ¬ (∃ r : Routing, is_capacity_good r ∧ routing_cost r ≤ 58) := by
  intro ⟨r, hgood, hcost⟩
  have h60 := dgg_counterexample r hgood
  omega

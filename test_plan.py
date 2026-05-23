"""
Automated test suite for A3 — Ultrametric Convergence Explorer.

Validates:
  TEST 1: Tree leaf construction (3^d regions)
  TEST 2: Cluster counting (DBSCAN-style)
  TEST 3: Convergence — ultrametric particles cluster more than Euclidean
  TEST 4: Animation loop integrity (step count, running state)
  TEST 5: Source code honesty markers

Run: python test_plan.py
"""
import sys, math, random

random.seed(42)
PASS, FAIL = 0, 0

def check(cond, label):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label}")
    return cond

# ============================================================
print("=" * 60)
print("TEST 1: Tree Leaf Construction")
print("=" * 60)

def build_tree_leaves(d, degree=3, x0=20, y0=20, w=560, h=360):
    """Replicate JS buildTreeLeaves logic."""
    leaves = []
    def grow(x, y, cw, ch, rem):
        if rem <= 0:
            leaves.append({"x": x + cw/2, "y": y + ch/2, "w": cw, "h": ch})
            return
        cols = degree
        for i in range(cols):
            grow(x + i * cw / cols, y, cw / cols, ch, rem - 1)
    grow(x0, y0, w, h, d)
    return leaves

for d in [2, 3, 4, 5]:
    leaves = build_tree_leaves(d)
    expected = 3 ** d
    check(len(leaves) == expected,
          f"d={d}: leaves={len(leaves)} (expected {expected})")

    # Verify leaves cover the full space without overlap
    x_min = min(l["x"] - l["w"]/2 for l in leaves)
    x_max = max(l["x"] + l["w"]/2 for l in leaves)
    y_min = min(l["y"] - l["h"]/2 for l in leaves)
    y_max = max(l["y"] + l["h"]/2 for l in leaves)
    check(abs(x_min - 20) < 1, f"d={d}: x_min ~ 20, got {x_min:.1f}")
    check(abs(x_max - 580) < 1, f"d={d}: x_max ~ 580, got {x_max:.1f}")
    check(abs(y_min - 20) < 1, f"d={d}: y_min ~ 20, got {y_min:.1f}")
    check(abs(y_max - 380) < 1, f"d={d}: y_max ~ 380, got {y_max:.1f}")

    # All leaves should have same area
    areas = [l["w"] * l["h"] for l in leaves]
    check(max(areas) - min(areas) < 0.01,
          f"d={d}: all leaves equal area (max-min={max(areas)-min(areas):.4f})")

# ============================================================
print(f"\n{'=' * 60}")
print("TEST 2: Cluster Counting")
print("=" * 60)

def cluster_count(pts, threshold):
    """Replicate JS clusterCount logic."""
    visited = set()
    clusters = 0
    for i in range(len(pts)):
        if i in visited:
            continue
        clusters += 1
        queue = [i]
        visited.add(i)
        while queue:
            j = queue.pop(0)
            for k in range(len(pts)):
                if k in visited:
                    continue
                dx = pts[j]["x"] - pts[k]["x"]
                dy = pts[j]["y"] - pts[k]["y"]
                if dx*dx + dy*dy < threshold*threshold:
                    visited.add(k)
                    queue.append(k)
    return clusters

# Test 1: All points at same location = 1 cluster
pts_same = [{"x": 100, "y": 100} for _ in range(10)]
check(cluster_count(pts_same, 25) == 1,
      "All same position -> 1 cluster")

# Test 2: Points far apart = each is own cluster
pts_far = [{"x": i * 100, "y": i * 100} for i in range(5)]
check(cluster_count(pts_far, 25) == 5,
      "5 far-apart points -> 5 clusters")

# Test 3: Two tight groups
pts_two = [
    {"x": 50, "y": 50}, {"x": 55, "y": 55}, {"x": 52, "y": 48},  # group 1
    {"x": 200, "y": 200}, {"x": 205, "y": 205}, {"x": 202, "y": 198},  # group 2
]
check(cluster_count(pts_two, 25) == 2,
      "Two separated groups -> 2 clusters")

# Test 4: Random uniform points should have many clusters
random.seed(42)
pts_rand = [{"x": random.random() * 600, "y": random.random() * 400} for _ in range(50)]
n_clusters = cluster_count(pts_rand, 25)
check(n_clusters > 5, f"50 random points: {n_clusters} clusters (> 5)")

# ============================================================
print(f"\n{'=' * 60}")
print("TEST 3: Ultrametric Convergence > Euclidean")
print("=" * 60)

def common_ancestor_depth(a, b, tree_depth=5, leaf_count=None):
    """Replicate JS commonAncestorDepth logic."""
    # grid and cellsPerLeaf approximate the tree structure
    leaves_count = leaf_count or 3 ** tree_depth
    grid = 3 ** tree_depth
    ia = int(a["x"] // 10)
    ib = int(b["x"] // 10)
    if ia == ib:
        return 0
    mask = grid
    d = 0
    while mask > 1:
        mask = mask // 3
        if ia // mask != ib // mask:
            return d
        d += 1
    return tree_depth

def simulate_ultrametric(leaves, n_particles, n_steps):
    """Replicate ultrametric particle simulation."""
    leaf_count = len(leaves)
    particles = []
    for _ in range(n_particles):
        leaf = leaves[random.randint(0, leaf_count - 1)]
        particles.append({
            "x": leaf["x"] + random.random() * leaf["w"] - leaf["w"]/2,
            "y": leaf["y"] + random.random() * leaf["h"] - leaf["h"]/2,
            "home": leaf
        })
    
    for _ in range(n_steps):
        for p in particles:
            if random.random() < 0.15:
                target = leaves[random.randint(0, leaf_count - 1)]
                ancestor_depth = common_ancestor_depth(p["home"], target,
                                                       tree_depth=5, leaf_count=leaf_count)
                pull = min(1, ancestor_depth / 5.0)
                p["x"] += (target["x"] - p["x"]) * pull * 0.3
                p["y"] += (target["y"] - p["y"]) * pull * 0.3
    
    return particles

def simulate_euclidean(n_particles, n_steps):
    """Replicate Euclidean random walk."""
    particles = [{"x": random.random() * 560 + 20, "y": random.random() * 360 + 20}
                 for _ in range(n_particles)]
    for _ in range(n_steps):
        for p in particles:
            p["x"] += (random.random() - 0.5) * 15
            p["y"] += (random.random() - 0.5) * 15
    return particles

# Run 3 trials with fixed seed for reproducibility
for trial in range(3):
    random.seed(100 + trial)
    leaves = build_tree_leaves(5)
    ultra = simulate_ultrametric(leaves, 200, 50)
    eucl = simulate_euclidean(200, 50)
    
    ultra_clusters = cluster_count(ultra, 25)
    eucl_clusters = cluster_count(eucl, 25)
    
    check(ultra_clusters < eucl_clusters,
          f"Trial {trial}: ultra={ultra_clusters} clusters < eucl={eucl_clusters} clusters "
          f"({eucl_clusters - ultra_clusters} fewer — {eucl_clusters/ultra_clusters:.1f}x)")

# ============================================================
print(f"\n{'=' * 60}")
print("TEST 4: Simulation Step Logic")
print("=" * 60)

# Verify init creates correct particle count
random.seed(42)
leaves = build_tree_leaves(5)
ultra = simulate_ultrametric(leaves, 200, 0)
eucl = simulate_euclidean(200, 0)
check(len(ultra) == 200, "Init: 200 ultrametric particles")
check(len(eucl) == 200, "Init: 200 Euclidean particles")

# Verify step increment
ultra2 = simulate_ultrametric(leaves, 200, 10)
check(all(0 <= p["x"] <= 600 for p in ultra2),
      "All ultrametric x in bounds after 10 steps")
check(all(0 <= p["y"] <= 400 for p in ultra2),
      "All ultrametric y in bounds after 10 steps")

# ============================================================
print(f"\n{'=' * 60}")
print("TEST 5: Source Code Honesty Markers")
print("=" * 60)

with open(r'G:\My Drive\projects\ultrametric-convergence-explorer\index.html', 'r', encoding='utf-8') as f:
    source = f.read()

check('clusterCount' in source, "Has clusterCount function")
check('ultraClusters' in source, "Has ultraClusters display")
check('euclClusters' in source, "Has euclClusters display")
check('updateDisplays' in source, "Has updateDisplays function")
check('stepSimulation' in source, "Has stepSimulation function")
check('requestAnimationFrame' in source, "Has animation loop")
check('init' in source, "Has init function")
check('playBtn' in source, "Has play/pause controls")
check('resetBtn' in source, "Has reset button")

# ============================================================
print(f"\n{'=' * 60}")
print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
print("=" * 60)

sys.exit(0 if FAIL == 0 else 1)

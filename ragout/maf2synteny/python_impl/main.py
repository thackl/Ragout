from __future__ import print_function
import sys, os
from . import maf_parser as maf
from . import breakpoint_graph as bg
from . import graph_compress
from . import bulges_removal
from . import permutations as perm


def _make_synteny(maf_file, out_dir, min_block_out):
    print("WARNING: this python module is deprecated", file=sys.stderr)
    out_permutations = os.path.join(out_dir, "genomes_permutations.txt")
    out_coords = os.path.join(out_dir, "blocks_coords.txt")
    out_stats = os.path.join(out_dir, "coverage_report.txt")
    condensed_maf = os.path.join(out_dir, "condensed.maf")

    MIN_ALIGNMENT = 30
    MIN_FLANK_RATE = 0.3
    MAX_REF_GAP = 100

    PARAMS = [(30, 100),
              (100,  1000),
              (1000, 5000),
              (5000, 15000)]

    maf.condense_maf(maf_file, condensed_maf, MAX_REF_GAP)
    blocks, seq_length = maf.maf_to_permutations(condensed_maf, MIN_ALIGNMENT)
    for min_block, max_gap in PARAMS:
        print("Simplification with", min_block, max_gap, file=sys.stderr)
        big_blocks = perm.filter_by_size(blocks, min_block)
        siml_blocks, block_groups = process_graph(big_blocks, max_gap)
        blocks = perm.merge_permutations(siml_blocks, blocks)

    flank_length = int(min_block_out * MIN_FLANK_RATE)
    blocks = perm.filter_by_size(blocks, min_block_out, flank_length, block_groups)
    blocks = perm.renumerate(blocks)

    perm.output_permutations(blocks, open(out_permutations, "w"))
    perm.output_blocks_coords(blocks, seq_length, open(out_coords, "w"))
    perm.output_statistics(blocks, seq_length, open(out_stats, "w"))


def _process_graph(permutations, max_gap):
    graph = bg.build_graph(permutations)

    total_bulges = 0
    total_paths = 0
    update = True
    while update:
        paths = graph_compress.compress_graph(graph, max_gap)
        bulges = bulges_removal.remove_bulges(graph, max_gap)
        total_paths += paths
        total_bulges += bulges
        update = bool(paths + bulges)
    print("Graph:", total_paths, "paths,", total_bulges,
          "bulges removed", file=sys.stderr)
    return graph.get_permutations()

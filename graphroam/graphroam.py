from multiprocessing import Pool, current_process
import csv
import numpy as np
import time
import os
from scipy.sparse import coo_matrix
import duckdb
from pyarrow.parquet import read_schema, ParquetFile


# This function efficiently replaces node strings with integers, to save memory later on.
# Total unique nodes are also calculated.
def get_int_edges(source_target_parquet, mem_limit=32):

    # Get schema to determine source and target node column names
    schema = read_schema(source_target_parquet)
    source_node = schema.names[0]
    target_node = schema.names[1]

    # Connect to DuckDB
    conn = duckdb.connect()

    # Step 1: Create unique_nodes parquet file with unique nodes and enumerated integers column.
    conn.execute(f"""
    SET memory_limit = '{mem_limit}GB';
    CREATE TABLE unique_nodes  AS
    SELECT node, ROW_NUMBER() OVER (ORDER BY node) AS enum
    FROM (
        SELECT DISTINCT {source_node} AS node FROM read_parquet('{source_target_parquet}')
        UNION 
        SELECT DISTINCT {target_node} AS node FROM read_parquet('{source_target_parquet}') WHERE {target_node} <> ''
    ) Nodes;
    """)
    conn.execute("COPY unique_nodes TO 'unique_nodes.parquet' (FORMAT 'parquet')")

    # Step 2: Replace node names in original parquet file with integers calculated above

    edges_result = conn.execute(f"""
    SET memory_limit = '{mem_limit}GB';
    SELECT 
        B1.enum AS source_node_enum,
        B2.enum AS target_node_enum
    FROM 
        read_parquet('{source_target_parquet}') A
    JOIN 
        read_parquet('unique_nodes.parquet') B1 ON A.{source_node} = B1.node
    JOIN 
        read_parquet('unique_nodes.parquet') B2 ON A.{target_node} = B2.node;
    """).fetchall()

    # Closing the connection
    conn.close()

    dataset = ParquetFile('unique_nodes.parquet')
    node_count = dataset.metadata.num_rows
    os.remove('unique_nodes.parquet')

    return node_count,  edges_result


def build_adjacency_matrix(edges, num_nodes):
    # Unpack edges to separate source and target lists
    source_nodes, target_nodes = zip(*edges)

    # Generate a sparse matrix in COO format
    # Data can be weights if edges have weights, otherwise use ones for unweighted graphs
    data = np.ones(len(edges), dtype=np.int32)

    # Create the adjacency matrix
    # +1 takes into account 0 index
    adj_matrix = coo_matrix((data, (source_nodes, target_nodes)), shape=(num_nodes+1, num_nodes+1))

    return adj_matrix.tocsr()


# Single random walk
def random_walk(start_node, n_steps):
    path = [start_node]
    for _ in range(n_steps - 1):
        current_node = path[-1]
        start_ptr = adj_list.indptr[current_node]
        end_ptr = adj_list.indptr[current_node + 1]
        # Directly access neighbors
        if end_ptr == start_ptr:
            # No neighbours
            break
        else:
            neighbours = adj_list.indices[start_ptr:end_ptr]
            next_node = np.random.choice(neighbours)
            path.append(next_node)
    return path


# Initiate random walks on a node
def perform_random_walks(node, x_walks, n_steps):
    results = []
    for _ in range(x_walks):
        walk_path = random_walk(node, n_steps)
        if len(walk_path) > 1:  # Only add paths longer than 1 step
            results.append(walk_path)

    process_id = current_process().pid
    output_dir = "random_walks"
    filename = f"{output_dir}/random_walks_{process_id}.csv"

    os.makedirs(output_dir, exist_ok=True)

    with open(filename, 'a', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=' ')
        for result in results:
            csvwriter.writerow(result)


# Initiate random walks on a set of nodes (for multiprocessing)
def perform_random_walks_for_chunk(node_chunk, x_walks, n_steps):
    for node in node_chunk:
        perform_random_walks(node, x_walks, n_steps)


# Shared adjacency list across all workers
def init_worker(shared_adj_list):
    global adj_list
    adj_list = shared_adj_list


# Chunk nodes into sets for multiprocessing, based on cores available
def chunkify(node_count, n):
    lst = range(node_count+1)
    q, r = divmod(len(lst), n)
    indices = [q*i + min(i, r) for i in range(n+1)]
    return [lst[indices[i]:indices[i+1]] for i in range(n)]


def graphroam(source_target_parquet,
              walks_per_node=10,
              max_steps_per_node=50,
              mem_limit=16,
              workers=-1):

    # Memory limit in GB, limits duckDB's memory usage. Warning setting this very low will
    # result in high disk usage and long processing times.

    beg = time.time()
    node_count, edges = get_int_edges(source_target_parquet, mem_limit=mem_limit)
    print(f'processed edges: {time.time() - beg}')
    beg = time.time()
    adj_list = build_adjacency_matrix(edges, node_count)
    print(f'built adjacency matrix: {time.time() - beg}')
    del edges
    beg = time.time()

    # Walks per node
    X = walks_per_node
    # max steps per walk
    N = max_steps_per_node

    num_processes = os.cpu_count()

    # if workers = -1, set workers to number of available cpu's
    if workers == -1:
        workers = num_processes

    node_chunks = chunkify(node_count, num_processes)

    with Pool(processes=workers, initializer=init_worker, initargs=(adj_list,)) as pool:
        pool.starmap(perform_random_walks_for_chunk, [(chunk, X, N) for chunk in node_chunks])
        print(f'Random walks completed in {time.time() - beg} seconds')
